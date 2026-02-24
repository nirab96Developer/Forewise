// @ts-nocheck
// src/pages/Settings/SupplierSettings.tsx
// הגדרות ספקים - ניהול ספקים, ציוד ותמחור
import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  ArrowRight, Truck, Plus, Search, Edit, Trash2, 
  ToggleLeft, ToggleRight, DollarSign, Wrench,
  ChevronDown, Filter, MoreVertical, Eye, History,
  CheckCircle, XCircle, AlertCircle
} from 'lucide-react';
import api from '../../services/api';

// Types
interface Supplier {
  id: number;
  name: string;
  contact_person?: string;
  phone?: string;
  email?: string;
  is_active: boolean;
  region_id?: number;
  region_name?: string;
  equipment_count?: number;
  created_at?: string;
}

interface SupplierEquipment {
  id: number;
  supplier_id: number;
  supplier_name?: string;
  equipment_category_id: number;
  equipment_name: string;
  base_rate: number;
  night_rate?: number;
  weekend_rate?: number;
  is_active: boolean;
}

type TabType = 'suppliers' | 'equipment' | 'pricing' | 'rotation' | 'constraints';

// Map paths to tabs
const pathToTab: Record<string, TabType> = {
  '/settings/suppliers': 'suppliers',
  '/settings/supplier-equipment': 'equipment',
  '/settings/pricing': 'pricing',
  '/settings/fair-rotation': 'rotation',
  '/settings/constraint-reasons': 'constraints',
};

const SupplierSettings: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  
  // Determine initial tab from URL
  const getInitialTab = (): TabType => {
    return pathToTab[location.pathname] || 'suppliers';
  };
  
  const [activeTab, setActiveTab] = useState<TabType>(getInitialTab());
  const [suppliers, setSuppliers] = useState<Supplier[]>([]);
  const [supplierEquipment, setSupplierEquipment] = useState<SupplierEquipment[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [showAddModal, setShowAddModal] = useState(false);
  const [editingItem, setEditingItem] = useState<Supplier | SupplierEquipment | null>(null);

  // Update tab when URL changes
  useEffect(() => {
    const newTab = pathToTab[location.pathname];
    if (newTab && newTab !== activeTab) {
      setActiveTab(newTab);
    }
  }, [location.pathname]);

  // Load data
  useEffect(() => {
    loadData();
  }, [activeTab]);

  const loadData = async () => {
    setLoading(true);
    try {
      if (activeTab === 'suppliers') {
        const response = await api.get('/suppliers');
        const data = response.data?.items || response.data || [];
        setSuppliers(Array.isArray(data) ? data : []);
      } else if (activeTab === 'equipment') {
        const response = await api.get('/supplier-equipment');
        const data = response.data?.items || response.data || [];
        setSupplierEquipment(Array.isArray(data) ? data : []);
      }
    } catch (error) {
      console.error('Error loading data:', error);
      setSuppliers([]);
      setSupplierEquipment([]);
    } finally {
      setLoading(false);
    }
  };

  const toggleSupplierStatus = async (supplier: Supplier) => {
    try {
      await api.patch(`/suppliers/${supplier.id}`, {
        is_active: !supplier.is_active
      });
      loadData();
    } catch (error) {
      console.error('Error toggling supplier status:', error);
    }
  };

  const filteredSuppliers = (suppliers || []).filter(s => 
    s.name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    s.contact_person?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const tabs = [
    { id: 'suppliers' as TabType, label: 'רשימת ספקים', icon: <Truck className="w-4 h-4" /> },
    { id: 'equipment' as TabType, label: 'ציוד ספקים', icon: <Wrench className="w-4 h-4" /> },
    { id: 'pricing' as TabType, label: 'תמחור כלים', icon: <DollarSign className="w-4 h-4" /> },
    { id: 'rotation' as TabType, label: 'סבב הוגן', icon: <History className="w-4 h-4" /> },
    { id: 'constraints' as TabType, label: 'סיבות אילוץ', icon: <AlertCircle className="w-4 h-4" /> },
  ];

  return (
    <div className="min-h-screen bg-kkl-bg" dir="rtl">
      <div className="max-w-7xl mx-auto px-4 py-6">
        {/* Header */}
        <div className="mb-6">
          <button 
            onClick={() => navigate('/settings')}
            className="text-kkl-green hover:text-kkl-green-dark flex items-center gap-1 mb-4 text-sm"
          >
            <ArrowRight className="w-4 h-4" />
            חזרה להגדרות
          </button>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 bg-kkl-green rounded-xl flex items-center justify-center">
                <Truck className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-kkl-text">הגדרות ספקים</h1>
                <p className="text-gray-500">ניהול ספקים, ציוד ותמחור</p>
              </div>
            </div>
            <button
              onClick={() => setShowAddModal(true)}
              className="px-4 py-2 bg-kkl-green text-white rounded-lg hover:bg-kkl-green-dark transition-colors flex items-center gap-2"
            >
              <Plus className="w-4 h-4" />
              הוסף {activeTab === 'suppliers' ? 'ספק' : 'ציוד'}
            </button>
          </div>
        </div>

        {/* Tabs */}
        <div className="bg-white rounded-xl shadow-sm border border-kkl-border mb-6">
          <div className="flex overflow-x-auto">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-2 px-5 py-4 text-sm font-medium whitespace-nowrap border-b-2 transition-colors ${
                  activeTab === tab.id
                    ? 'border-kkl-green text-kkl-green bg-kkl-green-light/30'
                    : 'border-transparent text-gray-500 hover:text-kkl-green hover:bg-gray-50'
                }`}
              >
                {tab.icon}
                {tab.label}
              </button>
            ))}
          </div>
        </div>

        {/* Search & Filters */}
        <div className="bg-white rounded-xl shadow-sm border border-kkl-border p-4 mb-6">
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="flex-1 relative">
              <Search className="absolute right-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
              <input
                type="text"
                placeholder={`חיפוש ${activeTab === 'suppliers' ? 'ספקים' : 'ציוד'}...`}
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pr-10 pl-4 py-2.5 border border-kkl-border rounded-lg focus:ring-2 focus:ring-kkl-green focus:border-transparent"
              />
            </div>
            <button className="px-4 py-2.5 border border-kkl-border rounded-lg hover:bg-gray-50 flex items-center gap-2 text-gray-600">
              <Filter className="w-4 h-4" />
              סינון
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="bg-white rounded-xl shadow-sm border border-kkl-border overflow-hidden">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <div className="w-8 h-8 border-2 border-kkl-green border-t-transparent rounded-full animate-spin" />
            </div>
          ) : activeTab === 'suppliers' ? (
            /* Suppliers Table */
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50 border-b border-kkl-border">
                  <tr>
                    <th className="text-right px-4 py-3 text-sm font-semibold text-gray-600">שם ספק</th>
                    <th className="text-right px-4 py-3 text-sm font-semibold text-gray-600">איש קשר</th>
                    <th className="text-right px-4 py-3 text-sm font-semibold text-gray-600">טלפון</th>
                    <th className="text-right px-4 py-3 text-sm font-semibold text-gray-600">מרחב</th>
                    <th className="text-center px-4 py-3 text-sm font-semibold text-gray-600">כלים</th>
                    <th className="text-center px-4 py-3 text-sm font-semibold text-gray-600">סטטוס</th>
                    <th className="text-center px-4 py-3 text-sm font-semibold text-gray-600">פעולות</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredSuppliers.length === 0 ? (
                    <tr>
                      <td colSpan={7} className="text-center py-12 text-gray-500">
                        לא נמצאו ספקים
                      </td>
                    </tr>
                  ) : (
                    filteredSuppliers.map((supplier) => (
                      <tr key={supplier.id} className="border-b border-kkl-border hover:bg-gray-50">
                        <td className="px-4 py-3">
                          <div className="flex items-center gap-3">
                            <div className="w-10 h-10 bg-kkl-green-light rounded-lg flex items-center justify-center">
                              <Truck className="w-5 h-5 text-kkl-green" />
                            </div>
                            <span className="font-medium text-kkl-text">{supplier.name}</span>
                          </div>
                        </td>
                        <td className="px-4 py-3 text-gray-600">{supplier.contact_person || '-'}</td>
                        <td className="px-4 py-3 text-gray-600 direction-ltr">{supplier.phone || '-'}</td>
                        <td className="px-4 py-3 text-gray-600">{supplier.region_name || '-'}</td>
                        <td className="px-4 py-3 text-center">
                          <span className="px-2 py-1 bg-kkl-green-light text-kkl-green text-sm rounded-full">
                            {supplier.equipment_count || 0}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-center">
                          <button
                            onClick={() => toggleSupplierStatus(supplier)}
                            className={`inline-flex items-center gap-1 px-3 py-1 rounded-full text-sm ${
                              supplier.is_active 
                                ? 'bg-green-100 text-green-700' 
                                : 'bg-gray-100 text-gray-500'
                            }`}
                          >
                            {supplier.is_active ? (
                              <>
                                <CheckCircle className="w-4 h-4" />
                                פעיל
                              </>
                            ) : (
                              <>
                                <XCircle className="w-4 h-4" />
                                מושבת
                              </>
                            )}
                          </button>
                        </td>
                        <td className="px-4 py-3">
                          <div className="flex items-center justify-center gap-2">
                            <button 
                              onClick={() => navigate(`/settings/suppliers/${supplier.id}`)}
                              className="p-2 text-gray-400 hover:text-kkl-green hover:bg-kkl-green-light rounded-lg transition-colors"
                              title="צפייה"
                            >
                              <Eye className="w-4 h-4" />
                            </button>
                            <button 
                              onClick={() => setEditingItem(supplier)}
                              className="p-2 text-gray-400 hover:text-kkl-green hover:bg-kkl-green-light rounded-lg transition-colors"
                              title="עריכה"
                            >
                              <Edit className="w-4 h-4" />
                            </button>
                            <button 
                              className="p-2 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded-lg transition-colors"
                              title="מחיקה"
                            >
                              <Trash2 className="w-4 h-4" />
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          ) : activeTab === 'equipment' ? (
            /* Supplier Equipment Table */
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50 border-b border-kkl-border">
                  <tr>
                    <th className="text-right px-4 py-3 text-sm font-semibold text-gray-600">ספק</th>
                    <th className="text-right px-4 py-3 text-sm font-semibold text-gray-600">סוג כלי</th>
                    <th className="text-center px-4 py-3 text-sm font-semibold text-gray-600">תעריף בסיס</th>
                    <th className="text-center px-4 py-3 text-sm font-semibold text-gray-600">תעריף לילה</th>
                    <th className="text-center px-4 py-3 text-sm font-semibold text-gray-600">תעריף שבת/חג</th>
                    <th className="text-center px-4 py-3 text-sm font-semibold text-gray-600">סטטוס</th>
                    <th className="text-center px-4 py-3 text-sm font-semibold text-gray-600">פעולות</th>
                  </tr>
                </thead>
                <tbody>
                  {supplierEquipment.length === 0 ? (
                    <tr>
                      <td colSpan={7} className="text-center py-12 text-gray-500">
                        לא נמצא ציוד ספקים
                      </td>
                    </tr>
                  ) : (
                    supplierEquipment.map((equipment) => (
                      <tr key={equipment.id} className="border-b border-kkl-border hover:bg-gray-50">
                        <td className="px-4 py-3 font-medium text-kkl-text">{equipment.supplier_name}</td>
                        <td className="px-4 py-3">
                          <div className="flex items-center gap-2">
                            <Wrench className="w-4 h-4 text-kkl-green" />
                            {equipment.equipment_name}
                          </div>
                        </td>
                        <td className="px-4 py-3 text-center font-medium">₪{equipment.base_rate}</td>
                        <td className="px-4 py-3 text-center">{equipment.night_rate ? `₪${equipment.night_rate}` : '-'}</td>
                        <td className="px-4 py-3 text-center">{equipment.weekend_rate ? `₪${equipment.weekend_rate}` : '-'}</td>
                        <td className="px-4 py-3 text-center">
                          <span className={`inline-flex items-center gap-1 px-3 py-1 rounded-full text-sm ${
                            equipment.is_active 
                              ? 'bg-green-100 text-green-700' 
                              : 'bg-gray-100 text-gray-500'
                          }`}>
                            {equipment.is_active ? 'פעיל' : 'מושבת'}
                          </span>
                        </td>
                        <td className="px-4 py-3">
                          <div className="flex items-center justify-center gap-2">
                            <button className="p-2 text-gray-400 hover:text-kkl-green hover:bg-kkl-green-light rounded-lg transition-colors">
                              <Edit className="w-4 h-4" />
                            </button>
                            <button className="p-2 text-gray-400 hover:text-blue-500 hover:bg-blue-50 rounded-lg transition-colors" title="היסטוריית תמחור">
                              <History className="w-4 h-4" />
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          ) : activeTab === 'pricing' ? (
            /* Pricing Tab */
            <div className="p-8 text-center">
              <DollarSign className="w-16 h-16 text-gray-300 mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-kkl-text mb-2">תמחור כלים</h3>
              <p className="text-gray-500 mb-4">ניהול תעריפים לכל סוגי הכלים</p>
              <button className="px-4 py-2 bg-kkl-green text-white rounded-lg hover:bg-kkl-green-dark transition-colors">
                הגדר תמחור
              </button>
            </div>
          ) : activeTab === 'rotation' ? (
            /* Fair Rotation Tab */
            <div className="p-8 text-center">
              <History className="w-16 h-16 text-gray-300 mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-kkl-text mb-2">סבב הוגן</h3>
              <p className="text-gray-500 mb-4">הגדרת כללי סבב הקצאת ספקים</p>
              <button className="px-4 py-2 bg-kkl-green text-white rounded-lg hover:bg-kkl-green-dark transition-colors">
                הגדר סבב
              </button>
            </div>
          ) : (
            /* Constraint Reasons Tab */
            <div className="p-8 text-center">
              <AlertCircle className="w-16 h-16 text-gray-300 mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-kkl-text mb-2">סיבות אילוץ ספק</h3>
              <p className="text-gray-500 mb-4">ניהול סיבות לבחירת ספק ידנית</p>
              <button 
                onClick={() => navigate('/settings/constraint-reasons')}
                className="px-4 py-2 bg-kkl-green text-white rounded-lg hover:bg-kkl-green-dark transition-colors"
              >
                נהל סיבות
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default SupplierSettings;

