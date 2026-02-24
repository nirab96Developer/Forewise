import React, { useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import api from "../../services/api";

const ResetPassword: React.FC = () => {
  const [search] = useSearchParams();
  const token = useMemo(() => search.get("token") || "", [search]);
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    if (!token) {
      setError("קישור איפוס לא תקין.");
      return;
    }
    if (newPassword !== confirmPassword) {
      setError("הסיסמאות אינן תואמות.");
      return;
    }
    setLoading(true);
    try {
      await api.post("/auth/reset-password/confirm", {
        token,
        new_password: newPassword,
      });
      setMessage("הסיסמה עודכנה בהצלחה. ניתן להתחבר מחדש.");
      setNewPassword("");
      setConfirmPassword("");
    } catch (err: any) {
      setError(err?.response?.data?.detail || "קישור לא תקין או שפג תוקף.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 via-white to-green-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-2xl border-2 border-green-100 w-full max-w-md p-6">
        <h1 className="text-2xl font-bold text-green-900 mb-2 text-right">איפוס סיסמה</h1>
        <p className="text-sm text-gray-600 mb-5 text-right">הזן סיסמה חדשה לחשבון.</p>
        <form onSubmit={handleSubmit} className="space-y-4">
          <input
            type="password"
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
            required
            minLength={8}
            className="w-full p-3 text-right border-2 border-gray-200 rounded-xl focus:outline-none focus:border-green-500"
            placeholder="סיסמה חדשה"
          />
          <input
            type="password"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            required
            minLength={8}
            className="w-full p-3 text-right border-2 border-gray-200 rounded-xl focus:outline-none focus:border-green-500"
            placeholder="אימות סיסמה חדשה"
          />
          {message && <div className="text-green-700 text-sm bg-green-50 p-3 rounded-lg">{message}</div>}
          {error && <div className="text-red-700 text-sm bg-red-50 p-3 rounded-lg">{error}</div>}
          <button
            type="submit"
            disabled={loading}
            className="w-full bg-green-600 hover:bg-green-700 text-white py-3 rounded-xl font-bold disabled:opacity-50"
          >
            {loading ? "מעדכן..." : "עדכן סיסמה"}
          </button>
        </form>
        <div className="mt-4 text-sm text-right">
          <Link to="/login" className="text-kkl-blue hover:underline">
            חזרה להתחברות
          </Link>
        </div>
      </div>
    </div>
  );
};

export default ResetPassword;
