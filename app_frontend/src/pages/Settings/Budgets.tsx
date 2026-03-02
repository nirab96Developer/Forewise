
import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { DollarSign, ChevronLeft } from "lucide-react";
import api from "../../services/api";

const Budgets: React.FC = () => {
  const navigate = useNavigate();
  const [budgets, setBudgets] = useState<any[]>([]);
  const [summary, setSummary] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [budgetsRes, summaryRes] = await Promise.all([
        api.get('/budgets'),
        api.get('/dashboard/financial-summary').catch(() => ({ data: null })),
      ]);
      setBudgets(budgetsRes.data?.items || budgetsRes.data || []);
      setSummary(summaryRes.data);
    } catch (err) {
      console.error('Error:', err);
    }
    setLoading(false);
  };

  const fmt = (n: any) => n ? Number(n).toLocaleString('he-IL') : '0';
  const pct = (spent: any, total: any) => total > 0 ? Math.round((Number(spent || 0) / Number(total)) * 100) : 0;

  if (loading) return <div className="flex items-center justify-center min-h-screen"><div className="w-10 h-10 border-4 border-green-200 border-t-green-600 rounded-full animate-spin" /></div>;

  return (
    <div className="min-h-screen bg-gray-50 p-6" dir="rtl">
      <div className="max-w-6xl mx-auto">
        <div className="flex items-center gap-3 mb-6">
          <button onClick={() => navigate('/settings')} className="p-2 hover:bg-gray-200 rounded-lg"><ChevronLeft className="w-5 h-5" /></button>
          <DollarSign className="w-8 h-8 text-orange-600" />
          <div>
            <h1 className="text-2xl font-bold text-gray-900">ניהול תקציבים</h1>
            <p className="text-gray-500 text-sm">תקציבי פרויקטים, ניצול והתחייבויות</p>
          </div>
        </div>

        {/* Financial KPIs */}
        {summary?.budgets && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            <div className="bg-white rounded-xl border p-4">
              <div className="text-sm text-gray-500">סה"כ תקציב</div>
              <div className="text-xl font-bold text-gray-900">{fmt(summary.budgets.total)}₪</div>
            </div>
            <div className="bg-white rounded-xl border p-4">
              <div className="text-sm text-gray-500">התחייבויות</div>
              <div className="text-xl font-bold text-orange-600">{fmt(summary.budgets.committed)}₪</div>
            </div>
            <div className="bg-white rounded-xl border p-4">
              <div className="text-sm text-gray-500">ביצוע בפועל</div>
              <div className="text-xl font-bold text-blue-600">{fmt(summary.budgets.spent)}₪</div>
            </div>
            <div className="bg-white rounded-xl border p-4">
              <div className="text-sm text-gray-500">יתרה</div>
              <div className="text-xl font-bold text-green-600">{fmt(summary.budgets.remaining)}₪</div>
            </div>
          </div>
        )}

        {/* Budgets Table */}
        <div className="bg-white rounded-xl shadow-sm overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500">פרויקט</th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500">סה"כ</th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500">ביצוע</th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500">ניצול %</th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500">סטטוס</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {budgets.filter(b => b.project_id).slice(0, 30).map((b) => {
                const usage = pct(b.spent_amount, b.total_amount);
                return (
                  <tr key={b.id} className="hover:bg-gray-50 cursor-pointer" onClick={() => navigate(`/settings/budgets/${b.id}`)}>
                    <td className="px-4 py-3 text-sm font-medium text-gray-900">{b.name}</td>
                    <td className="px-4 py-3 text-sm text-gray-700">{fmt(b.total_amount)}₪</td>
                    <td className="px-4 py-3 text-sm text-gray-700">{fmt(b.spent_amount)}₪</td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <div className="flex-1 h-2 bg-gray-200 rounded-full overflow-hidden">
                          <div className={`h-full rounded-full ${usage > 90 ? 'bg-red-500' : usage > 70 ? 'bg-orange-500' : 'bg-green-500'}`} style={{width: `${Math.min(usage, 100)}%`}} />
                        </div>
                        <span className="text-xs font-medium text-gray-600 w-10">{usage}%</span>
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <span className={`px-2 py-1 rounded-full text-xs ${b.status === 'ACTIVE' ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-600'}`}>
                        {b.status === 'ACTIVE' ? 'פעיל' : b.status}
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
          <div className="p-4 bg-gray-50 text-center text-sm text-gray-500">
            {budgets.filter(b => b.project_id).length} תקציבים פעילים
          </div>
        </div>
      </div>
    </div>
  );
};

export default Budgets;
