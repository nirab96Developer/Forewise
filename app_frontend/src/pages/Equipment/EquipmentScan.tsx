
// src/pages/Equipment/EquipmentScan.tsx
// אימות כלי לפי מספר רישוי — primary: plate entry, secondary: QR camera
import React, { useState, useEffect, useRef } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import {
  Search, Truck, User, Building2, CheckCircle, AlertCircle,
  Loader2, X, ArrowLeft, Clock, DollarSign, Camera, Keyboard,
  ShieldCheck, AlertTriangle
} from 'lucide-react';
import api from '../../services/api';
import { saveOfflineScan } from '../../utils/offlineStorage';
import { showToast } from '../../components/common/Toast';

interface EquipmentResult {
  id: number;
  code: string;
  name: string;
  license_plate: string;
  equipment_type: string;
  supplier_id: number;
  supplier_name?: string;
  hourly_rate?: number;
  daily_rate?: number;
  status?: string;
  current_project_name?: string;
}

interface ValidationResult {
  valid: boolean;
  license_plate: string;
  equipment_id: number | null;
  supplier_equipment_id: number | null;
  equipment_name: string;
  supplier_id: number | null;
  supplier_name?: string;
  warnings: string[];
  work_order_id?: number;
  work_order_status?: string;
}

type ScanMode = 'plate' | 'camera';

const EquipmentScan: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const woIdParam = searchParams.get('wo');
  const inputRef = useRef<HTMLInputElement>(null);
  const scannerRef = useRef<HTMLDivElement>(null);
  const html5QrCodeRef = useRef<any>(null);

  const [mode, setMode] = useState<ScanMode>('plate');
  const [searchValue, setSearchValue] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [equipment, setEquipment] = useState<EquipmentResult | null>(null);
  const [validation, setValidation] = useState<ValidationResult | null>(null);
  const [recentScans, setRecentScans] = useState<EquipmentResult[]>([]);
  const [cameraActive, setCameraActive] = useState(false);
  const [scanRegistered, setScanRegistered] = useState(false);

  useEffect(() => {
    const saved = localStorage.getItem('recentEquipmentScans');
    if (saved) {
      try { setRecentScans(JSON.parse(saved).slice(0, 5)); } catch (e) {}
    }
  }, []);

  useEffect(() => {
    if (mode === 'plate') {
      stopCamera();
      inputRef.current?.focus();
    }
    return () => { stopCamera(); };
  }, [mode]);

  const startCamera = async () => {
    if (cameraActive || !scannerRef.current) return;
    try {
      if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
        const testStream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' } });
        testStream.getTracks().forEach(t => t.stop());
      }
      const { Html5Qrcode } = await import('html5-qrcode');
      const scanner = new Html5Qrcode('qr-reader');
      html5QrCodeRef.current = scanner;
      await scanner.start(
        { facingMode: 'environment' },
        { fps: 10, qrbox: { width: 220, height: 220 }, aspectRatio: 1.0, disableFlip: false },
        (text: string) => handleQRResult(text),
        () => {}
      );
      setCameraActive(true);
    } catch (err: any) {
      const msg = err?.message || '';
      if (msg.includes('NotAllowed') || msg.includes('Permission')) {
        setError('אין גישה למצלמה — יש לאשר הרשאה או להשתמש בהזנת מספר רישוי');
      } else if (msg.includes('insecure') || msg.includes('https')) {
        setError('סריקת מצלמה דורשת חיבור HTTPS מאובטח');
      } else {
        setError('שגיאה בהפעלת המצלמה — השתמש בהזנת מספר רישוי');
      }
    }
  };

  const stopCamera = async () => {
    if (html5QrCodeRef.current) {
      try {
        await html5QrCodeRef.current.stop();
        html5QrCodeRef.current.clear();
      } catch (e) {}
      html5QrCodeRef.current = null;
    }
    setCameraActive(false);
  };

  useEffect(() => {
    if (mode === 'camera' && !equipment) {
      const timer = setTimeout(() => startCamera(), 300);
      return () => clearTimeout(timer);
    }
  }, [mode, equipment]);

  const handleQRResult = async (value: string) => {
    await stopCamera();
    const cleaned = value.replace(/[^0-9a-zA-Zא-ת\-]/g, '').trim();
    if (cleaned) {
      setSearchValue(cleaned);
      await validatePlate(cleaned);
    }
  };

  const validatePlate = async (plateValue?: string) => {
    const plate = (plateValue || searchValue).trim();
    if (!plate) {
      setError('יש להזין מספר רישוי');
      return;
    }
    setLoading(true);
    setError(null);
    setEquipment(null);
    setValidation(null);
    setScanRegistered(false);

    try {
      const payload: any = { license_plate: plate };
      if (woIdParam) payload.work_order_id = parseInt(woIdParam);

      const res = await api.post('/equipment/validate-plate', payload);
      const v: ValidationResult = res.data;
      setValidation(v);

      if (v.equipment_id) {
        try {
          const eqRes = await api.get(`/equipment/${v.equipment_id}`);
          setEquipment(eqRes.data);
          saveRecentScan(eqRes.data);
        } catch {
          setEquipment({
            id: v.equipment_id || 0,
            code: '',
            name: v.equipment_name,
            license_plate: plate,
            equipment_type: '',
            supplier_id: v.supplier_id || 0,
            supplier_name: v.supplier_name,
          });
        }
        if (v.valid) {
          registerScan(v.equipment_id, plate);
        }
      }
    } catch (err: any) {
      if (err.response?.status === 404) {
        try {
          const fallbackRes = await api.get(`/equipment/by-code/${encodeURIComponent(plate)}`);
          if (fallbackRes.data) {
            setEquipment(fallbackRes.data);
            saveRecentScan(fallbackRes.data);
            setValidation({ valid: true, license_plate: plate, equipment_id: fallbackRes.data.id,
              supplier_equipment_id: null, equipment_name: fallbackRes.data.name,
              supplier_id: fallbackRes.data.supplier_id, warnings: [] });
            registerScan(fallbackRes.data.id, plate);
          }
        } catch {
          setError(`לא נמצא כלי עם מספר רישוי: ${plate}`);
        }
      } else {
        setError(err.response?.data?.detail || 'שגיאה באימות. נסה שוב.');
      }
    } finally {
      setLoading(false);
    }
  };

  const registerScan = async (equipmentId: number, _scanValue?: string) => {
    if (!navigator.onLine) {
      await saveOfflineScan({ equipment_id: equipmentId, scan_type: 'plate_validation' });
showToast(' האימות נשמר — יסונכרן כשיחזור חיבור', 'info', 5000);
      setScanRegistered(true);
      return;
    }
    try {
      await api.post(`/equipment/${equipmentId}/scan`, null, {
        params: { scan_type: 'plate_validation' }
      });
      setScanRegistered(true);
    } catch (e: any) {
      if (!e.response) {
        await saveOfflineScan({ equipment_id: equipmentId, scan_type: 'plate_validation' });
showToast(' האימות נשמר — יסונכרן כשיחזור חיבור', 'info', 5000);
        setScanRegistered(true);
      }
    }
  };

  const saveRecentScan = (eq: EquipmentResult) => {
    const updated = [eq, ...recentScans.filter(r => r.id !== eq.id)].slice(0, 5);
    setRecentScans(updated);
    localStorage.setItem('recentEquipmentScans', JSON.stringify(updated));
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') validatePlate();
  };

  const [activeWorkOrderId, setActiveWorkOrderId] = useState<number | null>(null);

  useEffect(() => {
    if (woIdParam) setActiveWorkOrderId(parseInt(woIdParam));
  }, [woIdParam]);

  const handleContinueToReport = () => {
    if (!equipment) return;
    const woId = validation?.work_order_id || activeWorkOrderId;
    if (woId) {
      navigate(`/work-orders/${woId}/report-hours?equipment_id=${equipment.id}`);
    } else {
      navigate(`/projects?equipment_id=${equipment.id}`);
    }
  };

  const handleClear = () => {
    setSearchValue('');
    setEquipment(null);
    setValidation(null);
    setError(null);
    setScanRegistered(false);
    if (mode === 'camera') startCamera();
    else inputRef.current?.focus();
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 to-blue-50" dir="rtl">
      {/* Header */}
      <div className="bg-white shadow-sm sticky top-0 z-10">
        <div className="max-w-lg mx-auto px-4 py-3 flex items-center justify-between">
          <button onClick={() => navigate(-1)} className="p-2 hover:bg-gray-100 rounded-lg min-h-[44px] min-w-[44px] flex items-center justify-center">
            <ArrowLeft className="w-5 h-5 text-gray-600" />
          </button>
          <h1 className="text-lg font-bold text-gray-900">אימות כלי לפי מספר רישוי</h1>
          <div className="w-11" />
        </div>
      </div>

      <div className="max-w-lg mx-auto px-4 py-6">
        {/* Mode Toggle — plate first */}
        {!equipment && (
          <div className="flex gap-2 mb-4">
            <button
              onClick={() => setMode('plate')}
              className={`flex-1 py-3 rounded-xl font-medium text-sm flex items-center justify-center gap-2 transition-colors min-h-[48px] ${
                mode === 'plate'
                  ? 'bg-green-600 text-white shadow-sm'
                  : 'bg-white text-gray-600 border border-gray-200'
              }`}
            >
              <Keyboard className="w-4 h-4" />
              מספר רישוי
            </button>
            <button
              onClick={() => setMode('camera')}
              className={`flex-1 py-3 rounded-xl font-medium text-sm flex items-center justify-center gap-2 transition-colors min-h-[48px] ${
                mode === 'camera'
                  ? 'bg-green-600 text-white shadow-sm'
                  : 'bg-white text-gray-600 border border-gray-200'
              }`}
            >
              <Camera className="w-4 h-4" />
              סריקת QR
            </button>
          </div>
        )}

        {/* Primary: License Plate Input */}
        {mode === 'plate' && !equipment && (
          <div className="bg-white rounded-2xl shadow-lg p-6 mb-6">
            <div className="text-center mb-6">
              <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-3">
                <ShieldCheck className="w-8 h-8 text-green-600" />
              </div>
              <h2 className="text-xl font-bold text-gray-900">אימות כלי</h2>
              <p className="text-gray-500 text-sm mt-1">הזן את מספר הרישוי של הכלי לאימות</p>
            </div>

            <div className="relative mb-4">
              <input
                ref={inputRef}
                type="text"
                value={searchValue}
                onChange={(e) => setSearchValue(e.target.value.toUpperCase())}
                onKeyPress={handleKeyPress}
                placeholder="לדוגמה: 12-345-67"
                className="w-full text-center text-2xl font-bold py-4 px-4 border-2 border-gray-200 rounded-xl
                           focus:border-green-500 focus:ring-2 focus:ring-green-200 placeholder:text-gray-300 placeholder:font-normal placeholder:text-lg"
                autoComplete="off"
                inputMode="numeric"
                style={{ fontSize: '16px' }}
              />
              {searchValue && (
                <button onClick={() => { setSearchValue(''); setError(null); }} className="absolute left-3 top-1/2 -translate-y-1/2 p-2 text-gray-400 hover:text-gray-600 min-h-[44px] min-w-[44px] flex items-center justify-center">
                  <X className="w-5 h-5" />
                </button>
              )}
            </div>

            <button
              onClick={() => validatePlate()}
              disabled={loading || !searchValue.trim()}
              className="w-full py-4 bg-green-600 text-white rounded-xl font-bold text-lg hover:bg-green-700 disabled:opacity-50 flex items-center justify-center gap-2 min-h-[52px]"
            >
              {loading ? <><Loader2 className="w-5 h-5 animate-spin" />מאמת...</> : <><ShieldCheck className="w-5 h-5" />אמת כלי</>}
            </button>
          </div>
        )}

        {/* Secondary: QR Camera Scanner */}
        {mode === 'camera' && !equipment && (
          <div className="bg-white rounded-2xl shadow-lg p-6 mb-6">
            <div className="text-center mb-4">
              <h2 className="text-xl font-bold text-gray-900">סריקת QR (אופציונלי)</h2>
              <p className="text-gray-500 text-sm mt-1">כוון את המצלמה אל קוד ה-QR שעל הציוד</p>
            </div>

            <div className="relative rounded-xl overflow-hidden bg-black" style={{ minHeight: 300 }}>
              <div id="qr-reader" ref={scannerRef} className="w-full" />
              {!cameraActive && !error && (
                <div className="absolute inset-0 flex items-center justify-center bg-gray-900">
                  <div className="text-center">
                    <Loader2 className="w-8 h-8 animate-spin text-green-400 mx-auto mb-2" />
                    <p className="text-gray-300 text-sm">מפעיל מצלמה...</p>
                  </div>
                </div>
              )}
            </div>

            {loading && (
              <div className="mt-4 flex items-center justify-center gap-2 text-green-600">
                <Loader2 className="w-5 h-5 animate-spin" />
                <span>מאמת כלי...</span>
              </div>
            )}
          </div>
        )}

        {/* Error */}
        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-xl flex items-center gap-3">
            <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0" />
            <span className="text-red-700 text-sm">{error}</span>
          </div>
        )}

        {/* Validation Warnings */}
        {validation && !validation.valid && validation.warnings.length > 0 && (
          <div className="mb-6 p-4 bg-amber-50 border border-amber-200 rounded-xl">
            <div className="flex items-center gap-2 mb-2">
              <AlertTriangle className="w-5 h-5 text-amber-600" />
              <span className="font-bold text-amber-800">אימות נכשל</span>
            </div>
            <ul className="space-y-1">
              {validation.warnings.map((w, i) => (
                <li key={i} className="text-amber-700 text-sm flex items-start gap-2">
                  <span className="mt-1">•</span>
                  <span>{w}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Equipment Result */}
        {equipment && (
          <div className="bg-white rounded-2xl shadow-lg overflow-hidden mb-6">
            <div className={`${validation?.valid ? 'bg-green-600' : 'bg-amber-500'} text-white p-4 flex items-center justify-between`}>
              <div className="flex items-center gap-3">
                {validation?.valid ? <CheckCircle className="w-6 h-6" /> : <AlertTriangle className="w-6 h-6" />}
                <span className="font-bold">{validation?.valid ? 'כלי אומת בהצלחה!' : 'כלי נמצא — אימות חלקי'}</span>
              </div>
              {scanRegistered && (
                <span className="bg-white/20 px-2 py-1 rounded text-xs">אימות נרשם</span>
              )}
            </div>

            <div className="p-5">
              <div className="text-center mb-4">
                <div className="text-2xl font-bold text-gray-900 mb-1">{equipment.name || equipment.equipment_type}</div>
                <div className="text-lg text-green-600 font-medium">{equipment.license_plate || equipment.code}</div>
                {equipment.status && (
                  <span className={`inline-block mt-2 px-3 py-1 rounded-full text-xs font-medium ${
                    equipment.status === 'in_use' || equipment.status === 'active' || equipment.status === 'פעיל'
                      ? 'bg-green-100 text-green-800'
                      : equipment.status === 'maintenance' || equipment.status === 'תחזוקה'
                      ? 'bg-yellow-100 text-yellow-800'
                      : 'bg-gray-100 text-gray-800'
                  }`}>
                    {equipment.status}
                  </span>
                )}
              </div>

              <div className="space-y-3 border-t border-gray-100 pt-4">
                <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
                  <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                    <User className="w-5 h-5 text-blue-600" />
                  </div>
                  <div>
                    <div className="text-xs text-gray-500">ספק</div>
                    <div className="font-medium text-gray-900">{equipment.supplier_name || validation?.supplier_name || `ספק #${equipment.supplier_id}`}</div>
                  </div>
                </div>

                <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
                  <div className="w-10 h-10 bg-orange-100 rounded-lg flex items-center justify-center">
                    <Truck className="w-5 h-5 text-orange-600" />
                  </div>
                  <div>
                    <div className="text-xs text-gray-500">סוג כלי</div>
                    <div className="font-medium text-gray-900">{equipment.equipment_type || equipment.name || 'לא צוין'}</div>
                  </div>
                </div>

                {equipment.hourly_rate != null && equipment.hourly_rate > 0 && (
                  <div className="flex items-center gap-3 p-3 bg-green-50 rounded-lg border border-green-200">
                    <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center">
                      <DollarSign className="w-5 h-5 text-green-600" />
                    </div>
                    <div className="flex-1">
                      <div className="text-xs text-green-700">תעריף שעתי</div>
<div className="font-bold text-green-800 text-lg">{equipment.hourly_rate.toLocaleString()}</div>
                    </div>
                    {equipment.daily_rate != null && equipment.daily_rate > 0 && (
                      <div className="text-left">
                        <div className="text-xs text-gray-500">יומי</div>
<div className="font-medium text-gray-700">{equipment.daily_rate.toLocaleString()}</div>
                      </div>
                    )}
                  </div>
                )}

                {equipment.current_project_name && (
                  <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
                    <div className="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center">
                      <Building2 className="w-5 h-5 text-purple-600" />
                    </div>
                    <div>
                      <div className="text-xs text-gray-500">פרויקט נוכחי</div>
                      <div className="font-medium text-gray-900">{equipment.current_project_name}</div>
                    </div>
                  </div>
                )}
              </div>

              <div className="space-y-3 mt-5">
                {validation?.valid && (
                  <button
                    onClick={handleContinueToReport}
                    className="w-full py-4 bg-blue-600 text-white rounded-xl font-bold text-lg hover:bg-blue-700 flex items-center justify-center gap-2 min-h-[52px]"
                  >
                    <Clock className="w-5 h-5" />
                    המשך לדיווח שעות
                  </button>
                )}
                <button
                  onClick={handleClear}
                  className="w-full py-3 bg-gray-100 text-gray-700 rounded-xl font-medium hover:bg-gray-200 flex items-center justify-center gap-2 min-h-[48px]"
                >
                  <Search className="w-4 h-4" />
                  אמת כלי נוסף
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Recent validations */}
        {!equipment && recentScans.length > 0 && (
          <div className="bg-white rounded-2xl shadow-lg p-5">
            <h3 className="font-bold text-gray-900 mb-3 flex items-center gap-2">
              <Clock className="w-4 h-4 text-gray-400" />
              אימותים אחרונים
            </h3>
            <div className="space-y-2">
              {recentScans.map((eq) => (
                <button
                  key={eq.id}
                  onClick={() => { stopCamera(); setSearchValue(eq.license_plate || eq.code); validatePlate(eq.license_plate || eq.code); }}
                  className="w-full p-3 bg-gray-50 hover:bg-green-50 rounded-lg text-right flex items-center justify-between group min-h-[48px]"
                >
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-gray-200 group-hover:bg-green-100 rounded-lg flex items-center justify-center">
                      <Truck className="w-5 h-5 text-gray-500 group-hover:text-green-600" />
                    </div>
                    <div>
                      <div className="font-medium text-gray-900">{eq.name || eq.equipment_type}</div>
                      <div className="text-sm text-gray-500">{eq.license_plate || eq.code}</div>
                    </div>
                  </div>
                  <ArrowLeft className="w-4 h-4 text-gray-400 group-hover:text-green-600" />
                </button>
              ))}
            </div>
          </div>
        )}

        {!equipment && !error && mode === 'plate' && (
          <div className="mt-6 text-center text-gray-500 text-sm">
            <p>הזן את מספר הרישוי של הכלי כדי לאמת אותו מול הזמנת העבודה</p>
            <p className="mt-1">לאחר האימות תוכל להמשיך לדיווח שעות</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default EquipmentScan;
