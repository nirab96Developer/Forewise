
import React, { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { ChevronLeft, Truck, Clock, Wallet } from "lucide-react";
import api from "../../services/api";
import UnifiedLoader from "../../components/common/UnifiedLoader";
import { getBudgetStatusLabel, getWorkOrderStatusLabel, getWorklogStatusLabel } from "../../strings";

const BudgetDetail: React.FC = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [budget, setBudget] = useState<any>(null);
  const [committed, setCommitted] = useState<any>(null);
  const [spent, setSpent] = useState<any>(null);
  const [activeTab, setActiveTab] = useState<'overview' | 'committed' | 'spent'>('overview');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, [id]);

  const loadData = async () => {
    try {
      const [detailRes, committedRes, spentRes] = await Promise.all([
        api.get(`/budgets/${id}/detail`),
        api.get(`/budgets/${id}/committed`),
        api.get(`/budgets/${id}/spent`),
      ]);
      setBudget(detailRes.data);
      setCommitted(committedRes.data);
      setSpent(spentRes.data);
    } catch (err) {
      console.error('Error loading budget:', err);
    }
    setLoading(false);
  };

  const fmt = (n: any) => n ? Number(n).toLocaleString('he-IL') : '0';
  const pct = (v: any) => v !== undefined ? `${v}%` : '0%';

  if (loading) return <UnifiedLoader size="full" />;
  if (!budget) return <div className="p-8 text-center text-gray-500">תקציב לא נמצא</div>;

  const tabs = [
    { id: 'overview', label: 'פירוט', icon: Wallet },
    { id: 'committed', label: `התחייבויות (${committed?.total || 0})`, icon: Truck },
    { id: 'spent', label: `ביצוע (${spent?.total || 0})`, icon: Clock },
  ];

  return (
    <div className="min-h-screen bg-gray-50 p-6" dir="rtl">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="flex items-center gap-3 mb-6">
          <button onClick={() => navigate('/settings/budgets')} className="p-2 hover:bg-gray-200 rounded-lg"><ChevronLeft className="w-5 h-5" /></button>
          <span className="w-8 h-8 text-orange-600 font-bold leading-none inline-flex items-center justify-center">₪</span>
          <div className="flex-1">
            <h1 className="text-2xl font-bold text-gray-900">{budget.name}</h1>
            <div className="flex gap-3 mt-1">
              {budget.region_name && <span className="px-2 py-0.5 bg-green-100 text-green-700 rounded text-xs">{budget.region_name}</span>}
              {budget.area_name && <span className="px-2 py-0.5 bg-purple-100 text-purple-700 rounded text-xs">{budget.area_name}</span>}
              <span className={`px-2 py-0.5 rounded text-xs ${budget.status === 'ACTIVE' ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-600'}`}>{getBudgetStatusLabel(budget.status)}</span>
            </div>
          </div>
        </div>

        {/* KPI Cards */}
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-6">
          <div className="bg-white rounded-xl border p-4">
            <div className="text-xs text-gray-500">סה"כ תקציב</div>
<div className="text-lg font-bold text-gray-900">{fmt(budget.total_amount)}</div>
          </div>
          <div className="bg-white rounded-xl border p-4">
            <div className="text-xs text-gray-500">התחייבויות</div>
<div className="text-lg font-bold text-orange-600">{fmt(budget.committed_amount)}</div>
          </div>
          <div className="bg-white rounded-xl border p-4">
            <div className="text-xs text-gray-500">ביצוע בפועל</div>
<div className="text-lg font-bold text-blue-600">{fmt(budget.spent_amount)}</div>
          </div>
          <div className="bg-white rounded-xl border p-4">
            <div className="text-xs text-gray-500">יתרה</div>
<div className="text-lg font-bold text-green-600">{fmt(budget.remaining_amount)}</div>
          </div>
          <div className="bg-white rounded-xl border p-4">
            <div className="text-xs text-gray-500">ניצול</div>
            <div className="flex items-center gap-2">
              <div className="flex-1 h-3 bg-gray-200 rounded-full overflow-hidden">
                <div className={`h-full rounded-full ${budget.utilization_pct > 90 ? 'bg-red-500' : budget.utilization_pct > 70 ? 'bg-orange-500' : 'bg-green-500'}`} style={{width: `${Math.min(budget.utilization_pct, 100)}%`}} />
              </div>
              <span className="text-sm font-bold">{pct(budget.utilization_pct)}</span>
            </div>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex gap-1 mb-4 border-b">
          {tabs.map(tab => {
            const Icon = tab.icon;
            return (
              <button key={tab.id} onClick={() => setActiveTab(tab.id as any)}
                className={`flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 transition-colors ${activeTab === tab.id ? 'border-green-600 text-green-700' : 'border-transparent text-gray-500 hover:text-gray-700'}`}>
                <Icon className="w-4 h-4" />{tab.label}
              </button>
            );
          })}
        </div>

        {/* Tab Content */}
        <div className="bg-white rounded-xl shadow-sm overflow-hidden">
          {activeTab === 'overview' && (
            <div className="p-6">
              <h3 className="font-semibold text-gray-900 mb-4">סעיפי תקציב</h3>
              {budget.items?.length > 0 ? (
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-4 py-3 text-right text-xs font-medium text-gray-500">סעיף</th>
                      <th className="px-4 py-3 text-right text-xs font-medium text-gray-500">קטגוריה</th>
                      <th className="px-4 py-3 text-right text-xs font-medium text-gray-500">הקצאה</th>
                      <th className="px-4 py-3 text-right text-xs font-medium text-gray-500">ביצוע</th>
                      <th className="px-4 py-3 text-right text-xs font-medium text-gray-500">יתרה</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200">
                    {budget.items.map((item: any) => (
                      <tr key={item.id}>
                        <td className="px-4 py-3 text-sm font-medium text-gray-900">{item.name}</td>
                        <td className="px-4 py-3 text-sm"><span className="px-2 py-0.5 bg-blue-50 text-blue-700 rounded text-xs">{item.category}</span></td>
<td className="px-4 py-3 text-sm text-gray-700">{fmt(item.allocated)}</td>
<td className="px-4 py-3 text-sm text-gray-700">{fmt(item.used)}</td>
<td className="px-4 py-3 text-sm font-medium text-green-600">{fmt(item.remaining)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              ) : <p className="text-gray-500">אין סעיפי תקציב</p>}
            </div>
          )}

          {activeTab === 'committed' && (
            <div>
              <div className="p-4 bg-orange-50 border-b border-orange-200 flex items-center justify-between">
<span className="text-sm font-medium text-orange-800">{committed?.total || 0} הזמנות פעילות · סה"כ {fmt(committed?.sum)}</span>
              </div>
              {committed?.items?.length > 0 ? (
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-4 py-3 text-right text-xs font-medium text-gray-500">הזמנה</th>
                      <th className="px-4 py-3 text-right text-xs font-medium text-gray-500">ספק</th>
                      <th className="px-4 py-3 text-right text-xs font-medium text-gray-500">סטטוס</th>
                      <th className="px-4 py-3 text-right text-xs font-medium text-gray-500">סכום</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200">
                    {committed.items.map((wo: any) => (
                      <tr key={wo.work_order_id} className="hover:bg-gray-50 cursor-pointer" onClick={() => navigate(`/work-orders/${wo.work_order_id}`)}>
                        <td className="px-4 py-3 text-sm"><span className="font-medium text-blue-600">{wo.order_number || `#${wo.work_order_id}`}</span><br/><span className="text-xs text-gray-500">{wo.title}</span></td>
                        <td className="px-4 py-3 text-sm text-gray-700">{wo.supplier_name}</td>
                        <td className="px-4 py-3"><span className="px-2 py-0.5 bg-yellow-100 text-yellow-800 rounded text-xs">{getWorkOrderStatusLabel(wo.status)}</span></td>
<td className="px-4 py-3 text-sm font-medium text-orange-600">{fmt(wo.committed_amount)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              ) : <div className="p-8 text-center text-gray-500">אין התחייבויות פעילות</div>}
            </div>
          )}

          {activeTab === 'spent' && (
            <div>
              <div className="p-4 bg-blue-50 border-b border-blue-200 flex items-center justify-between">
<span className="text-sm font-medium text-blue-800">{spent?.total || 0} דיווחים · סה"כ {fmt(spent?.sum)} (+ {fmt(spent?.vat_sum)} מע"מ)</span>
              </div>
              {spent?.items?.length > 0 ? (
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-4 py-3 text-right text-xs font-medium text-gray-500">תאריך</th>
                      <th className="px-4 py-3 text-right text-xs font-medium text-gray-500">שעות</th>
                      <th className="px-4 py-3 text-right text-xs font-medium text-gray-500">תעריף</th>
                      <th className="px-4 py-3 text-right text-xs font-medium text-gray-500">סכום</th>
                      <th className="px-4 py-3 text-right text-xs font-medium text-gray-500">כולל מע"מ</th>
                      <th className="px-4 py-3 text-right text-xs font-medium text-gray-500">סטטוס</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200">
                    {spent.items.map((wl: any) => (
                      <tr key={wl.worklog_id} className="hover:bg-gray-50 cursor-pointer" onClick={() => navigate(`/work-logs/${wl.worklog_id}`)}>
                        <td className="px-4 py-3 text-sm text-gray-700">{wl.report_date}</td>
                        <td className="px-4 py-3 text-sm text-gray-700">{wl.hours}</td>
<td className="px-4 py-3 text-sm text-gray-700">{fmt(wl.hourly_rate)}</td>
<td className="px-4 py-3 text-sm font-medium text-gray-900">{fmt(wl.amount)}</td>
<td className="px-4 py-3 text-sm text-gray-700">{fmt(wl.total_with_vat)}</td>
                        <td className="px-4 py-3">{(() => {
                          const upper = (wl.status || '').toUpperCase();
                          const cls = upper === 'APPROVED' ? 'bg-green-100 text-green-700'
                            : upper === 'SUBMITTED' ? 'bg-yellow-100 text-yellow-700'
                            : 'bg-gray-100 text-gray-600';
                          return <span className={`px-2 py-0.5 rounded text-xs ${cls}`}>{getWorklogStatusLabel(wl.status)}</span>;
                        })()}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              ) : <div className="p-8 text-center text-gray-500">אין דיווחים עם עלות</div>}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default BudgetDetail;
