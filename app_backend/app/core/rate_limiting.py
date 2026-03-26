# app/core/rate_limiting.py
"""
Rate limiting middleware and utilities
"""
import time
from typing import Dict, Optional
from fastapi import Request, HTTPException, status
from collections import defaultdict, deque
import asyncio
import logging

logger = logging.getLogger(__name__)

class RateLimiter:
    def __init__(self):
        self.requests: Dict[str, deque] = defaultdict(deque)
        self.otp_attempts: Dict[str, deque] = defaultdict(deque)
        self.locked_accounts: Dict[str, float] = {}
        
    def is_rate_limited(self, key: str, max_requests: int = 100, window: int = 60) -> bool:
        """Check if IP is rate limited"""
        now = time.time()
        requests = self.requests[key]
        
        # Remove old requests outside the window
        while requests and requests[0] <= now - window:
            requests.popleft()
            
        # Check if limit exceeded
        if len(requests) >= max_requests:
            logger.warning(f"Rate limit exceeded for {key}: {len(requests)} requests in {window}s")
            return True
            
        # Add current request
        requests.append(now)
        return False
    
    def is_otp_rate_limited(self, key: str, max_attempts: int = 5, window: int = 300) -> bool:
        """Check if OTP attempts are rate limited (5 attempts per 5 minutes)"""
        now = time.time()
        attempts = self.otp_attempts[key]
        
        # Remove old attempts outside the window
        while attempts and attempts[0] <= now - window:
            attempts.popleft()
            
        # Check if limit exceeded
        if len(attempts) >= max_attempts:
            return True
            
        # Add current attempt
        attempts.append(now)
        return False
    
    def is_account_locked(self, email: str) -> bool:
        """Check if account is temporarily locked"""
        if email in self.locked_accounts:
            lock_until = self.locked_accounts[email]
            if time.time() < lock_until:
                return True
            else:
                # Remove expired lock
                del self.locked_accounts[email]
        return False
    
    def lock_account(self, email: str, duration: int = 900):  # 15 minutes
        """Lock account temporarily"""
        self.locked_accounts[email] = time.time() + duration
        logger.warning(f"Account {email} locked for {duration} seconds")

# Global rate limiter instance
rate_limiter = RateLimiter()

def get_client_ip(request: Request) -> str:
    """Extract client IP from request"""
    # Check for forwarded headers first
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    # Fallback to direct connection
    return request.client.host if request.client else "unknown"

async def rate_limit_middleware(request: Request, call_next):
    """Rate limiting middleware.

    NOTE: In-memory per-worker. With N Gunicorn workers the effective
    per-IP limit is N * max_requests.  For true shared state, enable
    Redis and switch to a Redis-backed counter (Phase 9 improvement).
    """
    from app.core.config import settings

    if settings.ENVIRONMENT in ["development", "testing"]:
        return await call_next(request)

    client_ip = get_client_ip(request)
    path = request.url.path

    if path in ("/health", "/api/v1/health"):
        return await call_next(request)

    # Stricter limits for sensitive endpoints
    auth_paths = ("/api/v1/auth/login", "/api/v1/auth/register",
                  "/api/v1/auth/forgot-password", "/api/v1/auth/reset-password")
    portal_prefix = "/api/v1/supplier-portal/"

    if path in auth_paths:
        if rate_limiter.is_rate_limited(f"auth:{client_ip}", max_requests=15, window=60):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many authentication attempts. Please wait before trying again."
            )
    elif path.startswith(portal_prefix):
        if rate_limiter.is_rate_limited(f"portal:{client_ip}", max_requests=30, window=60):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many requests. Please try again later."
            )

    # General API limit
    if rate_limiter.is_rate_limited(client_ip, max_requests=100, window=60):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many requests. Please try again later."
        )

    return await call_next(request)

def check_otp_rate_limit(email: str) -> None:
    """Check OTP rate limit and raise exception if exceeded"""
    if rate_limiter.is_otp_rate_limited(email, max_attempts=5, window=300):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many OTP attempts. Please wait 5 minutes before trying again."
        )

def check_account_lock(email: str) -> None:
    """Check if account is locked and raise exception if so"""
    if rate_limiter.is_account_locked(email):
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail="Account temporarily locked due to multiple failed attempts. Please try again later."
        )

def lock_account_on_failure(email: str, failed_attempts: int) -> None:
    """Lock account after multiple failed attempts"""
    if failed_attempts >= 5:  # Lock after 5 failed attempts
        rate_limiter.lock_account(email, duration=900)  # 15 minutes
        logger.warning(f"Account {email} locked after {failed_attempts} failed attempts")
