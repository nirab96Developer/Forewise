// @ts-nocheck
// OTP Page - אימות דו-שלבי (ללא כפילות שליחה)
import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Fingerprint, ArrowRight, AlertCircle, Mail, Clock, CheckCircle } from 'lucide-react';
import otpService from '../../services/otpService';
import { getRememberPreference, setAuthSession } from '../../utils/authStorage';

interface OTPProps {
  setGlobalLoading: (loading: boolean) => void;
}

const OTP: React.FC<OTPProps> = ({ setGlobalLoading }) => {
  const navigate = useNavigate();
  const location = useLocation();
  const [otpCode, setOtpCode] = useState(['', '', '', '', '', '']);
  const [isLoading, setIsLoading] = useState(false);
  const [isVerifying, setIsVerifying] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);
  const [error, setError] = useState('');
  const [timeLeft, setTimeLeft] = useState(300); // 5 דקות
  const [canResend, setCanResend] = useState(false);
  const [userId, setUserId] = useState<number | null>(null);
  const inputRefs = useRef<(HTMLInputElement | null)[]>([]);
  
  // Prevent double OTP send and double navigation
  const hasSentOTP = useRef(false);
  const hasNavigated = useRef(false);

  // קבלת פרטי המשתמש מה-location state או localStorage
  const userEmail = location.state?.email || localStorage.getItem('otp_email') || '';
  const username = location.state?.username || localStorage.getItem('otp_username') || '';
  const userIdFromState = location.state?.userId || parseInt(localStorage.getItem('otp_user_id') || '0');
  const otpToken = location.state?.otpToken || localStorage.getItem('otp_token');

  // קבלת userId מה-state
  useEffect(() => {
    if (userIdFromState) {
      setUserId(userIdFromState);
    }
  }, [userIdFromState]);

  // טיימר לספירה לאחור
  useEffect(() => {
    if (timeLeft > 0) {
      const timer = setTimeout(() => setTimeLeft(timeLeft - 1), 1000);
      return () => clearTimeout(timer);
    } else {
      setCanResend(true);
    }
  }, [timeLeft]);

  // פוקוס אוטומטי על השדה הראשון
  useEffect(() => {
    if (inputRefs.current[0]) {
      inputRefs.current[0].focus();
    }
  }, []);

  // שליחת OTP פעם אחת בלבד
  useEffect(() => {
    // Don't send if already sent or if we have a token
    if (hasSentOTP.current || otpToken) {
      return;
    }
    
    // Validate email
    if (!userEmail || !userEmail.includes('@')) {
      console.error('Invalid email:', userEmail);
      setError('כתובת מייל לא תקינה. אנא חזור להתחברות.');
      return;
    }
    
    const sendInitialOTP = async () => {
      hasSentOTP.current = true; // Mark as sent immediately to prevent double calls
      
      try {
        console.log('Sending OTP to:', userEmail);
        setIsLoading(true);
        setError('');
        
        await otpService.sendOTP(userEmail);
        console.log('OTP sent successfully');
      } catch (error: any) {
        console.error('Error sending OTP:', error);
        // Don't show error if OTP was already sent
        if (!error.response?.data?.detail?.includes('already sent')) {
          setError('שגיאה בשליחת OTP. אנא נסה שוב');
        }
      } finally {
        setIsLoading(false);
      }
    };

    sendInitialOTP();
  }, []); // Empty deps - run only once on mount

  // טיפול בהקלדה בשדות OTP
  const handleInputChange = (index: number, value: string) => {
    if (value.length > 1) return; // מונע הכנסת יותר מתו אחד

    const newOtpCode = [...otpCode];
    newOtpCode[index] = value;
    setOtpCode(newOtpCode);

    // מעבר אוטומטי לשדה הבא
    if (value && index < 5) {
      inputRefs.current[index + 1]?.focus();
    }

    // בדיקה אם הקוד מלא
    if (newOtpCode.every(digit => digit !== '')) {
      handleSubmit(newOtpCode.join(''));
    }
  };

  // טיפול במקש Backspace
  const handleKeyDown = (index: number, e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Backspace' && !otpCode[index] && index > 0) {
      inputRefs.current[index - 1]?.focus();
    }
  };

  // טיפול בהדבקה
  const handlePaste = (e: React.ClipboardEvent<HTMLInputElement>) => {
    e.preventDefault();
    const pastedData = e.clipboardData.getData('text').replace(/\D/g, '').slice(0, 6);
    const newOtpCode = [...otpCode];
    
    for (let i = 0; i < pastedData.length && i < 6; i++) {
      newOtpCode[i] = pastedData[i];
    }
    
    setOtpCode(newOtpCode);
    
    // פוקוס על השדה האחרון שהוכן
    const lastFilledIndex = Math.min(pastedData.length - 1, 5);
    inputRefs.current[lastFilledIndex]?.focus();
  };

  const handleSubmit = async (code?: string) => {
    const finalCode = code || otpCode.join('');
    if (finalCode.length !== 6) return;
    
    // Prevent double submit
    if (isVerifying || hasNavigated.current) return;

    setError('');
    setIsVerifying(true);
    setIsLoading(true);
    setGlobalLoading(true);

    try {
      // Use userId from state or try to get from email
      const effectiveUserId = userId || userIdFromState || 0;
      
      if (!effectiveUserId) {
        setError('משתמש לא זוהה. אנא התחבר שוב.');
        setGlobalLoading(false);
        setIsVerifying(false);
        setIsLoading(false);
        return;
      }

      const result = await otpService.verifyOTP(effectiveUserId, finalCode, userEmail);
      
      if (result.access_token) {
        // Extract user data from result
        const userData = result.user || {};
        
        // Extract role - backend returns role as object with code, name, permissions
        const roleCode = typeof userData.role === 'object' && userData.role?.code 
          ? userData.role.code 
          : (userData.role || 'USER');
        
        // Extract permissions
        let permissions: string[] = userData.permissions || [];
        if (typeof userData.role === 'object' && userData.role?.permissions) {
          permissions = userData.role.permissions.map((p: any) => 
            typeof p === 'object' ? p.code : p
          );
        }
        
        // הגדרת נתוני המשתמש
        const userObject = {
          id: userData.id?.toString() || effectiveUserId.toString(),
          name: userData.full_name || userData.username || username || 'משתמש',
          email: userData.email || userEmail,
          role: roleCode,
          roles: [roleCode],
          permissions: permissions
        };

        const rememberMe = getRememberPreference();
        setAuthSession({
          accessToken: result.access_token,
          refreshToken: result.refresh_token || "",
          user: userObject,
          userName: userObject.name,
          rememberMe,
        });
        
        // Clear OTP temp data
        localStorage.removeItem('otp_email');
        localStorage.removeItem('otp_username');
        localStorage.removeItem('otp_user_id');
        localStorage.removeItem('otp_token');
        
        // Show success state
        setIsSuccess(true);
        
        // Wait for animation (max 500ms, not 1500)
        await new Promise(resolve => setTimeout(resolve, 500));
        
        // Prevent double navigation
        if (hasNavigated.current) return;
        hasNavigated.current = true;
        
        setGlobalLoading(false);
        
        // עדכון הסטטוס של ההתחברות
        window.dispatchEvent(new Event('storage'));
        
        navigate('/', { replace: true });
      } else {
        setError('קוד OTP שגוי. אנא נסה שוב');
        setGlobalLoading(false);
        setIsVerifying(false);
        // ניקוי הקוד
        setOtpCode(['', '', '', '', '', '']);
        inputRefs.current[0]?.focus();
      }
    } catch (err: any) {
      console.error('OTP verification error:', err);
      setError(err.response?.data?.detail || 'אירעה שגיאה. אנא נסה שוב');
      setGlobalLoading(false);
      setIsVerifying(false);
      // ניקוי הקוד
      setOtpCode(['', '', '', '', '', '']);
      inputRefs.current[0]?.focus();
    } finally {
      setIsLoading(false);
    }
  };

  const handleResend = async () => {
    setError('');
    setIsLoading(true);
    
    try {
      if (!userId) {
        setError('לא נמצא מזהה משתמש');
        return;
      }
      await otpService.resendOTP(userId);
      setTimeLeft(300);
      setCanResend(false);
      setOtpCode(['', '', '', '', '', '']);
      inputRefs.current[0]?.focus();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'שגיאה בשליחת OTP חדש');
    } finally {
      setIsLoading(false);
    }
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 via-white to-green-50 flex items-center justify-center p-4 animate-fadeIn">
      <div className="w-full max-w-lg animate-slideUp">
        {/* לוגו */}
        <div className="text-center mb-6">
          <div className="w-20 h-20 mx-auto mb-4 hover:scale-105 transition-transform duration-300">
            <img
              src="/logo-kkl-transparent.png"
              alt="KKL Logo"
              className="w-full h-full object-contain drop-shadow-xl"
            />
          </div>
        </div>
        
        {/* כותרת */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-20 h-20 bg-green-100 rounded-full mb-4 animate-scaleIn shadow-lg">
            <Fingerprint className="w-10 h-10 text-green-600" />
          </div>
          <h1 className="text-3xl font-bold text-green-900 mb-3">אימות דו-שלבי</h1>
          <p className="text-gray-600 text-lg">
            שלחנו קוד אימות לכתובת המייל שלך
          </p>
          <div className="flex items-center justify-center mt-3 text-base text-green-700 font-medium bg-green-50 rounded-lg py-2 px-4 inline-flex">
            <Mail className="w-5 h-5 mr-2" />
            {userEmail}
          </div>
        </div>

        {/* טופס OTP */}
        <div className="bg-white rounded-2xl shadow-2xl border-2 border-green-100 p-8">
          <form onSubmit={(e) => { e.preventDefault(); handleSubmit(); }} className="space-y-6">
            {/* שדות OTP */}
            <div className="space-y-4">
              <label className="block text-sm font-medium text-gray-700 text-right">
                הזן את הקוד בן 6 הספרות
              </label>
              {/* Input נסתר ל-iOS Autofill */}
              <input
                type="text"
                name="otp"
                autoComplete="one-time-code"
                inputMode="numeric"
                pattern="[0-9]*"
                className="sr-only"
                aria-hidden="true"
                tabIndex={-1}
                data-1p-ignore
                onChange={(e) => {
                  const value = e.target.value.replace(/\D/g, '').slice(0, 6);
                  if (value.length === 6) {
                    const newOtpCode = value.split('');
                    setOtpCode(newOtpCode);
                    handleSubmit(value);
                  }
                }}
              />
              <div className="flex justify-center gap-3">
                {otpCode.map((digit, index) => (
                  <input
                    key={index}
                    ref={(el) => (inputRefs.current[index] = el)}
                    type="text"
                    inputMode="numeric"
                    pattern="[0-9]*"
                    maxLength={1}
                    value={digit}
                    onChange={(e) => handleInputChange(index, e.target.value)}
                    onKeyDown={(e) => handleKeyDown(index, e)}
                    onPaste={handlePaste}
                    autoComplete={index === 0 ? 'one-time-code' : 'off'}
                    className={`w-14 h-16 text-center text-2xl font-bold border-2 rounded-xl transition-all duration-200 shadow-md ${
                      error 
                        ? 'border-red-400 bg-red-50 focus:border-red-500 focus:ring-4 focus:ring-red-500/20 animate-shake' 
                        : digit
                        ? 'border-green-500 bg-green-50 text-green-900 focus:border-green-600 focus:ring-4 focus:ring-green-500/30'
                        : 'border-gray-300 bg-white focus:border-green-500 focus:ring-4 focus:ring-green-500/20'
                    }`}
                    disabled={isLoading}
                  />
                ))}
              </div>
            </div>

            {/* הודעת שגיאה */}
            {error && (
              <div className="flex items-center space-x-2 space-x-reverse text-red-600 bg-red-50 p-3 rounded-lg animate-shake">
                <AlertCircle className="w-5 h-5 flex-shrink-0" />
                <span className="text-sm">{error}</span>
              </div>
            )}

            {/* טיימר */}
            <div className="text-center">
              <div className={`inline-flex items-center justify-center px-4 py-2 rounded-lg text-base font-medium ${
                timeLeft < 60 ? 'bg-red-50 text-red-700' : 'bg-blue-50 text-blue-700'
              }`}>
                <Clock className="w-5 h-5 mr-2" />
                <span>הקוד יפוג בעוד {formatTime(timeLeft)}</span>
              </div>
            </div>

            {/* כפתור שליחה */}
            <button
              type="submit"
              data-testid="login-verify-otp"
              disabled={isLoading || otpCode.some(digit => digit === '')}
              className="w-full py-4 px-6 bg-green-600 hover:bg-green-700 text-white text-lg font-bold rounded-xl shadow-lg hover:shadow-xl transition-all duration-200 flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed disabled:shadow-none"
            >
              {isLoading ? (
                <div className="w-6 h-6 border-3 border-white border-t-transparent rounded-full animate-spin" />
              ) : (
                <>
                  <span>אמת קוד</span>
                  <ArrowRight className="w-5 h-5" />
                </>
              )}
            </button>

            {/* כפתור שליחה מחדש */}
            <div className="text-center">
              <button
                type="button"
                data-testid="login-get-otp"
                onClick={handleResend}
                disabled={!canResend || isLoading}
                className="text-green-600 hover:text-green-800 text-base font-semibold disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-200 underline-offset-4 hover:underline"
              >
                {canResend ? '✨ שלח קוד חדש' : `שלח שוב בעוד ${formatTime(timeLeft)}`}
              </button>
            </div>
          </form>
        </div>

        {/* קישור חזרה */}
        <div className="text-center mt-6">
          <button
            onClick={() => navigate('/login')}
            className="text-gray-600 hover:text-gray-800 text-sm font-medium transition-colors duration-200"
          >
            ← חזרה להתחברות
          </button>
        </div>
      </div>
      
      {/* Loading Overlay */}
      {isLoading && (
        <div className="loading-overlay">
          <div className="flex flex-col items-center gap-4">
            <div className="loading-spinner"></div>
            <p className="text-white text-lg font-medium">המערכת טוענת...</p>
          </div>
        </div>
      )}
    </div>
  );
};

export default OTP;
