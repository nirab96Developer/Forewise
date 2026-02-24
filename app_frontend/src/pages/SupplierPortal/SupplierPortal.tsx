// @ts-nocheck
// src/pages/SupplierPortal/SupplierPortal.tsx
// פורטל ספקים חיצוני - דף נחיתה לספקים לצפייה ואישור הזמנות
// הספק לא מחובר לאפליקציה - מקבל לינק ייחודי

import React, { useState, useEffect, useCallback } from "react";
import { useParams, useSearchParams } from "react-router-dom";
import { 
  Loader2, 
  Package,
  CheckCircle,
  XCircle,
  Clock,
  Truck,
  Phone,
  Mail,
  FileText,
  AlertCircle,
  Check,
  X,
  ChevronDown,
  ChevronUp,
  Calendar,
  MapPin,
  DollarSign,
  Building,
  AlertTriangle,
  Timer
} from "lucide-react";
import api from "../../services/api";

// KKL Logo
import kklLogo from "/logo-kkl-transparent.png";

interface SupplierOrder {
  order_number: number;
  title: string | null;
  description: string | null;
  status: string | null;
  priority: string | null;
  equipment_type: string | null;
  work_start_date: string | null;
  work_end_date: string | null;
  estimated_hours: number | null;
  hourly_rate: number | null;
  total_amount: number | null;
  project_name: string | null;
  region_name: string | null;
  area_name: string | null;
  supplier_name: string | null;
  supplier_id: number | null;
  portal_token: string;
  expires_at: string | null;
  time_remaining_seconds: number | null;
  is_forced_selection: boolean;
  is_expired: boolean;
  already_responded: boolean;
}

const SupplierPortal: React.FC = () => {
  const { token } = useParams<{ token: string }>();
  const [searchParams] = useSearchParams();
  const queryToken = searchParams.get('token');
  
  const portalToken = token || queryToken;
  
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [order, setOrder] = useState<SupplierOrder | null>(null);
  const [showDetails, setShowDetails] = useState(true);
  const [isProcessing, setIsProcessing] = useState(false);
  const [actionComplete, setActionComplete] = useState<'accepted' | 'rejected' | null>(null);
  const [licensePlate, setLicensePlate] = useState('');
  const [notes, setNotes] = useState('');
  const [rejectReason, setRejectReason] = useState('');
  const [timeRemaining, setTimeRemaining] = useState<number | null>(null);

  const loadOrderData = useCallback(async () => {
    if (!portalToken) {
      setError('לינק לא תקין - חסר טוקן');
      setIsLoading(false);
      return;
    }

    try {
      setIsLoading(true);
      setError(null);
      
      // Call the real API
      const response = await api.get(`/supplier-portal/${portalToken}`);
      
      if (response.data) {
        setOrder(response.data);
        setTimeRemaining(response.data.time_remaining_seconds);
        
        // Check if already expired or responded
        if (response.data.is_expired) {
          setError('פג תוקף הקישור. אנא פנה למנהל העבודה לקבלת קישור חדש.');
        } else if (response.data.already_responded) {
          setError('כבר נענית להזמנה זו.');
        }
      }
      setIsLoading(false);
    } catch (err: any) {
      console.error('Error loading supplier portal:', err);
      if (err.response?.status === 404) {
        setError('ההזמנה לא נמצאה או פג תוקפה');
      } else if (err.response?.status === 400) {
        setError(err.response?.data?.detail || 'ההזמנה כבר טופלה');
      } else {
        setError('שגיאה בטעינת נתוני ההזמנה');
      }
      setIsLoading(false);
    }
  }, [portalToken]);

  useEffect(() => {
    loadOrderData();
  }, [loadOrderData]);

  // Countdown timer
  useEffect(() => {
    if (timeRemaining === null || timeRemaining <= 0) return;
    
    const interval = setInterval(() => {
      setTimeRemaining(prev => {
        if (prev === null || prev <= 0) return 0;
        return prev - 1;
      });
    }, 1000);
    
    return () => clearInterval(interval);
  }, [timeRemaining]);

  const formatTimeRemaining = (seconds: number): string => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    
    if (hours > 0) {
      return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    }
    return `${minutes}:${secs.toString().padStart(2, '0')}`;
  };

  const handleAccept = async () => {
    if (!portalToken) return;
    
    try {
      setIsProcessing(true);
      
      await api.post(`/supplier-portal/${portalToken}/accept`, {
        notes: notes,
        license_plate: licensePlate
      });
      
      setActionComplete('accepted');
    } catch (err: any) {
      console.error('Error accepting order:', err);
      alert(err.response?.data?.detail || 'שגיאה באישור ההזמנה');
    } finally {
      setIsProcessing(false);
    }
  };

  const handleReject = async () => {
    if (!portalToken) return;
    
    if (!rejectReason.trim()) {
      alert('נא לציין סיבת הדחייה');
      return;
    }
    
    try {
      setIsProcessing(true);
      
      await api.post(`/supplier-portal/${portalToken}/reject`, {
        notes: `${rejectReason}${notes ? ` - ${notes}` : ''}`
      });
      
      setActionComplete('rejected');
    } catch (err: any) {
      console.error('Error rejecting order:', err);
      alert(err.response?.data?.detail || 'שגיאה בדחיית ההזמנה');
    } finally {
      setIsProcessing(false);
    }
  };

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return 'לא צוין';
    const date = new Date(dateStr);
    return date.toLocaleDateString('he-IL', { 
      day: 'numeric', 
      month: 'long', 
      year: 'numeric' 
    });
  };

  const getPriorityBadge = (priority: string | null) => {
    const badges: Record<string, { bg: string; text: string; label: string }> = {
      'LOW': { bg: 'bg-gray-100', text: 'text-gray-600', label: 'נמוכה' },
      'MEDIUM': { bg: 'bg-blue-100', text: 'text-blue-600', label: 'בינונית' },
      'HIGH': { bg: 'bg-orange-100', text: 'text-orange-600', label: 'גבוהה' },
      'URGENT': { bg: 'bg-red-100', text: 'text-red-600', label: 'דחופה' },
    };
    const badge = badges[priority || 'MEDIUM'] || badges['MEDIUM'];
    return (
      <span className={`px-2 py-1 rounded-full text-xs font-medium ${badge.bg} ${badge.text}`}>
        {badge.label}
      </span>
    );
  };

  // Loading state
  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-slate-50 to-slate-100 flex items-center justify-center" dir="rtl">
        <div className="bg-white rounded-2xl shadow-xl p-8 flex items-center gap-4">
          <Loader2 className="w-8 h-8 animate-spin text-emerald-600" />
          <span className="text-lg text-slate-700">טוען הזמנה...</span>
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-slate-50 to-slate-100 flex items-center justify-center p-4" dir="rtl">
        <div className="bg-white rounded-2xl shadow-xl p-8 max-w-md text-center">
          <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <AlertCircle className="w-8 h-8 text-red-600" />
          </div>
          <h1 className="text-xl font-bold text-slate-800 mb-2">שגיאה</h1>
          <p className="text-slate-600">{error}</p>
          <p className="text-sm text-slate-400 mt-4">אנא פנה למנהל העבודה לקבלת לינק חדש</p>
        </div>
      </div>
    );
  }

  // Action complete state
  if (actionComplete) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-slate-50 to-slate-100 flex items-center justify-center p-4" dir="rtl">
        <div className="bg-white rounded-2xl shadow-xl p-8 max-w-md text-center">
          {/* Logo */}
          <img src={kklLogo} alt="KKL Logo" className="w-20 h-20 mx-auto mb-4 object-contain" />
          
          <div className={`w-20 h-20 ${actionComplete === 'accepted' ? 'bg-emerald-100' : 'bg-red-100'} rounded-full flex items-center justify-center mx-auto mb-6`}>
            {actionComplete === 'accepted' ? (
              <CheckCircle className="w-10 h-10 text-emerald-600" />
            ) : (
              <XCircle className="w-10 h-10 text-red-600" />
            )}
          </div>
          <h1 className="text-2xl font-bold text-slate-800 mb-3">
            {actionComplete === 'accepted' ? 'ההזמנה אושרה!' : 'ההזמנה נדחתה'}
          </h1>
          <p className="text-slate-600 mb-4">
            {actionComplete === 'accepted' 
              ? 'תודה! נשלחה הודעה למנהל העבודה. ייצרו איתך קשר בהקדם.'
              : 'נשלחה הודעה למנהל העבודה.'
            }
          </p>
          <div className="bg-slate-50 rounded-lg p-4 text-sm text-slate-600">
            <div className="font-medium">מספר הזמנה: {order?.order_number}</div>
            <div className="mt-1">פרויקט: {order?.project_name || 'לא צוין'}</div>
          </div>
          <p className="text-sm text-slate-400 mt-6">
            ניתן לסגור את הדף
          </p>
        </div>
      </div>
    );
  }

  if (!order) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-slate-50 to-slate-100 flex items-center justify-center p-4" dir="rtl">
        <div className="bg-white rounded-2xl shadow-xl p-8 max-w-md text-center">
          <Package className="w-16 h-16 text-slate-300 mx-auto mb-4" />
          <h1 className="text-xl font-bold text-slate-800 mb-2">לא נמצאה הזמנה</h1>
          <p className="text-slate-600">אנא פנה למנהל העבודה</p>
        </div>
      </div>
    );
  }

  const isTimeRunningLow = timeRemaining !== null && timeRemaining < 1800; // Less than 30 min

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 to-slate-100" dir="rtl">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-slate-200">
        <div className="max-w-2xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <img src={kklLogo} alt="KKL Logo" className="w-14 h-14 object-contain" />
              <div>
                <h1 className="text-xl font-bold text-slate-800">הזמנת עבודה</h1>
                <p className="text-sm text-slate-500">קק"ל - ניהול יערות</p>
              </div>
            </div>
            <div className="text-left">
              <div className="text-lg font-bold text-emerald-700">#{order.order_number}</div>
              <div className="flex items-center gap-2">
                {getPriorityBadge(order.priority)}
                {order.is_forced_selection && (
                  <span className="text-xs bg-orange-100 text-orange-700 px-2 py-0.5 rounded-full">
                    כפייה
                  </span>
                )}
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Timer Banner */}
      {timeRemaining !== null && timeRemaining > 0 && (
        <div className={`${isTimeRunningLow ? 'bg-red-500' : 'bg-emerald-600'} text-white py-2`}>
          <div className="max-w-2xl mx-auto px-4 flex items-center justify-center gap-2">
            <Timer className="w-4 h-4" />
            <span className="text-sm font-medium">
              זמן נותר לתגובה: {formatTimeRemaining(timeRemaining)}
            </span>
          </div>
        </div>
      )}

      <main className="max-w-2xl mx-auto px-4 py-6 space-y-6">
        
        {/* Order Title */}
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
          <h2 className="text-xl font-bold text-slate-800 mb-2">
            {order.title || `הזמנת עבודה #${order.order_number}`}
          </h2>
          {order.description && (
            <p className="text-slate-600">{order.description}</p>
          )}
          
          {/* Supplier Welcome */}
          {order.supplier_name && (
            <div className="mt-4 p-3 bg-emerald-50 border border-emerald-200 rounded-lg">
              <div className="text-sm text-emerald-800">
                שלום <span className="font-bold">{order.supplier_name}</span>,
                אנא עיין בפרטי ההזמנה ובחר לאשר או לדחות.
              </div>
            </div>
          )}
          
          {order.is_forced_selection && (
            <div className="mt-4 p-3 bg-orange-50 border border-orange-200 rounded-lg flex items-start gap-2">
              <AlertTriangle className="w-5 h-5 text-orange-600 flex-shrink-0 mt-0.5" />
              <div>
                <div className="text-sm font-medium text-orange-800">בחירה ישירה</div>
                <div className="text-sm text-orange-700">הזמנה זו הוקצתה לך ישירות על ידי מנהל העבודה.</div>
              </div>
            </div>
          )}
        </div>

        {/* Order Details */}
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
          <button
            onClick={() => setShowDetails(!showDetails)}
            className="w-full p-4 flex items-center justify-between hover:bg-slate-50 transition-colors"
          >
            <h3 className="font-bold text-slate-800 flex items-center gap-2">
              <FileText className="w-5 h-5 text-emerald-600" />
              פרטי ההזמנה
            </h3>
            {showDetails ? (
              <ChevronUp className="w-5 h-5 text-slate-400" />
            ) : (
              <ChevronDown className="w-5 h-5 text-slate-400" />
            )}
          </button>
          
          {showDetails && (
            <div className="border-t border-slate-100 p-4 space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="flex items-start gap-3">
                  <Building className="w-5 h-5 text-slate-400 mt-0.5" />
                  <div>
                    <div className="text-sm text-slate-500">פרויקט</div>
                    <div className="font-medium text-slate-800">{order.project_name || 'לא צוין'}</div>
                  </div>
                </div>
                
                <div className="flex items-start gap-3">
                  <MapPin className="w-5 h-5 text-slate-400 mt-0.5" />
                  <div>
                    <div className="text-sm text-slate-500">מיקום</div>
                    <div className="font-medium text-slate-800">
                      {order.region_name && order.area_name 
                        ? `${order.region_name} / ${order.area_name}`
                        : order.region_name || order.area_name || 'לא צוין'}
                    </div>
                  </div>
                </div>
                
                <div className="flex items-start gap-3">
                  <Calendar className="w-5 h-5 text-slate-400 mt-0.5" />
                  <div>
                    <div className="text-sm text-slate-500">תאריכים</div>
                    <div className="font-medium text-slate-800">
                      {formatDate(order.work_start_date)}
                      {order.work_end_date && order.work_end_date !== order.work_start_date && (
                        <> - {formatDate(order.work_end_date)}</>
                      )}
                    </div>
                  </div>
                </div>
                
                <div className="flex items-start gap-3">
                  <Truck className="w-5 h-5 text-slate-400 mt-0.5" />
                  <div>
                    <div className="text-sm text-slate-500">סוג ציוד נדרש</div>
                    <div className="font-medium text-slate-800">
                      {order.equipment_type || 'לא צוין'}
                    </div>
                  </div>
                </div>
                
                <div className="flex items-start gap-3">
                  <Clock className="w-5 h-5 text-slate-400 mt-0.5" />
                  <div>
                    <div className="text-sm text-slate-500">שעות מוערכות</div>
                    <div className="font-medium text-slate-800">
                      {order.estimated_hours ? `${order.estimated_hours} שעות` : 'לא צוין'}
                    </div>
                  </div>
                </div>
                
                <div className="flex items-start gap-3">
                  <DollarSign className="w-5 h-5 text-slate-400 mt-0.5" />
                  <div>
                    <div className="text-sm text-slate-500">תעריף לשעה</div>
                    <div className="font-medium text-slate-800">
                      {order.hourly_rate ? `₪${order.hourly_rate.toFixed(2)}` : 'לפי הסכם'}
                    </div>
                  </div>
                </div>
              </div>
              
              {/* Total Amount */}
              {order.total_amount && (
                <div className="pt-4 border-t border-slate-100">
                  <div className="bg-emerald-50 rounded-lg p-4 text-center">
                    <div className="text-sm text-emerald-700">סכום משוער</div>
                    <div className="text-2xl font-bold text-emerald-800">₪{order.total_amount.toFixed(2)}</div>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Accept Form */}
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
          <h3 className="font-bold text-slate-800 mb-4 flex items-center gap-2">
            <Check className="w-5 h-5 text-emerald-600" />
            פרטים לאישור
          </h3>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">
                מספר רישוי הכלי <span className="text-slate-400">(אופציונלי)</span>
              </label>
              <input
                type="text"
                value={licensePlate}
                onChange={(e) => setLicensePlate(e.target.value)}
                placeholder="לדוגמה: 12-345-67"
                className="w-full p-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
                dir="ltr"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">
                הערות <span className="text-slate-400">(אופציונלי)</span>
              </label>
              <textarea
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                placeholder="הערות נוספות למנהל העבודה..."
                rows={2}
                className="w-full p-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
              />
            </div>
          </div>
        </div>

        {/* Reject Reason */}
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
          <h3 className="font-bold text-slate-800 mb-4 flex items-center gap-2">
            <X className="w-5 h-5 text-red-600" />
            במקרה של דחייה
          </h3>
          
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">
              סיבת הדחייה <span className="text-red-500">*</span>
            </label>
            <select
              value={rejectReason}
              onChange={(e) => setRejectReason(e.target.value)}
              className="w-full p-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
            >
              <option value="">בחר סיבה...</option>
              <option value="לא זמין בתאריכים המבוקשים">לא זמין בתאריכים המבוקשים</option>
              <option value="כלי בתיקון">כלי בתיקון</option>
              <option value="עומס עבודה">עומס עבודה</option>
              <option value="מרחק גדול מדי">מרחק גדול מדי</option>
              <option value="אין כלי מתאים">אין כלי מתאים</option>
              <option value="סיבה אחרת">סיבה אחרת</option>
            </select>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex gap-4">
          <button
            onClick={handleAccept}
            disabled={isProcessing}
            className="flex-1 flex items-center justify-center gap-2 bg-emerald-600 text-white py-4 rounded-xl font-bold text-lg hover:bg-emerald-700 transition-colors disabled:opacity-50 shadow-lg"
          >
            {isProcessing ? (
              <Loader2 className="w-6 h-6 animate-spin" />
            ) : (
              <>
                <Check className="w-6 h-6" />
                אישור ההזמנה
              </>
            )}
          </button>
          
          <button
            onClick={handleReject}
            disabled={isProcessing || !rejectReason}
            className="flex-1 flex items-center justify-center gap-2 bg-white text-red-600 border-2 border-red-200 py-4 rounded-xl font-bold text-lg hover:bg-red-50 transition-colors disabled:opacity-50"
          >
            <X className="w-6 h-6" />
            דחייה
          </button>
        </div>

        {/* Expiry Warning */}
        {timeRemaining !== null && timeRemaining > 0 && (
          <div className={`${isTimeRunningLow ? 'bg-red-50 border-red-200' : 'bg-amber-50 border-amber-200'} border rounded-lg p-4 text-center`}>
            <div className={`text-sm ${isTimeRunningLow ? 'text-red-800' : 'text-amber-800'}`}>
              <Clock className="w-4 h-4 inline-block ml-1" />
              {isTimeRunningLow 
                ? 'הזמן עומד לפוג! אנא השב בהקדם.'
                : `תוקף הלינק יפוג בעוד ${formatTimeRemaining(timeRemaining)}`
              }
            </div>
          </div>
        )}

      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-slate-200 mt-12">
        <div className="max-w-2xl mx-auto px-4 py-4 text-center">
          <p className="text-sm text-slate-500">
            קרן קיימת לישראל - מערכת ניהול יערות
          </p>
          <p className="text-xs text-slate-400 mt-1">
            לשאלות או בעיות טכניות, פנה למנהל העבודה
          </p>
        </div>
      </footer>
    </div>
  );
};

export default SupplierPortal;
