
// src/pages/WorkOrders/NewWorkOrder.tsx
// דרישת כלים - עיצוב נקי בסגנון קק"ל עם 4 בלוקים ברורים
import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams, useParams } from 'react-router-dom';
import { 
  ArrowRight, Calendar, Clock, Truck, Users, FileText, 
  AlertCircle, CheckCircle, Info, Shield, Moon
} from 'lucide-react';
import workOrderService, { WorkOrderCreate } from '../../services/workOrderService';
import projectService from '../../services/projectService';
import supplierService from '../../services/supplierService';
import equipmentService from '../../services/equipmentService';
import api from '../../services/api';
import { saveOfflineWorkOrder } from '../../utils/offlineStorage';
import { showToast } from '../../components/common/Toast';

interface Project {
  id: number;
  name: string;
  code: string;
  allocated_budget?: number;
  spent_budget?: number;
}

interface Supplier {
  id: number;
  name: string;
  equipment_types?: string[];
}

interface ConstraintReason {
  id: number;
  code: string;
  name_he: string;
  name_en?: string;
  description?: string;
  category: string;
  requires_additional_text: boolean;
  requires_approval: boolean;
}

interface EquipmentCategory {
  id: number;
  name: string;
  code: string;
}

// Section Title Component
const SectionTitle: React.FC<{ icon: React.ReactNode; children: React.ReactNode }> = ({ icon, children }) => (
  <div className="flex items-center gap-2 mb-4 pb-2 border-b border-kkl-border">
    <span className="text-kkl-green">{icon}</span>
    <h3 className="text-base font-semibold text-kkl-text">{children}</h3>
  </div>
);

const NewWorkOrder: React.FC = () => {
  const navigate = useNavigate();
  const { code: urlProjectCode } = useParams<{ code: string }>();
  const [searchParams] = useSearchParams();
  // Support URL path (/projects/:code/...), ?project_code=CODE, or ?project=ID
  const projectCode = urlProjectCode || searchParams.get('project_code');
  const projectIdFromUrl = searchParams.get('project');
  
  const [formData, setFormData] = useState({
    tool_type: '',
    quantity: '',
    work_days: '',
    start_date: new Date().toISOString().split('T')[0],
    allocation_method: 'fair_rotation' as 'fair_rotation' | 'supplier_selection',
    supplier_id: '',
    constraint_reason_id: '',
    constraint_explanation: '',
    notes: '',
    requires_guard: false,  // האם כלי עם שמירה
    guard_days: 0,          // מספר ימי שמירה
  });
  
  const [projects, setProjects] = useState<Project[]>([]);
  const [equipmentCategories, setEquipmentCategories] = useState<EquipmentCategory[]>([]);
  const [filteredSuppliers, setFilteredSuppliers] = useState<Supplier[]>([]);
  const [constraintReasons, setConstraintReasons] = useState<ConstraintReason[]>([]);
  const [selectedProject, setSelectedProject] = useState<Project | null>(null);
  const [selectedCategoryId, setSelectedCategoryId] = useState<number | null>(null);
  const [selectedConstraintReason, setSelectedConstraintReason] = useState<ConstraintReason | null>(null);
  const [loading, setLoading] = useState(false);
  const [loadingData, setLoadingData] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [_touched, setTouched] = useState<Record<string, boolean>>({});
  const [overnightGuardRate, setOvernightGuardRate] = useState<number>(250); // fetched from API

  // Billable hours = 9h/day net (shift is 10.5h total, but 1.5h break is excluded from billing)
  const BILLABLE_HOURS_PER_DAY = 9;
  const workDaysNumber = formData.work_days === '' ? null : Number(formData.work_days);
  const quantityNumber = formData.quantity === '' ? null : Number(formData.quantity);
  const totalHours = workDaysNumber && workDaysNumber > 0 ? workDaysNumber * BILLABLE_HOURS_PER_DAY : 0;
  
  // Calculate end date
  const endDate = formData.start_date && workDaysNumber && workDaysNumber > 0 ? (() => {
    const date = new Date(formData.start_date);
    date.setDate(date.getDate() + workDaysNumber - 1);
    return date.toISOString().split('T')[0];
  })() : '';

  useEffect(() => {
    loadData();
  }, []);

  useEffect(() => {
    if (projects.length === 0) return;
    // Priority: URL path code > ?project_code= > ?project=ID
    if (projectCode) {
      const project = projects.find(p => p.code === projectCode);
      if (project) setSelectedProject(project);
    } else if (projectIdFromUrl) {
      const project = projects.find(p => p.id === parseInt(projectIdFromUrl));
      if (project) setSelectedProject(project);
    }
  }, [projectCode, projectIdFromUrl, projects]);

  // Load suppliers based on selected category ID
  useEffect(() => {
    if (selectedCategoryId == null) {
      setFilteredSuppliers([]);
      return;
    }

    supplierService.getActiveSuppliersByCategory(selectedCategoryId)
      .then(suppliersList => {
        if (formData.allocation_method === 'supplier_selection') {
          setFilteredSuppliers(suppliersList);
        } else {
          setFilteredSuppliers([]);
        }
      })
      .catch(error => {
        console.error('Error loading suppliers:', error);
        setFilteredSuppliers([]);
      });
  }, [selectedCategoryId, formData.allocation_method]);

  const loadData = async () => {
    setLoadingData(true);
    setError(null);
    
    try {
      // Load projects
      try {
        const projectsResponse = await projectService.getProjects({});
        setProjects(projectsResponse?.projects || projectsResponse || []);
      } catch (err: any) {
        console.error('Error loading projects:', err);
        setProjects([]);
      }
      
      // Load equipment categories
      try {
        const categories = await equipmentService.getEquipmentCategories();
        setEquipmentCategories(Array.isArray(categories) ? categories : []);
      } catch (err) {
        console.error('Error loading equipment categories:', err);
        setEquipmentCategories([]);
      }
      
      // Load constraint reasons
      try {
        const response = await api.get('/supplier-constraint-reasons', {
          params: { is_active: true }
        });
        const crData = response?.data;
        setConstraintReasons(Array.isArray(crData) ? crData : (crData?.items || []));
      } catch (err) {
        console.error('Error loading constraint reasons:', err);
        setConstraintReasons([]);
      }
    } catch (error: any) {
      console.error('Error loading data:', error);
      setError('שגיאה בטעינת נתונים');
    }
    
    // Fetch overnight guard rate from work_hour_settings
    try {
      const whRes = await api.get('/settings/work-hours').catch(() => null);
      if (whRes?.data?.overnight_guard_rate !== undefined) {
        setOvernightGuardRate(Number(whRes.data.overnight_guard_rate) || 250);
      }
    } catch {
      // keep default 250
    }

    // Always stop loading
    setLoadingData(false);
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value, type } = e.target;
    const isCheckbox = type === 'checkbox';
    
    setTouched(prev => ({ ...prev, [name]: true }));
    
    if (name === 'constraint_reason_id') {
      const reasonId = value ? Number(value) : null;
      const reason = constraintReasons.find(r => r.id === reasonId);
      setSelectedConstraintReason(reason || null);
      setFormData(prev => ({
        ...prev,
        [name]: value,
        constraint_explanation: reason?.requires_additional_text ? prev.constraint_explanation : ''
      }));
    } else {
      setFormData(prev => ({
        ...prev,
        [name]: isCheckbox 
          ? (e.target as HTMLInputElement).checked
          : (name === 'quantity' || name === 'work_days' || name === 'supplier_id' || name === 'constraint_reason_id')
            ? (value ? parseInt(value) : '')
            : value
      }));
    }
  };

  const handleCategoryChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const value = e.target.value;
    const categoryId = value ? Number(value) : null;
    setSelectedCategoryId(categoryId);
    setTouched(prev => ({ ...prev, tool_type: true }));
    
    const category = equipmentCategories.find(cat => cat.id === categoryId);
    setFormData(prev => ({
      ...prev,
      tool_type: category ? category.name : ''
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    // Validate
    if (!selectedProject) {
      setError('יש לבחור פרויקט');
      setLoading(false);
      return;
    }

    if (!formData.tool_type) {
      setError('יש לבחור סוג כלי');
      setLoading(false);
      return;
    }
    
    if (!workDaysNumber || workDaysNumber < 1) {
      setError('יש להזין מספר ימי עבודה תקין');
      setLoading(false);
      return;
    }

    if (!quantityNumber || quantityNumber < 1) {
      setError('יש להזין כמות כלים תקינה');
      setLoading(false);
      return;
    }

    if (formData.allocation_method === 'supplier_selection' && !formData.supplier_id) {
      setError('יש לבחור ספק כאשר בוחרים "בחירת ספק"');
      setLoading(false);
      return;
    }

    if (formData.allocation_method === 'supplier_selection' && !formData.constraint_reason_id) {
      setError('יש לבחור סיבת אילוץ כאשר בוחרים ספק ידנית');
      setLoading(false);
      return;
    }

    if (selectedConstraintReason?.requires_additional_text && (!formData.constraint_explanation || formData.constraint_explanation.trim().length < 10)) {
      setError('יש לספק הסבר לסיבת האילוץ (לפחות 10 תווים)');
      setLoading(false);
      return;
    }

    // הערות חובה רק בסבב הוגן אם רוצים, או אופציונלי תמיד
    // כרגע: הערות אופציונליות בשני המקרים

    const workOrderData: WorkOrderCreate = {
      title: `דרישת כלי: ${formData.tool_type} (${quantityNumber} יחידות)`,
      description: formData.notes || `דרישת כלי ${formData.tool_type} לפרויקט ${selectedProject.name}`,
      project_id: selectedProject.id,
      supplier_id: formData.allocation_method === 'supplier_selection' && formData.supplier_id ? parseInt(formData.supplier_id.toString()) : undefined,
      equipment_type: formData.tool_type,
      work_start_date: formData.start_date,
      work_end_date: endDate,
      priority: 'medium',
      estimated_hours: totalHours,
      is_forced_selection: formData.allocation_method === 'supplier_selection',
      constraint_reason_id: formData.allocation_method === 'supplier_selection' && formData.constraint_reason_id
        ? parseInt(formData.constraint_reason_id.toString())
        : undefined,
      constraint_notes: formData.constraint_explanation?.trim() || undefined,
      requires_guard: formData.requires_guard,
      guard_days: formData.guard_days,
    };

    try {
      if (!navigator.onLine) {
        await saveOfflineWorkOrder(workOrderData);
        showToast('📋 ההזמנה נשמרה במכשיר — תועלה כשיחזור חיבור', 'info', 7000);
        showToast('⚠️ זכור: אחרי סנכרון תצטרך לשלוח את ההזמנה לספק ידנית', 'warning', 8000);
        setTimeout(() => navigate('/pending-sync'), 1800);
        return;
      }

      await workOrderService.createWorkOrder(workOrderData);
      showToast('דרישת הכלים נשלחה בהצלחה!', 'success');
      navigate('/order-coordination');
    } catch (error: any) {
      if (!error.response) {
        // Network error — save offline
        await saveOfflineWorkOrder(workOrderData);
        showToast('📋 ההזמנה נשמרה במכשיר — תועלה כשיחזור חיבור', 'info', 7000);
        showToast('⚠️ זכור: אחרי סנכרון תצטרך לשלוח את ההזמנה לספק ידנית', 'warning', 8000);
        setTimeout(() => navigate('/pending-sync'), 1800);
      } else {
        console.error('Error creating work order:', error);
        const errorMessage = error.response?.data?.detail || error.response?.data?.message || 'שגיאה ביצירת דרישת כלים';
        setError(errorMessage);
      }
    } finally {
      setLoading(false);
    }
  };

  if (loadingData) {
    return (
      <div className="min-h-screen bg-kkl-bg flex items-center justify-center" dir="rtl">
        <div className="flex items-center gap-3 bg-white p-6 rounded-xl shadow-sm">
          <div className="w-6 h-6 border-2 border-kkl-green border-t-transparent rounded-full animate-spin" />
          <span className="text-kkl-text">טוען נתונים...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-kkl-bg" dir="rtl">
      <div className="max-w-3xl mx-auto px-4 py-6">
        {/* Header */}
        <div className="mb-6">
          <button 
            onClick={() => projectCode ? navigate(`/projects/${projectCode}`) : navigate('/work-orders')}
            className="text-kkl-green hover:text-kkl-green-dark flex items-center gap-1 mb-4 text-sm"
          >
            <ArrowRight className="w-4 h-4" />
            חזרה
          </button>
          <h1 className="text-2xl font-bold text-kkl-text">דרישת כלים</h1>
          {selectedProject && (
            <p className="text-gray-500 mt-1">פרויקט: {selectedProject.name}</p>
          )}
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-6">
          
          {/* === בלוק 1: פרטי עבודה === */}
          <div className="bg-white rounded-xl shadow-sm border border-kkl-border p-5">
            <SectionTitle icon={<Calendar className="w-5 h-5" />}>
              פרטי עבודה
            </SectionTitle>

            {/* Project Selection — locked when coming from project page */}
            {projectCode ? (
              /* Locked project display */
              <div className="mb-4">
                <label className="block text-sm font-medium text-kkl-text mb-2">פרויקט</label>
                <div className="w-full pr-4 pl-4 py-2.5 border border-kkl-border bg-gray-50 rounded-lg text-sm text-kkl-text flex items-center justify-between">
                  <span className="font-medium">{selectedProject?.name || '...'}</span>
                  <span className="text-gray-400 text-xs">{selectedProject?.code || projectCode}</span>
                </div>
                <p className="text-xs text-gray-400 mt-1">הפרויקט נקבע אוטומטית מהסביבה הנוכחית</p>
              </div>
            ) : (
              <div className="mb-4">
                <label className="block text-sm font-medium text-kkl-text mb-2">
                  פרויקט *
                </label>
                <select
                  value={selectedProject?.id || ''}
                  onChange={(e) => {
                    const project = projects.find(p => p.id === parseInt(e.target.value));
                    setSelectedProject(project || null);
                  }}
                  required
                  className="w-full pr-4 pl-10 py-2.5 text-base border border-kkl-border rounded-lg focus:ring-2 focus:ring-kkl-green focus:border-transparent min-h-[44px]"
                >
                  <option value="">בחר פרויקט</option>
                  {projects.map(project => (
                    <option key={project.id} value={project.id}>
                      {project.name} ({project.code})
                    </option>
                  ))}
                </select>
              </div>
            )}

            {/* Budget Display */}
            {selectedProject && (selectedProject.allocated_budget || 0) > 0 && (
              <div className={`mb-4 p-3 rounded-lg border ${
                (selectedProject.spent_budget || 0) >= (selectedProject.allocated_budget || 0) 
                  ? 'bg-red-50 border-red-200' 
                  : 'bg-kkl-green-light border-kkl-green/20'
              }`}>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Info className="w-4 h-4 text-kkl-green" />
                    <span className="text-sm font-medium text-kkl-text">יתרה תקציבית:</span>
                  </div>
                  <div className="text-left">
                    <span className={`text-lg font-bold ${
                      (selectedProject.spent_budget || 0) >= (selectedProject.allocated_budget || 0) 
                        ? 'text-red-600' 
                        : 'text-kkl-green'
                    }`}>
                      ₪{((selectedProject.allocated_budget || 0) - (selectedProject.spent_budget || 0)).toLocaleString('he-IL')}
                    </span>
                    <span className="text-xs text-gray-500 block">
                      מתוך ₪{(selectedProject.allocated_budget || 0).toLocaleString('he-IL')}
                    </span>
                  </div>
                </div>
                {(selectedProject.spent_budget || 0) >= (selectedProject.allocated_budget || 0) && (
                  <div className="mt-2 flex items-center gap-2 text-sm text-red-600">
                    <AlertCircle className="w-4 h-4" />
                    <span>אין יתרה זמינה - נדרש אישור מנהל</span>
                  </div>
                )}
              </div>
            )}

            <div className="grid grid-cols-12 gap-4">
              {/* Start Date */}
              <div className="col-span-12 sm:col-span-4">
                <label className="block text-sm font-medium text-kkl-text mb-2">
                  תאריך התחלה
                </label>
                <input
                  type="date"
                  name="start_date"
                  value={formData.start_date}
                  onChange={handleChange}
                  required
                  className="w-full pr-4 pl-10 py-2.5 text-base border border-kkl-border rounded-lg focus:ring-2 focus:ring-kkl-green focus:border-transparent min-h-[44px]"
                />
              </div>

              {/* Work Days */}
              <div className="col-span-12 sm:col-span-4">
                <label className="block text-sm font-medium text-kkl-text mb-2">
                  מספר ימי עבודה
                </label>
                <input
                  type="number"
                  name="work_days"
                  value={formData.work_days}
                  onChange={handleChange}
                  required
                  min="1"
                  className="w-full pr-4 pl-10 py-2.5 text-base border border-kkl-border rounded-lg focus:ring-2 focus:ring-kkl-green focus:border-transparent min-h-[44px]"
                />
              </div>

              {/* Total Hours - Highlighted Box */}
              <div className="col-span-12 sm:col-span-4">
                <div className="bg-kkl-green-light border border-kkl-green/20 rounded-lg p-4 h-full flex flex-col justify-center">
                  <div className="flex items-center gap-2 text-sm text-kkl-green mb-1">
                    <Clock className="w-4 h-4" />
                    סה"כ שעות עבודה
                  </div>
                  <div className="text-2xl font-bold text-kkl-green">{totalHours} שעות</div>
                  {workDaysNumber && workDaysNumber > 0 ? (
                    <p className="text-xs text-gray-500 mt-1 leading-tight max-w-full break-words">
                      {totalHours} שעות ({BILLABLE_HOURS_PER_DAY} שעות נטו × {workDaysNumber} ימים)
                    </p>
                  ) : (
                    <p className="text-xs text-gray-500 mt-1 leading-tight max-w-full break-words">
                      מחושב לפי {BILLABLE_HOURS_PER_DAY} שעות עבודה נטו ביום
                    </p>
                  )}
                  {/* Guard cost inline */}
                  {formData.requires_guard && formData.guard_days > 0 && overnightGuardRate > 0 && (
                    <p className="text-xs text-indigo-600 mt-1 font-medium">
                      🌙 שמירה: {formData.guard_days} לילות × ₪{overnightGuardRate} = ₪{(formData.guard_days * overnightGuardRate).toLocaleString('he-IL')}
                    </p>
                  )}
                </div>
              </div>
            </div>
          </div>

          {/* === בלוק 2: הגדרת כלים === */}
          <div className="bg-white rounded-xl shadow-sm border border-kkl-border p-5">
            <SectionTitle icon={<Truck className="w-5 h-5" />}>
              הגדרת כלים
            </SectionTitle>

            <div className="grid grid-cols-12 gap-4">
              {/* Tool Type */}
              <div className="col-span-12 sm:col-span-6">
                <label className="block text-sm font-medium text-kkl-text mb-2">
                  סוג כלי *
                </label>
                <select
                  value={selectedCategoryId?.toString() || ''}
                  onChange={handleCategoryChange}
                  required
                  className="w-full pr-4 pl-10 py-2.5 text-base border border-kkl-border rounded-lg focus:ring-2 focus:ring-kkl-green focus:border-transparent min-h-[44px]"
                >
                  <option value="">בחר סוג כלי...</option>
                  {equipmentCategories.map((category) => (
                    <option key={category.id} value={category.id}>
                      {category.name}
                    </option>
                  ))}
                </select>
              </div>

              {/* Quantity */}
              <div className="col-span-12 sm:col-span-6">
                <label className="block text-sm font-medium text-kkl-text mb-2">
                  כמות כלים
                </label>
                <input
                  type="number"
                  name="quantity"
                  value={formData.quantity}
                  onChange={handleChange}
                  required
                  min="1"
                  max="5"
                  className="w-full pr-4 pl-10 py-2.5 text-base border border-kkl-border rounded-lg focus:ring-2 focus:ring-kkl-green focus:border-transparent min-h-[44px]"
                />
              </div>
            </div>

            {/* Guard/Overnight toggle */}
            <div className="mt-3">
              <label className="flex items-center gap-3 cursor-pointer">
                <input
                  type="checkbox"
                  name="requires_guard"
                  checked={formData.requires_guard}
                  onChange={(e) => {
                    const checked = e.target.checked;
                    setFormData(prev => ({
                      ...prev,
                      requires_guard: checked,
                      // Default guard days = work_days - 1 (לילות שמירה)
                      guard_days: checked ? Math.max(0, Number(prev.work_days || 0) - 1) : 0
                    }));
                  }}
                  className="w-5 h-5 rounded border-kkl-border text-kkl-green focus:ring-kkl-green"
                />
                <div className="flex items-center gap-2">
                  <Moon className="w-4 h-4 text-indigo-500" />
                  <span className="text-sm text-kkl-text">כלי עם שמירה (לינת שטח)</span>
                </div>
              </label>
            </div>

            {/* Guard Days Input - Only shown when requires_guard is checked */}
            {formData.requires_guard && (
              <div className="mt-3 p-4 bg-indigo-50 border border-indigo-200 rounded-lg">
                <div className="flex items-start gap-3">
                  <Shield className="w-5 h-5 text-indigo-600 mt-0.5" />
                  <div className="flex-1">
                    <h4 className="text-sm font-medium text-indigo-900 mb-2">הגדרות שמירה</h4>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="block text-xs text-indigo-700 mb-1.5">מספר ימי שמירה</label>
                        <input
                          type="number"
                          name="guard_days"
                          value={formData.guard_days}
                          onChange={handleChange}
                          min="0"
                          max={formData.work_days}
                          className="w-full px-3 py-2 border border-indigo-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                        />
                      </div>
                      <div className="flex items-end">
                        <div className="bg-white border border-indigo-200 rounded-lg px-3 py-2 text-sm">
                          <span className="text-indigo-600 font-medium">{formData.guard_days} לילות</span>
                          <span className="text-gray-500 text-xs block">יחושב בניצול תקציבי</span>
                        </div>
                      </div>
                    </div>
                    <p className="text-xs text-indigo-600 mt-2 flex items-center gap-1">
                      <Info className="w-3 h-3" />
                      בדיווח השעות תוכל לסמן האם בוצעה שמירה בפועל
                    </p>

                    {/* ✅ תחזית עלות שמירה */}
                    {formData.guard_days > 0 && overnightGuardRate > 0 && (
                      <div className="mt-3 p-3 bg-indigo-100 border border-indigo-200 rounded-lg">
                        <p className="text-xs font-semibold text-indigo-800 mb-1">תחזית עלות שמירת לילה</p>
                        <div className="flex items-center justify-between">
                          <span className="text-sm text-indigo-700">
                            {formData.guard_days} לילות × ₪{overnightGuardRate.toLocaleString('he-IL')}
                          </span>
                          <span className="text-base font-bold text-indigo-900">
                            = ₪{(formData.guard_days * overnightGuardRate).toLocaleString('he-IL')}
                          </span>
                        </div>
                        <p className="text-xs text-indigo-500 mt-1">
                          תעריף לפי הגדרות מערכת (₪{overnightGuardRate}/לילה)
                        </p>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* === בלוק 3: שיטת הקצאת ספק === */}
          <div className="bg-white rounded-xl shadow-sm border border-kkl-border p-5">
            <SectionTitle icon={<Users className="w-5 h-5" />}>
              שיטת הקצאת ספק
            </SectionTitle>

            <div className="space-y-2">
              {/* Fair Rotation Option */}
              <label className={`flex items-center gap-2 p-3 rounded-lg border cursor-pointer transition-all ${
                formData.allocation_method === 'fair_rotation' 
                  ? 'border-kkl-green bg-kkl-green-light' 
                  : 'border-gray-200 hover:border-kkl-green/50'
              }`}>
                <input
                  type="radio"
                  name="allocation_method"
                  value="fair_rotation"
                  checked={formData.allocation_method === 'fair_rotation'}
                  onChange={handleChange}
                  className="w-4 h-4 text-kkl-green focus:ring-kkl-green"
                />
                <div className="flex-1">
                  <span className="text-sm font-medium text-kkl-text">סבב הוגן</span>
                  <span className="text-xs text-gray-500 mr-2">- המערכת תבחר ספק אוטומטית</span>
                </div>
              </label>

              {/* Supplier Selection Option */}
              <label className={`flex items-center gap-2 p-3 rounded-lg border cursor-pointer transition-all ${
                formData.allocation_method === 'supplier_selection' 
                  ? 'border-kkl-green bg-kkl-green-light' 
                  : 'border-gray-200 hover:border-kkl-green/50'
              }`}>
                <input
                  type="radio"
                  name="allocation_method"
                  value="supplier_selection"
                  checked={formData.allocation_method === 'supplier_selection'}
                  onChange={handleChange}
                  className="w-4 h-4 text-kkl-green focus:ring-kkl-green"
                />
                <div className="flex-1">
                  <span className="text-sm font-medium text-kkl-text">בחירת ספק</span>
                  <span className="text-xs text-gray-500 mr-2">- בחירה ידנית של ספק</span>
                </div>
              </label>
            </div>

            {/* Supplier Selection Fields - Only shown when supplier_selection is chosen */}
            {formData.allocation_method === 'supplier_selection' && (
              <div className="mt-4 p-4 bg-gray-50 rounded-lg border border-kkl-border space-y-4">
                <div className="flex items-start gap-2 text-sm text-gray-600 mb-3">
                  <Info className="w-4 h-4 mt-0.5 text-kkl-info flex-shrink-0" />
                  <span>נדרש לפי נהלי קק"ל כאשר סוטים מסבב הוגן</span>
                </div>

                <div className="grid grid-cols-12 gap-4">
                  {/* Supplier Select */}
                  <div className="col-span-12 sm:col-span-6">
                    <label className="block text-sm font-medium text-kkl-text mb-2">
                      בחר ספק *
                    </label>
                    <select
                      name="supplier_id"
                      value={formData.supplier_id}
                      onChange={handleChange}
                      required
                      className="w-full pr-4 pl-10 py-2.5 text-base border border-kkl-border rounded-lg focus:ring-2 focus:ring-kkl-green focus:border-transparent min-h-[44px]"
                    >
                      <option value="">בחר ספק...</option>
                      {filteredSuppliers.map(supplier => (
                        <option key={supplier.id} value={supplier.id}>
                          {supplier.name}
                        </option>
                      ))}
                    </select>
                    {selectedCategoryId && filteredSuppliers.length === 0 && (
                      <p className="text-xs text-kkl-warning mt-1">
                        אין ספקים זמינים לסוג כלי זה
                      </p>
                    )}
                  </div>

                  {/* Constraint Reason */}
                  <div className="col-span-12 sm:col-span-6">
                    <label className="block text-sm font-medium text-kkl-text mb-2">
                      סיבת אילוץ ספק *
                    </label>
                    <select
                      name="constraint_reason_id"
                      value={formData.constraint_reason_id}
                      onChange={handleChange}
                      required
                      className="w-full pr-4 pl-10 py-2.5 text-base border border-kkl-border rounded-lg focus:ring-2 focus:ring-kkl-green focus:border-transparent min-h-[44px]"
                    >
                      <option value="">בחר סיבת אילוץ...</option>
                      {constraintReasons.map(reason => (
                        <option key={reason.id} value={reason.id}>
                          {reason.name_he}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>

                {/* Constraint Explanation - Only if reason requires it */}
                {selectedConstraintReason?.requires_additional_text && (
                  <div>
                    <label className="block text-sm font-medium text-kkl-text mb-2">
                      הסבר סיבת האילוץ *
                    </label>
                    <textarea
                      name="constraint_explanation"
                      value={formData.constraint_explanation}
                      onChange={handleChange}
                      required
                      rows={2}
                      placeholder="נא לפרט את סיבת האילוץ..."
                      className="w-full px-4 py-2.5 border border-kkl-border rounded-lg focus:ring-2 focus:ring-kkl-green focus:border-transparent resize-none"
                    />
                  </div>
                )}
              </div>
            )}
          </div>

          {/* === בלוק 4: הערות נוספות (אופציונלי) === */}
          <div className="bg-white rounded-xl shadow-sm border border-kkl-border p-5">
            <SectionTitle icon={<FileText className="w-5 h-5" />}>
              הערות נוספות
            </SectionTitle>

            <textarea
              name="notes"
              value={formData.notes}
              onChange={handleChange}
              rows={3}
              placeholder="הערות נוספות (אופציונלי)"
              className="w-full px-4 py-3 border border-kkl-border rounded-lg focus:ring-2 focus:ring-kkl-green focus:border-transparent resize-none"
            />
          </div>

          {/* Error Message */}
          {error && (
            <div className="bg-red-50 border border-kkl-error/30 rounded-lg p-4 flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-kkl-error flex-shrink-0 mt-0.5" />
              <p className="text-kkl-error text-sm">{error}</p>
            </div>
          )}

          {/* === כפתורים === */}
          <div className="flex justify-end gap-3 pt-4 border-t border-kkl-border">
            <button
              type="button"
              onClick={() => projectCode ? navigate(`/projects/${projectCode}`) : navigate('/work-orders')}
              className="px-6 py-2.5 rounded-lg border border-kkl-border text-kkl-text hover:bg-gray-50 transition-colors font-medium"
            >
              ביטול
            </button>
            <button
              type="submit"
              disabled={loading}
              className="px-6 py-2.5 rounded-lg bg-kkl-green text-white hover:bg-kkl-green-dark disabled:opacity-50 transition-colors font-medium flex items-center gap-2"
            >
              {loading ? (
                <>
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  שולח...
                </>
              ) : (
                <>
                  <CheckCircle className="w-4 h-4" />
                  שלח דרישה
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default NewWorkOrder;
