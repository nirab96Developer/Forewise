// src/components/HelpWidget/HelpWidget.tsx
// בוט עזרה קטן וחמוד - לא "מסך מפחיד"
import React, { useState } from 'react';
import { 
  MessageCircle, 
  X, 
  Send, 
  HelpCircle, 
  Clock, 
  FileText, 
  Truck,
  User,
  ChevronRight
} from 'lucide-react';

interface HelpCategory {
  id: string;
  label: string;
  icon: React.ReactNode;
  description: string;
}

const HelpWidget: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const [message, setMessage] = useState('');
  const [isSending, setIsSending] = useState(false);
  const [sent, setSent] = useState(false);

  const categories: HelpCategory[] = [
    { 
      id: 'login', 
      label: 'בעיית התחברות', 
      icon: <User className="w-5 h-5" />,
      description: 'לא מצליח להתחבר, שכחתי סיסמה'
    },
    { 
      id: 'worklog', 
      label: 'בעיה בדיווח שעות', 
      icon: <Clock className="w-5 h-5" />,
      description: 'לא מצליח לדווח, שגיאה בדיווח'
    },
    { 
      id: 'supplier', 
      label: 'בעיה בהזמנת ספק', 
      icon: <Truck className="w-5 h-5" />,
      description: 'ספק לא מגיב, בעיה בהזמנה'
    },
    { 
      id: 'other', 
      label: 'אחר', 
      icon: <FileText className="w-5 h-5" />,
      description: 'בעיה אחרת'
    },
  ];

  const handleSend = async () => {
    if (!message.trim() || !selectedCategory) return;
    
    setIsSending(true);
    
    // Simulate sending
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    // Here you would actually send to your support API
    
    setIsSending(false);
    setSent(true);
    
    // Reset after 3 seconds
    setTimeout(() => {
      setSent(false);
      setSelectedCategory(null);
      setMessage('');
      setIsOpen(false);
    }, 3000);
  };

  const handleBack = () => {
    setSelectedCategory(null);
    setMessage('');
  };

  return (
    <>
      {/* Floating Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={`fixed bottom-6 left-6 z-50 p-4 rounded-full shadow-lg transition-all duration-300 ${
          isOpen 
            ? 'bg-gray-700 hover:bg-gray-800' 
            : 'bg-gradient-to-r from-fw-green to-green-600 hover:shadow-xl hover:scale-110'
        }`}
        aria-label={isOpen ? 'סגור עזרה' : 'פתח עזרה'}
      >
        {isOpen ? (
          <X className="w-6 h-6 text-white" />
        ) : (
          <MessageCircle className="w-6 h-6 text-white" />
        )}
      </button>

      {/* Help Panel */}
      {isOpen && (
        <div className="fixed bottom-24 left-6 z-50 w-80 bg-white rounded-2xl shadow-2xl overflow-hidden animate-slideUp" dir="rtl">
          {/* Header */}
          <div className="bg-gradient-to-r from-fw-green to-green-600 p-4 text-white">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-white/20 rounded-lg">
                <HelpCircle className="w-6 h-6" />
              </div>
              <div>
                <h3 className="font-bold text-lg">צריך עזרה?</h3>
                <p className="text-sm text-white/80">אנחנו כאן בשבילך</p>
              </div>
            </div>
          </div>

          {/* Content */}
          <div className="p-4">
            {sent ? (
              // Success Message
              <div className="text-center py-8">
                <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <svg className="w-8 h-8 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                </div>
                <h4 className="text-lg font-semibold text-gray-900 mb-2">נשלח בהצלחה!</h4>
                <p className="text-gray-600 text-sm">נחזור אליך בהקדם</p>
              </div>
            ) : selectedCategory ? (
              // Message Form
              <div>
                <button 
                  onClick={handleBack}
                  className="flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700 mb-4"
                >
                  <ChevronRight className="w-4 h-4" />
                  חזרה
                </button>
                
                <div className="mb-4">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    תאר את הבעיה
                  </label>
                  <textarea
                    value={message}
                    onChange={(e) => setMessage(e.target.value)}
                    placeholder="ספר לנו מה קורה..."
                    className="w-full p-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-fw-green focus:border-transparent resize-none"
                    rows={4}
                  />
                </div>

                <button
                  onClick={handleSend}
                  disabled={!message.trim() || isSending}
                  className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-gradient-to-r from-fw-green to-green-600 text-white rounded-xl font-medium disabled:opacity-50 disabled:cursor-not-allowed hover:shadow-lg transition-all"
                >
                  {isSending ? (
                    <>
                      <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
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
            ) : (
              // Category Selection
              <div className="space-y-2">
                <p className="text-sm text-gray-600 mb-4">בחר את סוג הבעיה:</p>
                
                {categories.map((category) => (
                  <button
                    key={category.id}
                    onClick={() => setSelectedCategory(category.id)}
                    className="w-full flex items-center gap-3 p-3 bg-gray-50 rounded-xl hover:bg-gray-100 transition-colors text-right"
                  >
                    <div className="p-2 bg-white rounded-lg shadow-sm">
                      {category.icon}
                    </div>
                    <div className="flex-1">
                      <p className="font-medium text-gray-900">{category.label}</p>
                      <p className="text-xs text-gray-500">{category.description}</p>
                    </div>
                    <ChevronRight className="w-4 h-4 text-gray-400 rotate-180" />
                  </button>
                ))}

                <div className="pt-4 mt-4 border-t border-gray-200">
                  <p className="text-xs text-gray-500 text-center">
                    שעות פעילות: א'-ה' 08:00-17:00
                    <br />
                    טלפון: 03-1234567
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Styles */}
      <style>{`
        @keyframes slideUp {
          from {
            opacity: 0;
            transform: translateY(20px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
        .animate-slideUp {
          animation: slideUp 0.3s ease-out;
        }
      `}</style>
    </>
  );
};

export default HelpWidget;

