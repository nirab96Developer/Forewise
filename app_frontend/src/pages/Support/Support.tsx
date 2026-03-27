// src/pages/Support/Support.tsx
// ניהול קריאות תמיכה — WhatsApp style
import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  MessageSquare, CheckCircle2, Clock, AlertCircle,
  Send, RefreshCw, ChevronRight, X, User, Shield,
} from 'lucide-react';
import api from '../../services/api';

// Types 

type TicketStatus = 'open' | 'in_progress' | 'resolved';

interface Ticket {
  id: number;
  ticket_number: string;
  title: string;
  description: string;
  status: TicketStatus;
  priority: string;
  category: string;
  user_id: number;
  created_at: string;
  updated_at: string;
  // enriched
  user_name?: string;
}

interface Comment {
  id: number;
  ticket_id: number;
  user_id: number;
  user_name: string;
  is_staff: boolean;
  content: string;
  created_at: string;
}

// Helpers 

const STATUS_LABEL: Record<TicketStatus, string> = {
  open: 'פתוחה',
  in_progress: 'בטיפול',
  resolved: 'טופלה',
};

const STATUS_COLOR: Record<TicketStatus, string> = {
  open: 'bg-red-100 text-red-700',
  in_progress: 'bg-yellow-100 text-yellow-700',
  resolved: 'bg-green-100 text-green-700',
};

const STATUS_DOT: Record<TicketStatus, string> = {
  open: 'bg-red-500',
  in_progress: 'bg-yellow-400',
  resolved: 'bg-green-500',
};

const fmtDate = (iso: string) => {
  if (!iso) return '';
  const d = new Date(iso);
  return d.toLocaleDateString('he-IL') + ' ' + d.toLocaleTimeString('he-IL', { hour: '2-digit', minute: '2-digit' });
};

const fmtTime = (iso: string) => {
  if (!iso) return '';
  const d = new Date(iso);
  return d.toLocaleTimeString('he-IL', { hour: '2-digit', minute: '2-digit' });
};

// Component 

const Support: React.FC = () => {
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [selected, setSelected] = useState<Ticket | null>(null);
  const [comments, setComments] = useState<Comment[]>([]);
  const [reply, setReply] = useState('');
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [toastMsg, setToastMsg] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  const currentUser = useRef({ id: 0, name: '', role: '' });

  useEffect(() => {
    try {
      const u = JSON.parse(localStorage.getItem('user') || '{}');
      currentUser.current = { id: u.id || 0, name: u.full_name || u.name || '', role: u.role || '' };
    } catch {}
  }, []);

  const isAdmin = currentUser.current.role === 'ADMIN';

  const showToast = (msg: string) => {
    setToastMsg(msg);
    setTimeout(() => setToastMsg(null), 3000);
  };

  const loadTickets = useCallback(async () => {
    setLoading(true);
    try {
      const params = isAdmin ? {} : { user_id: currentUser.current.id };
      const res = await api.get('/support-tickets/', { params });
      const items: Ticket[] = Array.isArray(res.data)
        ? res.data
        : res.data?.items || res.data?.tickets || [];
      // Sort: open first, then by updated_at desc
      items.sort((a, b) => {
        const statusOrder: Record<TicketStatus, number> = { open: 0, in_progress: 1, resolved: 2 };
        const sa = statusOrder[a.status as TicketStatus] ?? 3;
        const sb = statusOrder[b.status as TicketStatus] ?? 3;
        if (sa !== sb) return sa - sb;
        return new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime();
      });
      setTickets(items);
    } catch (err) {
      console.error('Failed to load tickets', err);
    } finally {
      setLoading(false);
    }
  }, [isAdmin]);

  useEffect(() => { loadTickets(); }, [loadTickets]);

  const loadComments = useCallback(async (ticketId: number) => {
    try {
      const res = await api.get(`/support-tickets/${ticketId}/comments`);
      setComments(res.data || []);
      setTimeout(() => bottomRef.current?.scrollIntoView({ behavior: 'smooth' }), 100);
    } catch {}
  }, []);

  const openTicket = (ticket: Ticket) => {
    setSelected(ticket);
    setReply('');
    loadComments(ticket.id);
  };

  const sendReply = async () => {
    if (!reply.trim() || !selected) return;
    setSending(true);
    try {
      const res = await api.post(`/support-tickets/${selected.id}/comments`, { content: reply });
      setComments(prev => [...prev, res.data]);
      setReply('');
      setTimeout(() => bottomRef.current?.scrollIntoView({ behavior: 'smooth' }), 100);
    } catch {
      showToast('שגיאה בשליחת תגובה');
    } finally {
      setSending(false);
    }
  };

  const changeStatus = async (ticketId: number, newStatus: TicketStatus) => {
    try {
      await api.patch(`/support-tickets/${ticketId}/status`, { status: newStatus });
      setTickets(prev =>
        prev.map(t => t.id === ticketId ? { ...t, status: newStatus } : t)
      );
      if (selected?.id === ticketId) {
        setSelected(prev => prev ? { ...prev, status: newStatus } : prev);
      }
showToast(newStatus === 'resolved' ? ' הקריאה סומנה כטופלה' : ' סטטוס עודכן');
    } catch {
      showToast('שגיאה בעדכון סטטוס');
    }
  };

// Render 

  return (
    <div className="min-h-screen bg-gray-50" dir="rtl">
      {/* Toast */}
      {toastMsg && (
        <div className="fixed top-4 left-1/2 -translate-x-1/2 z-[2000] bg-gray-800 text-white text-sm px-5 py-2.5 rounded-xl shadow-xl">
          {toastMsg}
        </div>
      )}

      <div className="flex h-screen">
{/* LEFT: Ticket List */}
        <div className={`bg-white border-l border-gray-200 flex flex-col ${selected ? 'hidden md:flex w-80 flex-shrink-0' : 'flex-1 md:w-80 md:flex-none'}`}>
          {/* Header */}
          <div className="px-4 py-4 border-b border-gray-100 bg-green-600">
            <div className="flex items-center justify-between">
              <h1 className="text-white font-bold text-lg flex items-center gap-2">
                <MessageSquare className="w-5 h-5" />
                קריאות תמיכה
              </h1>
              <button onClick={loadTickets} className="text-green-200 hover:text-white p-1.5 rounded-lg hover:bg-white/10">
                <RefreshCw className="w-4 h-4" />
              </button>
            </div>
            <div className="flex gap-3 mt-2 text-xs text-green-200">
              <span className="flex items-center gap-1">
                <span className="w-2 h-2 rounded-full bg-red-400" />
                {tickets.filter(t => t.status === 'open').length} פתוחות
              </span>
              <span className="flex items-center gap-1">
                <span className="w-2 h-2 rounded-full bg-yellow-300" />
                {tickets.filter(t => t.status === 'in_progress').length} בטיפול
              </span>
            </div>
          </div>

          {/* List */}
          <div className="flex-1 overflow-y-auto divide-y divide-gray-100">
            {loading ? (
              <div className="flex items-center justify-center h-40 text-gray-400 text-sm">טוען...</div>
            ) : tickets.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-40 text-gray-400 text-sm gap-2">
                <MessageSquare className="w-8 h-8 opacity-30" />
                אין קריאות תמיכה
              </div>
            ) : (
              tickets.map(ticket => (
                <button
                  key={ticket.id}
                  onClick={() => openTicket(ticket)}
                  className={`w-full text-right px-4 py-3.5 hover:bg-gray-50 transition-colors ${selected?.id === ticket.id ? 'bg-green-50 border-r-4 border-r-green-600' : ''}`}
                >
                  <div className="flex items-start gap-3">
                    <div className={`w-2.5 h-2.5 rounded-full mt-1.5 flex-shrink-0 ${STATUS_DOT[ticket.status as TicketStatus] || 'bg-gray-400'}`} />
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between mb-0.5">
                        <span className="text-xs font-mono text-gray-400">{ticket.ticket_number}</span>
                        <span className="text-xs text-gray-400">
                          {new Date(ticket.updated_at).toLocaleDateString('he-IL')}
                        </span>
                      </div>
                      <p className="font-medium text-gray-900 text-sm truncate">{ticket.title}</p>
                      <p className="text-xs text-gray-500 truncate mt-0.5">{ticket.description}</p>
                      <div className="flex items-center justify-between mt-1.5">
                        <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${STATUS_COLOR[ticket.status as TicketStatus] || 'bg-gray-100 text-gray-600'}`}>
                          {STATUS_LABEL[ticket.status as TicketStatus] || ticket.status}
                        </span>
                        {ticket.user_name && (
                          <span className="text-xs text-gray-400 flex items-center gap-1">
                            <User className="w-3 h-3" />
                            {ticket.user_name}
                          </span>
                        )}
                      </div>
                    </div>
                    <ChevronRight className="w-4 h-4 text-gray-300 flex-shrink-0 mt-2" />
                  </div>
                </button>
              ))
            )}
          </div>
        </div>

{/* RIGHT: Conversation Thread */}
        {selected ? (
          <div className="flex-1 flex flex-col bg-gray-50">
            {/* Thread Header */}
            <div className="bg-white border-b border-gray-200 px-4 py-3 flex items-center gap-3 shadow-sm">
              <button
                onClick={() => setSelected(null)}
                className="md:hidden p-1.5 rounded-lg hover:bg-gray-100 text-gray-500"
              >
                <X className="w-4 h-4" />
              </button>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-mono text-gray-400">{selected.ticket_number}</span>
                  <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${STATUS_COLOR[selected.status as TicketStatus] || 'bg-gray-100 text-gray-600'}`}>
                    {STATUS_LABEL[selected.status as TicketStatus] || selected.status}
                  </span>
                </div>
                <p className="font-semibold text-gray-900 text-sm truncate mt-0.5">{selected.title}</p>
                <p className="text-xs text-gray-400">נפתח: {fmtDate(selected.created_at)}</p>
              </div>
              {/* Admin actions */}
              {isAdmin && (
                <div className="flex gap-2 flex-shrink-0">
                  {selected.status !== 'in_progress' && selected.status !== 'resolved' && (
                    <button
                      onClick={() => changeStatus(selected.id, 'in_progress')}
                      className="flex items-center gap-1 px-3 py-1.5 bg-yellow-50 text-yellow-700 border border-yellow-200 rounded-lg text-xs font-medium hover:bg-yellow-100 transition-colors"
                    >
                      <Clock className="w-3.5 h-3.5" />
                      בטיפול
                    </button>
                  )}
                  {selected.status !== 'resolved' && (
                    <button
                      onClick={() => changeStatus(selected.id, 'resolved')}
                      className="flex items-center gap-1 px-3 py-1.5 bg-green-50 text-green-700 border border-green-200 rounded-lg text-xs font-medium hover:bg-green-100 transition-colors"
                    >
                      <CheckCircle2 className="w-3.5 h-3.5" />
                      סגור וטפל
                    </button>
                  )}
                  {selected.status === 'resolved' && (
                    <button
                      onClick={() => changeStatus(selected.id, 'open')}
                      className="flex items-center gap-1 px-3 py-1.5 bg-gray-100 text-gray-600 rounded-lg text-xs font-medium hover:bg-gray-200 transition-colors"
                    >
                      <AlertCircle className="w-3.5 h-3.5" />
                      פתח מחדש
                    </button>
                  )}
                </div>
              )}
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto px-4 py-4 space-y-3">
              {/* Original message */}
              <div className="flex flex-col items-start">
                <div className="flex items-center gap-2 mb-1">
                  <div className="w-7 h-7 bg-gray-300 rounded-full flex items-center justify-center">
                    <User className="w-4 h-4 text-gray-600" />
                  </div>
                  <span className="text-xs text-gray-500">
                    {selected.user_name || 'משתמש'} · {fmtDate(selected.created_at)}
                  </span>
                </div>
                <div className="mr-9 bg-white text-gray-800 text-sm px-4 py-3 rounded-2xl rounded-tr-sm shadow-sm border border-gray-100 max-w-[80%]">
                  <p className="whitespace-pre-line leading-relaxed">{selected.description}</p>
                </div>
              </div>

              {/* Comments */}
              {comments.map(c => {
                const isStaff = c.is_staff;
                return (
                  <div
                    key={c.id}
                    className={`flex flex-col ${isStaff ? 'items-end' : 'items-start'}`}
                  >
                    <div className={`flex items-center gap-2 mb-1 ${isStaff ? 'flex-row-reverse' : ''}`}>
                      <div className={`w-7 h-7 rounded-full flex items-center justify-center ${isStaff ? 'bg-green-600' : 'bg-gray-300'}`}>
                        {isStaff
                          ? <Shield className="w-4 h-4 text-white" />
                          : <User className="w-4 h-4 text-gray-600" />}
                      </div>
                      <span className="text-xs text-gray-500">
                        {c.user_name} · {fmtTime(c.created_at)}
                      </span>
                    </div>
                    <div
                      className={`max-w-[78%] px-4 py-2.5 rounded-2xl text-sm shadow-sm ${
                        isStaff
                          ? 'bg-green-600 text-white rounded-tl-sm ml-9'
                          : 'bg-white text-gray-800 rounded-tr-sm mr-9 border border-gray-100'
                      }`}
                    >
                      <p className="whitespace-pre-line leading-relaxed">{c.content}</p>
                    </div>
                  </div>
                );
              })}
              <div ref={bottomRef} />
            </div>

            {/* Reply input */}
            {selected.status !== 'resolved' ? (
              <div className="bg-white border-t border-gray-200 px-4 py-3 flex gap-2 items-end">
                <textarea
                  value={reply}
                  onChange={e => setReply(e.target.value)}
                  onKeyDown={e => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault();
                      sendReply();
                    }
                  }}
                  placeholder="הקלד תגובה... (Enter לשליחה, Shift+Enter לשורה חדשה)"
                  rows={2}
                  className="flex-1 text-sm px-3 py-2 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-green-500 bg-gray-50 resize-none"
                />
                <button
                  onClick={sendReply}
                  disabled={!reply.trim() || sending}
                  className="p-2.5 bg-green-600 text-white rounded-xl hover:bg-green-700 disabled:opacity-40 transition-colors flex-shrink-0"
                >
                  {sending
                    ? <RefreshCw className="w-4 h-4 animate-spin" />
                    : <Send className="w-4 h-4" />}
                </button>
              </div>
            ) : (
              <div className="bg-green-50 border-t border-green-200 px-4 py-3 text-center">
                <p className="text-green-700 text-sm flex items-center justify-center gap-2">
                  <CheckCircle2 className="w-4 h-4" />
                  קריאה זו טופלה ונסגרה
                </p>
              </div>
            )}
          </div>
        ) : (
          <div className="hidden md:flex flex-1 items-center justify-center text-gray-400 flex-col gap-3 bg-gray-50">
            <MessageSquare className="w-16 h-16 opacity-20" />
            <p className="text-sm">בחר קריאה לצפייה בשיחה</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default Support;
