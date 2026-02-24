# app/routers/otp.py
"""OTP endpoints for two-factor authentication"""
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.models.user import User
from app.services.otp_service import otp_service
from app.core.logging import logger

router = APIRouter(prefix="/otp", tags=["OTP"])


class OTPRequest(BaseModel):
    """Request model for OTP generation"""
    purpose: str = "login"


class OTPVerifyRequest(BaseModel):
    """Request model for OTP verification"""
    token: str
    purpose: str = "login"


@router.post("/send")
async def send_otp(
    request: OTPRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Send OTP token to user's email"""
    try:
        result = otp_service.create_otp_token(
            db=db,
            user_id=current_user.id,
            purpose=request.purpose
        )
        
        if result["success"]:
            return {
                "success": True,
                "message": "OTP sent successfully",
                "expires_in_minutes": 5
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["error"]
            )
            
    except Exception as e:
        logger.error(f"Error sending OTP: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send OTP"
        )


@router.post("/verify")
async def verify_otp(
    request: OTPVerifyRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Verify OTP token"""
    try:
        result = otp_service.verify_otp_token(
            db=db,
            user_id=current_user.id,
            token=request.token,
            purpose=request.purpose
        )
        
        if result["success"]:
            return {
                "success": True,
                "message": "OTP verified successfully"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["error"]
            )
            
    except Exception as e:
        logger.error(f"Error verifying OTP: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to verify OTP"
        )


@router.post("/cleanup")
async def cleanup_expired_tokens(
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Clean up expired OTP tokens (admin only)"""
    try:
        count = otp_service.cleanup_expired_tokens(db)
        return {
            "success": True,
            "message": f"Cleaned up {count} expired tokens"
        }
        
    except Exception as e:
        logger.error(f"Error cleaning up tokens: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cleanup tokens"
        )

