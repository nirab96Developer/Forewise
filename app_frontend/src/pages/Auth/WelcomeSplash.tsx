// src/pages/Auth/WelcomeSplash.tsx
import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { TreeDeciduous, Fingerprint, ScanFace, Monitor, CheckCircle } from 'lucide-react';
import biometricService from '../../services/biometricService';
import { getBiometricLabel } from '../../utils/deviceDetector';

const DURATION_MS = 5000;
const CIRCLE_R = 48;
const CIRCUMFERENCE = 2 * Math.PI * CIRCLE_R;

function relativeTime(isoDate?: string | null): string {
  if (!isoDate) return '';
  const d = new Date(isoDate);
  if (Number.isNaN(d.getTime())) return '';
  const diff = Date.now() - d.getTime();
  const mins  = Math.floor(diff / 60_000);
  const hours = Math.floor(diff / 3_600_000);
  const days  = Math.floor(diff / 86_400_000);
  if (mins  < 2)  return 'לפני רגע';
  if (mins  < 60) return `לפני ${mins} דקות`;
  if (hours < 24) return `לפני ${hours} שעות`;
  if (days  === 1) return 'לפני יום';
  if (days  < 7)  return `לפני ${days} ימים`;
  if (days  < 14) return 'לפני שבוע';
  return `לפני ${Math.floor(days / 7)} שבועות`;
}

/** Read first name from all possible localStorage keys */
function readFirstName(): string {
  try {
    // 1. Try the user JSON object (multiple possible field names)
    const userStr = localStorage.getItem('user');
    if (userStr) {
      const u = JSON.parse(userStr);
      const full: string =
        u.first_name ||
        (u.full_name  ? u.full_name.split(' ')[0]  : '') ||
        (u.name       ? u.name.split(' ')[0]        : '') ||
        '';
      if (full) return full;
    }
    // 2. Try the standalone userName key
    const userName = localStorage.getItem('userName') || localStorage.getItem('user_name');
    if (userName) return userName.split(' ')[0];
  } catch { /* ignore */ }
  return '';
}

function readLastLogin(): string | null {
  try {
    const u = JSON.parse(localStorage.getItem('user') || '{}');
    return u.last_login || null;
  } catch { return null; }
}

const WelcomeSplash: React.FC = () => {
  const navigate = useNavigate();
  const [progress, setProgress]         = useState(0);
  const [showBioPrompt, setShowBioPrompt] = useState(false);
  const [bioStatus, setBioStatus]       = useState<'idle'|'registering'|'done'|'error'>('idle');
  const [bioError, setBioError]         = useState('');
  const [paused, setPaused]             = useState(false);  // pause countdown while prompt is shown

  const firstName    = readFirstName();
  const lastLogin    = readLastLogin();
  const lastLoginTxt = relativeTime(lastLogin);
  const biometric    = getBiometricLabel();

  // Decide whether to show biometric prompt
  useEffect(() => {
    (async () => {
      if (!biometricService.isRegistered() && await biometricService.isAvailable()) {
        setShowBioPrompt(true);
        setPaused(true);
      }
    })();
  }, []);

  // Countdown
  useEffect(() => {
    if (paused) return;
    const start = Date.now();
    const id = setInterval(() => {
      const pct = Math.min(((Date.now() - start) / DURATION_MS) * 100, 100);
      setProgress(pct);
      if (pct >= 100) { clearInterval(id); navigate('/', { replace: true }); }
    }, 40);
    return () => clearInterval(id);
  }, [navigate, paused]);

  const handleRegister = async () => {
    setBioStatus('registering');
    setBioError('');
    try {
      await biometricService.register();
      setBioStatus('done');
      setTimeout(() => {
        setShowBioPrompt(false);
        setPaused(false);
      }, 1500);
    } catch (e: any) {
      setBioStatus('error');
      setBioError(e.message || 'שגיאה בהפעלת הביומטריה');
    }
  };

  const handleSkip = () => {
    setShowBioPrompt(false);
    setPaused(false);
  };

  const dashOffset = CIRCUMFERENCE * (1 - progress / 100);

  return (
    <div
      className="fixed inset-0 bg-white flex flex-col items-center justify-center gap-7"
      dir="rtl"
    >
      {/* ── Progress ring + tree ── */}
      <div className="relative" style={{ width: 120, height: 120 }}>
        {/* SVG ring */}
        <svg
          width="120" height="120"
          style={{ transform: 'rotate(-90deg)', position: 'absolute', inset: 0 }}
        >
          <circle cx="60" cy="60" r={CIRCLE_R} fill="none" stroke="#d1fae5" strokeWidth="8" />
          <circle
            cx="60" cy="60" r={CIRCLE_R}
            fill="none"
            stroke="#16a34a"
            strokeWidth="8"
            strokeLinecap="round"
            strokeDasharray={CIRCUMFERENCE}
            strokeDashoffset={dashOffset}
            style={{ transition: 'stroke-dashoffset 40ms linear' }}
          />
        </svg>
        {/* Tree icon — same as LoadingScreen */}
        <div className="absolute inset-0 flex items-center justify-center">
          <TreeDeciduous size={52} className="text-green-600" strokeWidth={1.4} />
        </div>
      </div>

      {/* ── Text ── */}
      <div className="text-center space-y-2">
        <h2 className="text-2xl font-bold text-green-900">
          {firstName ? `שלום, ${firstName}! 👋` : 'ברוך הבא! 👋'}
        </h2>
        {lastLoginTxt && (
          <p className="text-sm text-gray-500">
            ההתחברות האחרונה שלך הייתה{' '}
            <span className="font-semibold text-gray-700">{lastLoginTxt}</span>
          </p>
        )}
        {!showBioPrompt && <p className="text-xs text-gray-400">טוען נתונים...</p>}
      </div>

      {/* ── Biometric registration prompt ── */}
      {showBioPrompt && (
        <div className="bg-white border border-green-200 rounded-2xl shadow-lg p-5 w-80 text-center space-y-4" dir="rtl">
          {/* Icon */}
          <div className="flex justify-center">
            <div className="w-14 h-14 bg-green-50 rounded-full flex items-center justify-center">
              {biometric.icon === 'scan-face'
                ? <ScanFace className="w-7 h-7 text-green-600" />
                : biometric.icon === 'monitor'
                ? <Monitor className="w-7 h-7 text-green-600" />
                : <Fingerprint className="w-7 h-7 text-green-600" />}
            </div>
          </div>

          {bioStatus === 'done' ? (
            <div className="flex flex-col items-center gap-2 text-green-700">
              <CheckCircle className="w-8 h-8" />
              <p className="font-semibold">הופעל בהצלחה! 🎉</p>
            </div>
          ) : (
            <>
              <div>
                <h3 className="font-bold text-gray-800 text-base">הפעל {biometric.text.replace('התחברות עם ', '').replace('התחברות ביומטרית', 'ביומטריה')}</h3>
                <p className="text-sm text-gray-500 mt-1">
                  כנס בקליק אחד בפעמים הבאות — ללא סיסמה
                </p>
              </div>

              {bioStatus === 'error' && (
                <p className="text-xs text-red-500 bg-red-50 rounded-lg px-3 py-2">{bioError}</p>
              )}

              <div className="flex gap-2">
                <button
                  onClick={handleSkip}
                  className="flex-1 py-2 border border-gray-200 rounded-xl text-gray-500 text-sm hover:bg-gray-50 transition-colors"
                >
                  אחר כך
                </button>
                <button
                  onClick={handleRegister}
                  disabled={bioStatus === 'registering'}
                  className="flex-1 py-2 bg-green-600 hover:bg-green-700 text-white rounded-xl text-sm font-medium transition-colors disabled:opacity-50"
                >
                  {bioStatus === 'registering' ? 'מפעיל...' : 'הפעל'}
                </button>
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
};

export default WelcomeSplash;
