// src/pages/Auth/ChangePassword.tsx
// שינוי סיסמה בכניסה ראשונה — מוצג אוטומטית כשmust_change_password=true
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Lock, Eye, EyeOff, CheckCircle, AlertCircle } from 'lucide-react';
import api from '../../services/api';

const ChangePassword: React.FC = () => {
  const navigate = useNavigate();
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showCurrent, setShowCurrent] = useState(false);
  const [showNew, setShowNew] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);

  const validate = () => {
    if (!currentPassword) return 'חובה להזין סיסמה נוכחית';
    if (newPassword.length < 8) return 'סיסמה חדשה חייבת להכיל לפחות 8 תווים';
    if (newPassword === currentPassword) return 'הסיסמה החדשה חייבת להיות שונה מהישנה';
    if (newPassword !== confirmPassword) return 'הסיסמאות אינן תואמות';
    return null;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const err = validate();
    if (err) { setError(err); return; }

    setLoading(true);
    setError('');
    try {
      const rawUser = localStorage.getItem('user');
      const userId = rawUser ? JSON.parse(rawUser).id : null;
      if (!userId) throw new Error('משתמש לא מחובר');
      await api.post(`/users/${userId}/password`, {
        current_password: currentPassword,
        new_password: newPassword,
      });

      // Update local user object to clear must_change_password
      if (rawUser) {
        try {
          const user = JSON.parse(rawUser);
          user.must_change_password = false;
          localStorage.setItem('user', JSON.stringify(user));
        } catch {}
      }

      setSuccess(true);
      setTimeout(() => navigate('/', { replace: true }), 1800);
    } catch (e: any) {
      setError(e?.response?.data?.detail || 'שגיאה בשינוי הסיסמה');
    } finally {
      setLoading(false);
    }
  };

  const strength = (pw: string) => {
    if (pw.length === 0) return 0;
    let score = 0;
    if (pw.length >= 8) score++;
    if (/[A-Z]/.test(pw)) score++;
    if (/[0-9]/.test(pw)) score++;
    if (/[^A-Za-z0-9]/.test(pw)) score++;
    return score;
  };

  const strengthLabel = ['', 'חלשה', 'בינונית', 'חזקה', 'חזקה מאוד'];
  const strengthColor = ['', 'bg-red-500', 'bg-orange-400', 'bg-yellow-400', 'bg-green-500'];
  const pw_strength = strength(newPassword);

  if (success) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50" dir="rtl">
        <div className="bg-white rounded-2xl shadow-lg p-8 max-w-sm w-full text-center">
          <CheckCircle className="w-16 h-16 text-green-500 mx-auto mb-4" />
          <h2 className="text-xl font-bold text-gray-900 mb-2">הסיסמה שונתה בהצלחה!</h2>
          <p className="text-gray-500 text-sm">מעביר אותך לדף הראשי...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 p-4" dir="rtl">
      <div className="bg-white rounded-2xl shadow-lg w-full max-w-sm">
        {/* Header */}
        <div className="bg-gradient-to-r from-green-600 to-green-700 px-6 py-5 rounded-t-2xl text-white text-center">
          <Lock className="w-10 h-10 mx-auto mb-2 opacity-90" />
          <h1 className="text-xl font-bold">שינוי סיסמה ראשוני</h1>
          <p className="text-green-100 text-sm mt-1">עליך לשנות את הסיסמה הזמנית לפני כניסה למערכת</p>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {error && (
            <div className="flex items-center gap-2 bg-red-50 text-red-700 text-sm px-4 py-3 rounded-xl border border-red-200">
              <AlertCircle className="w-4 h-4 flex-shrink-0" />
              {error}
            </div>
          )}

          {/* Current password */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">סיסמה נוכחית (זמנית)</label>
            <div className="relative">
              <input
                type={showCurrent ? 'text' : 'password'}
                value={currentPassword}
                onChange={e => setCurrentPassword(e.target.value)}
                className="w-full px-4 py-2.5 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-green-500 pl-10"
                placeholder="הסיסמה שקיבלת במייל"
                autoComplete="current-password"
              />
              <button type="button" onClick={() => setShowCurrent(!showCurrent)}
                className="absolute left-3 top-2.5 text-gray-400 hover:text-gray-600">
                {showCurrent ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>
          </div>

          {/* New password */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">סיסמה חדשה</label>
            <div className="relative">
              <input
                type={showNew ? 'text' : 'password'}
                value={newPassword}
                onChange={e => setNewPassword(e.target.value)}
                className="w-full px-4 py-2.5 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-green-500 pl-10"
                placeholder="לפחות 8 תווים"
                autoComplete="new-password"
              />
              <button type="button" onClick={() => setShowNew(!showNew)}
                className="absolute left-3 top-2.5 text-gray-400 hover:text-gray-600">
                {showNew ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>
            {/* Strength bar */}
            {newPassword && (
              <div className="mt-1.5">
                <div className="flex gap-1 mb-1">
                  {[1, 2, 3, 4].map(i => (
                    <div key={i} className={`h-1 flex-1 rounded-full ${i <= pw_strength ? strengthColor[pw_strength] : 'bg-gray-200'}`} />
                  ))}
                </div>
                <p className="text-xs text-gray-500">חוזק: <span className="font-medium">{strengthLabel[pw_strength]}</span></p>
              </div>
            )}
          </div>

          {/* Confirm */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">אימות סיסמה חדשה</label>
            <input
              type="password"
              value={confirmPassword}
              onChange={e => setConfirmPassword(e.target.value)}
              className={`w-full px-4 py-2.5 border rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-green-500 ${
                confirmPassword && confirmPassword !== newPassword ? 'border-red-300 bg-red-50' : 'border-gray-200'
              }`}
              placeholder="הקלד שוב את הסיסמה החדשה"
              autoComplete="new-password"
            />
            {confirmPassword && confirmPassword !== newPassword && (
              <p className="text-xs text-red-500 mt-1">הסיסמאות אינן תואמות</p>
            )}
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-3 bg-green-600 hover:bg-green-700 text-white rounded-xl font-medium text-sm disabled:opacity-50 transition-colors mt-2"
          >
            {loading ? 'שומר...' : 'שמור סיסמה חדשה'}
          </button>

          <button
            type="button"
            onClick={() => navigate('/login', { replace: true })}
            className="w-full py-2 text-sm text-gray-500 hover:text-gray-700 transition-colors"
          >
            חזרה לכניסה
          </button>
        </form>
      </div>
    </div>
  );
};

export default ChangePassword;
