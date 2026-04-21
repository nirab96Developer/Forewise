import React, { useEffect, useState, useCallback } from 'react';
import { ArrowLeftRight, Plus, X } from 'lucide-react';
import api from '../../services/api';
import { useRoleAccess } from '../../hooks/useRoleAccess';
import { getBudgetTransferStatusLabel } from '../../strings';

interface Transfer {
  id: number;
  from_budget_id: number | null;
  to_budget_id: number;
  requested_by: number;
  approved_by: number | null;
  amount: number;
  transfer_type: string;
  reason: string;
  status: string;
  notes: string | null;
  rejected_reason: string | null;
  requested_at: string | null;
  approved_at: string | null;
}

const STATUS_BADGE: Record<string, string> = {
  PENDING:  'bg-yellow-100 text-yellow-800',
  APPROVED: 'bg-green-100 text-green-700',
  REJECTED: 'bg-red-100 text-red-700',
  COMPLETED:'bg-blue-100 text-blue-700',
};
// Labels live in `src/strings/statuses.ts` — see BUDGET_TRANSFER_STATUS_LABELS.
const STATUS_LABEL = (s: string) => getBudgetTransferStatusLabel(s);

// Request Modal 
interface RequestModalProps {
  budgets: any[];
  onClose: () => void;
  onDone: () => void;
}
const RequestModal: React.FC<RequestModalProps> = ({ budgets, onClose, onDone }) => {
  const [toBudgetId, setToBudgetId] = useState('');
  const [amount, setAmount] = useState('');
  const [reason, setReason] = useState('');
  const [saving, setSaving] = useState(false);
  const [err, setErr] = useState('');

  const handleSubmit = async () => {
    if (!toBudgetId || !amount || !reason.trim()) { setErr('מלא את כל השדות'); return; }
    if (Number(amount) <= 0) { setErr('סכום חייב להיות חיובי'); return; }
    setSaving(true); setErr('');
    try {
      await api.post('/budget-transfers/request', {
        to_budget_id: Number(toBudgetId),
        amount: Number(amount),
        reason: reason.trim(),
        transfer_type: 'regular',
      });
      onDone();
    } catch (e: any) {
      setErr(e?.response?.data?.detail || 'שגיאה ביצירת הבקשה');
    }
    setSaving(false);
  };

  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4" dir="rtl">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-md">
        <div className="flex items-center justify-between px-5 py-4 border-b border-gray-100">
          <h2 className="font-bold text-gray-900 text-lg flex items-center gap-2">
            <ArrowLeftRight className="w-5 h-5 text-blue-500" />
            בקשת תוספת תקציב
          </h2>
          <button onClick={onClose} className="p-1.5 hover:bg-gray-100 rounded-lg text-gray-400"><X className="w-4 h-4" /></button>
        </div>
        <div className="p-5 space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">תקציב יעד *</label>
            <select value={toBudgetId} onChange={e => setToBudgetId(e.target.value)}
              className="w-full border border-gray-300 rounded-xl px-3 pr-3 pl-10 py-2 text-sm">
              <option value="">בחר תקציב...</option>
              {budgets.map((b: any) => (
<option key={b.id} value={b.id}>{b.name || b.code} — {Number(b.total_amount||0).toLocaleString()}</option>
              ))}
            </select>
          </div>
          <div>
<label className="block text-sm font-medium text-gray-700 mb-1">סכום מבוקש () *</label>
            <input type="number" value={amount} onChange={e => setAmount(e.target.value)} min="1"
              className="w-full border border-gray-300 rounded-xl px-3 py-2 text-sm" placeholder="0" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">סיבת הבקשה *</label>
            <textarea rows={3} value={reason} onChange={e => setReason(e.target.value)}
              className="w-full border border-gray-300 rounded-xl px-3 py-2 text-sm resize-none"
              placeholder="תאר את הצורך בתוספת תקציב..." />
          </div>
          {err && <p className="text-sm text-red-600">{err}</p>}
        </div>
        <div className="flex gap-2 px-5 py-4 border-t border-gray-100">
          <button onClick={handleSubmit} disabled={saving}
            className="flex-1 py-2.5 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white font-medium rounded-xl">
{saving ? 'שולח...' : ' שלח בקשה'}
          </button>
          <button onClick={onClose} className="px-4 py-2.5 border border-gray-200 rounded-xl text-gray-600 hover:bg-gray-50 text-sm">ביטול</button>
        </div>
      </div>
    </div>
  );
};

// Approve Modal 
interface ApproveModalProps {
  transfer: Transfer;
  onClose: () => void;
  onDone: () => void;
}
const ApproveModal: React.FC<ApproveModalProps> = ({ transfer, onClose, onDone }) => {
  const [approvedAmount, setApprovedAmount] = useState(String(transfer.amount));
  const [notes, setNotes] = useState('');
  const [saving, setSaving] = useState(false);
  const [err, setErr] = useState('');

  const handleApprove = async () => {
    setSaving(true); setErr('');
    try {
      await api.post(`/budget-transfers/${transfer.id}/approve`, {
        approved_amount: Number(approvedAmount), notes,
      });
      onDone();
    } catch (e: any) { setErr(e?.response?.data?.detail || 'שגיאה'); }
    setSaving(false);
  };

  const handleReject = async () => {
    if (!notes.trim()) { setErr('נדרשת סיבת דחייה'); return; }
    setSaving(true); setErr('');
    try {
      await api.post(`/budget-transfers/${transfer.id}/reject`, { reason: notes });
      onDone();
    } catch (e: any) { setErr(e?.response?.data?.detail || 'שגיאה'); }
    setSaving(false);
  };

  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4" dir="rtl">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-md">
        <div className="flex items-center justify-between px-5 py-4 border-b border-gray-100">
          <h2 className="font-bold text-gray-900 text-lg">אישור / דחיית בקשה</h2>
          <button onClick={onClose} className="p-1.5 hover:bg-gray-100 rounded-lg text-gray-400"><X className="w-4 h-4" /></button>
        </div>
        <div className="p-5 space-y-4">
          <div className="bg-gray-50 rounded-xl p-3 text-sm">
            <div className="font-medium text-gray-700 mb-1">סיבת הבקשה:</div>
            <div className="text-gray-600">{transfer.reason}</div>
          </div>
          <div>
<label className="block text-sm font-medium text-gray-700 mb-1">סכום לאישור ()</label>
            <input type="number" value={approvedAmount} onChange={e => setApprovedAmount(e.target.value)}
              min="1" max={transfer.amount}
              className="w-full border border-gray-300 rounded-xl px-3 py-2 text-sm" />
<p className="text-xs text-gray-400 mt-1">ניתן לאשר סכום חלקי (מקסימום {transfer.amount.toLocaleString()})</p>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">הערות (חובה לדחייה)</label>
            <textarea rows={2} value={notes} onChange={e => setNotes(e.target.value)}
              className="w-full border border-gray-300 rounded-xl px-3 py-2 text-sm resize-none" />
          </div>
          {err && <p className="text-sm text-red-600">{err}</p>}
        </div>
        <div className="flex gap-2 px-5 py-4 border-t border-gray-100">
          <button onClick={handleApprove} disabled={saving}
            className="flex-1 py-2.5 bg-green-600 hover:bg-green-700 disabled:opacity-50 text-white font-medium rounded-xl text-sm">
אשר
          </button>
          <button onClick={handleReject} disabled={saving}
            className="flex-1 py-2.5 bg-red-500 hover:bg-red-600 disabled:opacity-50 text-white font-medium rounded-xl text-sm">
דחה
          </button>
          <button onClick={onClose} className="px-3 border border-gray-200 rounded-xl text-gray-600 hover:bg-gray-50 text-sm">ביטול</button>
        </div>
      </div>
    </div>
  );
};

// Main Page 
const BudgetTransfers: React.FC = () => {
  const [transfers, setTransfers] = useState<Transfer[]>([]);
  const [budgets, setBudgets] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const { canApproveBudgetTransfers, canManageBudgets } = useRoleAccess();
  const [filterStatus, setFilterStatus] = useState('');
  const [showRequestModal, setShowRequestModal] = useState(false);
  const [approveTarget, setApproveTarget] = useState<Transfer | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [tr, bud] = await Promise.all([
        api.get('/budget-transfers', { params: filterStatus ? { status_filter: filterStatus } : {} }),
        api.get('/budgets').catch(() => ({ data: [] })),
      ]);
      setTransfers(tr.data?.items || tr.data || []);
      setBudgets(bud.data?.items || bud.data || []);
    } catch { /* silent */ }
    setLoading(false);
  }, [filterStatus]);

  useEffect(() => { load(); }, [load]);

  const handleDone = () => {
    setShowRequestModal(false);
    setApproveTarget(null);
    load();
  };

  const pending = transfers.filter(t => t.status === 'PENDING');
  const rest = transfers.filter(t => t.status !== 'PENDING');

  return (
    <div className="min-h-screen bg-gray-50 pt-6 pb-10 px-4" dir="rtl">
      {showRequestModal && <RequestModal budgets={budgets} onClose={() => setShowRequestModal(false)} onDone={handleDone} />}
      {approveTarget && <ApproveModal transfer={approveTarget} onClose={() => setApproveTarget(null)} onDone={handleDone} />}

      <div className="max-w-4xl mx-auto">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
              <ArrowLeftRight className="w-6 h-6 text-blue-500" />
              בקשות העברת תקציב
            </h1>
            <p className="text-sm text-gray-500 mt-0.5">{pending.length} ממתינות לאישור</p>
          </div>
          {canManageBudgets && (
            <button onClick={() => setShowRequestModal(true)}
              className="flex items-center gap-2 px-4 py-2.5 bg-blue-600 text-white rounded-xl hover:bg-blue-700 font-medium shadow-sm">
              <Plus className="w-4 h-4" /> בקשה חדשה
            </button>
          )}
        </div>

        {/* Filter */}
        <div className="flex gap-2 mb-4">
          {['', 'PENDING', 'APPROVED', 'REJECTED'].map(s => (
            <button key={s} onClick={() => setFilterStatus(s)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                filterStatus === s ? 'bg-blue-600 text-white' : 'bg-white text-gray-600 hover:bg-gray-100 border border-gray-200'
              }`}>
              {s === '' ? 'הכל' : STATUS_LABEL(s)}
            </button>
          ))}
        </div>

        {loading ? (
          <div className="flex justify-center py-16"><div className="relative overflow-visible" style={{ padding: 4 }}>
          <div className="w-12 h-12 rounded-full border-[3px] border-emerald-200 border-t-emerald-500 animate-spin" style={{animationDuration:'0.9s'}} />
          <div className="absolute inset-0 flex items-center justify-center">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 100" width="24" height="20">
                <defs>
                  <linearGradient id="bt1_t" x1="0%" y1="0%" x2="100%" y2="0%"><stop offset="0%" stopColor="#1565c0"/><stop offset="100%" stopColor="#0097a7"/></linearGradient>
                  <linearGradient id="bt1_m" x1="0%" y1="0%" x2="100%" y2="0%"><stop offset="0%" stopColor="#0097a7"/><stop offset="50%" stopColor="#2e7d32"/><stop offset="100%" stopColor="#66bb6a"/></linearGradient>
                  <linearGradient id="bt1_b" x1="0%" y1="0%" x2="100%" y2="0%"><stop offset="0%" stopColor="#2e7d32"/><stop offset="40%" stopColor="#66bb6a"/><stop offset="100%" stopColor="#8B5e3c"/></linearGradient>
                </defs>
                <path d="M46 20 Q60 9 74 20" stroke="url(#bt1_t)" strokeWidth="5.5" fill="none" strokeLinecap="round"/>
                <path d="M30 47 Q42 34 60 43 Q78 34 90 47" stroke="url(#bt1_m)" strokeWidth="5.5" fill="none" strokeLinecap="round"/>
                <path d="M14 74 Q28 60 46 69 Q60 76 74 69 Q92 60 106 74" stroke="url(#bt1_b)" strokeWidth="5.5" fill="none" strokeLinecap="round"/>
                <line x1="60" y1="76" x2="60" y2="90" stroke="#8B5e3c" strokeWidth="3.5" strokeLinecap="round"/>
                <circle cx="60" cy="95" r="5" fill="#8B5e3c"/>
              </svg>
          </div>
        </div></div>
        ) : transfers.length === 0 ? (
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-12 text-center">
            <ArrowLeftRight className="w-14 h-14 text-gray-300 mx-auto mb-3" />
            <p className="text-gray-500">אין בקשות העברה</p>
          </div>
        ) : (
          <div className="space-y-3">
            {/* Pending first */}
            {pending.length > 0 && (
              <div className="bg-yellow-50 border border-yellow-200 rounded-xl overflow-hidden">
                <div className="px-4 py-2 bg-yellow-100 text-yellow-800 text-xs font-semibold">ממתינות לאישור</div>
                {pending.map(t => (
                  <TransferRow key={t.id} t={t} onApprove={canApproveBudgetTransfers ? () => setApproveTarget(t) : undefined} />
                ))}
              </div>
            )}
            {/* Rest */}
            {rest.length > 0 && (
              <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
                {rest.map(t => (
                  <TransferRow key={t.id} t={t} />
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

const TransferRow: React.FC<{ t: Transfer; onApprove?: () => void }> = ({ t, onApprove }) => (
  <div className="flex items-start gap-4 px-5 py-4 border-b border-gray-100 last:border-0 hover:bg-gray-50">
    <div className="flex-1 min-w-0">
      <div className="flex items-center gap-2 flex-wrap">
        <span className={`px-2.5 py-0.5 rounded-full text-xs font-medium ${STATUS_BADGE[t.status] || 'bg-gray-100 text-gray-600'}`}>
          {STATUS_LABEL(t.status)}
        </span>
<span className="text-sm font-semibold text-gray-900">{t.amount.toLocaleString()}</span>
        <span className="text-xs text-gray-400">{t.transfer_type}</span>
      </div>
      <p className="text-sm text-gray-600 mt-1">{t.reason}</p>
      {t.rejected_reason && (
        <p className="text-xs text-red-500 mt-0.5">סיבת דחייה: {t.rejected_reason}</p>
      )}
      <p className="text-xs text-gray-400 mt-0.5">
        {t.requested_at ? new Date(t.requested_at).toLocaleDateString('he-IL') : ''}
      </p>
    </div>
    {onApprove && t.status === 'PENDING' && (
      <button onClick={onApprove}
        className="flex-shrink-0 px-3 py-1.5 bg-green-600 hover:bg-green-700 text-white text-xs font-medium rounded-lg">
        אשר / דחה
      </button>
    )}
  </div>
);

export default BudgetTransfers;
