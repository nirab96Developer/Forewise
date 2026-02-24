// @ts-nocheck
// src/components/HelpWidget/HumanSupportChat.tsx
// בוט תמיכה אנושי - מרגיש כמו נציג אמיתי
import React, { useState, useEffect, useRef } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { 
  MessageCircle, 
  X, 
  Send, 
  Phone,
  Mail,
  Loader2,
  CheckCircle,
  User,
  Bot,
  ArrowLeft,
  Sparkles,
} from 'lucide-react';

// Types
interface Message {
  id: string;
  from: 'bot' | 'user' | 'system';
  text: string;
  timestamp: Date;
  options?: string[];
  isTyping?: boolean;
}

interface ConversationStep {
  bot?: string;
  options?: string[];
  nextStep?: Record<string, string>;
  action?: 'open_ticket' | 'resolve' | 'navigate';
  navigateTo?: string;
}

// Bot Flow - שיחות אנושיות לפי נושא
const BOT_FLOWS: Record<string, ConversationStep[]> = {
  // התחלה
  start: [
    { 
      bot: "היי 👋 אני כאן לעזור לך.\nמה מפריע לך כרגע?",
      options: [
        "🔐 לא מצליח להתחבר",
        "🕒 בעיה בדיווח שעות", 
        "📝 בעיה בהזמנת עבודה",
        "📁 בעיה בפרויקט",
        "❓ משהו אחר"
      ],
      nextStep: {
        "🔐 לא מצליח להתחבר": "login_1",
        "🕒 בעיה בדיווח שעות": "worklog_1",
        "📝 בעיה בהזמנת עבודה": "workorder_1",
        "📁 בעיה בפרויקט": "project_1",
        "❓ משהו אחר": "other_1"
      }
    }
  ],

  // בעיות התחברות
  login_1: [
    { 
      bot: "אוקיי, בוא ננסה לפתור את זה ביחד 🙂\n\nכשאתה מנסה להתחבר – מה קורה?",
      options: ["יש הודעת שגיאה", "הדף לא מתקדם", "שכחתי סיסמה", "משהו אחר"],
      nextStep: {
        "יש הודעת שגיאה": "login_error",
        "הדף לא מתקדם": "login_stuck",
        "שכחתי סיסמה": "login_password",
        "משהו אחר": "login_other"
      }
    }
  ],
  login_error: [
    { 
      bot: "מבין. הודעות שגיאה יכולות להיות מבלבלות 😅\n\nמה ההודעה אומרת?",
      options: ["שם משתמש או סיסמה שגויים", "החשבון נעול", "שגיאת שרת", "לא זוכר"]
    },
    {
      bot: "אוקיי, תודה שסיפרת.\n\nבוא ננסה:\n1. ודא שהמקלדת באנגלית\n2. בדוק Caps Lock כבוי\n3. נסה להקליד את הסיסמה בנפרד ולהעתיק\n\nעזר?",
      options: ["✅ כן, עבד!", "❌ עדיין לא עובד"],
      nextStep: {
        "✅ כן, עבד!": "resolved",
        "❌ עדיין לא עובד": "escalate"
      }
    }
  ],
  login_stuck: [
    {
      bot: "זה יכול להיות בעיית דפדפן.\n\nננסה כמה דברים:\n1. רענן את הדף (F5)\n2. נקה מטמון (Ctrl+Shift+Delete)\n3. נסה דפדפן אחר\n\nעזר?",
      options: ["✅ כן, עבד!", "❌ עדיין תקוע"],
      nextStep: {
        "✅ כן, עבד!": "resolved",
        "❌ עדיין תקוע": "escalate"
      }
    }
  ],
  login_password: [
    {
      bot: "אין בעיה! 😊\n\nלחץ על 'שכחתי סיסמה' במסך ההתחברות.\nתקבל מייל עם קישור לאיפוס.\n\nאם לא קיבלת – בדוק בספאם.",
      options: ["✅ קיבלתי מייל", "❌ לא קיבלתי כלום"],
      nextStep: {
        "✅ קיבלתי מייל": "resolved",
        "❌ לא קיבלתי כלום": "escalate"
      }
    }
  ],
  login_other: [
    {
      bot: "אוקיי, תספר לי במילים שלך מה קורה?",
      options: []
    }
  ],

  // בעיות דיווח שעות
  worklog_1: [
    {
      bot: "מבסוט שהגעת – ננסה לפתור את זה ביחד 🙂\n\nקורה אצל הרבה מנהלי עבודה...\n\nקודם נבדוק: האם הפרויקט שאתה מדווח עליו **פתוח**?",
      options: ["✔ כן, פתוח", "✖ לא בטוח", "✖ נראה סגור"],
      nextStep: {
        "✔ כן, פתוח": "worklog_date",
        "✖ לא בטוח": "worklog_check_project",
        "✖ נראה סגור": "worklog_closed_project"
      }
    }
  ],
  worklog_date: [
    {
      bot: "מצוין! 👍\n\nעכשיו, האם אתה מנסה לדווח על **תאריך שעבר**?\n(לא היום)",
      options: ["כן, על אתמול או לפני", "לא, על היום"],
      nextStep: {
        "כן, על אתמול או לפני": "worklog_past_date",
        "לא, על היום": "worklog_today"
      }
    }
  ],
  worklog_past_date: [
    {
      bot: "אהה, מכיר את זה! 😊\n\nהמערכת מאפשרת לדווח רק על 7 ימים אחורה.\nאם עבר יותר זמן – צריך אישור מנהל.\n\nזה המצב?",
      options: ["כן, עבר יותר מ-7 ימים", "לא, זה בטווח"],
      nextStep: {
        "כן, עבר יותר מ-7 ימים": "worklog_need_manager",
        "לא, זה בטווח": "escalate"
      }
    }
  ],
  worklog_need_manager: [
    {
      bot: "במקרה הזה, תצטרך לפנות למנהל האזור שלך.\nהוא יכול לאשר דיווח רטרואקטיבי.\n\nרוצה שאעביר את זה לנציג שיעזור?",
      options: ["✅ כן, תעביר", "❌ לא, אפנה למנהל"],
      nextStep: {
        "✅ כן, תעביר": "escalate",
        "❌ לא, אפנה למנהל": "resolved"
      }
    }
  ],
  worklog_today: [
    {
      bot: "אוקיי, אז זה משהו אחר.\n\nיש הודעת שגיאה כלשהי?",
      options: ["כן, יש שגיאה", "לא, פשוט לא עובד"],
      nextStep: {
        "כן, יש שגיאה": "escalate",
        "לא, פשוט לא עובד": "escalate"
      }
    }
  ],
  worklog_check_project: [
    {
      bot: "בוא נבדוק יחד:\n\n1. לך לרשימת הפרויקטים\n2. חפש את הפרויקט שלך\n3. בדוק אם יש לידו תג 'פעיל' ירוק\n\nמה אתה רואה?",
      options: ["יש תג ירוק 'פעיל'", "יש תג אפור 'סגור'", "לא מוצא את הפרויקט"],
      nextStep: {
        "יש תג ירוק 'פעיל'": "worklog_date",
        "יש תג אפור 'סגור'": "worklog_closed_project",
        "לא מוצא את הפרויקט": "escalate"
      }
    }
  ],
  worklog_closed_project: [
    {
      bot: "אהה, זה מסביר! 💡\n\nפרויקט סגור = אי אפשר לדווח עליו שעות.\nתצטרך לפנות למנהל האזור לפתוח אותו מחדש.\n\nרוצה שאעביר את זה לנציג?",
      options: ["✅ כן, תעביר", "❌ לא צריך"],
      nextStep: {
        "✅ כן, תעביר": "escalate",
        "❌ לא צריך": "resolved"
      }
    }
  ],

  // בעיות הזמנת עבודה
  workorder_1: [
    {
      bot: "בוא נטפל בזה 📋\n\nמה הבעיה עם ההזמנה?",
      options: ["לא מצליח ליצור הזמנה", "הספק לא מגיב", "צריך לבטל הזמנה", "משהו אחר"],
      nextStep: {
        "לא מצליח ליצור הזמנה": "workorder_create",
        "הספק לא מגיב": "workorder_supplier",
        "צריך לבטל הזמנה": "workorder_cancel",
        "משהו אחר": "escalate"
      }
    }
  ],
  workorder_create: [
    {
      bot: "אוקיי, בוא נראה...\n\nהאם בחרת פרויקט להזמנה?",
      options: ["כן", "לא בטוח"],
      nextStep: {
        "כן": "workorder_create_2",
        "לא בטוח": "workorder_create_2"
      }
    }
  ],
  workorder_create_2: [
    {
      bot: "כדי ליצור הזמנה צריך:\n\n1. לבחור פרויקט פעיל\n2. לבחור סוג עבודה\n3. לבחור ציוד\n4. לבחור ספק\n\nאיפה נתקעת?",
      options: ["בבחירת פרויקט", "בבחירת ספק", "בשמירה", "אחר"],
      nextStep: {
        "בבחירת פרויקט": "escalate",
        "בבחירת ספק": "escalate",
        "בשמירה": "escalate",
        "אחר": "escalate"
      }
    }
  ],
  workorder_supplier: [
    {
      bot: "ספקים לפעמים לוקחים זמן להגיב 😅\n\nכמה זמן עבר מאז ששלחת?",
      options: ["פחות מ-24 שעות", "יותר מ-24 שעות", "יותר משבוע"],
      nextStep: {
        "פחות מ-24 שעות": "workorder_supplier_wait",
        "יותר מ-24 שעות": "workorder_supplier_contact",
        "יותר משבוע": "escalate"
      }
    }
  ],
  workorder_supplier_wait: [
    {
      bot: "תן לו עוד קצת זמן 😊\n\nספקים מקבלים התראה במייל ובמערכת.\nאם לא יגיב תוך 24 שעות – נסה ליצור קשר טלפוני.\n\nעזרתי?",
      options: ["✅ כן, תודה!", "❌ עדיין צריך עזרה"],
      nextStep: {
        "✅ כן, תודה!": "resolved",
        "❌ עדיין צריך עזרה": "escalate"
      }
    }
  ],
  workorder_supplier_contact: [
    {
      bot: "24 שעות זה הרבה.\n\nאני ממליץ:\n1. להתקשר לספק ישירות\n2. או לבטל ולשלוח לספק אחר\n\nרוצה שנציג יעזור לך?",
      options: ["✅ כן, תעביר לנציג", "❌ אסתדר לבד"],
      nextStep: {
        "✅ כן, תעביר לנציג": "escalate",
        "❌ אסתדר לבד": "resolved"
      }
    }
  ],
  workorder_cancel: [
    {
      bot: "לבטל הזמנה אפשר רק אם היא בסטטוס 'ממתין' או 'נשלח לספק'.\n\nמה הסטטוס של ההזמנה שלך?",
      options: ["ממתין", "נשלח לספק", "אושר", "לא יודע"],
      nextStep: {
        "ממתין": "workorder_cancel_how",
        "נשלח לספק": "workorder_cancel_how",
        "אושר": "escalate",
        "לא יודע": "escalate"
      }
    }
  ],
  workorder_cancel_how: [
    {
      bot: "מצוין! 👍\n\nלך להזמנה, לחץ עליה, ובחר 'בטל הזמנה'.\n\nעבד?",
      options: ["✅ כן, ביטלתי!", "❌ לא מוצא את הכפתור"],
      nextStep: {
        "✅ כן, ביטלתי!": "resolved",
        "❌ לא מוצא את הכפתור": "escalate"
      }
    }
  ],

  // בעיות פרויקט
  project_1: [
    {
      bot: "בעיה בפרויקט? בוא נראה מה קורה 🏗️\n\nמה הבעיה?",
      options: ["לא רואה את הפרויקט שלי", "צריך להוסיף פרויקט", "צריך לשנות משהו בפרויקט", "אחר"],
      nextStep: {
        "לא רואה את הפרויקט שלי": "project_missing",
        "צריך להוסיף פרויקט": "project_add",
        "צריך לשנות משהו בפרויקט": "project_edit",
        "אחר": "escalate"
      }
    }
  ],
  project_missing: [
    {
      bot: "אתה רואה רק פרויקטים שמשויכים אליך.\n\nאם חסר פרויקט – צריך לבקש ממנהל האזור לשייך אותך.\n\nרוצה שאעביר את זה לנציג?",
      options: ["✅ כן", "❌ לא, אפנה למנהל"],
      nextStep: {
        "✅ כן": "escalate",
        "❌ לא, אפנה למנהל": "resolved"
      }
    }
  ],
  project_add: [
    {
      bot: "רק מנהלי אזור ומעלה יכולים ליצור פרויקטים חדשים.\n\nאם אתה מנהל אזור – יש לך כפתור 'הוסף פרויקט' בתפריט.\n\nמה התפקיד שלך?",
      options: ["מנהל עבודה", "מנהל אזור", "מנהל מרחב", "אחר"],
      nextStep: {
        "מנהל עבודה": "project_add_no_permission",
        "מנהל אזור": "escalate",
        "מנהל מרחב": "escalate",
        "אחר": "escalate"
      }
    }
  ],
  project_add_no_permission: [
    {
      bot: "כמנהל עבודה, אתה לא יכול ליצור פרויקטים.\n\nפנה למנהל האזור שלך – הוא יכול ליצור ולשייך אותך.\n\nעזרתי?",
      options: ["✅ כן, תודה!", "❌ צריך עוד עזרה"],
      nextStep: {
        "✅ כן, תודה!": "resolved",
        "❌ צריך עוד עזרה": "escalate"
      }
    }
  ],
  project_edit: [
    {
      bot: "מה אתה צריך לשנות בפרויקט?",
      options: ["שם הפרויקט", "תאריכים", "תקציב", "צוות", "אחר"]
    },
    {
      bot: "שינויים בפרויקט דורשים הרשאות מנהל.\n\nרוצה שנציג יעזור לך?",
      options: ["✅ כן", "❌ לא צריך"],
      nextStep: {
        "✅ כן": "escalate",
        "❌ לא צריך": "resolved"
      }
    }
  ],

  // משהו אחר
  other_1: [
    {
      bot: "אין בעיה! 😊\n\nספר לי במילים שלך מה קורה:",
      options: []
    }
  ],

  // סיום מוצלח
  resolved: [
    {
      bot: "מעולה! 🎉\n\nשמח שהצלחתי לעזור!\nאם תצטרך עוד משהו – אני כאן.",
      action: "resolve"
    }
  ],

  // העברה לנציג
  escalate: [
    {
      bot: "אוקיי, אני מעביר את זה לנציג תמיכה 📞\n\nהוא יקבל:\n• איפה היית במערכת\n• מה ניסינו לפתור\n• הפרטים שלך\n\nתכתוב לי בקצרה מה הבעיה:",
      options: [],
      action: "open_ticket"
    }
  ]
};

const HumanSupportChat: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const messagesEndRef = useRef<HTMLDivElement>(null);
  
  // State
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [currentFlow, setCurrentFlow] = useState('start');
  const [currentStepIndex, setCurrentStepIndex] = useState(0);
  const [inputText, setInputText] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [isSending, setIsSending] = useState(false);
  const [conversationHistory, setConversationHistory] = useState<string[]>([]);
  const [ticketSent, setTicketSent] = useState(false);

  // User info
  const [userInfo, setUserInfo] = useState({
    id: '',
    name: 'משתמש',
    role: 'USER',
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
        });
      } catch (e) {
        console.error('Error parsing user info:', e);
      }
    }
  }, []);

  // Scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Start conversation when opened
  useEffect(() => {
    if (isOpen && messages.length === 0) {
      startConversation();
    }
  }, [isOpen]);

  // Generate unique ID
  const generateId = () => `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

  // Add bot message with typing effect
  const addBotMessage = async (text: string, options?: string[]) => {
    // Show typing indicator
    setIsTyping(true);
    
    // Wait for "typing" effect
    await new Promise(resolve => setTimeout(resolve, 800 + Math.random() * 400));
    
    setIsTyping(false);
    
    const newMessage: Message = {
      id: generateId(),
      from: 'bot',
      text,
      timestamp: new Date(),
      options
    };
    
    setMessages(prev => [...prev, newMessage]);
  };

  // Add user message
  const addUserMessage = (text: string) => {
    const newMessage: Message = {
      id: generateId(),
      from: 'user',
      text,
      timestamp: new Date()
    };
    
    setMessages(prev => [...prev, newMessage]);
    setConversationHistory(prev => [...prev, text]);
  };

  // Start conversation
  const startConversation = async () => {
    const flow = BOT_FLOWS['start'];
    if (flow && flow[0]) {
      await addBotMessage(flow[0].bot!, flow[0].options);
    }
  };

  // Handle option click
  const handleOptionClick = async (option: string) => {
    addUserMessage(option);
    
    const flow = BOT_FLOWS[currentFlow];
    const currentStep = flow?.[currentStepIndex];
    
    if (currentStep?.nextStep && currentStep.nextStep[option]) {
      // Move to next flow
      const nextFlowName = currentStep.nextStep[option];
      setCurrentFlow(nextFlowName);
      setCurrentStepIndex(0);
      
      const nextFlow = BOT_FLOWS[nextFlowName];
      if (nextFlow && nextFlow[0]) {
        await addBotMessage(nextFlow[0].bot!, nextFlow[0].options);
        
        // Check for actions
        if (nextFlow[0].action === 'resolve') {
          // Conversation resolved
        } else if (nextFlow[0].action === 'open_ticket') {
          // Wait for user input
        }
      }
    } else if (flow && currentStepIndex < flow.length - 1) {
      // Move to next step in same flow
      setCurrentStepIndex(prev => prev + 1);
      const nextStep = flow[currentStepIndex + 1];
      if (nextStep) {
        await addBotMessage(nextStep.bot!, nextStep.options);
      }
    }
  };

  // Handle text input
  const handleSendMessage = async () => {
    if (!inputText.trim()) return;
    
    const text = inputText.trim();
    setInputText('');
    addUserMessage(text);
    
    const flow = BOT_FLOWS[currentFlow];
    const currentStep = flow?.[currentStepIndex];
    
    // Check if we need to send ticket
    if (currentStep?.action === 'open_ticket' || currentFlow === 'escalate' || currentFlow === 'other_1') {
      await sendTicket(text);
    } else if (flow && currentStepIndex < flow.length - 1) {
      // Move to next step
      setCurrentStepIndex(prev => prev + 1);
      const nextStep = flow[currentStepIndex + 1];
      if (nextStep) {
        await addBotMessage(nextStep.bot!, nextStep.options);
      }
    } else {
      // Default: escalate
      setCurrentFlow('escalate');
      setCurrentStepIndex(0);
      const escalateFlow = BOT_FLOWS['escalate'];
      if (escalateFlow && escalateFlow[0]) {
        await addBotMessage(escalateFlow[0].bot!, escalateFlow[0].options);
      }
    }
  };

  // Send ticket to backend
  const sendTicket = async (userMessage: string) => {
    setIsSending(true);
    
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch('/api/v1/support-tickets/from-widget', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          userId: userInfo.id,
          userName: userInfo.name,
          userRole: userInfo.role,
          currentRoute: location.pathname,
          category: currentFlow.split('_')[0].toUpperCase(),
          stepsWalked: conversationHistory.map((text, i) => ({ stepId: `step_${i}`, helped: false })),
          userMessage,
          clientContext: {
            url: window.location.href,
            browser: navigator.userAgent.substring(0, 100),
            resolution: `${window.innerWidth}x${window.innerHeight}`,
            timestamp: new Date().toISOString(),
          },
        }),
      });

      setTicketSent(true);
      
      await addBotMessage(
        "נשלח! 🎉\n\nנציג תמיכה יחזור אליך בהקדם.\nבדרך כלל תוך כמה שעות.\n\nתודה על הסבלנות! 💚"
      );
    } catch (error) {
      console.error('Error sending ticket:', error);
      await addBotMessage(
        "אופס, משהו השתבש 😅\n\nנסה שוב או שלח מייל:\n📧 avitbulnir@gmail.com"
      );
    } finally {
      setIsSending(false);
    }
  };

  // Reset conversation
  const handleReset = () => {
    setMessages([]);
    setCurrentFlow('start');
    setCurrentStepIndex(0);
    setConversationHistory([]);
    setTicketSent(false);
    startConversation();
  };

  // Close chat
  const handleClose = () => {
    setIsOpen(false);
  };

  // Get current options
  const getCurrentOptions = (): string[] => {
    const flow = BOT_FLOWS[currentFlow];
    const currentStep = flow?.[currentStepIndex];
    return currentStep?.options || [];
  };

  const showInput = getCurrentOptions().length === 0 && !ticketSent;

  return (
    <>
      {/* Floating Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={`fixed bottom-6 left-6 z-50 p-4 rounded-full shadow-xl transition-all duration-300 ${
          isOpen 
            ? 'bg-gray-700 hover:bg-gray-800 scale-90' 
            : 'bg-gradient-to-br from-kkl-green to-kkl-green-dark hover:shadow-2xl hover:scale-110'
        }`}
        aria-label={isOpen ? 'סגור צ\'אט' : 'פתח צ\'אט תמיכה'}
      >
        {isOpen ? (
          <X className="w-6 h-6 text-white" />
        ) : (
          <div className="relative">
            <MessageCircle className="w-6 h-6 text-white" />
            <span className="absolute -top-1 -right-1 w-3 h-3 bg-green-400 rounded-full animate-pulse" />
          </div>
        )}
      </button>

      {/* Chat Window */}
      {isOpen && (
        <div 
          className="fixed bottom-24 left-6 z-50 w-[380px] h-[520px] bg-white rounded-2xl shadow-2xl overflow-hidden flex flex-col animate-slideUp border border-gray-200"
          dir="rtl"
        >
          {/* Header */}
          <div className="bg-gradient-to-r from-kkl-green to-kkl-green-dark p-4 text-white flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-white/20 rounded-full flex items-center justify-center">
                <Sparkles className="w-5 h-5" />
              </div>
              <div>
                <h3 className="font-bold">תמיכה קק"ל</h3>
                <p className="text-xs text-white/80 flex items-center gap-1">
                  <span className="w-2 h-2 bg-green-300 rounded-full animate-pulse" />
                  מחובר עכשיו
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <button 
                onClick={handleReset}
                className="p-2 hover:bg-white/20 rounded-lg transition-colors text-sm"
                title="התחל מחדש"
              >
                <ArrowLeft className="w-4 h-4" />
              </button>
              <button 
                onClick={handleClose}
                className="p-2 hover:bg-white/20 rounded-lg transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-gray-50">
            {messages.map((message) => (
              <div
                key={message.id}
                className={`flex ${message.from === 'user' ? 'justify-start' : 'justify-end'}`}
              >
                <div
                  className={`max-w-[85%] rounded-2xl px-4 py-3 ${
                    message.from === 'user'
                      ? 'bg-white border border-gray-200 text-gray-800'
                      : 'bg-gradient-to-br from-kkl-green to-kkl-green-dark text-white'
                  }`}
                >
                  <p className="text-sm whitespace-pre-line leading-relaxed">{message.text}</p>
                  
                  {/* Options */}
                  {message.options && message.options.length > 0 && (
                    <div className="mt-3 space-y-2">
                      {message.options.map((option, index) => (
                        <button
                          key={index}
                          onClick={() => handleOptionClick(option)}
                          className="w-full text-right px-3 py-2 bg-white/20 hover:bg-white/30 rounded-xl text-sm transition-colors border border-white/20"
                        >
                          {option}
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ))}

            {/* Typing indicator */}
            {isTyping && (
              <div className="flex justify-end">
                <div className="bg-gradient-to-br from-kkl-green to-kkl-green-dark text-white rounded-2xl px-4 py-3">
                  <div className="flex items-center gap-1">
                    <span className="w-2 h-2 bg-white/60 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                    <span className="w-2 h-2 bg-white/60 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                    <span className="w-2 h-2 bg-white/60 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                  </div>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* Input */}
          {showInput && (
            <div className="p-4 bg-white border-t border-gray-200">
              <div className="flex items-center gap-2">
                <input
                  type="text"
                  value={inputText}
                  onChange={(e) => setInputText(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
                  placeholder="כתוב הודעה..."
                  className="flex-1 px-4 py-3 bg-gray-100 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-kkl-green"
                  disabled={isSending}
                />
                <button
                  onClick={handleSendMessage}
                  disabled={!inputText.trim() || isSending}
                  className="p-3 bg-kkl-green text-white rounded-xl hover:bg-kkl-green-dark transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isSending ? (
                    <Loader2 className="w-5 h-5 animate-spin" />
                  ) : (
                    <Send className="w-5 h-5" />
                  )}
                </button>
              </div>
            </div>
          )}

          {/* Phone footer */}
          {ticketSent && (
            <div className="p-3 bg-gray-100 border-t border-gray-200 text-center">
              <p className="text-xs text-gray-500 flex items-center justify-center gap-2">
                <Mail className="w-3 h-3" />
                מייל: avitbulnir@gmail.com
              </p>
            </div>
          )}
        </div>
      )}

      {/* Styles */}
      <style>{`
        @keyframes slideUp {
          from {
            opacity: 0;
            transform: translateY(20px) scale(0.95);
          }
          to {
            opacity: 1;
            transform: translateY(0) scale(1);
          }
        }
        .animate-slideUp {
          animation: slideUp 0.3s ease-out;
        }
      `}</style>
    </>
  );
};

export default HumanSupportChat;

