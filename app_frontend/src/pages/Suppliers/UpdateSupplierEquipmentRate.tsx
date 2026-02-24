// @ts-nocheck
import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { ArrowRight, AlertCircle, DollarSign, Package } from 'lucide-react';
import api from '../../services/api';

interface SupplierEquipment {
  id: number;
  supplier_id: number;
  equipment_category_id: number;
  equipment_category_name: string;
  quantity_available: number;
  hourly_rate: number | null;
  daily_rate: number | null;
}

const UpdateSupplierEquipmentRate: React.FC = () => {
  const { equipmentId } = useParams<{ equipmentId: string }>();
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    hourly_rate: '',
    daily_rate: '',
  });
  const [equipment, setEquipment] = useState<SupplierEquipment | null>(null);
  const [loading, setLoading] = useState(false);
  const [loadingData, setLoadingData] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (equipmentId) {
      loadEquipment();
    }
  }, [equipmentId]);

  const loadEquipment = async () => {
    try {
      setLoadingData(true);
      const response = await api.get(`/suppliers/equipment/${equipmentId}`);
      const eq = response.data;
      setEquipment(eq);
      setFormData({
        hourly_rate: eq.hourly_rate?.toString() || '',
        daily_rate: eq.daily_rate?.toString() || '',
      });
    } catch (err: any) {
      setError('שגיאה בטעינת נתוני הציוד');
      console.error(err);
    } finally {
      setLoadingData(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    setLoading(true);
    setError(null);

    try {
      await api.put(`/suppliers/equipment/${equipmentId}`, {
        hourly_rate: formData.hourly_rate ? Number(formData.hourly_rate) : null,
        daily_rate: formData.daily_rate ? Number(formData.daily_rate) : null,
      });
      alert('תעריף עודכן בהצלחה!');
      navigate(`/suppliers/${equipment?.supplier_id}`);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'שגיאה בעדכון תעריף');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-2xl mx-auto">
        <div className="bg-white rounded-xl shadow-lg p-8">
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-gray-900 mb-2">שינוי תעריף</h1>
            <p className="text-gray-600">
              {equipment ? `עדכון תעריף עבור: ${equipment.equipment_category_name}` : 'טוען...'}
            </p>
          </div>

          {error && (
            <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-center gap-2">
              <AlertCircle className="w-5 h-5 text-red-600" />
              <span className="text-red-800">{error}</span>
            </div>
          )}

          {loadingData ? (
            <div className="text-center py-8">טוען...</div>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-6">
              <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                <div className="flex items-center gap-2 mb-2">
                  <Package className="w-5 h-5 text-gray-600" />
                  <span className="font-medium text-gray-900">קטגוריית ציוד:</span>
                </div>
                <p className="text-gray-700">{equipment?.equipment_category_name}</p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    <DollarSign className="inline w-4 h-4 ml-1" />
                    תעריף שעתי (ש"ח) *
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    value={formData.hourly_rate}
                    onChange={(e) => setFormData({ ...formData, hourly_rate: e.target.value })}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-kkl-green focus:border-transparent"
                    placeholder="0.00"
                    required
                  />
                  <p className="mt-1 text-xs text-gray-500">תעריף לשעת עבודה</p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    <DollarSign className="inline w-4 h-4 ml-1" />
                    תעריף יומי (ש"ח) *
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    value={formData.daily_rate}
                    onChange={(e) => setFormData({ ...formData, daily_rate: e.target.value })}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-kkl-green focus:border-transparent"
                    placeholder="0.00"
                    required
                  />
                  <p className="mt-1 text-xs text-gray-500">תעריף ליום עבודה (9 שעות)</p>
                </div>
              </div>

              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                <p className="text-sm text-yellow-800">
                  <strong>שימו לב:</strong> שינוי התעריף ישפיע על כל ההזמנות החדשות. הזמנות קיימות ישמרו את התעריף המקורי שלהן.
                </p>
              </div>

              <div className="flex gap-4">
                <button
                  type="button"
                  onClick={() => navigate(`/suppliers/${equipment?.supplier_id}`)}
                  className="flex-1 px-6 py-3 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors"
                >
                  ביטול
                </button>
                <button
                  type="submit"
                  disabled={loading}
                  className="flex-1 px-6 py-3 bg-kkl-green text-white rounded-lg hover:bg-green-700 transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                >
                  {loading ? 'שומר...' : 'שמור תעריף'}
                  <ArrowRight className="w-5 h-5" />
                </button>
              </div>
            </form>
          )}
        </div>
      </div>
    </div>
  );
};

export default UpdateSupplierEquipmentRate;








