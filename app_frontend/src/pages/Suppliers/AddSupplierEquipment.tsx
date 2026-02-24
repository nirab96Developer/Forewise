// @ts-nocheck
import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { ArrowRight, AlertCircle, Package, DollarSign } from 'lucide-react';
import api from '../../services/api';
import supplierService from '../../services/supplierService';

interface EquipmentCategory {
  id: number;
  name: string;
  code: string;
}

interface Supplier {
  id: number;
  name: string;
}

const AddSupplierEquipment: React.FC = () => {
  const { supplierId } = useParams<{ supplierId: string }>();
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    equipment_category_id: '',
    quantity_available: 1,
    hourly_rate: '',
    daily_rate: '',
  });
  const [supplier, setSupplier] = useState<Supplier | null>(null);
  const [categories, setCategories] = useState<EquipmentCategory[]>([]);
  const [loading, setLoading] = useState(false);
  const [loadingData, setLoadingData] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (supplierId) {
      loadData();
    }
  }, [supplierId]);

  const loadData = async () => {
    try {
      setLoadingData(true);
      const [supplierRes, categoriesRes] = await Promise.all([
        supplierService.getSupplier(Number(supplierId)),
        api.get('/equipment/categories'),
      ]);
      
      setSupplier({
        id: supplierRes.id,
        name: supplierRes.name,
      });
      setCategories(categoriesRes.data.items || categoriesRes.data || []);
    } catch (err: any) {
      setError('שגיאה בטעינת נתונים');
      console.error(err);
    } finally {
      setLoadingData(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!formData.equipment_category_id) {
      setError('חובה לבחור קטגוריית ציוד');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      await api.post('/suppliers/equipment', {
        supplier_id: Number(supplierId),
        equipment_category_id: Number(formData.equipment_category_id),
        quantity_available: formData.quantity_available,
        hourly_rate: formData.hourly_rate ? Number(formData.hourly_rate) : null,
        daily_rate: formData.daily_rate ? Number(formData.daily_rate) : null,
      });
      alert('ציוד נוסף לספק בהצלחה!');
      navigate(`/suppliers/${supplierId}`);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'שגיאה בהוספת ציוד');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-2xl mx-auto">
        <div className="bg-white rounded-xl shadow-lg p-8">
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-gray-900 mb-2">הוספת ציוד לספק</h1>
            <p className="text-gray-600">
              {supplier ? `הוספת ציוד לספק: ${supplier.name}` : 'טוען...'}
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
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  <Package className="inline w-4 h-4 ml-1" />
                  קטגוריית ציוד *
                </label>
                <select
                  value={formData.equipment_category_id}
                  onChange={(e) => setFormData({ ...formData, equipment_category_id: e.target.value })}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-kkl-green focus:border-transparent"
                  required
                >
                  <option value="">בחר קטגוריית ציוד</option>
                  {categories.map((cat) => (
                    <option key={cat.id} value={cat.id}>
                      {cat.name} ({cat.code})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  כמות זמינה
                </label>
                <input
                  type="number"
                  min="1"
                  value={formData.quantity_available}
                  onChange={(e) => setFormData({ ...formData, quantity_available: Number(e.target.value) })}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-kkl-green focus:border-transparent"
                />
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    <DollarSign className="inline w-4 h-4 ml-1" />
                    תעריף שעתי (ש"ח)
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    value={formData.hourly_rate}
                    onChange={(e) => setFormData({ ...formData, hourly_rate: e.target.value })}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-kkl-green focus:border-transparent"
                    placeholder="0.00"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    <DollarSign className="inline w-4 h-4 ml-1" />
                    תעריף יומי (ש"ח)
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    value={formData.daily_rate}
                    onChange={(e) => setFormData({ ...formData, daily_rate: e.target.value })}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-kkl-green focus:border-transparent"
                    placeholder="0.00"
                  />
                </div>
              </div>

              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <p className="text-sm text-blue-800">
                  <strong>הערה:</strong> ניתן להזין תעריף שעתי או יומי (או שניהם). התעריף ישמש לחישוב עלויות בהזמנות עבודה.
                </p>
              </div>

              <div className="flex gap-4">
                <button
                  type="button"
                  onClick={() => navigate(`/suppliers/${supplierId}`)}
                  className="flex-1 px-6 py-3 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors"
                >
                  ביטול
                </button>
                <button
                  type="submit"
                  disabled={loading}
                  className="flex-1 px-6 py-3 bg-kkl-green text-white rounded-lg hover:bg-green-700 transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                >
                  {loading ? 'מוסיף...' : 'הוסף ציוד'}
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

export default AddSupplierEquipment;

