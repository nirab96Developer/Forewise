
// OTP Page - אימות דו-שלבי: ביומטרי (ראשי) + OTP (גיבוי)
import React, { useState, useEffect, useRef } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Fingerprint, ArrowRight, AlertCircle, Mail, Clock, ScanFace, KeyRound } from 'lucide-react';
import otpService from '../../services/otpService';
import authService from '../../services/authService';
import biometricService from '../../services/biometricService';
import { getBiometricLabel } from '../../utils/deviceDetector';
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
  const [error, setError] = useState('');
  const [timeLeft, setTimeLeft] = useState(300); // 5 דקות
  const [canResend, setCanResend] = useState(false);
  const [userId, setUserId] = useState<number | null>(null);
  const inputRefs = useRef<(HTMLInputElement | null)[]>([]);
  
  const [authMethod, setAuthMethod] = useState<'choose' | 'otp' | 'biometric'>('choose');
  const [biometricAvailable, setBiometricAvailable] = useState(false);
  const _biometric = getBiometricLabel(); void _biometric;
  
  // Prevent double OTP send and double navigation
  const hasSentOTP = useRef(false);
  const hasNavigated = useRef(false);

  // קבלת פרטי המשתמש מה-location state או localStorage
  const userEmail = location.state?.email || localStorage.getItem('otp_email') || '';
  const username = location.state?.username || localStorage.getItem('otp_username') || '';
  const userIdFromState = location.state?.userId || parseInt(localStorage.getItem('otp_user_id') || '0');
  const otpToken = location.state?.otpToken || localStorage.getItem('otp_token');
  const otpAlreadySent = Boolean(location.state?.otpAlreadySent) || localStorage.getItem('otp_sent_via_login') === 'true';
  const isFirstLogin = location.state?.isFirstLogin || false;
  const deliveryTarget = userEmail || username || 'המשתמש שלך';

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

  // Check biometric availability
  useEffect(() => {
    const checkBio = async () => {
      if (biometricService.isSupported() && biometricService.isRegistered()) {
        try {
          const avail = await biometricService.isAvailable();
          setBiometricAvailable(avail);
        } catch { setBiometricAvailable(false); }
      } else {
        setBiometricAvailable(false);
        setAuthMethod('otp');
      }
    };
    checkBio();
  }, []);

  // Send OTP when user chooses OTP method (or if no biometric available)
  useEffect(() => {
    if (authMethod !== 'otp') return;
    if (hasSentOTP.current || otpToken || otpAlreadySent) return;
    if (!userEmail || !userEmail.includes('@')) {
      setError('קוד האימות נשלח במהלך ההתחברות. אם לא התקבל, ניתן לבקש שליחה מחדש.');
      return;
    }
    
    const sendInitialOTP = async () => {
      hasSentOTP.current = true;
      try {
        setIsLoading(true);
        setError('');
        await otpService.sendOTP(userEmail);
      } catch (error: any) {
        if (!error.response?.data?.detail?.includes('already sent')) {
          setError('שגיאה בשליחת OTP. אנא נסה שוב');
        }
      } finally {
        setIsLoading(false);
      }
    };
    sendInitialOTP();
  }, [authMethod]);

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

      const result = await otpService.verifyOTP(
        effectiveUserId,
        finalCode,
        userEmail || username || String(effectiveUserId)
      );
      
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
          first_name: userData.first_name || (userData.full_name || userData.username || username || 'משתמש').split(' ')[0],
          full_name: userData.full_name || userData.username || username || 'משתמש',
          email: userData.email || userEmail,
          role: roleCode,
          role_code: roleCode,
          roles: [roleCode],
          permissions: permissions,
          region_id: userData.region_id,
          area_id: userData.area_id,
          department_id: userData.department_id,
          last_login: userData.last_login || null,
        };

// שמירה מפורשת ב-localStorage — תמיד, ללא תנאי 
        localStorage.setItem('access_token',    result.access_token);
        localStorage.setItem('token',           result.access_token);
        localStorage.setItem('user',            JSON.stringify(userObject));
        localStorage.setItem('isAuthenticated', 'true');
        if (result.refresh_token) {
          localStorage.setItem('refresh_token', result.refresh_token);
        }

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
        localStorage.removeItem('otp_sent_via_login');
        
        // Wait for animation (max 500ms, not 1500)
        await new Promise(resolve => setTimeout(resolve, 500));
        
        // Prevent double navigation
        if (hasNavigated.current) return;
        hasNavigated.current = true;
        
        setGlobalLoading(false);
        
        // עדכון הסטטוס של ההתחברות
        window.dispatchEvent(new Event('auth-change'));
        window.dispatchEvent(new Event('storage'));

        // Phase 2.2: refresh from /users/me so role/permissions reflect
        // the DB and not the cached snapshot inside the verify-otp payload.
        try {
          await authService.refreshCurrentUser();
        } catch { /* keep cached */ }

        if (result.user?.must_change_password) {
          navigate('/change-password', { replace: true });
        } else {
          navigate('/welcome', { replace: true });
        }
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
      await otpService.resendOTP(userId, userEmail || username || String(userId));
      localStorage.removeItem('otp_sent_via_login');
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

  const handleBiometricAuth = async () => {
    if (!username) {
      setError('שם משתמש חסר. אנא חזור להתחברות.');
      return;
    }
    try {
      setIsLoading(true);
      setError('');
      setGlobalLoading(true);

      const result = await biometricService.authenticate(username);
      if (result?.access_token) {
        // WebAuthn returns role as a nested object — flatten it so the rest of
        // the app's permission stack works (same fix as in Login.tsx).
        const rawUser: any = result.user || {};
        const roleCode = (typeof rawUser.role === 'object' && rawUser.role?.code)
          ? rawUser.role.code
          : (rawUser.role || rawUser.role_code || 'USER');

        let permissions: string[] = rawUser.permissions || [];
        if (typeof rawUser.role === 'object' && rawUser.role?.permissions) {
          permissions = rawUser.role.permissions.map((p: any) =>
            typeof p === 'object' ? p.code : p
          );
        }

        const fullName = rawUser.full_name || rawUser.username || username || '';
        const userObject = {
          id: rawUser.id?.toString() || '',
          name: fullName,
          first_name: rawUser.first_name || (fullName.split(' ')[0] || fullName),
          full_name: fullName,
          email: rawUser.email,
          role: roleCode,
          role_code: roleCode,
          roles: [roleCode],
          permissions,
          region_id: rawUser.region_id,
          area_id: rawUser.area_id,
          department_id: rawUser.department_id,
          last_login: rawUser.last_login || null,
        };

        localStorage.setItem('access_token', result.access_token);
        localStorage.setItem('token', result.access_token);
        localStorage.setItem('user', JSON.stringify(userObject));
        localStorage.setItem('isAuthenticated', 'true');
        if (result.refresh_token) localStorage.setItem('refresh_token', result.refresh_token);

        setAuthSession({
          accessToken: result.access_token,
          refreshToken: result.refresh_token || '',
          user: userObject,
          userName: userObject.name || userObject.full_name || '',
          rememberMe: true,
        });

        localStorage.removeItem('otp_email');
        localStorage.removeItem('otp_username');
        localStorage.removeItem('otp_user_id');
        localStorage.removeItem('otp_token');
        localStorage.removeItem('otp_sent_via_login');

        window.dispatchEvent(new Event('storage'));

        // Phase 2.2 — same canonical refresh as the standard OTP path.
        try {
          await authService.refreshCurrentUser();
        } catch { /* keep cached */ }

        hasNavigated.current = true;
        setGlobalLoading(false);
        navigate('/welcome', { replace: true });
      } else {
        setError('אימות ביומטרי נכשל. נסה שוב או השתמש בקוד אימות.');
        setGlobalLoading(false);
      }
    } catch (err: any) {
      setError(err.message || 'שגיאה באימות ביומטרי. ניתן להשתמש בקוד אימות.');
      setGlobalLoading(false);
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
        <div className="flex flex-col items-center mb-6 hover:scale-105 transition-transform duration-300">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 100" width="80" height="67">
            <defs>
              <linearGradient id="otp_t" x1="0%" y1="0%" x2="100%" y2="0%"><stop offset="0%" style={{stopColor:'#1565c0'}}/><stop offset="100%" style={{stopColor:'#0097a7'}}/></linearGradient>
              <linearGradient id="otp_m" x1="0%" y1="0%" x2="100%" y2="0%"><stop offset="0%" style={{stopColor:'#0097a7'}}/><stop offset="50%" style={{stopColor:'#2e7d32'}}/><stop offset="100%" style={{stopColor:'#66bb6a'}}/></linearGradient>
              <linearGradient id="otp_b" x1="0%" y1="0%" x2="100%" y2="0%"><stop offset="0%" style={{stopColor:'#2e7d32'}}/><stop offset="40%" style={{stopColor:'#66bb6a'}}/><stop offset="100%" style={{stopColor:'#8B5e3c'}}/></linearGradient>
            </defs>
            <path d="M46 20 Q60 9 74 20" stroke="url(#otp_t)" strokeWidth="5.5" fill="none" strokeLinecap="round"/>
            <path d="M30 47 Q42 34 60 43 Q78 34 90 47" stroke="url(#otp_m)" strokeWidth="5.5" fill="none" strokeLinecap="round"/>
            <path d="M14 74 Q28 60 46 69 Q60 76 74 69 Q92 60 106 74" stroke="url(#otp_b)" strokeWidth="5.5" fill="none" strokeLinecap="round"/>
            <line x1="60" y1="76" x2="60" y2="90" stroke="#8B5e3c" strokeWidth="3.5" strokeLinecap="round"/>
            <circle cx="60" cy="95" r="5" fill="#8B5e3c"/>
          </svg>
          <div style={{fontFamily:"'Montserrat',sans-serif", fontWeight:800, fontSize:'20px', letterSpacing:'4px', color:'#1F6F43', marginTop:'6px'}}>
            FOREWISE
          </div>
        </div>
        
        {/* כותרת */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-20 h-20 bg-green-100 rounded-full mb-4 animate-scaleIn shadow-lg">
            <Fingerprint className="w-10 h-10 text-green-600" />
          </div>
          <h1 className="text-3xl font-bold text-green-900 mb-3">אימות דו-שלבי</h1>
          {isFirstLogin && (
            <div className="mb-3 px-4 py-2 bg-amber-50 border border-amber-200 rounded-lg text-amber-800 text-sm font-medium">
              כניסה ראשונה — אמת את זהותך ואז תועבר לשינוי סיסמה
            </div>
          )}
        </div>

        {/* Choice screen — biometric vs OTP */}
        {authMethod === 'choose' && biometricAvailable && (
          <div className="bg-white rounded-2xl shadow-2xl border-2 border-green-100 p-8 mb-6">
            <p className="text-gray-700 text-center text-lg mb-6 font-medium">בחר אופן אימות:</p>
            <div className="space-y-4">
              <button
                type="button"
                onClick={handleBiometricAuth}
                disabled={isLoading}
                className="w-full py-4 bg-gradient-to-r from-blue-600 to-green-600 text-white text-lg font-bold rounded-xl shadow-lg hover:shadow-xl transition-all flex items-center justify-center gap-3 min-h-[56px] disabled:opacity-50"
              >
                <ScanFace className="w-6 h-6" />
                כניסה ביומטרית
              </button>
              <button
                type="button"
                onClick={() => setAuthMethod('otp')}
                disabled={isLoading}
                className="w-full py-4 bg-white border-2 border-green-300 text-green-700 text-lg font-bold rounded-xl hover:bg-green-50 transition-all flex items-center justify-center gap-3 min-h-[56px] disabled:opacity-50"
              >
                <KeyRound className="w-6 h-6" />
                המשך עם קוד אימות
              </button>
            </div>
            {error && (
              <div className="mt-4 flex items-center gap-2 text-red-600 bg-red-50 p-3 rounded-lg">
                <AlertCircle className="w-5 h-5 flex-shrink-0" />
                <span className="text-sm">{error}</span>
              </div>
            )}
          </div>
        )}

        {/* OTP form — shown when OTP method is chosen or biometric not available */}
        {(authMethod === 'otp' || (!biometricAvailable && authMethod === 'choose')) && (
        <>
        <div className="text-center mb-6">
          <p className="text-gray-600 text-lg">
            שלחנו קוד אימות לצורך התחברות מאובטחת
          </p>
          <div className="flex items-center justify-center mt-3 text-base text-green-700 font-medium bg-green-50 rounded-lg py-2 px-4 inline-flex">
            <Mail className="w-5 h-5 mr-2" />
            {deliveryTarget}
          </div>
        </div>

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
{canResend ? ' שלח קוד חדש' : `שלח שוב בעוד ${formatTime(timeLeft)}`}
              </button>
            </div>
          </form>
        </div>

        {/* Switch to biometric from OTP view */}
        {authMethod === 'otp' && biometricAvailable && (
          <div className="text-center mt-4">
            <button
              type="button"
              onClick={() => { setError(''); handleBiometricAuth(); }}
              className="text-blue-600 hover:text-blue-800 text-sm font-medium transition-colors"
            >
              <ScanFace className="w-4 h-4 inline mr-1" />
              השתמש באימות ביומטרי במקום
            </button>
          </div>
        )}
        </>
        )}

        {/* קישור חזרה */}
        <div className="text-center mt-6">
          <button
            onClick={() => navigate('/login')}
            className="text-gray-600 hover:text-gray-800 text-sm font-medium transition-colors duration-200"
          >
חזרה להתחברות
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
