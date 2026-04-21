// src/components/equipment/ScanEquipmentModal.tsx
//
// UNIFIED equipment intake modal — the single source of truth for scanning a
// piece of equipment against a work order in the field.
//
// Flow (matches the backend `scan-equipment` 3-scenario contract):
//   A) Match — same plate as the order → WO advances to IN_PROGRESS.
//   B) Same type, different plate → ask the user to transfer, then call
//      `confirm-equipment` which releases the equipment from any old WO.
//   C) Wrong type → blocked. Backend already moved the WO to
//      NEEDS_RE_COORDINATION and notified the coordinator. We surface the
//      result, plus an admin-only override path.
//
// The public props are kept identical so existing call sites (WorkOrderDetail,
// any future entry point) work without changes. `onSuccess` fires only when
// the equipment is actually attached to the WO (states A or B success, or
// admin override). Wrong-type closes the modal with an info toast — there is
// no equipment to attach.
import React, { useState, useEffect, useRef } from 'react';
import {
  Camera, Keyboard, Search, X, Loader2,
  AlertCircle, ScanLine, AlertTriangle, ArrowRightLeft, ShieldAlert
} from 'lucide-react';
import api from '../../services/api';
import { showToast } from '../common/Toast';
import { getUserRole } from '../../utils/permissions';

interface ScanEquipmentModalProps {
  isOpen: boolean;
  onClose: () => void;
  workOrderId: number;
  onSuccess: (equipmentId: number, licensePlate: string, name: string) => void;
}

type ScanMode = 'camera' | 'manual';

type Phase =
  | 'scanning'
  | 'different_plate'
  | 'wrong_type'
  | 'admin_override';

interface ScanResult {
  status: 'ok' | 'different_plate' | 'wrong_type';
  message?: string;
  question?: string;
  equipment_id?: number | null;
  equipment_type?: string;
  ordered_type?: string;
  scanned_type?: string;
  admin_can_override?: boolean;
  wo_status?: string;
  previous_status?: string;
  old_project?: {
    wo_id: number;
    wo_number: number | null;
    project_name: string | null;
  } | null;
  work_order?: any;
}

const ScanEquipmentModal: React.FC<ScanEquipmentModalProps> = ({
  isOpen, onClose, workOrderId, onSuccess
}) => {
  const [mode, setMode] = useState<ScanMode>('camera');
  const [manualInput, setManualInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [cameraActive, setCameraActive] = useState(false);
  const [phase, setPhase] = useState<Phase>('scanning');
  const [scanResult, setScanResult] = useState<ScanResult | null>(null);
  const [scannedPlate, setScannedPlate] = useState<string>('');
  const [overrideReason, setOverrideReason] = useState('');
  const scannerRef = useRef<HTMLDivElement>(null);
  const html5QrCodeRef = useRef<any>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const isAdmin = (() => {
    const r = (getUserRole() || '').toUpperCase();
    return r === 'ADMIN' || r === 'SUPER_ADMIN';
  })();

  useEffect(() => {
    if (!isOpen) {
      stopCamera();
      setManualInput('');
      setError(null);
      setMode('camera');
      setPhase('scanning');
      setScanResult(null);
      setScannedPlate('');
      setOverrideReason('');
      return;
    }
    if (phase !== 'scanning') return;
    if (mode === 'camera') {
      const timer = setTimeout(() => startCamera(), 400);
      return () => clearTimeout(timer);
    }
    if (mode === 'manual') {
      stopCamera();
      setTimeout(() => inputRef.current?.focus(), 100);
    }
  }, [isOpen, mode, phase]);

  useEffect(() => {
    return () => { stopCamera(); };
  }, []);

  const startCamera = async () => {
    if (cameraActive || !isOpen) return;
    try {
      if (navigator.mediaDevices?.getUserMedia) {
        const testStream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' } });
        testStream.getTracks().forEach(t => t.stop());
      }
      const { Html5Qrcode } = await import('html5-qrcode');
      const scanner = new Html5Qrcode('scan-modal-qr-reader');
      html5QrCodeRef.current = scanner;
      await scanner.start(
        { facingMode: 'environment' },
        { fps: 10, qrbox: { width: 200, height: 200 }, aspectRatio: 1.0, disableFlip: false },
        (decodedText: string) => { handleResult(decodedText.trim()); },
        () => {}
      );
      setCameraActive(true);
      setError(null);
    } catch (err: any) {
      const isSecure = window.location.protocol !== 'https:' && window.location.hostname !== 'localhost';
      if (isSecure) {
        setError('המצלמה דורשת HTTPS. עבור ל-https://forewise.co');
      } else if (err?.name === 'NotAllowedError') {
        setError('גישה למצלמה נדחתה. אפשר בהגדרות הדפדפן.');
      } else {
        setError('לא ניתן לפתוח מצלמה. השתמש בהזנה ידנית.');
      }
      setMode('manual');
    }
  };

  const stopCamera = async () => {
    if (html5QrCodeRef.current) {
      try {
        await html5QrCodeRef.current.stop();
        html5QrCodeRef.current.clear();
      } catch {}
      html5QrCodeRef.current = null;
    }
    setCameraActive(false);
  };

  const handleResult = async (value: string) => {
    await stopCamera();
    // Accept either a raw plate or a QR payload like "equipment_id=42" — extract.
    let identifier = value;
    const idMatch = value.match(/equipment[_\/]?id[=\/:]?\s*(\d+)/i);
    if (idMatch) {
      // Numeric equipment id from QR — resolve to plate first
      try {
        const r = await api.get(`/equipment/by-code/${encodeURIComponent(idMatch[1])}`);
        identifier = r.data?.license_plate || identifier;
      } catch {}
    }
    await submitScan(identifier);
  };

  const handleManualSubmit = async () => {
    if (!manualInput.trim()) return;
    await submitScan(manualInput.trim());
  };

  const submitScan = async (rawPlate: string) => {
    const plate = rawPlate.trim();
    if (!plate) return;
    setLoading(true);
    setError(null);
    setScannedPlate(plate);
    try {
      const resp = await api.post(`/work-orders/${workOrderId}/scan-equipment`, { license_plate: plate });
      const data: ScanResult = resp.data;
      setScanResult(data);

      if (data.status === 'ok') {
        const eqId = data.equipment_id ?? data.work_order?.equipment_id ?? 0;
        onSuccess(eqId, plate, data.work_order?.equipment_name || data.equipment_type || '');
        showToast(data.message || 'כלי תואם — אומת בהצלחה', 'success');
        onClose();
        return;
      }

      if (data.status === 'different_plate') {
        setPhase('different_plate');
        return;
      }

      if (data.status === 'wrong_type') {
        // Backend already moved WO to NEEDS_RE_COORDINATION + notified.
        setPhase('wrong_type');
        return;
      }
    } catch (err: any) {
      const detail = err.response?.data?.detail || 'שגיאה בסריקת כלי';
      setError(detail);
      if (mode === 'camera' && phase === 'scanning') setTimeout(() => startCamera(), 1500);
    } finally {
      setLoading(false);
    }
  };

  // Scenario B confirm: transfer the equipment from any other active WO to this one.
  const handleConfirmDifferentPlate = async () => {
    if (!scanResult?.equipment_id) return;
    setLoading(true);
    setError(null);
    try {
      const resp = await api.post(`/work-orders/${workOrderId}/confirm-equipment`, {
        equipment_id: scanResult.equipment_id,
      });
      const wo = resp.data?.work_order;
      onSuccess(scanResult.equipment_id, scannedPlate, wo?.equipment_name || scanResult.equipment_type || '');
      showToast(resp.data?.message || 'כלי שויך להזמנה', 'success');
      onClose();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'שגיאה באישור העברת הכלי');
    } finally {
      setLoading(false);
    }
  };

  // Scenario C admin override: forcibly attach equipment despite type mismatch.
  const handleAdminOverride = async () => {
    if (!isAdmin) return;
    if (!overrideReason.trim() || overrideReason.trim().length < 5) {
      setError('יש לציין סיבה מפורטת לאישור החריג (לפחות 5 תווים)');
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const resp = await api.post(`/work-orders/${workOrderId}/admin-override-equipment`, {
        license_plate: scannedPlate,
        reason: overrideReason.trim(),
      });
      const wo = resp.data?.work_order;
      onSuccess(scanResult?.equipment_id || 0, scannedPlate, wo?.equipment_name || '');
      showToast(resp.data?.message || 'אישור חריג בוצע', 'success');
      onClose();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'שגיאה באישור חריג');
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4" dir="rtl">
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={onClose} />
      <div className="relative z-10 w-full max-w-md bg-white rounded-2xl shadow-2xl overflow-hidden">

        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-gray-100 bg-gray-50">
          <div className="flex items-center gap-2">
            <ScanLine className="w-5 h-5 text-green-600" />
            <h2 className="text-lg font-bold text-gray-900">
              {phase === 'scanning' && 'סריקת ציוד'}
              {phase === 'different_plate' && 'אישור העברת כלי'}
              {phase === 'wrong_type' && 'סוג ציוד לא תואם'}
              {phase === 'admin_override' && 'אישור חריג (מנהל)'}
            </h2>
          </div>
          <button onClick={onClose} className="p-1.5 hover:bg-gray-200 rounded-lg text-gray-400 hover:text-gray-600">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* PHASE: SCANNING */}
        {phase === 'scanning' && (
          <>
            <div className="flex gap-2 px-5 pt-4">
              <button
                onClick={() => setMode('camera')}
                className={`flex-1 py-2.5 rounded-xl font-medium text-sm flex items-center justify-center gap-2 transition-colors ${
                  mode === 'camera' ? 'bg-green-600 text-white shadow-sm' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
              >
                <Camera className="w-4 h-4" />
                סריקה מהירה
              </button>
              <button
                onClick={() => setMode('manual')}
                className={`flex-1 py-2.5 rounded-xl font-medium text-sm flex items-center justify-center gap-2 transition-colors ${
                  mode === 'manual' ? 'bg-green-600 text-white shadow-sm' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
              >
                <Keyboard className="w-4 h-4" />
                הזנה ידנית
              </button>
            </div>

            <div className="p-5">
              {mode === 'camera' && (
                <div>
                  <p className="text-sm text-gray-500 text-center mb-3">כוון את המצלמה אל סימון הזיהוי שעל הציוד</p>
                  <div className="relative rounded-xl overflow-hidden bg-black" style={{ minHeight: 260 }}>
                    <div id="scan-modal-qr-reader" ref={scannerRef} className="w-full" />
                    {!cameraActive && !error && (
                      <div className="absolute inset-0 flex items-center justify-center bg-gray-900">
                        <div className="text-center">
                          <Loader2 className="w-8 h-8 animate-spin text-green-400 mx-auto mb-2" />
                          <p className="text-gray-300 text-sm">מפעיל מצלמה...</p>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {mode === 'manual' && (
                <div>
                  <p className="text-sm text-gray-500 text-center mb-4">הקלד מספר רישוי</p>
                  <div className="flex gap-2">
                    <input
                      ref={inputRef}
                      type="text"
                      value={manualInput}
                      onChange={e => setManualInput(e.target.value)}
                      onKeyDown={e => e.key === 'Enter' && handleManualSubmit()}
                      placeholder="12-345-67"
                      className="flex-1 text-center text-lg font-bold py-3 px-4 border-2 border-gray-200 rounded-xl focus:border-green-500 focus:ring-2 focus:ring-green-200 placeholder:text-gray-300 placeholder:font-normal placeholder:text-base"
                      autoComplete="off"
                    />
                    <button
                      onClick={handleManualSubmit}
                      disabled={loading || !manualInput.trim()}
                      className="px-5 py-3 bg-green-600 text-white rounded-xl font-semibold hover:bg-green-700 disabled:opacity-50 flex items-center gap-2"
                    >
                      {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : <Search className="w-5 h-5" />}
                    </button>
                  </div>
                </div>
              )}

              {loading && mode === 'camera' && (
                <div className="mt-3 flex items-center justify-center gap-2 text-green-600">
                  <Loader2 className="w-5 h-5 animate-spin" />
                  <span className="text-sm font-medium">מאמת מול ההזמנה...</span>
                </div>
              )}

              {error && (
                <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-xl flex items-center gap-3">
                  <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0" />
                  <span className="text-red-700 text-sm">{error}</span>
                </div>
              )}
            </div>

            <div className="px-5 pb-4 text-center">
              <p className="text-xs text-gray-400">{`כל סריקה מאומתת מול הזמנה #${workOrderId}`}</p>
            </div>
          </>
        )}

        {/* PHASE: DIFFERENT PLATE — ask to transfer */}
        {phase === 'different_plate' && scanResult && (
          <div className="p-5">
            <div className="flex items-start gap-3 p-4 bg-amber-50 border border-amber-200 rounded-xl mb-4">
              <ArrowRightLeft className="w-5 h-5 text-amber-600 mt-0.5 flex-shrink-0" />
              <div className="text-sm text-amber-900">
                <p className="font-semibold mb-1">{scanResult.message}</p>
                <p className="leading-snug">{scanResult.question}</p>
              </div>
            </div>

            {scanResult.old_project && (
              <div className="p-3 bg-blue-50 border border-blue-200 rounded-xl mb-4 text-sm text-blue-900">
                הכלי משויך כעת לפרויקט: <strong>{scanResult.old_project.project_name || '—'}</strong>
                {scanResult.old_project.wo_number && (
                  <span className="text-xs text-blue-700 block mt-0.5">
                    הזמנה #{scanResult.old_project.wo_number} תועבר לסטטוס "הופסק" ויתרת התקציב תשוחרר.
                  </span>
                )}
              </div>
            )}

            {error && (
              <div className="p-3 bg-red-50 border border-red-200 rounded-xl mb-3 text-sm text-red-700 flex items-center gap-2">
                <AlertCircle className="w-4 h-4 flex-shrink-0" />
                {error}
              </div>
            )}

            <div className="flex gap-2">
              <button
                onClick={onClose}
                className="flex-1 py-2.5 rounded-xl border border-gray-200 text-gray-700 hover:bg-gray-50 text-sm font-medium"
              >
                ביטול
              </button>
              <button
                onClick={handleConfirmDifferentPlate}
                disabled={loading}
                className="flex-1 py-2.5 rounded-xl bg-amber-600 text-white hover:bg-amber-700 disabled:opacity-50 text-sm font-semibold flex items-center justify-center gap-2"
              >
                {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <ArrowRightLeft className="w-4 h-4" />}
                אישור והעברה
              </button>
            </div>
          </div>
        )}

        {/* PHASE: WRONG TYPE — blocked, returned to coordinator */}
        {phase === 'wrong_type' && scanResult && (
          <div className="p-5">
            <div className="flex items-start gap-3 p-4 bg-red-50 border border-red-200 rounded-xl mb-4">
              <AlertTriangle className="w-5 h-5 text-red-600 mt-0.5 flex-shrink-0" />
              <div className="text-sm text-red-900">
                <p className="font-semibold mb-1">סוג הכלי שנסרק שונה מההזמנה</p>
                <p className="leading-snug">
                  הוזמן: <strong>{scanResult.ordered_type}</strong> · נסרק: <strong>{scanResult.scanned_type}</strong>
                </p>
                <p className="text-xs mt-2 leading-snug">
                  ההזמנה הוחזרה אוטומטית לטיפול מתאם הזמנות.
                  לא ניתן להמשיך עבודה / קליטה / דיווח עד להחלטת המתאם.
                </p>
              </div>
            </div>

            <div className="flex gap-2">
              <button
                onClick={onClose}
                className="flex-1 py-2.5 rounded-xl border border-gray-200 text-gray-700 hover:bg-gray-50 text-sm font-medium"
              >
                סגור
              </button>
              {scanResult.admin_can_override && isAdmin && (
                <button
                  onClick={() => { setPhase('admin_override'); setError(null); }}
                  className="flex-1 py-2.5 rounded-xl bg-orange-600 text-white hover:bg-orange-700 text-sm font-semibold flex items-center justify-center gap-2"
                >
                  <ShieldAlert className="w-4 h-4" />
                  אישור חריג (מנהל)
                </button>
              )}
            </div>
          </div>
        )}

        {/* PHASE: ADMIN OVERRIDE */}
        {phase === 'admin_override' && (
          <div className="p-5">
            <div className="flex items-start gap-3 p-4 bg-orange-50 border border-orange-200 rounded-xl mb-4 text-sm text-orange-900">
              <ShieldAlert className="w-5 h-5 text-orange-600 mt-0.5 flex-shrink-0" />
              <div>
                <p className="font-semibold">אישור חריג של מנהל</p>
                <p className="text-xs mt-1">
                  הפעולה תאושר על אף שסוג הכלי לא תואם להזמנה. יש לתעד סיבה מפורטת — תישמר ב-audit log.
                </p>
              </div>
            </div>

            <textarea
              value={overrideReason}
              onChange={e => setOverrideReason(e.target.value)}
              rows={3}
              placeholder="סיבת אישור חריג (חובה — לפחות 5 תווים)"
              className="w-full px-3 py-2.5 border-2 border-gray-200 rounded-xl text-sm focus:border-orange-500 focus:ring-2 focus:ring-orange-200 mb-3"
            />

            {error && (
              <div className="p-3 bg-red-50 border border-red-200 rounded-xl mb-3 text-sm text-red-700 flex items-center gap-2">
                <AlertCircle className="w-4 h-4 flex-shrink-0" />
                {error}
              </div>
            )}

            <div className="flex gap-2">
              <button
                onClick={() => setPhase('wrong_type')}
                className="flex-1 py-2.5 rounded-xl border border-gray-200 text-gray-700 hover:bg-gray-50 text-sm font-medium"
              >
                חזור
              </button>
              <button
                onClick={handleAdminOverride}
                disabled={loading}
                className="flex-1 py-2.5 rounded-xl bg-orange-600 text-white hover:bg-orange-700 disabled:opacity-50 text-sm font-semibold flex items-center justify-center gap-2"
              >
                {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <ShieldAlert className="w-4 h-4" />}
                אשר חריג
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ScanEquipmentModal;
