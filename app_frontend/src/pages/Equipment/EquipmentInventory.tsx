
// src/pages/Equipment/EquipmentInventory.tsx
// מלאי כלים - רשימת כל הכלים עם מספר רישוי, ספק ומחיר
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  ArrowRight, Search, Truck, DollarSign, Eye,
  Package, Building2, ChevronDown
} from 'lucide-react';
import api from '../../services/api';
import TreeLoader from '../../components/common/TreeLoader';

interface Equipment {
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
  is_active: boolean;
}

interface Supplier {
  id: number;
  name: string;
}

const EquipmentInventory: React.FC = () => {
  const navigate = useNavigate();
  const [equipment, setEquipment] = useState<Equipment[]>([]);
  const [suppliers, setSuppliers] = useState<Supplier[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedSupplier, setSelectedSupplier] = useState<number | 'all'>('all');

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [equipmentRes, suppliersRes] = await Promise.all([
        api.get('/equipment'),
        api.get('/suppliers')
      ]);
      
      const eqData = equipmentRes.data?.items || equipmentRes.data || [];
      const supData = suppliersRes.data?.items || suppliersRes.data || [];
      
      setEquipment(Array.isArray(eqData) ? eqData : []);
      setSuppliers(Array.isArray(supData) ? supData : []);
    } catch (error) {
      console.error('Error loading data:', error);
    } finally {
      setLoading(false);
    }
  };

  const filteredEquipment = equipment.filter(eq => {
    const matchesSearch = 
      eq.name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      eq.license_plate?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      eq.supplier_name?.toLowerCase().includes(searchTerm.toLowerCase());
    
    const matchesSupplier = selectedSupplier === 'all' || eq.supplier_id === selectedSupplier;
    
    return matchesSearch && matchesSupplier;
  });

  // Group by supplier for stats
  const equipmentBySupplier = equipment.reduce((acc, eq) => {
    const supplierId = eq.supplier_id || 0;
    if (!acc[supplierId]) acc[supplierId] = [];
    acc[supplierId].push(eq);
    return acc;
  }, {} as Record<number, Equipment[]>);

  const getSupplierName = (supplierId: number | null | undefined) => {
    if (!supplierId) return 'לא שויך ספק';
    const supplier = suppliers.find(s => s.id === supplierId);
    return supplier?.name ?? 'לא שויך ספק';
  };

  if (loading) {
    return <TreeLoader fullScreen />;
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-emerald-50/30" dir="rtl">
      <div className="max-w-7xl mx-auto px-4 py-6">
        {/* Header */}
        <div className="mb-6">
          <button 
            onClick={() => navigate(-1)}
            className="text-emerald-600 hover:text-emerald-700 flex items-center gap-1 mb-4 text-sm font-medium"
          >
            <ArrowRight className="w-4 h-4" />
            חזרה
          </button>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="w-14 h-14 bg-gradient-to-br from-emerald-500 to-green-600 rounded-2xl flex items-center justify-center shadow-lg shadow-emerald-200">
                <Package className="w-7 h-7 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">מלאי כלים</h1>
                <p className="text-gray-500">כל הכלים הרשומים במערכת עם פרטי ספק ומחיר</p>
              </div>
            </div>
            <div className="text-left">
              <div className="text-3xl font-bold text-emerald-600">{equipment.length}</div>
              <div className="text-sm text-gray-500">כלים רשומים</div>
            </div>
          </div>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-6">
          {Object.entries(equipmentBySupplier).slice(0, 4).map(([supplierId, items]) => (
            <button
              key={supplierId}
              onClick={() => setSelectedSupplier(Number(supplierId))}
              className={`bg-white rounded-xl border-2 p-4 text-right transition-all hover:shadow-md ${
                selectedSupplier === Number(supplierId) 
                  ? 'border-emerald-500 shadow-md' 
                  : 'border-gray-100'
              }`}
            >
              <div className="text-2xl font-bold text-gray-900">{items.length}</div>
              <div className="text-sm text-gray-500 truncate">{getSupplierName(Number(supplierId))}</div>
            </button>
          ))}
        </div>

        {/* Search & Filters */}
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-4 mb-6">
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="flex-1 relative">
              <Search className="absolute right-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
              <input
                type="text"
                placeholder="חיפוש לפי שם, מספר רישוי או ספק..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pr-12 pl-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:border-transparent bg-gray-50"
              />
            </div>
            <div className="relative">
              <select
                value={selectedSupplier}
                onChange={(e) => setSelectedSupplier(e.target.value === 'all' ? 'all' : Number(e.target.value))}
                className="appearance-none px-4 py-3 pr-4 pl-10 border border-gray-200 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:border-transparent bg-white min-w-[200px]"
              >
                <option value="all">כל הספקים</option>
                {suppliers.map(s => (
                  <option key={s.id} value={s.id}>{s.name}</option>
                ))}
              </select>
              <ChevronDown className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400 pointer-events-none" />
            </div>
          </div>
        </div>

        {/* Equipment Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredEquipment.length === 0 ? (
            <div className="col-span-full text-center py-12 text-gray-500">
              לא נמצאו כלים
            </div>
          ) : (
            filteredEquipment.map((eq) => (
              <div
                key={eq.id}
                className="bg-white rounded-2xl border border-gray-100 overflow-hidden hover:shadow-lg transition-all duration-300 group"
              >
                {/* Header with license plate */}
                <div className="bg-gradient-to-r from-slate-800 to-slate-700 px-5 py-4 text-white">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 bg-white/10 rounded-xl flex items-center justify-center">
                        <Truck className="w-5 h-5" />
                      </div>
                      <div>
                        <div className="text-xs text-slate-300">מספר רישוי</div>
                        <div className="text-xl font-bold tracking-wider">{eq.license_plate || eq.code}</div>
                      </div>
                    </div>
                    <button
                      onClick={() => navigate(`/equipment/${eq.id}`)}
                      className="p-2 bg-white/10 rounded-lg hover:bg-white/20 transition-colors"
                    >
                      <Eye className="w-4 h-4" />
                    </button>
                  </div>
                </div>

                {/* Content */}
                <div className="p-5">
                  <h3 className="font-bold text-gray-900 text-lg mb-3">{eq.name || eq.equipment_type}</h3>
                  
                  <div className="space-y-3">
                    {/* Supplier */}
                    <div className="flex items-center gap-3 p-3 bg-blue-50 rounded-xl">
                      <div className="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center">
                        <Building2 className="w-4 h-4 text-blue-600" />
                      </div>
                      <div>
                        <div className="text-xs text-blue-600">ספק</div>
                        <div className="font-medium text-gray-900">{eq.supplier_name || getSupplierName(eq.supplier_id) || '—'}</div>
                      </div>
                    </div>

                    {/* Price */}
                    <div className="flex items-center gap-3 p-3 bg-emerald-50 rounded-xl">
                      <div className="w-8 h-8 bg-emerald-100 rounded-lg flex items-center justify-center">
                        <DollarSign className="w-4 h-4 text-emerald-600" />
                      </div>
                      <div className="flex-1">
                        <div className="text-xs text-emerald-600">תעריף שעתי</div>
                        <div className="font-bold text-emerald-700 text-lg">
                          {eq.hourly_rate ? `₪${eq.hourly_rate.toLocaleString()}` : 'לא נקבע'}
                        </div>
                      </div>
                      {eq.daily_rate && (
                        <div className="text-left">
                          <div className="text-xs text-gray-500">יומי</div>
                          <div className="font-medium text-gray-700">₪{eq.daily_rate.toLocaleString()}</div>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Status badge */}
                  <div className="mt-4 flex justify-between items-center">
                    <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                      eq.is_active 
                        ? 'bg-green-100 text-green-700' 
                        : 'bg-gray-100 text-gray-500'
                    }`}>
                      {eq.is_active ? 'פעיל' : 'לא פעיל'}
                    </span>
                    <span className="text-xs text-gray-400">#{eq.id}</span>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>

        {/* Summary */}
        <div className="mt-8 bg-gradient-to-r from-emerald-500 to-green-600 rounded-2xl p-6 text-white">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div>
              <h3 className="text-lg font-bold mb-1">סיכום מלאי</h3>
              <p className="text-emerald-100">כל הכלים הרשומים במערכת</p>
            </div>
            <div className="flex gap-8">
              <div className="text-center">
                <div className="text-3xl font-bold">{equipment.length}</div>
                <div className="text-sm text-emerald-100">סה"כ כלים</div>
              </div>
              <div className="text-center">
                <div className="text-3xl font-bold">{Object.keys(equipmentBySupplier).length}</div>
                <div className="text-sm text-emerald-100">ספקים</div>
              </div>
              <div className="text-center">
                <div className="text-3xl font-bold">{equipment.filter(e => e.is_active).length}</div>
                <div className="text-sm text-emerald-100">פעילים</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default EquipmentInventory;

