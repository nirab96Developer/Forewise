import React, { useState } from "react";
import { Link } from "react-router-dom";
import api from "../../services/api";

const ForgotPassword: React.FC = () => {
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      await api.post("/auth/reset-password", { email: email.trim() });
      setMessage("אם המייל קיים במערכת, נשלח אליו קישור לאיפוס סיסמה.");
    } catch (err: any) {
      setError(err?.response?.data?.detail || "אירעה שגיאה, נסה שוב.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 via-white to-green-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-2xl border-2 border-green-100 w-full max-w-md p-6">
        <h1 className="text-2xl font-bold text-green-900 mb-2 text-right">שכחתי סיסמה</h1>
        <p className="text-sm text-gray-600 mb-5 text-right">הזן את כתובת המייל לקבלת קישור לאיפוס.</p>
        <form onSubmit={handleSubmit} className="space-y-4">
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            className="w-full p-3 text-right border-2 border-gray-200 rounded-xl focus:outline-none focus:border-green-500"
            placeholder="email@example.com"
          />
          {message && <div className="text-green-700 text-sm bg-green-50 p-3 rounded-lg">{message}</div>}
          {error && <div className="text-red-700 text-sm bg-red-50 p-3 rounded-lg">{error}</div>}
          <button
            type="submit"
            disabled={loading}
            className="w-full bg-green-600 hover:bg-green-700 text-white py-3 rounded-xl font-bold disabled:opacity-50"
          >
            {loading ? "שולח..." : "שלח קישור איפוס"}
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

export default ForgotPassword;
