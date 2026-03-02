
// src/pages/Suppliers/Suppliers.tsx
import React, { useState, useEffect, useMemo } from "react";
import { useNavigate } from "react-router-dom";
import { Truck, Search, Plus, Eye, Edit, X } from "lucide-react";
import supplierService from "../../services/supplierService";

interface Supplier {
  id: number;
  name: string;
  code?: string;
  contact_name?: string;
  email?: string;
  phone?: string;
  is_active?: boolean;
  rating?: number;
  total_work_orders?: number;
  completed_work_orders?: number;
}

const Suppliers: React.FC = () => {
  const navigate = useNavigate();
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [suppliers, setSuppliers] = useState<Supplier[]>([]);
  const [searchTerm, setSearchTerm] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("all");

  useEffect(() => { loadSuppliers(); }, []);

  const loadSuppliers = async () => {
    try {
      setIsLoading(true);
      setError(null);
      const response = await supplierService.getSuppliers({});
      setSuppliers(response.suppliers || []);
    } catch (err: any) {
      console.error('Error loading suppliers:', err);
      setError('שגיאה בטעינת ספקים');
    }
    setIsLoading(false);
  };

  const filteredSuppliers = useMemo(() => suppliers.filter(s => {
    if (searchTerm) {
      const q = searchTerm.toLowerCase();
      if (!s.name?.toLowerCase().includes(q) &&
          !s.code?.toLowerCase().includes(q) &&
          !s.contact_name?.toLowerCase().includes(q)) return false;
    }
    if (statusFilter === 'active' && !s.is_active) return false;
    if (statusFilter === 'inactive' && s.is_active) return false;
    return true;
  }), [suppliers, searchTerm, statusFilter]);

  const hasFilters = searchTerm || statusFilter !== 'all';
  const activeCount = suppliers.filter(s => s.is_active).length;

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-green-200 border-t-green-600 rounded-full animate-spin mx-auto mb-4" />
          <p className="text-gray-600">טוען ספקים...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="bg-white p-6 rounded-xl shadow-sm max-w-sm text-center">
          <p className="text-red-600 mb-4">{error}</p>
          <button onClick={loadSuppliers} className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700">נסה שוב</button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 pt-6 pb-8 px-4" dir="rtl">
      <div className="max-w-5xl mx-auto">

        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">ניהול ספקים</h1>
            <p className="text-sm text-gray-500 mt-0.5">{suppliers.length} ספקים · {activeCount} פעילים</p>
          </div>
          <button
            onClick={() => navigate('/suppliers/new')}
            className="flex items-center gap-2 px-4 py-2.5 bg-green-600 text-white rounded-xl hover:bg-green-700 font-medium shadow-sm transition-colors"
          >
            <Plus className="w-4 h-4" />
            ספק חדש
          </button>
        </div>

        {/* Search + filter bar */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-3 mb-4">
          <div className="flex flex-wrap gap-2 items-center">
            <div className="relative flex-1 min-w-[180px]">
              <Search className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 w-4 h-4" />
              <input
                type="text"
                placeholder="חיפוש שם / קוד / איש קשר..."
                value={searchTerm}
                onChange={e => setSearchTerm(e.target.value)}
                className="w-full pr-9 pl-3 py-2 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-green-500 focus:border-green-500"
              />
            </div>

            {/* Status chips */}
            <div className="flex gap-1.5">
              {([['all', 'הכל'], ['active', 'פעילים'], ['inactive', 'לא פעילים']] as const).map(([v, label]) => (
                <button
                  key={v}
                  onClick={() => setStatusFilter(v)}
                  className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                    statusFilter === v
                      ? v === 'active' ? 'bg-green-600 text-white' : v === 'inactive' ? 'bg-gray-600 text-white' : 'bg-blue-600 text-white'
                      : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                  }`}
                >
                  {label}
                </button>
              ))}
            </div>

            {hasFilters && (
              <button onClick={() => { setSearchTerm(''); setStatusFilter('all'); }} className="flex items-center gap-1 text-xs text-gray-500 hover:text-red-600 px-2 py-1.5 rounded-lg hover:bg-red-50 transition-colors">
                <X className="w-3.5 h-3.5" /> נקה
              </button>
            )}
          </div>
        </div>

        {hasFilters && (
          <p className="text-xs text-gray-500 mb-3 px-1">מציג {filteredSuppliers.length} מתוך {suppliers.length} ספקים</p>
        )}

        {/* Suppliers list */}
        {filteredSuppliers.length === 0 ? (
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-12 text-center">
            <Truck className="w-14 h-14 text-gray-300 mx-auto mb-3" />
            <h3 className="text-lg font-semibold text-gray-700 mb-1">
              {hasFilters ? 'לא נמצאו ספקים' : 'אין ספקים'}
            </h3>
            <p className="text-sm text-gray-500">
              {hasFilters ? 'נסה לשנות את הפילטרים' : 'הוסף ספק ראשון'}
            </p>
          </div>
        ) : (
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
            {filteredSuppliers.map((supplier, idx) => (
              <div
                key={supplier.id}
                className={`flex items-center gap-4 px-5 py-3.5 hover:bg-gray-50 transition-colors ${
                  idx !== filteredSuppliers.length - 1 ? 'border-b border-gray-100' : ''
                }`}
              >
                {/* Icon */}
                <div className={`w-9 h-9 rounded-full flex items-center justify-center flex-shrink-0 ${
                  supplier.is_active ? 'bg-green-100' : 'bg-gray-100'
                }`}>
                  <Truck className={`w-4 h-4 ${supplier.is_active ? 'text-green-600' : 'text-gray-400'}`} />
                </div>

                {/* Name + contact */}
                <div className="flex-1 min-w-0">
                  <div className="font-medium text-gray-900 text-sm">{supplier.name}</div>
                  <div className="text-xs text-gray-400 truncate">
                    {supplier.contact_name && <span>{supplier.contact_name}</span>}
                    {supplier.contact_name && supplier.email && <span className="mx-1">·</span>}
                    {supplier.email && <span>{supplier.email}</span>}
                    {!supplier.contact_name && !supplier.email && <span>—</span>}
                  </div>
                </div>

                {/* Code */}
                {supplier.code && (
                  <span className="hidden sm:inline-flex px-2 py-1 bg-gray-100 text-gray-600 rounded text-xs font-mono flex-shrink-0">
                    {supplier.code}
                  </span>
                )}

                {/* Orders count */}
                <div className="hidden md:block text-xs text-gray-500 flex-shrink-0 min-w-[80px] text-center">
                  <div className="font-medium text-gray-700">{supplier.completed_work_orders || 0} / {supplier.total_work_orders || 0}</div>
                  <div>הזמנות</div>
                </div>

                {/* Status badge */}
                <span className={`hidden sm:inline-flex px-2.5 py-1 rounded-full text-xs font-medium flex-shrink-0 ${
                  supplier.is_active
                    ? 'bg-green-100 text-green-700'
                    : 'bg-gray-100 text-gray-500'
                }`}>
                  {supplier.is_active ? 'פעיל' : 'לא פעיל'}
                </span>

                {/* Actions */}
                <div className="flex items-center gap-1 flex-shrink-0">
                  <button
                    onClick={() => navigate(`/suppliers/${supplier.id}`)}
                    className="p-1.5 hover:bg-blue-50 rounded-lg text-gray-400 hover:text-blue-600 transition-colors"
                    title="צפייה"
                  >
                    <Eye className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => navigate(`/suppliers/${supplier.id}/edit`)}
                    className="p-1.5 hover:bg-green-50 rounded-lg text-gray-400 hover:text-green-600 transition-colors"
                    title="עריכה"
                  >
                    <Edit className="w-4 h-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default Suppliers;
