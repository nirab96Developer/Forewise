
import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { User, Lock, Fingerprint, Eye, EyeOff, AlertCircle, Loader2 } from 'lucide-react';
import api from '../../services/api';
import biometricService from '../../services/biometricService';
import { setAuthSession, setRememberPreference } from '../../utils/authStorage';

interface LoginProps {
  setGlobalLoading: (loading: boolean) => void;
}

const Login: React.FC<LoginProps> = ({ setGlobalLoading }) => {
  const navigate = useNavigate();
  const [showPassword, setShowPassword] = useState(false);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [rememberMe, setRememberMe] = useState(false);
  const [touchedFields, setTouchedFields] = useState<Set<string>>(new Set());
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [biometricAvailable, setBiometricAvailable] = useState(false);
  const [biometricSupported, setBiometricSupported] = useState(false);
  const [isMobileDevice, setIsMobileDevice] = useState(false);
  
  // Refs for fallback DOM access (for browser automation compatibility)
  const usernameRef = useRef<HTMLInputElement>(null);
  const passwordRef = useRef<HTMLInputElement>(null);

  // בדיקה האם יש שם משתמש שמור
  useEffect(() => {
    const savedUsername = localStorage.getItem('savedUsername');
    if (savedUsername) {
      setUsername(savedUsername);
      setRememberMe(true);
    }
  }, []);

  // בדיקת תמיכה בזיהוי ביומטרי
  useEffect(() => {
    const checkBiometric = async () => {
      const mobile =
        /Android|iPhone|iPad|iPod|Mobile/i.test(navigator.userAgent) ||
        navigator.maxTouchPoints > 1;
      setIsMobileDevice(mobile);

      const supported = biometricService.isSupported();
      setBiometricSupported(supported);
      
      if (supported && mobile) {
        try {
          const available = await biometricService.isAvailable();
          setBiometricAvailable(available);
        } catch (error) {
          console.error('Error checking biometric availability:', error);
          setBiometricAvailable(false);
        }
      }
    };

    checkBiometric();
  }, []);

  // טיפול בלחיצה על מקש Enter בשדה הסיסמה
  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !isLoading) {
      e.preventDefault();
      handleSubmit(e as unknown as React.FormEvent);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Fallback: אם ה-state ריק, נקרא ישירות מה-DOM (תאימות ל-browser automation)
    let actualUsername = username;
    let actualPassword = password;
    
    if (!actualUsername && usernameRef.current) {
      actualUsername = usernameRef.current.value;
      console.log('Using DOM fallback for username:', actualUsername);
    }
    if (!actualPassword && passwordRef.current) {
      actualPassword = passwordRef.current.value;
      console.log('Using DOM fallback for password');
    }
    
    // DEBUG - בדיקה שה-submit רץ
    console.log('LOGIN SUBMIT CALLED', { username: actualUsername, passwordLength: actualPassword?.length });
    
    // ולידציה בסיסית
    if (!actualUsername?.trim() || !actualPassword) {
      console.log('LOGIN VALIDATION FAILED', { username: actualUsername, password: !!actualPassword });
      setError('נא למלא שם משתמש וסיסמה');
      return;
    }
    
    setError('');
    setIsLoading(true);
    setGlobalLoading(true);

    try {
      console.log('LOGIN API CALL STARTING');
      // קריאה לשרת האמיתי באמצעות api service
      const response = await api.post('/auth/login', {
        username: actualUsername.trim(),
        password: actualPassword,
        remember_me: rememberMe,
      });
      console.log('LOGIN API RESPONSE', response.data);

      if (response.data) {
        const data = response.data;
        
        // בדיקה אם נדרש 2FA
        if (data.requires_2fa) {
          // שמירת נתוני OTP
          localStorage.setItem('otp_token', data.otp_token);
          localStorage.setItem('otp_user_id', data.user_id.toString());
          localStorage.setItem('otp_username', actualUsername);
          
          // שמירת זכור אותי אם נבחר
          if (rememberMe) {
            localStorage.setItem('rememberMe', 'true');
            localStorage.setItem('savedUsername', actualUsername);
          } else {
            localStorage.removeItem('rememberMe');
            localStorage.removeItem('savedUsername');
          }
          
          // ביטול הטעינה לפני הניווט
          setGlobalLoading(false);
          
          // ניווט לדף OTP
          navigate('/otp', { 
            replace: true,
            state: { 
              username: actualUsername,
              userId: data.user_id,
              otpToken: data.otp_token
            }
          });
          return;
        }
        
        // אם אין 2FA - התחברות רגילה
        if (data.user) {
          // Debug: Log the raw user data from API
          console.log('[Login] Raw user data from API:', JSON.stringify(data.user, null, 2));
          console.log('[Login] data.user.role type:', typeof data.user.role);
          console.log('[Login] data.user.role value:', data.user.role);
          
          // Extract role - backend returns role as object with code, name, permissions
          const roleCode = typeof data.user.role === 'object' && data.user.role?.code 
            ? data.user.role.code 
            : (data.user.role || 'USER');
          
          console.log('[Login] Extracted roleCode:', roleCode);
          
          // ספקים לא יכולים להתחבר לאפליקציה - הם משתמשים בפורטל החיצוני
          if (roleCode === 'SUPPLIER') {
            setError('ספקים אינם יכולים להתחבר למערכת זו. אנא השתמש בלינק שקיבלת מהמתאם לפורטל הספקים.');
            setIsLoading(false);
            setGlobalLoading(false);
            return;
          }
          
          // Extract permissions - could be in role.permissions or directly on user
          let permissions: string[] = data.user.permissions || [];
          if (typeof data.user.role === 'object' && data.user.role?.permissions) {
            permissions = data.user.role.permissions.map((p: any) => 
              typeof p === 'object' ? p.code : p
            );
          }
          
          // הגדרת נתוני המשתמש - שמירת role מהשרת
          const userObject = {
            id: data.user.id.toString(),
            name: data.user.full_name || data.user.username,
            email: data.user.email,
            role: roleCode,  // role code string from API
            roles: [roleCode],  // backwards compatibility
            permissions: permissions
          };

          setRememberPreference(rememberMe);
          setAuthSession({
            accessToken: data.access_token,
            refreshToken: data.refresh_token || '',
            user: userObject,
            userName: userObject.name,
            rememberMe,
          });

          // שמירת device_token אם הוחזר מהשרת (2FA remember device)
          if (data.device_token) {
            localStorage.setItem('device_token', data.device_token);
          }
          
          // שמירת זכור אותי אם נבחר
          if (rememberMe) {
            localStorage.setItem('rememberMe', 'true');
            localStorage.setItem('savedUsername', actualUsername);
          } else {
            localStorage.removeItem('rememberMe');
            localStorage.removeItem('savedUsername');
          }
          
          // שמירה ב-Electron אם אפשרי
          if (window.electron) {
            window.electron.send('set-auth', {
              isAuthenticated: true,
              user: userObject,
              rememberMe
            });
          }
          
          // עדכון הסטטוס של ההתחברות - חשוב מאוד לעשות את זה אחרי שמירת ה-localStorage
          window.dispatchEvent(new Event('auth-change'));
          window.dispatchEvent(new Event('storage'));
          
          // המתנה קצרה כדי לוודא שה-localStorage עודכן וה-ProtectedRoute מזהה את זה
          await new Promise(resolve => setTimeout(resolve, 100));
          
          // ביטול הטעינה לפני הניווט
          setIsLoading(false);
          setGlobalLoading(false);
          
          // המתנה קצרה נוספת כדי לוודא שה-globalLoading עודכן
          await new Promise(resolve => setTimeout(resolve, 50));
          
          // ניווט לדף הבית
          navigate('/', { replace: true });
        } else {
          // אם אין user בנתונים
          setError('שגיאה בנתוני המשתמש');
          setIsLoading(false);
          setGlobalLoading(false);
        }
      } else {
        // אם אין response.data
        setError('שגיאה בנתוני התגובה מהשרת');
        setIsLoading(false);
        setGlobalLoading(false);
      }
    } catch (err: any) {
      console.error('Login error:', err);
      
      // הודעת שגיאה מפורטת יותר
      let errorMessage = 'אירעה שגיאה. אנא נסה שוב';
      
      if (err.code === 'ECONNREFUSED' || err.code === 'ERR_NETWORK' || err.message?.includes('Network Error')) {
        errorMessage = 'לא ניתן להתחבר לשרת. אנא ודא שהשרת רץ על /api';
      } else if (err.response?.data?.detail) {
        errorMessage = err.response.data.detail;
      } else if (err.response?.data?.message) {
        errorMessage = err.response.data.message;
      } else if (err.message) {
        errorMessage = err.message;
      }
      
      setError(errorMessage);
      setIsLoading(false);
      setGlobalLoading(false);
    } finally {
      setIsLoading(false);
      setGlobalLoading(false);
    }
  };

  const handleBlur = (field: string) => {
    setTouchedFields(prev => new Set([...prev, field]));
  };

  const renderFieldError = (field: string, value: string) => {
    if (touchedFields.has(field) && !value) {
      return (
        <div className="flex items-center gap-1 text-red-500 text-sm mt-1 opacity-80">
          <AlertCircle className="w-4 h-4" />
          <span>נדרש למלא שדה זה</span>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 via-white to-green-50 flex items-center justify-center p-4">
      <div className="flex flex-col items-center w-full max-w-md animate-fadeIn">
        <div className="w-24 h-24 sm:w-28 sm:h-28 mb-4 hover:scale-105 transition-transform duration-300">
          <img
            src="/logo-kkl-transparent.png"
            alt="KKL Logo"
            className="w-full h-full object-contain drop-shadow-2xl"
          />
        </div>
        
        <h1 className="text-2xl sm:text-3xl font-bold text-green-900 mb-2">
          אפליקציית דיווחים
        </h1>
        <p className="text-base text-gray-600 mb-6">
          מערכת לניהול דיווחים קק"ל
        </p>

        <div className="bg-white rounded-2xl shadow-2xl border-2 border-green-100 w-full p-6 hover:shadow-3xl transition-shadow duration-300">
          <form onSubmit={handleSubmit} className="space-y-5">
            <div className="space-y-2">
              <label className="block text-right text-sm font-semibold text-gray-900">
                שם משתמש
              </label>
              <div className="relative group">
                <input
                  ref={usernameRef}
                  type="text"
                  name="username"
                  autoComplete="username"
                  data-testid="login-email"
                  defaultValue={username}
                  onChange={(e) => {
                    console.log('USERNAME CHANGE:', e.target.value);
                    setUsername(e.target.value);
                  }}
                  onBlur={() => handleBlur('username')}
                  onKeyDown={handleKeyDown}
                  className="w-full p-3 pl-4 pr-11 text-base text-right
                         border-2 border-gray-200 rounded-xl
                         focus:outline-none focus:border-green-500 focus:ring-4 focus:ring-green-500/20
                         transition-all duration-300 shadow-sm"
                  disabled={isLoading}
                />
                <User className="absolute right-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400 group-hover:text-green-600 transition-colors" />
              </div>
              {renderFieldError('username', username)}
            </div>

            <div className="space-y-2">
              <label className="block text-right text-sm font-semibold text-gray-900">
                סיסמה
              </label>
              <div className="relative group">
                <input
                  ref={passwordRef}
                  type={showPassword ? "text" : "password"}
                  name="password"
                  autoComplete="current-password"
                  data-testid="login-password"
                  defaultValue={password}
                  onChange={(e) => {
                    console.log('PASSWORD CHANGE:', e.target.value.length, 'chars');
                    setPassword(e.target.value);
                  }}
                  onBlur={() => handleBlur('password')}
                  onKeyDown={handleKeyDown}
                  className="w-full p-3 pl-11 pr-11 text-base text-right
                         border-2 border-gray-200 rounded-xl
                         focus:outline-none focus:border-green-500 focus:ring-4 focus:ring-green-500/20
                         transition-all duration-300 shadow-sm"
                  disabled={isLoading}
                />
                <Lock className="absolute right-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400 group-hover:text-green-600 transition-colors" />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-700 transition-colors"
                  disabled={isLoading}
                >
                  {showPassword ? 
                    <EyeOff className="h-5 w-5" /> : 
                    <Eye className="h-5 w-5" />
                  }
                </button>
              </div>
              {renderFieldError('password', password)}
            </div>

            <div className="flex justify-between items-center py-1">
              <a 
                href="/forgot-password"
                data-testid="login-forgot"
                className="text-sm text-kkl-blue hover:text-blue-700 transition-colors"
              >
                שכחת סיסמה?
              </a>
              {/* Remember me — large touch target for mobile (44px Apple HIG) */}
              <button
                type="button"
                role="checkbox"
                aria-checked={rememberMe}
                data-testid="login-remember"
                disabled={isLoading}
                onClick={() => setRememberMe(prev => !prev)}
                className="flex items-center gap-2 min-h-[44px] px-2 touch-manipulation select-none
                           focus:outline-none focus:ring-2 focus:ring-kkl-green/40 rounded-lg
                           disabled:opacity-50"
              >
                {/* Custom checkbox visual */}
                <span className={`w-5 h-5 rounded border-2 flex items-center justify-center flex-shrink-0 transition-colors ${
                  rememberMe
                    ? 'bg-kkl-green border-kkl-green'
                    : 'bg-white border-gray-300'
                }`}>
                  {rememberMe && (
                    <svg className="w-3 h-3 text-white" viewBox="0 0 12 12" fill="none">
                      <path d="M2 6l3 3 5-5" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                    </svg>
                  )}
                </span>
                <span className="text-sm text-gray-600">זכור אותי</span>
              </button>
            </div>

            {error && (
              <div className="flex items-center gap-2 text-red-600 text-sm text-center p-3 bg-red-50 border-2 border-red-200 rounded-xl animate-fadeIn">
                <AlertCircle className="w-5 h-5 flex-shrink-0" />
                <span>{error}</span>
              </div>
            )}

            <button
              type="submit"
              data-testid="login-submit"
              disabled={isLoading}
              className="w-full bg-green-600 hover:bg-green-700 text-white 
                      py-4 text-lg font-bold rounded-xl
                      shadow-lg hover:shadow-xl
                      transform transition-all duration-300
                      focus:outline-none focus:ring-4 focus:ring-green-500/30
                      active:scale-[0.98]
                      disabled:opacity-50 disabled:cursor-not-allowed disabled:shadow-none"
            >
              {isLoading ? (
                <span className="flex items-center justify-center gap-2">
                  <Loader2 className="w-6 h-6 animate-spin" />
                  מתחבר...
                </span>
              ) : 'התחברות'}
            </button>

            {isMobileDevice && biometricSupported && biometricAvailable && (
              <button
                type="button"
                data-testid="login-bio"
                disabled={isLoading}
                onClick={async () => {
                  try {
                    setIsLoading(true);
                    setError('');
                    setGlobalLoading(true);

                    const result = await biometricService.authenticate();
                    
                    if (result && result.access_token) {
                      setAuthSession({
                        accessToken: result.access_token,
                        refreshToken: result.refresh_token || '',
                        user: result.user,
                        userName: result.user?.name || result.user?.full_name || result.user?.username || '',
                        rememberMe: true,
                      });
                      
                      // עדכון הסטטוס
                      window.dispatchEvent(new Event('storage'));
                      
                      // המתנה קצרה לאנימציה
                      await new Promise(resolve => setTimeout(resolve, 500));
                      
                      setGlobalLoading(false);
                      navigate('/', { replace: true });
                    } else {
                      setError('אימות ביומטרי נכשל. אנא נסה שוב');
                      setGlobalLoading(false);
                    }
                  } catch (err: any) {
                    console.error('Biometric authentication error:', err);
                    setError(err.message || 'שגיאה בהתחברות ביומטרית. אנא נסה שוב');
                    setGlobalLoading(false);
                  } finally {
                    setIsLoading(false);
                  }
                }}
                className="w-full bg-gradient-to-r from-kkl-blue via-kkl-green to-kkl-brown
                        text-white py-3 text-base sm:text-lg rounded-lg
                        flex items-center justify-center gap-2
                        hover:opacity-90 active:opacity-80 hover:shadow-md font-medium min-h-[44px]
                        transform transition-all duration-300 touch-manipulation
                        focus:outline-none focus:ring-2 focus:ring-kkl-blue focus:ring-offset-2
                        active:scale-[0.98]
                        disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <Fingerprint className="h-5 w-5 sm:h-6 sm:w-6" />
                {isLoading ? 'מתחבר...' : 'התחברות ביומטרית (Face ID / Touch ID)'}
              </button>
            )}
          </form>
        </div>

        <footer className="text-center mt-6">
          <p className="text-lg text-gray-700 font-medium">קרן קיימת לישראל</p>
          <p className="text-base text-gray-500">KKL-JNF</p>
        </footer>
      </div>
    </div>
  );
};

export default Login;