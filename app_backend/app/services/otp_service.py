# app/services/otp_service.py
"""OTP Service for sending and verifying OTP codes"""
import secrets
import string
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.otp_token import OTPToken
from app.models.user import User
from app.core.email import send_email
from app.core.logging import logger


class OTPService:
    """Service for OTP operations"""
    
    def __init__(self):
        self.token_length = 6
        self.expiry_minutes = 5
    
    def generate_otp_token(self) -> str:
        """Generate a random 6-digit OTP token"""
        return ''.join(secrets.choice(string.digits) for _ in range(self.token_length))
    
    def create_otp_token(self, db: Session, user_id: int, purpose: str = "login") -> Dict[str, Any]:
        """Create and send OTP token"""
        try:
            # Get user details
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return {"success": False, "error": "User not found"}
            
            # Generate new token
            token = self.generate_otp_token()
            expires_at = datetime.utcnow() + timedelta(minutes=self.expiry_minutes)
            
            # Create OTP record
            otp_token = OTPToken(
                user_id=user_id,
                token=token,
                purpose=purpose,
                expires_at=expires_at,
                is_used=False,
                is_active=True,
                version=1
            )
            
            db.add(otp_token)
            db.commit()
            db.refresh(otp_token)
            
            # Send email
            email_sent = self.send_otp_email(user.email, token, user.full_name)
            
            if email_sent:
                logger.info(f"OTP sent to {user.email} for user {user_id}")
                return {
                    "success": True,
                    "token_id": otp_token.id,
                    "expires_at": expires_at.isoformat(),
                    "message": "OTP sent successfully"
                }
            else:
                # If email failed, mark token as used
                otp_token.is_used = True
                db.commit()
                return {"success": False, "error": "Failed to send email"}
                
        except Exception as e:
            logger.error(f"Error creating OTP token: {e}")
            db.rollback()
            return {"success": False, "error": str(e)}
    
    def verify_otp_token(self, db: Session, user_id: int, token: str, purpose: str = "login") -> Dict[str, Any]:
        """Verify OTP token"""
        try:
            # Find valid token
            otp_token = db.query(OTPToken).filter(
                and_(
                    OTPToken.user_id == user_id,
                    OTPToken.token == token,
                    OTPToken.purpose == purpose,
                    OTPToken.is_active == True,
                    OTPToken.is_used == False,
                    OTPToken.expires_at > datetime.utcnow()
                )
            ).first()
            
            if not otp_token:
                return {"success": False, "error": "Invalid or expired OTP"}
            
            # Mark token as used
            otp_token.is_used = True
            otp_token.updated_at = datetime.utcnow()
            db.commit()
            
            logger.info(f"OTP verified successfully for user {user_id}")
            return {"success": True, "message": "OTP verified successfully"}
            
        except Exception as e:
            logger.error(f"Error verifying OTP token: {e}")
            return {"success": False, "error": str(e)}
    
    def send_otp_email(self, email: str, token: str, user_name: str) -> bool:
        """Send OTP email"""
        try:
            subject = "קוד אימות למערכת ניהול יערות"
            
            # HTML template for OTP email
            html_content = f"""
            <!DOCTYPE html>
            <html dir="rtl" lang="he">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>קוד אימות</title>
                <style>
                    body {{
                        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                        direction: rtl;
                        text-align: right;
                        background-color: #f8f9fa;
                        margin: 0;
                        padding: 20px;
                    }}
                    .container {{
                        max-width: 600px;
                        margin: 0 auto;
                        background-color: white;
                        border-radius: 10px;
                        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                        overflow: hidden;
                    }}
                    .header {{
                        background: linear-gradient(135deg, #0072C6, #4CAF50);
                        color: white;
                        padding: 30px;
                        text-align: center;
                    }}
                    .header h1 {{
                        margin: 0;
                        font-size: 24px;
                        font-weight: bold;
                    }}
                    .content {{
                        padding: 30px;
                    }}
                    .otp-code {{
                        background-color: #f8f9fa;
                        border: 2px dashed #0072C6;
                        border-radius: 8px;
                        padding: 20px;
                        text-align: center;
                        margin: 20px 0;
                    }}
                    .otp-code .code {{
                        font-size: 32px;
                        font-weight: bold;
                        color: #0072C6;
                        letter-spacing: 5px;
                        font-family: 'Courier New', monospace;
                    }}
                    .warning {{
                        background-color: #fff3cd;
                        border: 1px solid #ffeaa7;
                        border-radius: 5px;
                        padding: 15px;
                        margin: 20px 0;
                        color: #856404;
                    }}
                    .footer {{
                        background-color: #f8f9fa;
                        padding: 20px;
                        text-align: center;
                        color: #6c757d;
                        font-size: 14px;
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>🌲 מערכת ניהול יערות</h1>
                        <p>קוד אימות דו-שלבי</p>
                    </div>
                    
                    <div class="content">
                        <h2>שלום {user_name},</h2>
                        <p>קיבלת קוד אימות למערכת ניהול יערות. אנא הזן את הקוד הבא:</p>
                        
                        <div class="otp-code">
                            <div class="code">{token}</div>
                        </div>
                        
                        <div class="warning">
                            <strong>⚠️ חשוב:</strong>
                            <ul>
                                <li>הקוד תקף למשך 5 דקות בלבד</li>
                                <li>אל תשתף את הקוד עם איש</li>
                                <li>אם לא ביקשת קוד זה, התעלם מהמייל</li>
                            </ul>
                        </div>
                        
                        <p>אם לא ביקשת קוד זה, אנא התעלם מהמייל או צור קשר עם התמיכה הטכנית.</p>
                    </div>
                    
                    <div class="footer">
                        <p>זהו מייל אוטומטי, אנא אל תשיב עליו</p>
                        <p>© 2025 מערכת ניהול יערות - Forewise</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            # Plain text version
            text_content = f"""
            שלום {user_name},
            
            קיבלת קוד אימות למערכת ניהול יערות.
            
            קוד האימות שלך: {token}
            
            הקוד תקף למשך 5 דקות בלבד.
            
            אם לא ביקשת קוד זה, אנא התעלם מהמייל.
            
            מערכת ניהול יערות - Forewise
            """
            
            # Send email
            success = send_email(
                to_email=email,
                subject=subject,
                html_content=html_content,
                text_content=text_content
            )
            
            return success
            
        except Exception as e:
            logger.error(f"Error sending OTP email: {e}")
            return False
    
    def cleanup_expired_tokens(self, db: Session) -> int:
        """Clean up expired OTP tokens"""
        try:
            expired_tokens = db.query(OTPToken).filter(
                OTPToken.expires_at < datetime.utcnow()
            ).all()
            
            count = len(expired_tokens)
            for token in expired_tokens:
                token.is_active = False
                token.updated_at = datetime.utcnow()
            
            db.commit()
            logger.info(f"Cleaned up {count} expired OTP tokens")
            return count
            
        except Exception as e:
            logger.error(f"Error cleaning up expired tokens: {e}")
            db.rollback()
            return 0


# Create service instance
otp_service = OTPService()

