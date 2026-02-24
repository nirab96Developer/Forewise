// @ts-nocheck
// src/pages/Equipment/EquipmentScan.tsx
// דף סריקת ציוד - חיפוש לפי מספר רישוי ומעבר לדיווח
import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Search, Truck, User, Building2, CheckCircle, AlertCircle, 
  Loader2, X, ArrowLeft, Clock, DollarSign
} from 'lucide-react';
import api from '../../services/api';

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

const EquipmentScan: React.FC = () => {
  const navigate = useNavigate();
  const inputRef = useRef<HTMLInputElement>(null);
  
  const [searchValue, setSearchValue] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [equipment, setEquipment] = useState<EquipmentResult | null>(null);
  const [recentScans, setRecentScans] = useState<EquipmentResult[]>([]);

  useEffect(() => {
    inputRef.current?.focus();
    const saved = localStorage.getItem('recentEquipmentScans');
    if (saved) {
      try { setRecentScans(JSON.parse(saved).slice(0, 5)); } catch (e) {}
    }
  }, []);

  const saveRecentScan = (eq: EquipmentResult) => {
    const updated = [eq, ...recentScans.filter(r => r.id !== eq.id)].slice(0, 5);
    setRecentScans(updated);
    localStorage.setItem('recentEquipmentScans', JSON.stringify(updated));
  };

  const handleSearch = async () => {
    if (!searchValue.trim()) {
      setError('יש להזין מספר רישוי');
      return;
    }
    setLoading(true);
    setError(null);
    setEquipment(null);

    try {
      const response = await api.get(`/equipment/by-code/${encodeURIComponent(searchValue.trim())}`);
      if (response.data) {
        setEquipment(response.data);
        saveRecentScan(response.data);
        try {
          await api.post(`/equipment/${response.data.id}/scan`, null, { params: { scan_type: 'field_check' } });
        } catch (e) {}
      }
    } catch (err: any) {
      if (err.response?.status === 404) {
        setError(`לא נמצא ציוד עם מספר רישוי: ${searchValue}`);
      } else {
        setError('שגיאה בחיפוש. אנא נסה שוב.');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') handleSearch();
  };

  const handleContinueToReport = () => {
    if (equipment) navigate(`/work-logs/new?equipment_id=${equipment.id}`);
  };

  const handleClear = () => {
    setSearchValue('');
    setEquipment(null);
    setError(null);
    inputRef.current?.focus();
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 to-blue-50" dir="rtl">
      {/* Header */}
      <div className="bg-white shadow-sm sticky top-0 z-10">
        <div className="max-w-lg mx-auto px-4 py-3 flex items-center justify-between">
          <button onClick={() => navigate(-1)} className="p-2 hover:bg-gray-100 rounded-lg">
            <ArrowLeft className="w-5 h-5 text-gray-600" />
          </button>
          <h1 className="text-lg font-bold text-gray-900">סריקת ציוד</h1>
          <div className="w-9" />
        </div>
      </div>

      <div className="max-w-lg mx-auto px-4 py-6">
        {/* Search Box */}
        <div className="bg-white rounded-2xl shadow-lg p-6 mb-6">
          <div className="text-center mb-6">
            <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-3">
              <Truck className="w-8 h-8 text-green-600" />
            </div>
            <h2 className="text-xl font-bold text-gray-900">הזן מספר רישוי</h2>
            <p className="text-gray-500 text-sm mt-1">הקלד את מספר הרישוי של הכלי</p>
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
              inputMode="text"
            />
            {searchValue && (
              <button onClick={handleClear} className="absolute left-3 top-1/2 -translate-y-1/2 p-1 text-gray-400 hover:text-gray-600">
                <X className="w-5 h-5" />
              </button>
            )}
          </div>

          <button
            onClick={handleSearch}
            disabled={loading || !searchValue.trim()}
            className="w-full py-4 bg-green-600 text-white rounded-xl font-bold text-lg hover:bg-green-700 disabled:opacity-50 flex items-center justify-center gap-2"
          >
            {loading ? <><Loader2 className="w-5 h-5 animate-spin" />מחפש...</> : <><Search className="w-5 h-5" />חפש ציוד</>}
          </button>

          {error && (
            <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-xl flex items-center gap-3">
              <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0" />
              <span className="text-red-700 text-sm">{error}</span>
            </div>
          )}
        </div>

        {/* Equipment Result */}
        {equipment && (
          <div className="bg-white rounded-2xl shadow-lg overflow-hidden mb-6">
            <div className="bg-green-600 text-white p-4 flex items-center gap-3">
              <CheckCircle className="w-6 h-6" />
              <span className="font-bold">ציוד נמצא!</span>
            </div>

            <div className="p-5">
              <div className="text-center mb-4">
                <div className="text-2xl font-bold text-gray-900 mb-1">{equipment.name || equipment.equipment_type}</div>
                <div className="text-lg text-green-600 font-medium">{equipment.license_plate || equipment.code}</div>
              </div>

              <div className="space-y-3 border-t border-gray-100 pt-4">
                <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
                  <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                    <User className="w-5 h-5 text-blue-600" />
                  </div>
                  <div>
                    <div className="text-xs text-gray-500">ספק</div>
                    <div className="font-medium text-gray-900">{equipment.supplier_name || `ספק #${equipment.supplier_id}`}</div>
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

                {/* מחיר שעתי */}
                {equipment.hourly_rate && (
                  <div className="flex items-center gap-3 p-3 bg-green-50 rounded-lg border border-green-200">
                    <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center">
                      <DollarSign className="w-5 h-5 text-green-600" />
                    </div>
                    <div className="flex-1">
                      <div className="text-xs text-green-700">תעריף שעתי</div>
                      <div className="font-bold text-green-800 text-lg">₪{equipment.hourly_rate.toLocaleString()}</div>
                    </div>
                    {equipment.daily_rate && (
                      <div className="text-left">
                        <div className="text-xs text-gray-500">יומי</div>
                        <div className="font-medium text-gray-700">₪{equipment.daily_rate.toLocaleString()}</div>
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

              <button
                onClick={handleContinueToReport}
                className="w-full mt-5 py-4 bg-blue-600 text-white rounded-xl font-bold text-lg hover:bg-blue-700 flex items-center justify-center gap-2"
              >
                <Clock className="w-5 h-5" />
                המשך לדיווח שעות
              </button>
            </div>
          </div>
        )}

        {/* Recent Scans */}
        {!equipment && recentScans.length > 0 && (
          <div className="bg-white rounded-2xl shadow-lg p-5">
            <h3 className="font-bold text-gray-900 mb-3 flex items-center gap-2">
              <Clock className="w-4 h-4 text-gray-400" />
              סריקות אחרונות
            </h3>
            <div className="space-y-2">
              {recentScans.map((eq) => (
                <button
                  key={eq.id}
                  onClick={() => { setSearchValue(eq.license_plate || eq.code); setEquipment(eq); }}
                  className="w-full p-3 bg-gray-50 hover:bg-green-50 rounded-lg text-right flex items-center justify-between group"
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

        {!equipment && !error && (
          <div className="mt-6 text-center text-gray-500 text-sm">
            <p>הזן את מספר הרישוי של הכלי כדי לזהות אותו</p>
            <p className="mt-1">לאחר הזיהוי תוכל להמשיך לדיווח שעות</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default EquipmentScan;
