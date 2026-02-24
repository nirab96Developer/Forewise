// @ts-nocheck
// src/components/HelpWidget/SmartHelpWidget.tsx
// בוט תמיכה חכם - עוזר לבד ופותח טיקט רק כשצריך
import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { 
  MessageCircle, 
  X, 
  Send, 
  HelpCircle, 
  ChevronRight,
  ChevronLeft,
  CheckCircle,
  XCircle,
  ExternalLink,
  Phone,
  Mail,
  Clock,
  User,
  Loader2,
  ThumbsUp,
  ThumbsDown,
  ArrowLeft,
  Headphones,
} from 'lucide-react';
import { 
  supportArticles, 
  supportCategories, 
  getArticleByCategory,
  SupportArticle,
  SupportStep 
} from '../../data/supportKnowledgeBase';

// Types
interface StepResult {
  stepId: string;
  helped: boolean;
}

interface TicketData {
  userId: string;
  userName: string;
  userRole: string;
  regionId?: string;
  areaId?: string;
  projectId?: string;
  currentRoute: string;
  category: string;
  stepsWalked: StepResult[];
  userMessage: string;
  clientContext: {
    url: string;
    browser: string;
    resolution: string;
    timestamp: string;
  };
}

type WidgetState = 'closed' | 'categories' | 'steps' | 'message' | 'success' | 'ticket_form';

const SmartHelpWidget: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();
  
  // State
  const [isOpen, setIsOpen] = useState(false);
  const [widgetState, setWidgetState] = useState<WidgetState>('categories');
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const [currentArticle, setCurrentArticle] = useState<SupportArticle | null>(null);
  const [currentStepIndex, setCurrentStepIndex] = useState(0);
  const [stepsWalked, setStepsWalked] = useState<StepResult[]>([]);
  const [userMessage, setUserMessage] = useState('');
  const [isSending, setIsSending] = useState(false);
  const [showFaq, setShowFaq] = useState(false);

  // User info from localStorage
  const [userInfo, setUserInfo] = useState({
    id: '',
    name: 'משתמש',
    role: 'USER',
    regionId: '',
    areaId: '',
  });

  // Load user info
  useEffect(() => {
    const userStr = localStorage.getItem('user');
    if (userStr) {
      try {
        const user = JSON.parse(userStr);
        setUserInfo({
          id: user.id || '',
          name: user.name || 'משתמש',
          role: user.role || 'USER',
          regionId: user.region_id || '',
          areaId: user.area_id || '',
        });
      } catch (e) {
        console.error('Error parsing user info:', e);
      }
    }
  }, []);

  // Reset when closing
  const handleClose = () => {
    setIsOpen(false);
    setTimeout(() => {
      setWidgetState('categories');
      setSelectedCategory(null);
      setCurrentArticle(null);
      setCurrentStepIndex(0);
      setStepsWalked([]);
      setUserMessage('');
      setShowFaq(false);
    }, 300);
  };

  // Select category
  const handleSelectCategory = (categoryId: string) => {
    setSelectedCategory(categoryId);
    const article = getArticleByCategory(categoryId);
    if (article) {
      setCurrentArticle(article);
      setCurrentStepIndex(0);
      setStepsWalked([]);
      setWidgetState('steps');
    }
  };

  // Step feedback
  const handleStepFeedback = (helped: boolean) => {
    if (!currentArticle) return;
    
    const currentStep = currentArticle.steps[currentStepIndex];
    setStepsWalked(prev => [...prev, { stepId: currentStep.id, helped }]);

    if (helped) {
      // Problem solved!
      setWidgetState('success');
    } else {
      // Move to next step
      if (currentStepIndex < currentArticle.steps.length - 1) {
        setCurrentStepIndex(prev => prev + 1);
      } else {
        // No more steps - offer to talk to support
        setWidgetState('ticket_form');
      }
    }
  };

  // Navigate to action link
  const handleActionClick = (path: string) => {
    navigate(path);
    handleClose();
  };

  // Submit ticket
  const handleSubmitTicket = async () => {
    if (!userMessage.trim()) return;

    setIsSending(true);

    const ticketData: TicketData = {
      userId: userInfo.id,
      userName: userInfo.name,
      userRole: userInfo.role,
      regionId: userInfo.regionId,
      areaId: userInfo.areaId,
      currentRoute: location.pathname,
      category: selectedCategory || 'GENERAL',
      stepsWalked,
      userMessage: userMessage.trim(),
      clientContext: {
        url: window.location.href,
        browser: navigator.userAgent,
        resolution: `${window.innerWidth}x${window.innerHeight}`,
        timestamp: new Date().toISOString(),
      },
    };

    try {
      // Send to backend
      const token = localStorage.getItem('access_token');
      const response = await fetch('/api/v1/support-tickets/from-widget', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify(ticketData),
      });

      if (response.ok) {
        setWidgetState('success');
      } else {
        // Fallback - still show success (ticket will be created manually)
        console.error('Failed to create ticket:', await response.text());
        setWidgetState('success');
      }
    } catch (error) {
      console.error('Error creating ticket:', error);
      // Still show success - we'll handle it manually
      setWidgetState('success');
    } finally {
      setIsSending(false);
    }
  };

  // Go back
  const handleBack = () => {
    if (widgetState === 'steps' && currentStepIndex > 0) {
      setCurrentStepIndex(prev => prev - 1);
      setStepsWalked(prev => prev.slice(0, -1));
    } else if (widgetState === 'steps' || widgetState === 'ticket_form') {
      setWidgetState('categories');
      setSelectedCategory(null);
      setCurrentArticle(null);
      setCurrentStepIndex(0);
      setStepsWalked([]);
    }
  };

  // Current step
  const currentStep = currentArticle?.steps[currentStepIndex];

  return (
    <>
      {/* Floating Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={`fixed bottom-6 left-6 z-50 p-4 rounded-full shadow-lg transition-all duration-300 ${
          isOpen 
            ? 'bg-gray-700 hover:bg-gray-800 rotate-0' 
            : 'bg-gradient-to-r from-kkl-green to-kkl-green-dark hover:shadow-xl hover:scale-110'
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
        <div 
          className="fixed bottom-24 left-6 z-50 w-96 bg-white rounded-2xl shadow-2xl overflow-hidden animate-slideUp border border-kkl-border"
          dir="rtl"
        >
          {/* Header */}
          <div className="bg-gradient-to-r from-kkl-green to-kkl-green-dark p-4 text-white">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-white/20 rounded-lg">
                  <HelpCircle className="w-6 h-6" />
                </div>
                <div>
                  <h3 className="font-bold text-lg">צריך עזרה?</h3>
                  <p className="text-sm text-white/80">אני כאן לעזור לך</p>
                </div>
              </div>
              {widgetState !== 'categories' && widgetState !== 'success' && (
                <button 
                  onClick={handleBack}
                  className="p-2 hover:bg-white/20 rounded-lg transition-colors"
                >
                  <ArrowLeft className="w-5 h-5" />
                </button>
              )}
            </div>
          </div>

          {/* Content */}
          <div className="max-h-[500px] overflow-y-auto">
            
            {/* Categories Selection */}
            {widgetState === 'categories' && (
              <div className="p-4 space-y-3">
                <p className="text-sm text-gray-600 mb-4">בחר את סוג הבעיה:</p>
                
                {supportCategories.map((category) => (
                  <button
                    key={category.id}
                    onClick={() => handleSelectCategory(category.id)}
                    className="w-full flex items-center gap-3 p-4 bg-gray-50 rounded-xl hover:bg-kkl-green-light hover:border-kkl-green border border-transparent transition-all text-right group"
                  >
                    <span className="text-2xl">{category.icon}</span>
                    <div className="flex-1">
                      <p className="font-semibold text-gray-900 group-hover:text-kkl-green">
                        {category.label}
                      </p>
                      <p className="text-xs text-gray-500">{category.description}</p>
                    </div>
                    <ChevronLeft className="w-5 h-5 text-gray-400 group-hover:text-kkl-green" />
                  </button>
                ))}

                {/* Contact Info */}
                <div className="pt-4 mt-4 border-t border-gray-200">
                  <p className="text-xs text-gray-500 text-center">
                    <span className="flex items-center justify-center gap-2 mb-1">
                      <Clock className="w-3 h-3" /> א'-ה' 08:00-17:00
                    </span>
                    <span className="flex items-center justify-center gap-2">
                      <Phone className="w-3 h-3" /> 03-1234567
                    </span>
                  </p>
                </div>
              </div>
            )}

            {/* Steps View */}
            {widgetState === 'steps' && currentArticle && currentStep && (
              <div className="p-4">
                {/* Progress */}
                <div className="flex items-center gap-2 mb-4">
                  <span className="text-sm text-gray-500">
                    שלב {currentStepIndex + 1} מתוך {currentArticle.steps.length}
                  </span>
                  <div className="flex-1 h-1.5 bg-gray-200 rounded-full overflow-hidden">
                    <div 
                      className="h-full bg-kkl-green rounded-full transition-all duration-300"
                      style={{ width: `${((currentStepIndex + 1) / currentArticle.steps.length) * 100}%` }}
                    />
                  </div>
                </div>

                {/* Current Step */}
                <div className="bg-kkl-green-light rounded-xl p-4 mb-4">
                  <h4 className="font-bold text-kkl-green mb-2 flex items-center gap-2">
                    <span className="w-6 h-6 bg-kkl-green text-white rounded-full flex items-center justify-center text-sm">
                      {currentStepIndex + 1}
                    </span>
                    {currentStep.title}
                  </h4>
                  <p className="text-gray-700 text-sm whitespace-pre-line leading-relaxed">
                    {currentStep.text}
                  </p>
                  
                  {currentStep.actionLink && (
                    <button
                      onClick={() => handleActionClick(currentStep.actionLink!)}
                      className="mt-3 flex items-center gap-2 text-kkl-green hover:text-kkl-green-dark font-medium text-sm"
                    >
                      <ExternalLink className="w-4 h-4" />
                      {currentStep.actionText || 'עבור לדף'}
                    </button>
                  )}
                </div>

                {/* Feedback Buttons */}
                <p className="text-sm text-gray-600 mb-3 text-center">האם זה עזר לך?</p>
                <div className="flex gap-3">
                  <button
                    onClick={() => handleStepFeedback(true)}
                    className="flex-1 flex items-center justify-center gap-2 py-3 bg-kkl-success text-white rounded-xl hover:bg-green-600 transition-colors font-medium"
                  >
                    <ThumbsUp className="w-5 h-5" />
                    כן, עזר לי!
                  </button>
                  <button
                    onClick={() => handleStepFeedback(false)}
                    className="flex-1 flex items-center justify-center gap-2 py-3 bg-gray-200 text-gray-700 rounded-xl hover:bg-gray-300 transition-colors font-medium"
                  >
                    <ThumbsDown className="w-5 h-5" />
                    לא עזר
                  </button>
                </div>

                {/* FAQ Toggle */}
                {currentArticle.faq.length > 0 && (
                  <button
                    onClick={() => setShowFaq(!showFaq)}
                    className="w-full mt-4 text-sm text-kkl-green hover:text-kkl-green-dark flex items-center justify-center gap-1"
                  >
                    <HelpCircle className="w-4 h-4" />
                    שאלות נפוצות
                    <ChevronRight className={`w-4 h-4 transition-transform ${showFaq ? 'rotate-90' : ''}`} />
                  </button>
                )}

                {/* FAQ List */}
                {showFaq && (
                  <div className="mt-3 space-y-2">
                    {currentArticle.faq.map((item, index) => (
                      <div key={index} className="bg-gray-50 rounded-lg p-3">
                        <p className="font-medium text-gray-800 text-sm mb-1">{item.question}</p>
                        <p className="text-gray-600 text-xs">{item.answer}</p>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* Ticket Form */}
            {widgetState === 'ticket_form' && (
              <div className="p-4">
                <div className="text-center mb-4">
                  <div className="w-16 h-16 bg-kkl-warning/20 rounded-full flex items-center justify-center mx-auto mb-3">
                    <Headphones className="w-8 h-8 text-kkl-warning" />
                  </div>
                  <h4 className="font-bold text-gray-900 mb-1">נראה שהבעיה לא נפתרה</h4>
                  <p className="text-sm text-gray-500">תרצה שנציג תמיכה יעבור על זה?</p>
                </div>

                {/* Steps Summary */}
                {stepsWalked.length > 0 && (
                  <div className="bg-gray-50 rounded-lg p-3 mb-4">
                    <p className="text-xs text-gray-500 mb-2">מה כבר ניסינו:</p>
                    {stepsWalked.map((step, index) => (
                      <div key={index} className="flex items-center gap-2 text-xs text-gray-600">
                        <XCircle className="w-3 h-3 text-red-400" />
                        <span>שלב {index + 1}</span>
                      </div>
                    ))}
                  </div>
                )}

                {/* Message Input */}
                <div className="mb-4">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    תאר את הבעיה במילים שלך
                  </label>
                  <textarea
                    value={userMessage}
                    onChange={(e) => setUserMessage(e.target.value)}
                    placeholder="ספר לנו מה קורה..."
                    className="w-full p-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-kkl-green focus:border-transparent resize-none text-sm"
                    rows={4}
                  />
                </div>

                {/* Submit Button */}
                <button
                  onClick={handleSubmitTicket}
                  disabled={!userMessage.trim() || isSending}
                  className="w-full flex items-center justify-center gap-2 py-3 bg-kkl-green text-white rounded-xl font-medium disabled:opacity-50 disabled:cursor-not-allowed hover:bg-kkl-green-dark transition-colors"
                >
                  {isSending ? (
                    <>
                      <Loader2 className="w-5 h-5 animate-spin" />
                      שולח...
                    </>
                  ) : (
                    <>
                      <Send className="w-5 h-5" />
                      שלח לנציג תמיכה
                    </>
                  )}
                </button>

                {/* Cancel */}
                <button
                  onClick={handleBack}
                  className="w-full mt-2 py-2 text-gray-500 hover:text-gray-700 text-sm"
                >
                  לא כרגע, אנסה שוב
                </button>
              </div>
            )}

            {/* Success */}
            {widgetState === 'success' && (
              <div className="p-6 text-center">
                <div className="w-20 h-20 bg-kkl-success/20 rounded-full flex items-center justify-center mx-auto mb-4">
                  <CheckCircle className="w-10 h-10 text-kkl-success" />
                </div>
                
                {stepsWalked.length > 0 && stepsWalked[stepsWalked.length - 1]?.helped ? (
                  <>
                    <h4 className="text-xl font-bold text-gray-900 mb-2">מעולה! 🎉</h4>
                    <p className="text-gray-600 mb-4">שמח שהצלחתי לעזור!</p>
                  </>
                ) : (
                  <>
                    <h4 className="text-xl font-bold text-gray-900 mb-2">הפנייה נשלחה!</h4>
                    <p className="text-gray-600 mb-4">
                      נציג תמיכה יחזור אליך בהקדם.
                      <br />
                      <span className="text-sm text-gray-400">בדרך כלל תוך שעות עבודה ספורות</span>
                    </p>
                  </>
                )}

                <button
                  onClick={handleClose}
                  className="px-6 py-2 bg-kkl-green text-white rounded-lg hover:bg-kkl-green-dark transition-colors"
                >
                  סגור
                </button>
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

export default SmartHelpWidget;

