import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { ChevronRight, DollarSign, Truck, Clock, Package, Info } from 'lucide-react';
import api from '../../services/api';

interface SystemRate {
  id: number;
  rate_code: string;
  rate_name: string;
  rate_value: number;
  currency: string;
  description?: string;
}

interface EquipmentType {
  id: number;
  name: string;
  hourly_rate: number;
  default_hourly_rate?: number;
  overnight_rate?: number;
  night_guard?: number;
}

const PriceList: React.FC = () => {
  const navigate = useNavigate();
  const [systemRates, setSystemRates] = useState<SystemRate[]>([]);
  const [equipmentTypes, setEquipmentTypes] = useState<EquipmentType[]>([]);
  const [loading, setLoading] = useState(true);
  const vatRate = 18;

  useEffect(() => { loadData(); }, []);

  const loadData = async () => {
    try {
      const [ratesRes, typesRes] = await Promise.allSettled([
        api.get('/system-rates'),
        api.get('/equipment-categories'),
      ]);
      if (ratesRes.status === 'fulfilled') {
        const d = ratesRes.value.data;
        setSystemRates(Array.isArray(d) ? d : d.items || d.results || []);
      }
      if (typesRes.status === 'fulfilled') {
        const d = typesRes.value.data;
        setEquipmentTypes(Array.isArray(d) ? d : d.items || d.results || []);
      }
    } catch { /* silent */ } finally { setLoading(false); }
  };

  const fmt = (val: number) =>
    new Intl.NumberFormat('he-IL', { style: 'currency', currency: 'ILS', maximumFractionDigits: 0 }).format(val);

  const rateIcon = (code: string) => {
    if (/TRACTOR|EXCAVATOR|BULLDOZER/.test(code)) return <Truck className="w-5 h-5" />;
    if (/WORKER|SUPERVISOR/.test(code)) return <Clock className="w-5 h-5" />;
    if (/TRANSPORT/.test(code)) return <Package className="w-5 h-5" />;
    return <DollarSign className="w-5 h-5" />;
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-kkl-bg flex items-center justify-center">
        <div className="animate-spin w-8 h-8 border-4 border-kkl-green border-t-transparent rounded-full" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-kkl-bg" dir="rtl">
      <div className="max-w-5xl mx-auto px-4 py-6">
        <div className="flex items-center gap-3 mb-6">
          <button onClick={() => navigate('/settings')} className="text-gray-400 hover:text-kkl-green">
            <ChevronRight className="w-6 h-6" />
          </button>
          <div className="w-12 h-12 bg-amber-500 rounded-xl flex items-center justify-center">
            <DollarSign className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-kkl-text">מחירון מערכת</h1>
            <p className="text-gray-500">תעריפי עבודה, ציוד ושירותים</p>
          </div>
        </div>

        <div className="bg-blue-50 border border-blue-200 rounded-xl p-4 mb-6 flex items-start gap-3">
          <Info className="w-5 h-5 text-blue-500 mt-0.5 shrink-0" />
          <div className="text-sm text-blue-700">
            <strong>מחירון מאושר</strong> — התעריפים נקבעו ע״י הנהלת Forewise ומשמשים כבסיס לחישוב עלויות הזמנות עבודה ודיווחי שעות. מע״מ {vatRate}% מתווסף אוטומטית.
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-kkl-border overflow-hidden mb-6">
          <div className="px-5 py-4 border-b border-kkl-border bg-gradient-to-l from-amber-50 to-white">
            <h2 className="text-lg font-semibold text-kkl-text">תעריפי מערכת</h2>
            <p className="text-sm text-gray-500">תעריפים כלליים לסוגי עבודה ושירותים</p>
          </div>
          <div className="divide-y divide-gray-100">
            {systemRates.map((rate) => (
              <div key={rate.id} className="px-5 py-4 flex items-center justify-between hover:bg-gray-50">
                <div className="flex items-center gap-4">
                  <div className="w-10 h-10 bg-amber-100 rounded-lg flex items-center justify-center text-amber-600">
                    {rateIcon(rate.rate_code)}
                  </div>
                  <div>
                    <div className="font-medium text-kkl-text">{rate.rate_name}</div>
                    {rate.description && <div className="text-xs text-gray-400">{rate.description}</div>}
                  </div>
                </div>
                <div className="text-left">
                  <div className="text-lg font-bold text-kkl-green">{fmt(rate.rate_value)}</div>
                  <div className="text-xs text-gray-400">
                    {rate.rate_code.includes('DAY') ? 'ליום' : rate.rate_code.includes('FEE') ? 'קבוע' : 'לשעה'}
                  </div>
                </div>
              </div>
            ))}
            {systemRates.length === 0 && (
              <div className="px-5 py-8 text-center text-gray-400">לא הוגדרו תעריפי מערכת</div>
            )}
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-kkl-border overflow-hidden mb-6">
          <div className="px-5 py-4 border-b border-kkl-border bg-gradient-to-l from-green-50 to-white">
            <h2 className="text-lg font-semibold text-kkl-text">תעריפי ציוד לפי סוג</h2>
            <p className="text-sm text-gray-500">תעריף שעתי ולינת ציוד לכל סוג כלי</p>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 text-gray-600">
                <tr>
                  <th className="px-5 py-3 text-right font-medium">סוג ציוד</th>
                  <th className="px-5 py-3 text-center font-medium">תעריף שעתי</th>
                  <th className="px-5 py-3 text-center font-medium">לינת ציוד</th>
                  <th className="px-5 py-3 text-center font-medium">כולל מע״מ (שעתי)</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {equipmentTypes.map((et) => {
                  const rate = et.hourly_rate || et.default_hourly_rate || 0;
                  const withVat = Math.round(rate * (1 + vatRate / 100));
                  return (
                    <tr key={et.id} className="hover:bg-gray-50">
                      <td className="px-5 py-3">
                        <div className="flex items-center gap-3">
                          <div className="w-8 h-8 bg-green-100 rounded-lg flex items-center justify-center text-green-600">
                            <Truck className="w-4 h-4" />
                          </div>
                          <span className="font-medium text-kkl-text">{et.name}</span>
                        </div>
                      </td>
                      <td className="px-5 py-3 text-center font-semibold text-kkl-green">{fmt(rate)}</td>
                      <td className="px-5 py-3 text-center text-gray-600">
                        {et.overnight_rate ? fmt(et.overnight_rate) : '—'}
                      </td>
                      <td className="px-5 py-3 text-center font-semibold text-gray-700">{fmt(withVat)}</td>
                    </tr>
                  );
                })}
                {equipmentTypes.length === 0 && (
                  <tr><td colSpan={4} className="px-5 py-8 text-center text-gray-400">לא הוגדרו סוגי ציוד</td></tr>
                )}
              </tbody>
            </table>
          </div>
        </div>

        <div className="bg-gray-50 rounded-xl border border-gray-200 p-4 text-sm text-gray-500 text-center">
          כל המחירים לפני מע״מ אלא אם צוין אחרת · מע״מ {vatRate}% · עדכון אחרון: מרץ 2026
        </div>
      </div>
    </div>
  );
};

export default PriceList;
