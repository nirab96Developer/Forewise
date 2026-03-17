// src/components/HelpWidget/SmartHelpWidget.tsx
// בוט תמיכה חכם — FAQ keyword matching + פתיחת קריאה לאדמין
import React, { useState, useEffect, useRef } from 'react';
import { MessageCircle, X, Send, HelpCircle, CheckCircle, Loader2 } from 'lucide-react';
import api from '../../services/api';

// ─── FAQ Knowledge Base ──────────────────────────────────────────────────────

const FAQ = [
  {
    keywords: ['סיסמה', 'סיסמא', 'שכחתי', 'לא זוכר', 'לא נכנס', 'התחברות'],
    answer: 'לאיפוס סיסמה — לחץ "שכחתי סיסמה" בדף הכניסה, או פנה למנהל המערכת.',
  },
  {
    keywords: ['הזמנה', 'להזמין', 'ספק', 'לשלוח ספק', 'הזמנת עבודה'],
    answer: 'ליצירת הזמנה: כנס לפרויקט → טאב הזמנות → "+ הזמנה חדשה" → בחר סוג כלי וספק.',
  },
  {
    keywords: ['דיווח', 'שעות', 'לדווח', 'worklog', 'דיווחים'],
    answer: 'לדיווח שעות: כנס לפרויקט → טאב דיווחים → "+ דיווח חדש". חובה לסרוק ציוד לפני דיווח.',
  },
  {
    keywords: ['ציוד', 'כלי', 'סריקה', 'QR', 'מספר רישוי', 'סרוק'],
    answer: 'לסריקת ציוד: בתוך ההזמנה הפעילה לחץ "סרוק ציוד" והזן מספר רישוי או סרוק QR.',
  },
  {
    keywords: ['חשבונית', 'תשלום', 'לאשר חשבונית', 'חשבוניות'],
    answer: 'חשבוניות ניתן לאשר תחת: הגדרות → תקציבים וניהול חשבונות.',
  },
  {
    keywords: ['תקציב', 'יתרה', 'כמה נשאר', 'תקציבים'],
    answer: 'לצפייה בתקציב: כנס לפרויקט → טאב סקירה → כרטיס תקציב.',
  },
  {
    keywords: ['משתמש', 'הרשאה', 'תפקיד', 'להוסיף משתמש', 'ניהול משתמשים'],
    answer: 'ניהול משתמשים: הגדרות מערכת → ניהול משתמשים.',
  },
  {
    keywords: ['פג תוקף', '3 שעות', 'לא מגיב', 'קישור ספק'],
    answer: 'אם פג תוקף קישור הספק — כנס לתיאום הזמנות וצור הזמנה חדשה לאותו ספק.',
  },
  {
    keywords: ['מפה', 'פוליגון', 'לא רואה', 'יער', 'שטח'],
    answer: 'המפה מציגה את שטח היער. אם לא נראה פוליגון — ייתכן שהיער לא ממופה עדיין במערכת.',
  },
  {
    keywords: ['שגיאה', 'תקלה', 'לא עובד', 'בעיה', 'נתקע', 'קורס'],
    answer: 'נסה לרענן את הדף (F5). אם הבעיה נמשכת — אוכל לפתוח קריאת שירות לאדמין.',
  },
  {
    keywords: ['תעריף', 'מחיר', 'עלות', 'שכר'],
    answer: 'תעריפי ציוד מנוהלים תחת: הגדרות מערכת → תעריפי ציוד.',
  },
];

function findAnswer(text: string): string | null {
  const lower = text.toLowerCase();
  for (const entry of FAQ) {
    if (entry.keywords.some(kw => lower.includes(kw.toLowerCase()))) {
      return entry.answer;
    }
  }
  return null;
}

// ─── Types ───────────────────────────────────────────────────────────────────

type MsgFrom = 'user' | 'bot';

interface ChatMsg {
  id: number;
  from: MsgFrom;
  text: string;
  ts: Date;
  // bot-only extras
  showButtons?: 'helped' | 'send_admin' | 'none';
}

type Phase = 'chat' | 'ask_description' | 'success';

// ─── Component ───────────────────────────────────────────────────────────────

const SmartHelpWidget: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [phase, setPhase] = useState<Phase>('chat');
  const [messages, setMessages] = useState<ChatMsg[]>([]);
  const [input, setInput] = useState('');
  const [description, setDescription] = useState('');
  const [isSending, setIsSending] = useState(false);
  const [_ticketNumber, setTicketNumber] = useState('');
  const msgCounter = useRef(0);
  const bottomRef = useRef<HTMLDivElement>(null);

  const userInfo = useRef({ id: '', name: 'משתמש', role: 'USER' });

  useEffect(() => {
    try {
      const u = JSON.parse(localStorage.getItem('user') || '{}');
      userInfo.current = {
        id: u.id || '',
        name: u.full_name || u.name || 'משתמש',
        role: u.role || 'USER',
      };
    } catch {}
  }, []);

  // Scroll to bottom on new message
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const addMsg = (from: MsgFrom, text: string, extra: Partial<ChatMsg> = {}) => {
    msgCounter.current += 1;
    const msg: ChatMsg = { id: msgCounter.current, from, text, ts: new Date(), ...extra };
    setMessages(prev => [...prev, msg]);
    return msg.id;
  };

  const openWidget = () => {
    setIsOpen(true);
    if (messages.length === 0) {
      setTimeout(() => {
        addMsg('bot', `שלום ${userInfo.current.name}! 👋 אני הבוט של מערכת Forewise. במה אוכל לעזור?`, { showButtons: 'none' });
      }, 200);
    }
  };

  const closeWidget = () => {
    setIsOpen(false);
    // Reset after close animation
    setTimeout(() => {
      setPhase('chat');
      setMessages([]);
      setInput('');
      setDescription('');
      setTicketNumber('');
      msgCounter.current = 0;
    }, 350);
  };

  const handleUserSend = () => {
    const text = input.trim();
    if (!text) return;
    setInput('');
    addMsg('user', text);

    // Short typing delay
    setTimeout(() => {
      const answer = findAnswer(text);
      if (answer) {
        addMsg('bot', answer, { showButtons: 'helped' });
      } else {
        addMsg('bot', 'לא מצאתי תשובה מוכנה לשאלתך. רוצה שאפתח קריאת שירות למנהל המערכת?', {
          showButtons: 'send_admin',
        });
      }
    }, 500);
  };

  const handleHelped = (msgId: number, helped: boolean) => {
    // Remove buttons from that message
    setMessages(prev =>
      prev.map(m => (m.id === msgId ? { ...m, showButtons: 'none' } : m))
    );
    if (helped) {
      addMsg('bot', 'מעולה! שמח שעזרתי 😊 אם יש עוד שאלות — כאן בשבילך.');
    } else {
      addMsg('bot', 'מבין. אפתח קריאת שירות עבורך כדי שמנהל המערכת יטפל בזה.', {
        showButtons: 'send_admin',
      });
    }
  };

  const handleRequestAdmin = (msgId: number) => {
    setMessages(prev =>
      prev.map(m => (m.id === msgId ? { ...m, showButtons: 'none' } : m))
    );
    setPhase('ask_description');
    addMsg('bot', 'תאר בקצרה את הבעיה (תוכן יישלח לאדמין):');
  };

  const handleSubmitTicket = async () => {
    const desc = description.trim();
    if (!desc) return;
    setIsSending(true);

    try {
      const token = localStorage.getItem('access_token');
      const res = await api.post('/support-tickets/from-widget', {
        userId: userInfo.current.id,
        userName: userInfo.current.name,
        userRole: userInfo.current.role,
        currentRoute: window.location.pathname,
        category: 'TECHNICAL',
        stepsWalked: [],
        userMessage: desc,
        clientContext: {
          url: window.location.href,
          browser: navigator.userAgent.slice(0, 150),
          resolution: `${window.innerWidth}x${window.innerHeight}`,
          timestamp: new Date().toISOString(),
        },
      }, { headers: { Authorization: `Bearer ${token}` } });

      const tNum = res.data?.ticket_number || res.data?.id || '—';
      setTicketNumber(String(tNum));
      setPhase('success');
      addMsg('bot', `✅ קריאה נפתחה (${tNum}). מנהל המערכת יחזור אליך בהקדם.`);
    } catch (err) {
      addMsg('bot', 'אירעה שגיאה בשליחה. נסה שוב או פנה ישירות למנהל המערכת.');
    } finally {
      setIsSending(false);
      setDescription('');
      setPhase('chat');
    }
  };

  const fmtTime = (d: Date) =>
    d.toLocaleTimeString('he-IL', { hour: '2-digit', minute: '2-digit' });

  return (
    <>
      {/* ── Floating Button ── */}
      <button
        onClick={isOpen ? closeWidget : openWidget}
        className={`fixed bottom-4 left-4 md:bottom-6 md:left-6 z-50 p-2.5 md:p-3.5 rounded-full shadow-lg transition-all duration-300 ${
          isOpen
            ? 'bg-gray-700 hover:bg-gray-800'
            : 'bg-gradient-to-br from-green-600 to-green-700 hover:shadow-xl hover:scale-110'
        }`}
        aria-label={isOpen ? 'סגור עזרה' : 'פתח עזרה'}
      >
        {isOpen ? (
          <X className="w-6 h-6 text-white" />
        ) : (
          <MessageCircle className="w-6 h-6 text-white" />
        )}
      </button>

      {/* ── Chat Panel ── */}
      {isOpen && (
        <div
          className="fixed bottom-20 left-4 md:bottom-24 md:left-6 z-50 w-80 sm:w-96 bg-white rounded-2xl shadow-2xl overflow-hidden border border-gray-200"
          dir="rtl"
          style={{ animation: 'slideUp 0.25s ease-out' }}
        >
          {/* Header */}
          <div className="bg-gradient-to-r from-green-600 to-green-700 px-4 py-3 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="p-1.5 bg-white/20 rounded-lg">
                <HelpCircle className="w-5 h-5 text-white" />
              </div>
              <div>
                <p className="text-white font-bold text-sm">בוט תמיכה Forewise</p>
                <p className="text-green-100 text-xs flex items-center gap-1">
                  <span className="w-1.5 h-1.5 bg-green-300 rounded-full inline-block" />
                  מחובר
                </p>
              </div>
            </div>
            <button
              onClick={closeWidget}
              className="p-1.5 hover:bg-white/20 rounded-lg transition-colors text-white"
              aria-label="סגור"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          {/* Messages */}
          <div className="h-80 overflow-y-auto px-3 py-3 space-y-3 bg-gray-50">
            {messages.map(msg => (
              <div key={msg.id} className={`flex flex-col ${msg.from === 'user' ? 'items-end' : 'items-start'}`}>
                <div
                  className={`max-w-[82%] px-3 py-2 rounded-2xl text-sm shadow-sm ${
                    msg.from === 'user'
                      ? 'bg-green-600 text-white rounded-tl-sm'
                      : 'bg-white text-gray-800 rounded-tr-sm border border-gray-100'
                  }`}
                >
                  <p className="leading-relaxed whitespace-pre-line">{msg.text}</p>
                  <p className={`text-xs mt-1 ${msg.from === 'user' ? 'text-green-200' : 'text-gray-400'}`}>
                    {fmtTime(msg.ts)}
                  </p>
                </div>

                {/* Action buttons */}
                {msg.from === 'bot' && msg.showButtons === 'helped' && (
                  <div className="flex gap-2 mt-1.5">
                    <button
                      onClick={() => handleHelped(msg.id, true)}
                      className="px-3 py-1.5 bg-green-100 text-green-700 text-xs rounded-full hover:bg-green-200 transition-colors font-medium flex items-center gap-1"
                    >
                      <CheckCircle className="w-3 h-3" />
                      זה עזר
                    </button>
                    <button
                      onClick={() => handleHelped(msg.id, false)}
                      className="px-3 py-1.5 bg-gray-100 text-gray-600 text-xs rounded-full hover:bg-gray-200 transition-colors font-medium"
                    >
                      ❌ עדיין לא פתור
                    </button>
                  </div>
                )}

                {msg.from === 'bot' && msg.showButtons === 'send_admin' && (
                  <button
                    onClick={() => handleRequestAdmin(msg.id)}
                    className="mt-1.5 px-4 py-1.5 bg-orange-500 text-white text-xs rounded-full hover:bg-orange-600 transition-colors font-medium flex items-center gap-1 shadow-sm"
                  >
                    📨 שלח לאדמין
                  </button>
                )}
              </div>
            ))}
            <div ref={bottomRef} />
          </div>

          {/* Input area */}
          {phase === 'chat' && (
            <div className="px-3 py-2 border-t border-gray-100 bg-white flex gap-2">
              <input
                type="text"
                value={input}
                onChange={e => setInput(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && !e.shiftKey && handleUserSend()}
                placeholder="כתוב שאלה..."
                className="flex-1 text-sm px-3 py-2 border border-gray-200 rounded-full focus:outline-none focus:ring-2 focus:ring-green-500 bg-gray-50"
                autoFocus
              />
              <button
                onClick={handleUserSend}
                disabled={!input.trim()}
                className="p-2 bg-green-600 text-white rounded-full hover:bg-green-700 disabled:opacity-40 transition-colors"
              >
                <Send className="w-4 h-4" />
              </button>
            </div>
          )}

          {phase === 'ask_description' && (
            <div className="px-3 py-2 border-t border-gray-100 bg-white space-y-2">
              <textarea
                value={description}
                onChange={e => setDescription(e.target.value)}
                placeholder="תאר את הבעיה בקצרה..."
                rows={3}
                className="w-full text-sm px-3 py-2 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-green-500 bg-gray-50 resize-none"
                autoFocus
              />
              <div className="flex gap-2">
                <button
                  onClick={handleSubmitTicket}
                  disabled={!description.trim() || isSending}
                  className="flex-1 py-2 bg-green-600 text-white text-sm rounded-xl hover:bg-green-700 disabled:opacity-50 font-medium flex items-center justify-center gap-1"
                >
                  {isSending ? <Loader2 className="w-4 h-4 animate-spin" /> : '📨'}
                  שלח לאדמין
                </button>
                <button
                  onClick={() => { setPhase('chat'); setDescription(''); }}
                  className="px-3 py-2 border border-gray-200 rounded-xl text-sm text-gray-500 hover:bg-gray-50"
                >
                  ביטול
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      <style>{`
        @keyframes slideUp {
          from { opacity: 0; transform: translateY(16px); }
          to { opacity: 1; transform: translateY(0); }
        }
      `}</style>
    </>
  );
};

export default SmartHelpWidget;
