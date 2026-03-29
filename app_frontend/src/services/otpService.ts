// src/services/otpService.ts
import api from './api';

export interface OTPSendRequest {
  email: string;
}

export interface OTPVerifyRequest {
  user_id: number;
  code: string;
  email: string;
}

export interface OTPSendResponse {
  message: string;
  email: string;
}

export interface OTPVerifyResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: any;
  requires_2fa: boolean;
}

class OTPService {
  /**
   * שליחת OTP למייל
   */
  async sendOTP(email: string): Promise<OTPSendResponse> {
    try {
      const response = await api.post('/auth/send-otp', {
        email: email
      });
      return response.data;
    } catch (error) {
      console.error('Error sending OTP:', error);
      throw error;
    }
  }

  /**
   * אימות OTP
   */
  async verifyOTP(userId: number, code: string, email?: string): Promise<OTPVerifyResponse> {
    try {
      const response = await api.post('/auth/verify-otp', {
        user_id: userId,
        code: code,
        email: email || String(userId)
      });
      return response.data;
    } catch (error) {
      console.error('Error verifying OTP:', error);
      throw error;
    }
  }

  /**
   * שליחה חוזרת של OTP
   */
  async resendOTP(userId: number, email?: string): Promise<OTPSendResponse> {
    try {
      const response = await api.post('/auth/resend-otp', {
        user_id: userId,
        code: '', // לא נדרש לשליחה חוזרת
        email: email || String(userId)
      });
      return response.data;
    } catch (error) {
      console.error('Error resending OTP:', error);
      throw error;
    }
  }
}

export default new OTPService();
