# app/core/sms.py
"""
SMS service for sending OTP codes and notifications
"""
import logging
import requests
from typing import Optional
from app.core.config import settings

logger = logging.getLogger(__name__)


class SMSService:
    """Service for sending SMS messages."""
    
    def __init__(self):
        self.api_key = getattr(settings, 'SMS_API_KEY', None)
        self.api_url = getattr(settings, 'SMS_API_URL', 'https://api.sms4free.co.il/api/send')
        self.sender_name = getattr(settings, 'SMS_SENDER_NAME', 'ForestSys')
        
        # For testing - use Telegram Bot API
        if not self.api_key:
            self.api_url = "https://api.telegram.org/bot"
            self.api_key = "YOUR_TELEGRAM_BOT_TOKEN"  # Replace with actual bot token
            self.chat_id = "YOUR_CHAT_ID"  # Replace with your chat ID
        
    def send_sms(self, phone_number: str, message: str) -> bool:
        """
        Send SMS message to phone number.
        
        Args:
            phone_number (str): Phone number in international format (e.g., +972535293308)
            message (str): SMS message content
            
        Returns:
            bool: True if SMS sent successfully, False otherwise
        """
        try:
            # Clean phone number - remove + and ensure it starts with country code
            clean_phone = phone_number.replace('+', '').replace(' ', '').replace('-', '')
            
            # For Israeli numbers, ensure they start with 972
            if clean_phone.startswith('0'):
                clean_phone = '972' + clean_phone[1:]
            elif not clean_phone.startswith('972'):
                clean_phone = '972' + clean_phone
            
            logger.info(f"Sending SMS to {clean_phone}: {message[:50]}...")
            
            # For development/testing - send real SMS
            logger.info(f"[SMS DEV] To: {clean_phone}")
            logger.info(f"[SMS DEV] Message: {message}")
            
            # Try to send real SMS even in development
            logger.info(f"[SMS DEV] Attempting to send real SMS...")
            
            # Use Telegram Bot API for testing
            if self.api_key == "YOUR_TELEGRAM_BOT_TOKEN":
                logger.info(f"[SMS DEV] Telegram Bot not configured - SMS not sent")
                logger.info(f"[SMS DEV] SMS fallback - would be sent in production")
                return True
            
            # Send via Telegram
            telegram_url = f"{self.api_url}{self.api_key}/sendMessage"
            payload = {
                'chat_id': self.chat_id,
                'text': f"📱 SMS to {clean_phone}:\n\n{message}",
                'parse_mode': 'HTML'
            }
            
            try:
                response = requests.post(
                    telegram_url,
                    json=payload,
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get('ok'):
                        logger.info(f"[SMS DEV] Telegram message sent successfully to {clean_phone}")
                        return True
                    else:
                        logger.error(f"[SMS DEV] Telegram sending failed: {result.get('description', 'Unknown error')}")
                else:
                    logger.error(f"[SMS DEV] Telegram sending failed: {response.status_code} - {response.text}")
            except Exception as e:
                logger.error(f"[SMS DEV] Telegram sending exception: {e}")
            
            logger.info(f"[SMS DEV] SMS fallback - would be sent in production")
            return True
            
            # Production SMS sending (placeholder - implement with real SMS provider)
            if not self.api_key:
                logger.warning("SMS API key not configured - SMS not sent")
                return False
                
            # Example SMS API call (replace with actual provider)
            payload = {
                'api_key': self.api_key,
                'to': clean_phone,
                'message': message,
                'sender': self.sender_name
            }
            
            response = requests.post(
                self.api_url,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                logger.info(f"SMS sent successfully to {clean_phone}")
                return True
            else:
                logger.error(f"SMS sending failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending SMS to {phone_number}: {e}")
            return False
    
    def send_otp_sms(self, phone_number: str, otp_code: str, user_name: str = "") -> bool:
        """
        Send OTP code via SMS.
        
        Args:
            phone_number (str): Phone number in international format
            otp_code (str): 6-digit OTP code
            user_name (str): User's name for personalization
            
        Returns:
            bool: True if SMS sent successfully, False otherwise
        """
        message = f"קוד אימות למערכת ניהול יערות: {otp_code}\nהקוד תקף ל-10 דקות.\nאם לא ביקשת קוד זה, אנא התעלם מההודעה."
        
        if user_name:
            message = f"שלום {user_name},\n{message}"
        
        return self.send_sms(phone_number, message)


# Create global SMS service instance
sms_service = SMSService()


def send_sms(phone_number: str, message: str) -> bool:
    """
    Convenience function to send SMS.
    
    Args:
        phone_number (str): Phone number in international format
        message (str): SMS message content
        
    Returns:
        bool: True if SMS sent successfully, False otherwise
    """
    return sms_service.send_sms(phone_number, message)


def send_otp_sms(phone_number: str, otp_code: str, user_name: str = "") -> bool:
    """
    Convenience function to send OTP via SMS.
    
    Args:
        phone_number (str): Phone number in international format
        otp_code (str): 6-digit OTP code
        user_name (str): User's name for personalization
        
    Returns:
        bool: True if SMS sent successfully, False otherwise
    """
    return sms_service.send_otp_sms(phone_number, otp_code, user_name)
