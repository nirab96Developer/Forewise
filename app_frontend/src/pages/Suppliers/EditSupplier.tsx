
import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { ArrowRight, AlertCircle, Building2, Mail, Phone, MapPin, Plus, Pencil } from 'lucide-react';
import supplierService, { SupplierEquipmentStatus } from '../../services/supplierService';
import api from '../../services/api';

const EditSupplier: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState<'general' | 'equipment'>('general');
  const [formData, setFormData] = useState({
    name: '',
    code: '',
    tax_id: '',
    contact_name: '',
    email: '',
    phone: '',
    address: '',
    supplier_type: '',
    region_id: '',
    area_id: '',
    is_active: true,
  });
  const [regions, setRegions] = useState<any[]>([]);
  const [areas, setAreas] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [loadingData, setLoadingData] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [equipment, setEquipment] = useState<any[]>([]);
  const [loadingEquipment, setLoadingEquipment] = useState(false);
  const [equipmentLoaded, setEquipmentLoaded] = useState(false);
  const [models, setModels] = useState<any[]>([]);
  const [showEquipmentModal, setShowEquipmentModal] = useState(false);
  const [equipmentModalLoading, setEquipmentModalLoading] = useState(false);
  const [editingEquipmentId, setEditingEquipmentId] = useState<number | null>(null);
  const [equipmentFormData, setEquipmentFormData] = useState({
    equipment_model_id: '',
    license_plate: '',
    status: 'available',
    quantity_available: 1,
  });

  useEffect(() => {
    if (id) {
      loadSupplier();
    }
  }, [id]);

  useEffect(() => {
    const loadGeo = async () => {
      try {
        const [regionsRes, areasRes] = await Promise.all([api.get('/regions'), api.get('/areas')]);
        setRegions(regionsRes.data?.items || regionsRes.data || []);
        setAreas(areasRes.data?.items || areasRes.data || []);
      } catch (err) {
        console.error('Failed loading regions/areas', err);
      }
    };
    loadGeo();
  }, []);

  useEffect(() => {
    if (activeTab === 'equipment' && !equipmentLoaded && id) {
      loadEquipment();
    }
  }, [activeTab, equipmentLoaded, id]);

  const loadSupplier = async () => {
    try {
      setLoadingData(true);
      const supplier = await supplierService.getSupplier(Number(id));
      setFormData({
        name: supplier.name || '',
        code: supplier.code || '',
        tax_id: '',
        contact_name: supplier.contact_name || '',
        email: supplier.email || '',
        phone: supplier.phone || '',
        address: supplier.address || '',
        supplier_type: supplier.supplier_type || '',
        region_id: supplier.region_id ? String(supplier.region_id) : '',
        area_id: supplier.area_id ? String(supplier.area_id) : '',
        is_active: supplier.is_active !== false,
      });
    } catch (err: any) {
      setError('שגיאה בטעינת נתוני הספק');
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
      await supplierService.updateSupplier(Number(id), {
        name: formData.name,
        code: formData.code,
        tax_id: formData.tax_id || undefined,
        contact_name: formData.contact_name,
        email: formData.email,
        phone: formData.phone,
        address: formData.address,
        supplier_type: formData.supplier_type || undefined,
        region_id: formData.region_id ? Number(formData.region_id) : undefined,
        area_id: formData.area_id ? Number(formData.area_id) : undefined,
        is_active: formData.is_active,
      });
      if ((window as any).showToast) {
        (window as any).showToast('ספק עודכן בהצלחה!', 'success');
      }
      navigate('/suppliers');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'שגיאה בעדכון ספק');
    } finally {
      setLoading(false);
    }
  };

  const loadEquipment = async () => {
    try {
      setLoadingEquipment(true);
      const requests: Promise<any>[] = [supplierService.getSupplierEquipment(Number(id))];
      if (!models.length) {
        requests.push(supplierService.getActiveEquipmentModels());
      }
      const results = await Promise.all(requests);
      const data = results[0] || [];
      if (results[1]) {
        setModels(results[1]);
      }
      setEquipment(data || []);
      setEquipmentLoaded(true);
    } catch (err) {
      console.error(err);
      if ((window as any).showToast) {
        (window as any).showToast('שגיאה בטעינת כלי הספק', 'error');
      }
    } finally {
      setLoadingEquipment(false);
    }
  };

  const openAddEquipmentModal = async () => {
    setEditingEquipmentId(null);
    setEquipmentFormData({
      equipment_model_id: '',
      license_plate: '',
      status: 'available',
      quantity_available: 1,
    });
    if (!models.length) {
      try {
        const rows = await supplierService.getActiveEquipmentModels();
        setModels(rows);
      } catch (err) {
        console.error(err);
        if ((window as any).showToast) {
          (window as any).showToast('שגיאה בטעינת דגמי ציוד', 'error');
        }
      }
    }
    setShowEquipmentModal(true);
  };

  const openEditEquipmentModal = async (item: any) => {
    if (!models.length) {
      try {
        const rows = await supplierService.getActiveEquipmentModels();
        setModels(rows);
      } catch (err) {
        console.error(err);
      }
    }
    setEditingEquipmentId(item.id);
    setEquipmentFormData({
      equipment_model_id: item.equipment_model_id ? String(item.equipment_model_id) : '',
      license_plate: item.license_plate || '',
      status: item.status || 'available',
      quantity_available: item.quantity_available ?? 1,
    });
    setShowEquipmentModal(true);
  };

  const handleSaveEquipment = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!id) return;

    setEquipmentModalLoading(true);
    try {
      if (editingEquipmentId) {
        await supplierService.updateSupplierEquipment(Number(id), editingEquipmentId, {
          status: equipmentFormData.status as SupplierEquipmentStatus,
          quantity_available: Number(equipmentFormData.quantity_available || 0),
        });
      } else {
        await supplierService.addSupplierEquipment(Number(id), {
          equipment_model_id: Number(equipmentFormData.equipment_model_id),
          license_plate: equipmentFormData.license_plate.trim().toUpperCase(),
          status: equipmentFormData.status as SupplierEquipmentStatus,
          quantity_available: Number(equipmentFormData.quantity_available || 0),
        });
      }
      if ((window as any).showToast) {
        (window as any).showToast('הכלי נשמר בהצלחה', 'success');
      }
      setShowEquipmentModal(false);
      await loadEquipment();
    } catch (err: any) {
      if (err?.response?.status === 409) {
        if ((window as any).showToast) {
          (window as any).showToast('לוחית רישוי כבר קיימת אצל ספק זה', 'error');
        }
      } else if ((window as any).showToast) {
        (window as any).showToast(err?.response?.data?.detail || 'שגיאה בשמירת כלי', 'error');
      }
    } finally {
      setEquipmentModalLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-2xl mx-auto">
        <div className="bg-white rounded-xl shadow-lg p-8">
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-gray-900 mb-2">עריכת ספק</h1>
            <p className="text-gray-600">עדכון פרטי ספק</p>
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
            <>
              <div className="mb-6 border-b border-gray-200">
                <nav className="-mb-px flex gap-6" aria-label="Tabs">
                  <button
                    type="button"
                    onClick={() => setActiveTab('general')}
                    className={`pb-3 text-sm font-medium border-b-2 ${activeTab === 'general' ? 'border-kkl-green text-kkl-green' : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'}`}
                  >
                    פרטים כלליים
                  </button>
                  <button
                    type="button"
                    onClick={() => setActiveTab('equipment')}
                    className={`pb-3 text-sm font-medium border-b-2 ${activeTab === 'equipment' ? 'border-kkl-green text-kkl-green' : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'}`}
                  >
                    כלים של הספק
                  </button>
                </nav>
              </div>

              {activeTab === 'general' ? (
                <form onSubmit={handleSubmit} className="space-y-6">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        <Building2 className="inline w-4 h-4 ml-1" />
                        שם הספק *
                      </label>
                      <input
                        type="text"
                        value={formData.name}
                        onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                        className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-kkl-green focus:border-transparent"
                        required
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        קוד ספק *
                      </label>
                      <input
                        type="text"
                        value={formData.code}
                        onChange={(e) => setFormData({ ...formData, code: e.target.value.toUpperCase() })}
                        className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-kkl-green focus:border-transparent"
                        required
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      ח.פ./ת.ז.
                    </label>
                    <input
                      type="text"
                      value={formData.tax_id}
                      onChange={(e) => setFormData({ ...formData, tax_id: e.target.value })}
                      className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-kkl-green focus:border-transparent"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      איש קשר *
                    </label>
                    <input
                      type="text"
                      value={formData.contact_name}
                      onChange={(e) => setFormData({ ...formData, contact_name: e.target.value })}
                      className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-kkl-green focus:border-transparent"
                      required
                    />
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        <Mail className="inline w-4 h-4 ml-1" />
                        אימייל *
                      </label>
                      <input
                        type="email"
                        value={formData.email}
                        onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                        className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-kkl-green focus:border-transparent"
                        required
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        <Phone className="inline w-4 h-4 ml-1" />
                        טלפון *
                      </label>
                      <input
                        type="tel"
                        value={formData.phone}
                        onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                        className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-kkl-green focus:border-transparent"
                        required
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      <MapPin className="inline w-4 h-4 ml-1" />
                      כתובת
                    </label>
                    <textarea
                      value={formData.address}
                      onChange={(e) => setFormData({ ...formData, address: e.target.value })}
                      rows={3}
                      className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-kkl-green focus:border-transparent"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      סוג ספק
                    </label>
                    <select
                      value={formData.supplier_type}
                      onChange={(e) => setFormData({ ...formData, supplier_type: e.target.value })}
                      className="w-full pr-4 pl-10 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-kkl-green focus:border-transparent"
                    >
                      <option value="">בחר סוג</option>
                      <option value="equipment">ציוד</option>
                      <option value="service">שירות</option>
                      <option value="both">שניהם</option>
                    </select>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">מרחב</label>
                      <select
                        value={formData.region_id}
                        onChange={(e) => setFormData({ ...formData, region_id: e.target.value })}
                        className="w-full pr-4 pl-10 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-kkl-green focus:border-transparent"
                      >
                        <option value="">בחר מרחב</option>
                        {regions.map((region) => (
                          <option key={region.id} value={region.id}>
                            {region.name}
                          </option>
                        ))}
                      </select>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">אזור</label>
                      <select
                        value={formData.area_id}
                        onChange={(e) => setFormData({ ...formData, area_id: e.target.value })}
                        className="w-full pr-4 pl-10 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-kkl-green focus:border-transparent"
                      >
                        <option value="">בחר אזור</option>
                        {areas
                          .filter((area) => !formData.region_id || String(area.region_id) === formData.region_id)
                          .map((area) => (
                            <option key={area.id} value={area.id}>
                              {area.name}
                            </option>
                          ))}
                      </select>
                    </div>
                  </div>

                  <div className="flex items-center">
                    <input
                      type="checkbox"
                      id="is_active"
                      checked={formData.is_active}
                      onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                      className="h-4 w-4 text-kkl-green focus:ring-kkl-green border-gray-300 rounded"
                    />
                    <label htmlFor="is_active" className="mr-2 text-sm text-gray-700">
                      ספק פעיל
                    </label>
                  </div>

                  <div className="flex gap-4">
                    <button
                      type="button"
                      onClick={() => navigate('/suppliers')}
                      className="flex-1 px-6 py-3 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors"
                    >
                      ביטול
                    </button>
                    <button
                      type="submit"
                      disabled={loading || showEquipmentModal}
                      className="flex-1 px-6 py-3 bg-kkl-green text-white rounded-lg hover:bg-green-700 transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                    >
                      {loading ? 'שומר...' : 'שמור שינויים'}
                      <ArrowRight className="w-5 h-5" />
                    </button>
                  </div>
                </form>
              ) : (
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <h2 className="text-lg font-semibold text-gray-900">כלים של הספק</h2>
                    <button
                      type="button"
                      onClick={openAddEquipmentModal}
                      className="inline-flex items-center gap-2 px-4 py-2 bg-kkl-green text-white rounded-lg hover:bg-green-700 transition-colors"
                    >
                      <Plus className="w-4 h-4" />
                      הוסף כלי
                    </button>
                  </div>

                  {loadingEquipment ? (
                    <div className="text-center py-8 text-gray-500">טוען כלים...</div>
                  ) : equipment.length === 0 ? (
                    <div className="text-center py-10 text-gray-500 border border-dashed border-gray-300 rounded-lg">
                      אין כלים לספק זה
                    </div>
                  ) : (
                    <div className="overflow-x-auto border border-gray-200 rounded-lg">
                      <table className="w-full">
                        <thead className="bg-gray-50 border-b border-gray-200">
                          <tr>
                            <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">דגם</th>
                            <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">לוחית</th>
                            <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">סטטוס</th>
                            <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">פעולות</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-200">
                          {equipment.map((item) => (
                            <tr key={item.id} className="hover:bg-gray-50">
                              <td className="px-4 py-3 text-sm text-gray-900">
                                {models.find((m) => m.id === item.equipment_model_id)?.name || item.equipment_model_id || '-'}
                              </td>
                              <td className="px-4 py-3 text-sm text-gray-900">{item.license_plate || '-'}</td>
                              <td className="px-4 py-3 text-sm text-gray-700">{item.status || '-'}</td>
                              <td className="px-4 py-3 text-sm">
                                <button
                                  type="button"
                                  onClick={() => openEditEquipmentModal(item)}
                                  className="inline-flex items-center gap-1 text-blue-600 hover:text-blue-800"
                                >
                                  <Pencil className="w-4 h-4" />
                                  ערוך
                                </button>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </div>
              )}
            </>
          )}
        </div>
      </div>

      {showEquipmentModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
          <div className="bg-white rounded-xl shadow-lg w-full max-w-md p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              {editingEquipmentId ? 'עריכת כלי ספק' : 'הוספת כלי ספק'}
            </h3>
            <form onSubmit={handleSaveEquipment} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">דגם כלי *</label>
                <select
                  value={equipmentFormData.equipment_model_id}
                  onChange={(e) => setEquipmentFormData({ ...equipmentFormData, equipment_model_id: e.target.value })}
                  className="w-full pr-4 pl-10 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-kkl-green focus:border-transparent"
                  disabled={!!editingEquipmentId}
                  required
                >
                  <option value="">בחר דגם</option>
                  {models.map((model) => (
                    <option key={model.id} value={model.id}>
                      {model.name}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">לוחית רישוי *</label>
                <input
                  type="text"
                  value={equipmentFormData.license_plate}
                  onChange={(e) => setEquipmentFormData({ ...equipmentFormData, license_plate: e.target.value.toUpperCase() })}
                  className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-kkl-green focus:border-transparent"
                  disabled={!!editingEquipmentId}
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">סטטוס</label>
                <select
                  value={equipmentFormData.status}
                  onChange={(e) => setEquipmentFormData({ ...equipmentFormData, status: e.target.value })}
                  className="w-full pr-4 pl-10 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-kkl-green focus:border-transparent"
                >
                  <option value="available">available</option>
                  <option value="busy">busy</option>
                  <option value="inactive">inactive</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">כמות זמינה</label>
                <input
                  type="number"
                  min={0}
                  value={equipmentFormData.quantity_available}
                  onChange={(e) => setEquipmentFormData({ ...equipmentFormData, quantity_available: Number(e.target.value || 0) })}
                  className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-kkl-green focus:border-transparent"
                />
              </div>
              <div className="flex justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setShowEquipmentModal(false)}
                  className="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50"
                >
                  ביטול
                </button>
                <button
                  type="submit"
                  disabled={equipmentModalLoading}
                  className="px-4 py-2 bg-kkl-green text-white rounded-lg hover:bg-green-700 disabled:bg-gray-400"
                >
                  {equipmentModalLoading ? 'שומר...' : 'שמור'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default EditSupplier;








