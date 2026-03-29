// src/components/equipment/ScanEquipmentModal.tsx
import React, { useState, useEffect, useRef } from 'react';
import {
  Camera, Keyboard, Search, X, Loader2,
  AlertCircle, ScanLine
} from 'lucide-react';
import api from '../../services/api';
import { showToast } from '../common/Toast';

interface ScanEquipmentModalProps {
  isOpen: boolean;
  onClose: () => void;
  workOrderId: number;
  onSuccess: (equipmentId: number, licensePlate: string, name: string) => void;
}

type ScanMode = 'camera' | 'manual';

const ScanEquipmentModal: React.FC<ScanEquipmentModalProps> = ({
  isOpen, onClose, workOrderId, onSuccess
}) => {
  const [mode, setMode] = useState<ScanMode>('camera');
  const [manualInput, setManualInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [cameraActive, setCameraActive] = useState(false);
  const scannerRef = useRef<HTMLDivElement>(null);
  const html5QrCodeRef = useRef<any>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (!isOpen) {
      stopCamera();
      setManualInput('');
      setError(null);
      setMode('camera');
      return;
    }
    if (mode === 'camera') {
      const timer = setTimeout(() => startCamera(), 400);
      return () => clearTimeout(timer);
    }
    if (mode === 'manual') {
      stopCamera();
      setTimeout(() => inputRef.current?.focus(), 100);
    }
  }, [isOpen, mode]);

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
    let identifier = value;
    const idMatch = value.match(/equipment[_\/]?id[=\/:]?\s*(\d+)/i);
    if (idMatch) identifier = idMatch[1];
    await submitScan(identifier);
  };

  const handleManualSubmit = async () => {
    if (!manualInput.trim()) return;
    await submitScan(manualInput.trim());
  };

  const submitScan = async (identifier: string) => {
    setLoading(true);
    setError(null);
    try {
      const response = await api.get(`/equipment/by-code/${encodeURIComponent(identifier)}`);
      const eq = response.data;
      if (!eq) throw new Error('not found');
      try {
        await api.post(`/equipment/${eq.id}/scan`, null, { params: { scan_type: 'work_order_attach' } });
      } catch {}
      onSuccess(eq.id, eq.license_plate || identifier, eq.name || eq.equipment_type || '');
      showToast(`ציוד נסרק: ${eq.license_plate || eq.name}`, 'success');
      onClose();
    } catch (err: any) {
      if (err.response?.status === 404) {
        setError(`לא נמצא ציוד עם מזהה: ${identifier}`);
      } else {
        setError(err.response?.data?.detail || 'שגיאה בחיפוש ציוד');
      }
      if (mode === 'camera') setTimeout(() => startCamera(), 1500);
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
            <h2 className="text-lg font-bold text-gray-900">סריקת ציוד</h2>
          </div>
          <button onClick={onClose} className="p-1.5 hover:bg-gray-200 rounded-lg text-gray-400 hover:text-gray-600">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Tabs */}
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

        {/* Body */}
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
              <p className="text-sm text-gray-500 text-center mb-4">הקלד מספר רישוי או קוד ציוד</p>
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
              <span className="text-sm font-medium">מחפש ציוד...</span>
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
          <p className="text-xs text-gray-400">{`הציוד ישויך להזמנה #${workOrderId} אוטומטית`}</p>
        </div>
      </div>
    </div>
  );
};

export default ScanEquipmentModal;
