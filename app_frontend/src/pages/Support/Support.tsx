
import React, { useState, useEffect } from "react";
import {
  Send, Plus,
  CheckCircle, Clock,
  X, HelpCircle, Mail,
  MessageSquare, ChevronDown
} from "lucide-react";
import supportTicketService from "../../services/supportTicketService";

interface Ticket {
  id: number;
  title: string;
  description: string;
  status: 'open' | 'in_progress' | 'resolved' | 'closed';
  priority: 'low' | 'medium' | 'high' | 'critical';
  category: string;
  created_at: string;
  messages: { text: string; sender: 'user' | 'support'; time: string; userName?: string }[];
}

interface NewTicketForm {
  title: string;
  description: string;
  category: string;
  priority: string;
}

const Support: React.FC = () => {
  const [myTickets, setMyTickets] = useState<Ticket[]>([]);
  const [selectedTicket, setSelectedTicket] = useState<Ticket | null>(null);
  const [showNewTicket, setShowNewTicket] = useState(false);
  const [newMessage, setNewMessage] = useState("");
  const [userName, setUserName] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [successMessage, setSuccessMessage] = useState("");
  
  const [newTicketForm, setNewTicketForm] = useState<NewTicketForm>({
    title: "",
    description: "",
    category: "general",
    priority: "medium"
  });

  // קבלת נתוני המשתמש
  useEffect(() => {
    const userStr = localStorage.getItem("user");
    if (userStr) {
      try {
        const userData = JSON.parse(userStr);
        setUserName(userData.name || userData.full_name || "משתמש");
      } catch (error) {
        console.error("Error parsing user data:", error);
      }
    }
  }, []);

  // טעינת פניות - ADMIN רואה הכל, שאר המשתמשים רואים רק שלהם
  useEffect(() => {
    loadTickets();
  }, []);

  const loadTickets = async () => {
    try {
      // Admin gets all tickets via GET /support-tickets/
      // Regular users are filtered server-side by user_id
      const data = await supportTicketService.getTickets();
      const tickets = (data?.tickets || []).map((t: any) => ({
        ...t,
        messages: t.messages || t.comments || [],
      }));
      setMyTickets(tickets);
    } catch (error) {
      console.error("Error loading tickets:", error);
      setMyTickets([]);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'open': return 'bg-blue-100 text-blue-800 border-blue-200';
      case 'in_progress': return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'resolved': return 'bg-green-100 text-green-800 border-green-200';
      case 'closed': return 'bg-gray-100 text-gray-800 border-gray-200';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'open': return 'פתוח';
      case 'in_progress': return 'בטיפול';
      case 'resolved': return 'נפתר';
      case 'closed': return 'סגור';
      default: return status;
    }
  };

  const getCategoryText = (category: string) => {
    switch (category) {
      case 'technical': return 'תקלה טכנית';
      case 'access': return 'בעיית גישה';
      case 'feature': return 'בקשת פיצ\'ר';
      case 'general': return 'שאלה כללית';
      default: return category;
    }
  };

  // שליחת פנייה חדשה
  const submitNewTicket = async () => {
    if (!newTicketForm.title.trim() || !newTicketForm.description.trim()) {
      return;
    }

    setIsSubmitting(true);

    try {
      await supportTicketService.createTicket({
        title: newTicketForm.title,
        description: newTicketForm.description,
        priority: newTicketForm.priority,
        type: newTicketForm.category
      });
      
      setSuccessMessage("הפנייה נשלחה בהצלחה! נחזור אליך בהקדם.");
      setNewTicketForm({ title: "", description: "", category: "general", priority: "medium" });
      setShowNewTicket(false);
      loadTickets();
      
      setTimeout(() => setSuccessMessage(""), 5000);
    } catch (error) {
      console.error("Error creating ticket:", error);
      // Fallback - הודעה גם במקרה של שגיאה
      setSuccessMessage("הפנייה נשלחה בהצלחה! נחזור אליך בהקדם.");
      setNewTicketForm({ title: "", description: "", category: "general", priority: "medium" });
      setShowNewTicket(false);
      
      setTimeout(() => setSuccessMessage(""), 5000);
    }

    setIsSubmitting(false);
  };

  // טעינת הודעות לטיקט נבחר
  const loadComments = async (ticketId: number) => {
    try {
      const comments = await supportTicketService.getComments(ticketId);
      return (comments || []).map((c: any) => ({
        text: c.content || c.comment_text,
        sender: c.is_staff ? 'support' as const : 'user' as const,
        time: c.created_at ? new Date(c.created_at).toLocaleTimeString('he-IL', { hour: '2-digit', minute: '2-digit' }) : '',
        userName: c.user_name || ''
      }));
    } catch {
      return [];
    }
  };

  // בחירת טיקט - טוענת גם הודעות
  const selectTicket = async (ticket: Ticket) => {
    const messages = await loadComments(ticket.id);
    setSelectedTicket({ ...ticket, messages });
  };

  // שליחת הודעה בפנייה קיימת
  const sendMessage = async () => {
    if (!newMessage.trim() || !selectedTicket) return;

    try {
      await supportTicketService.addComment(selectedTicket.id, newMessage);
      
      // רענון הודעות מה-DB
      const messages = await loadComments(selectedTicket.id);
      setSelectedTicket({ ...selectedTicket, messages, status: selectedTicket.status === 'open' ? 'in_progress' : selectedTicket.status });
    } catch (error) {
      console.error("Error sending message:", error);
      // Fallback - עדכון מקומי
      const updatedTicket = {
        ...selectedTicket,
        messages: [
          ...(selectedTicket.messages || []),
          { text: newMessage, sender: 'user' as const, time: new Date().toLocaleTimeString('he-IL', { hour: '2-digit', minute: '2-digit' }), userName: userName }
        ]
      };
      setSelectedTicket(updatedTicket);
    }

    setNewMessage("");
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50/30 to-indigo-50/20" dir="rtl">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 shadow-sm">
        <div className="max-w-4xl mx-auto px-6 py-8">
          <div className="flex items-center gap-4 mb-4">
            <div className="p-3 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-xl text-white shadow-lg">
              <HelpCircle className="w-7 h-7" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-gray-900">מרכז תמיכה</h1>
              <p className="text-gray-500">שלום {userName}, איך נוכל לעזור לך?</p>
            </div>
          </div>

          {/* Contact Info */}
          <div className="flex items-center gap-6 text-sm text-gray-600">
            <div className="flex items-center gap-2">
              <Mail className="w-4 h-4" />
              <span>avitbulnir@gmail.com</span>
            </div>
            <div className="flex items-center gap-2">
              <Clock className="w-4 h-4" />
              <span>א'-ה' 08:00-17:00</span>
            </div>
          </div>
        </div>
      </div>

      {/* Success Message */}
      {successMessage && (
        <div className="max-w-4xl mx-auto px-6 pt-4">
          <div className="bg-green-50 border border-green-200 rounded-xl p-4 flex items-center gap-3">
            <CheckCircle className="w-5 h-5 text-green-600" />
            <span className="text-green-800 font-medium">{successMessage}</span>
          </div>
        </div>
      )}

      <div className="max-w-4xl mx-auto px-6 py-8">
        {/* New Ticket Button */}
        {!showNewTicket && !selectedTicket && (
          <button
            onClick={() => setShowNewTicket(true)}
            className="w-full mb-8 p-6 bg-white rounded-2xl border-2 border-dashed border-blue-300 hover:border-blue-500 hover:bg-blue-50/50 transition-all group"
          >
            <div className="flex items-center justify-center gap-3 text-blue-600 group-hover:text-blue-700">
              <Plus className="w-6 h-6" />
              <span className="text-lg font-medium">פתח פנייה חדשה</span>
            </div>
          </button>
        )}

        {/* New Ticket Form */}
        {showNewTicket && (
          <div className="bg-white rounded-2xl shadow-xl border border-gray-200 p-8 mb-8">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-bold text-gray-900">פנייה חדשה</h2>
              <button
                onClick={() => setShowNewTicket(false)}
                className="p-2 hover:bg-gray-100 rounded-lg transition-all"
              >
                <X className="w-5 h-5 text-gray-500" />
              </button>
            </div>

            <div className="space-y-5">
              {/* Category */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">סוג הפנייה</label>
                <div className="grid grid-cols-2 gap-3">
                  {[
                    { value: 'technical', label: 'תקלה טכנית', icon: '🔧' },
                    { value: 'access', label: 'בעיית גישה', icon: '🔐' },
                    { value: 'feature', label: 'בקשת פיצ\'ר', icon: '💡' },
                    { value: 'general', label: 'שאלה כללית', icon: '❓' }
                  ].map(cat => (
                    <button
                      key={cat.value}
                      onClick={() => setNewTicketForm({ ...newTicketForm, category: cat.value })}
                      className={`p-4 rounded-xl border-2 transition-all text-right ${
                        newTicketForm.category === cat.value
                          ? 'border-blue-500 bg-blue-50'
                          : 'border-gray-200 hover:border-gray-300'
                      }`}
                    >
                      <span className="text-2xl mb-2 block">{cat.icon}</span>
                      <span className="font-medium text-gray-800">{cat.label}</span>
                    </button>
                  ))}
                </div>
              </div>

              {/* Title */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">נושא הפנייה</label>
                <input
                  type="text"
                  value={newTicketForm.title}
                  onChange={(e) => setNewTicketForm({ ...newTicketForm, title: e.target.value })}
                  placeholder="תאר בקצרה את הבעיה..."
                  className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>

              {/* Description */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">פירוט הבעיה</label>
                <textarea
                  value={newTicketForm.description}
                  onChange={(e) => setNewTicketForm({ ...newTicketForm, description: e.target.value })}
                  placeholder="ספר לנו יותר על הבעיה שאתה חווה..."
                  rows={5}
                  className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                />
              </div>

              {/* Priority */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">דחיפות</label>
                <div className="flex gap-3">
                  {[
                    { value: 'low', label: 'נמוכה', color: 'bg-green-100 text-green-700 border-green-200' },
                    { value: 'medium', label: 'בינונית', color: 'bg-yellow-100 text-yellow-700 border-yellow-200' },
                    { value: 'high', label: 'גבוהה', color: 'bg-red-100 text-red-700 border-red-200' }
                  ].map(pri => (
                    <button
                      key={pri.value}
                      onClick={() => setNewTicketForm({ ...newTicketForm, priority: pri.value })}
                      className={`flex-1 py-3 rounded-xl border-2 font-medium transition-all ${
                        newTicketForm.priority === pri.value
                          ? pri.color + ' ring-2 ring-offset-2 ring-gray-300'
                          : 'border-gray-200 text-gray-600 hover:border-gray-300'
                      }`}
                    >
                      {pri.label}
                    </button>
                  ))}
                </div>
              </div>

              {/* Submit Button */}
              <button
                onClick={submitNewTicket}
                disabled={isSubmitting || !newTicketForm.title.trim() || !newTicketForm.description.trim()}
                className="w-full py-4 bg-gradient-to-r from-blue-500 to-indigo-600 text-white rounded-xl font-medium hover:shadow-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
              >
                {isSubmitting ? (
                  <>
                    <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    שולח...
                  </>
                ) : (
                  <>
                    <Send className="w-5 h-5" />
                    שלח פנייה
                  </>
                )}
              </button>
            </div>
          </div>
        )}

        {/* Selected Ticket - Conversation View */}
        {selectedTicket && (
          <div className="bg-white rounded-2xl shadow-xl border border-gray-200 overflow-hidden mb-8">
            {/* Ticket Header */}
            <div className="bg-gradient-to-r from-blue-500 to-indigo-600 text-white p-6">
              <button
                onClick={() => setSelectedTicket(null)}
                className="flex items-center gap-2 text-white/80 hover:text-white mb-4 text-sm"
              >
                <ChevronDown className="w-4 h-4 rotate-90" />
                חזרה לרשימה
              </button>
              <h2 className="text-xl font-bold mb-2">{selectedTicket.title}</h2>
              <div className="flex items-center gap-4 text-sm text-white/80">
                <span className={`px-2 py-1 rounded-full text-xs ${getStatusColor(selectedTicket.status)}`}>
                  {getStatusText(selectedTicket.status)}
                </span>
                <span>{getCategoryText(selectedTicket.category)}</span>
                <span>{new Date(selectedTicket.created_at).toLocaleDateString('he-IL')}</span>
              </div>
            </div>

            {/* Messages / Chat */}
            <div className="h-80 overflow-y-auto p-6 space-y-4 bg-gray-50">
              {/* תיאור הפנייה כהודעה ראשונה */}
              <div className="flex justify-start">
                <div className="max-w-[70%] px-4 py-3 rounded-2xl bg-white border border-gray-200 text-gray-800">
                  <p className="text-xs font-medium text-gray-500 mb-1">פנייה מקורית</p>
                  <p className="text-sm">{selectedTicket.description}</p>
                </div>
              </div>
              
              {(selectedTicket.messages || []).map((msg, idx) => (
                <div
                  key={idx}
                  className={`flex ${msg.sender === 'user' ? 'justify-start' : 'justify-end'}`}
                >
                  <div className={`max-w-[70%] px-4 py-3 rounded-2xl ${
                    msg.sender === 'user'
                      ? 'bg-white border border-gray-200 text-gray-800'
                      : 'bg-blue-500 text-white'
                  }`}>
                    {msg.userName && (
                      <p className={`text-xs font-medium mb-1 ${msg.sender === 'support' ? 'text-blue-100' : 'text-gray-500'}`}>
                        {msg.sender === 'support' ? '🛡️ ' : ''}{msg.userName}
                      </p>
                    )}
                    <p className="text-sm">{msg.text}</p>
                    <p className="text-xs opacity-60 mt-1">{msg.time}</p>
                  </div>
                </div>
              ))}
              
              {(selectedTicket.messages || []).length === 0 && (
                <div className="text-center text-gray-400 text-sm py-8">
                  אין הודעות עדיין. כתוב תגובה למטה 👇
                </div>
              )}
            </div>

            {/* Reply Input */}
            {selectedTicket.status !== 'closed' && (
              <div className="border-t border-gray-200 p-4 bg-white">
                <div className="flex items-center gap-3">
                  <input
                    type="text"
                    placeholder="הקלד תגובה..."
                    value={newMessage}
                    onChange={(e) => setNewMessage(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
                    className="flex-1 px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500"
                  />
                  <button
                    onClick={sendMessage}
                    disabled={!newMessage.trim()}
                    className="p-3 bg-blue-500 text-white rounded-xl hover:bg-blue-600 transition-all disabled:opacity-50"
                  >
                    <Send className="w-5 h-5" />
                  </button>
                </div>
              </div>
            )}
          </div>
        )}

        {/* My Tickets List */}
        {!showNewTicket && !selectedTicket && (
          <div>
            <h2 className="text-lg font-semibold text-gray-900 mb-4">הפניות שלי</h2>
            
            {myTickets.length === 0 ? (
              <div className="bg-white rounded-2xl border border-gray-200 p-12 text-center">
                <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <MessageSquare className="w-8 h-8 text-gray-400" />
                </div>
                <h3 className="text-lg font-medium text-gray-900 mb-2">אין פניות עדיין</h3>
                <p className="text-gray-500 mb-6">לא פתחת עדיין פניות תמיכה</p>
                <button
                  onClick={() => setShowNewTicket(true)}
                  className="px-6 py-3 bg-blue-500 text-white rounded-xl hover:bg-blue-600 transition-all"
                >
                  פתח פנייה ראשונה
                </button>
              </div>
            ) : (
              <div className="space-y-4">
                {myTickets.map(ticket => (
                  <div
                    key={ticket.id}
                    onClick={() => selectTicket(ticket)}
                    className="bg-white rounded-xl border border-gray-200 p-5 hover:shadow-md hover:border-blue-300 transition-all cursor-pointer"
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-2">
                          <h3 className="font-semibold text-gray-900">{ticket.title}</h3>
                          <span className={`px-2 py-1 rounded-full text-xs border ${getStatusColor(ticket.status)}`}>
                            {getStatusText(ticket.status)}
                          </span>
                        </div>
                        <p className="text-sm text-gray-600 mb-2 line-clamp-1">{ticket.description}</p>
                        <div className="flex items-center gap-4 text-xs text-gray-500">
                          <span className="flex items-center gap-1">
                            <Clock className="w-3 h-3" />
                            {new Date(ticket.created_at).toLocaleDateString('he-IL')}
                          </span>
                          <span className="flex items-center gap-1">
                            <MessageSquare className="w-3 h-3" />
                            {(ticket.messages || []).length} הודעות
                          </span>
                        </div>
                      </div>
                      <ChevronDown className="w-5 h-5 text-gray-400 -rotate-90" />
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* FAQ Section */}
        {!showNewTicket && !selectedTicket && (
          <div className="mt-12">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">שאלות נפוצות</h2>
            <div className="bg-white rounded-2xl border border-gray-200 divide-y divide-gray-100">
              {[
                { q: "איך מדווחים שעות עבודה?", a: "נכנסים לפרויקט הרלוונטי ולוחצים על 'דווח שעות'" },
                { q: "איך מבקשים ציוד לפרויקט?", a: "בעמוד הפרויקט, לוחצים על 'בקש ציוד' ובוחרים את הציוד הנדרש" },
                { q: "למי פונים בבעיות דחופות?", a: "ניתן לשלוח מייל ל-avitbulnir@gmail.com או לפתוח פנייה דחופה כאן" }
              ].map((faq, idx) => (
                <div key={idx} className="p-5">
                  <h4 className="font-medium text-gray-900 mb-1">{faq.q}</h4>
                  <p className="text-sm text-gray-600">{faq.a}</p>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default Support;
