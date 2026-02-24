// @ts-nocheck
/**
 * WorklogCreateEnhanced - טופס דיווח שעות משופר
 * כולל: סוג עבודה, סוג כלי, חישוב תעריף בזמן אמת
 */
import React, { useState, useEffect, useMemo } from 'react';
import {
  Truck, Building2, Calendar, Clock, DollarSign,
  Warehouse, FileText, CheckCircle, AlertCircle,
  Calculator, Info, Send
} from 'lucide-react';
import equipmentTypeService, { 
  EquipmentType, 
  ComputeCostResponse 
} from '../../services/equipmentTypeService';
import workLogService, { WorkLogCreate } from '../../services/workLogService';

// === TYPES ===
type WorkType = 'fieldwork' | 'storage' | 'general';

interface WorklogFormData {
  work_type: WorkType;
  project_id?: number;
  work_order_id?: number;
  equipment_type_id?: number;
  equipment_id?: number;
  supplier_id?: number;
  report_date: string;
  hours: number;
  days?: number;
  description: string;
}

interface Props {
  projectId?: number;
  workOrderId?: number;
  supplierId?: number;
  onSuccess?: (worklogId: number) => void;
  onCancel?: () => void;
}

// === WORK TYPE CONFIG ===
const WORK_TYPES: { value: WorkType; label: string; icon: React.ReactNode; color: string; description: string }[] = [
  {
    value: 'fieldwork',
    label: 'עבודה בשטח',
    icon: <Truck className="w-6 h-6" />,
    color: 'green',
    description: 'עבודה רגילה עם כלי מכני'
  },
  {
    value: 'storage',
    label: 'שמירה/אחסנה',
    icon: <Warehouse className="w-6 h-6" />,
    color: 'blue',
    description: 'שמירת כלי ללא עבודה פעילה'
  },
  {
    value: 'general',
    label: 'דיווח כללי',
    icon: <FileText className="w-6 h-6" />,
    color: 'gray',
    description: 'דיווח ללא כלי - דורש פירוט'
  }
];

const WorklogCreateEnhanced: React.FC<Props> = ({
  projectId,
  workOrderId,
  supplierId,
  onSuccess,
  onCancel
}) => {
  // Form Data
  const [formData, setFormData] = useState<WorklogFormData>({
    work_type: 'fieldwork',
    project_id: projectId,
    work_order_id: workOrderId,
    supplier_id: supplierId,
    report_date: new Date().toISOString().split('T')[0],
    hours: 9,
    days: 1,
    description: ''
  });

  // Equipment Types
  const [equipmentTypes, setEquipmentTypes] = useState<EquipmentType[]>([]);
  const [loadingTypes, setLoadingTypes] = useState(true);

  // Pricing
  const [pricing, setPricing] = useState<ComputeCostResponse | null>(null);
  const [loadingPricing, setLoadingPricing] = useState(false);

  // Submit state
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Load equipment types
  useEffect(() => {
    loadEquipmentTypes();
  }, []);

  // Compute pricing when relevant fields change
  useEffect(() => {
    if (formData.work_type && formData.hours > 0) {
      computePricing();
    }
  }, [formData.work_type, formData.equipment_type_id, formData.hours, formData.days]);

  const loadEquipmentTypes = async () => {
    try {
      const types = await equipmentTypeService.getEquipmentTypes();
      setEquipmentTypes(types);
    } catch (err) {
      console.error('Error loading equipment types:', err);
    } finally {
      setLoadingTypes(false);
    }
  };

  const computePricing = async () => {
    setLoadingPricing(true);
    try {
      const totalHours = formData.days 
        ? formData.days * (formData.hours || 9)
        : formData.hours;

      const result = await equipmentTypeService.computeCost({
        work_type: formData.work_type,
        hours: totalHours,
        equipment_type_id: formData.equipment_type_id,
        supplier_id: formData.supplier_id,
        project_id: formData.project_id
      });
      setPricing(result);
    } catch (err) {
      console.error('Error computing pricing:', err);
      setPricing(null);
    } finally {
      setLoadingPricing(false);
    }
  };

  // Get selected equipment type
  const selectedEquipmentType = useMemo(() => {
    return equipmentTypes.find(t => t.id === formData.equipment_type_id);
  }, [equipmentTypes, formData.equipment_type_id]);

  // Validation
  const validationErrors = useMemo(() => {
    const errors: string[] = [];

    if (formData.work_type === 'fieldwork') {
      if (!formData.equipment_type_id) {
        errors.push('עבודה בשטח: יש לבחור סוג כלי');
      }
      if (!formData.work_order_id && !formData.project_id) {
        errors.push('עבודה בשטח: יש לבחור הזמנת עבודה או פרויקט');
      }
    }

    if (formData.work_type === 'storage') {
      if (!formData.equipment_type_id) {
        errors.push('שמירה: יש לבחור סוג כלי');
      }
      if (!formData.project_id) {
        errors.push('שמירה: יש לבחור פרויקט');
      }
    }

    if (formData.work_type === 'general') {
      if (!formData.description.trim()) {
        errors.push('דיווח כללי: פירוט הכרחי');
      }
      if (!formData.project_id) {
        errors.push('דיווח כללי: יש לבחור פרויקט');
      }
    }

    if (formData.hours <= 0 && !formData.days) {
      errors.push('יש להזין מספר שעות תקין');
    }

    return errors;
  }, [formData]);

  const isValid = validationErrors.length === 0;

  // Handle submit
  const handleSubmit = async () => {
    if (!isValid) return;
    
    setSubmitting(true);
    setError(null);

    try {
      // Build worklog payload
      const worklogData: WorkLogCreate = {
        work_type: formData.work_type,
        project_id: formData.project_id,
        work_order_id: formData.work_type === 'fieldwork' ? formData.work_order_id : undefined,
        equipment_type_id: formData.equipment_type_id,
        equipment_id: formData.equipment_id,
        supplier_id: formData.supplier_id,
        report_date: formData.report_date,
        work_hours: totalHours.toString(),
        break_hours: '0',
        total_hours: totalHours.toString(),
        activity_description: formData.description || undefined,
        is_standard: true,  // Default to standard for now
        start_time: '06:30:00',
      };

      console.log('Creating worklog:', worklogData);
      const created = await workLogService.createWorkLog(worklogData);
      
      if (onSuccess) onSuccess(created.id);
    } catch (err: any) {
      console.error('Error creating worklog:', err);
      setError(err.response?.data?.detail || 'שגיאה בשליחת הדיווח');
    } finally {
      setSubmitting(false);
    }
  };

  // Calculate total hours
  const totalHours = formData.days 
    ? formData.days * (formData.hours || 9)
    : formData.hours;

  return (
    <div className="bg-white rounded-xl shadow-lg overflow-hidden" dir="rtl">
      {/* Header */}
      <div className="bg-gradient-to-r from-green-600 to-green-700 text-white p-6">
        <h2 className="text-xl font-bold flex items-center">
          <Clock className="w-6 h-6 ml-2" />
          דיווח שעות עבודה
        </h2>
        <p className="text-green-100 text-sm mt-1">
          בחר סוג עבודה, סוג כלי וכמות שעות
        </p>
      </div>

      <div className="p-6 space-y-6">
        {/* === STEP 1: Work Type === */}
        <div>
          <label className="block text-sm font-semibold text-gray-700 mb-3">
            1. סוג עבודה
          </label>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            {WORK_TYPES.map(type => (
              <button
                key={type.value}
                type="button"
                onClick={() => setFormData({ ...formData, work_type: type.value })}
                className={`p-4 rounded-xl border-2 transition-all text-right ${
                  formData.work_type === type.value
                    ? `border-${type.color}-500 bg-${type.color}-50 ring-2 ring-${type.color}-200`
                    : 'border-gray-200 hover:border-gray-300'
                }`}
                style={{
                  borderColor: formData.work_type === type.value 
                    ? type.color === 'green' ? '#22c55e' 
                      : type.color === 'blue' ? '#3b82f6' 
                      : '#6b7280'
                    : undefined,
                  backgroundColor: formData.work_type === type.value
                    ? type.color === 'green' ? '#f0fdf4'
                      : type.color === 'blue' ? '#eff6ff'
                      : '#f9fafb'
                    : undefined
                }}
              >
                <div className="flex items-center mb-2">
                  <span className={`p-2 rounded-lg ${
                    type.color === 'green' ? 'bg-green-100 text-green-600' :
                    type.color === 'blue' ? 'bg-blue-100 text-blue-600' :
                    'bg-gray-100 text-gray-600'
                  }`}>
                    {type.icon}
                  </span>
                  <span className="mr-3 font-semibold text-gray-800">{type.label}</span>
                  {formData.work_type === type.value && (
                    <CheckCircle className="w-5 h-5 text-green-500 mr-auto" />
                  )}
                </div>
                <p className="text-xs text-gray-500">{type.description}</p>
              </button>
            ))}
          </div>
        </div>

        {/* === STEP 2: Equipment Type (for fieldwork and storage) === */}
        {(formData.work_type === 'fieldwork' || formData.work_type === 'storage') && (
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-3">
              <Truck className="w-4 h-4 inline ml-1" />
              2. סוג כלי
            </label>
            {loadingTypes ? (
              <div className="animate-pulse h-12 bg-gray-200 rounded-lg" />
            ) : (
              <select
                value={formData.equipment_type_id || ''}
                onChange={(e) => setFormData({ 
                  ...formData, 
                  equipment_type_id: e.target.value ? parseInt(e.target.value) : undefined 
                })}
                className="w-full px-4 py-3 border-2 rounded-xl focus:ring-2 focus:ring-green-500 focus:border-green-500 text-lg"
              >
                <option value="">בחר סוג כלי...</option>
                {equipmentTypes.map(type => (
                  <option key={type.id} value={type.id}>
                    {type.name} - ₪{type.default_hourly_rate}/שעה
                  </option>
                ))}
              </select>
            )}

            {/* Selected type info */}
            {selectedEquipmentType && (
              <div className="mt-3 p-3 bg-green-50 rounded-lg border border-green-200">
                <div className="flex items-center justify-between">
                  <span className="text-green-800 font-medium">{selectedEquipmentType.name}</span>
                  <span className="text-green-600 font-bold">
                    ₪{selectedEquipmentType.default_hourly_rate}/שעה
                  </span>
                </div>
                {selectedEquipmentType.description && (
                  <p className="text-green-700 text-sm mt-1">{selectedEquipmentType.description}</p>
                )}
              </div>
            )}
          </div>
        )}

        {/* === STEP 3: Date & Hours === */}
        <div>
          <label className="block text-sm font-semibold text-gray-700 mb-3">
            <Calendar className="w-4 h-4 inline ml-1" />
            {formData.work_type === 'fieldwork' ? '3' : '2'}. תאריך ושעות
          </label>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Date */}
            <div>
              <label className="block text-xs text-gray-500 mb-1">תאריך</label>
              <input
                type="date"
                value={formData.report_date}
                onChange={(e) => setFormData({ ...formData, report_date: e.target.value })}
                className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-green-500"
              />
            </div>

            {/* Days */}
            <div>
              <label className="block text-xs text-gray-500 mb-1">ימים</label>
              <input
                type="number"
                min={1}
                max={31}
                value={formData.days || ''}
                onChange={(e) => setFormData({ 
                  ...formData, 
                  days: e.target.value ? parseInt(e.target.value) : undefined 
                })}
                placeholder="1"
                className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-green-500"
              />
            </div>

            {/* Hours per day */}
            <div>
              <label className="block text-xs text-gray-500 mb-1">שעות ליום</label>
              <input
                type="number"
                min={0.5}
                max={24}
                step={0.5}
                value={formData.hours}
                onChange={(e) => setFormData({ ...formData, hours: parseFloat(e.target.value) || 0 })}
                className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-green-500"
              />
            </div>
          </div>

          {/* Total hours badge */}
          <div className="mt-3 flex items-center">
            <span className="bg-gray-100 text-gray-800 px-4 py-2 rounded-lg font-mono text-lg">
              סה"כ: <strong>{totalHours}</strong> שעות
            </span>
            {formData.days && formData.days > 1 && (
              <span className="text-gray-500 text-sm mr-3">
                ({formData.days} ימים × {formData.hours} שעות)
              </span>
            )}
          </div>
        </div>

        {/* === Description (for general) === */}
        {formData.work_type === 'general' && (
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-2">
              <FileText className="w-4 h-4 inline ml-1" />
              פירוט העבודה *
            </label>
            <textarea
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              placeholder="תאר את העבודה שבוצעה..."
              rows={4}
              className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-green-500"
            />
          </div>
        )}

        {/* === PRICING DISPLAY === */}
        {pricing && (
          <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-xl p-5 border border-blue-200">
            <h3 className="font-semibold text-blue-800 mb-4 flex items-center">
              <Calculator className="w-5 h-5 ml-2" />
              חישוב עלות
            </h3>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
              <div className="bg-white rounded-lg p-3 shadow-sm">
                <div className="text-2xl font-bold text-gray-800">{pricing.hours}</div>
                <div className="text-xs text-gray-500">שעות</div>
              </div>
              <div className="bg-white rounded-lg p-3 shadow-sm">
                <div className="text-2xl font-bold text-blue-600">₪{pricing.hourly_rate}</div>
                <div className="text-xs text-gray-500">לשעה</div>
              </div>
              <div className="bg-white rounded-lg p-3 shadow-sm">
                <div className="text-2xl font-bold text-green-600">₪{pricing.total_cost.toLocaleString()}</div>
                <div className="text-xs text-gray-500">לפני מע"מ</div>
              </div>
              <div className="bg-white rounded-lg p-3 shadow-sm border-2 border-green-300">
                <div className="text-2xl font-bold text-green-700">₪{pricing.total_cost_with_vat.toLocaleString()}</div>
                <div className="text-xs text-gray-500">כולל מע"מ (17%)</div>
              </div>
            </div>

            {/* Rate source */}
            <div className="mt-4 flex items-center justify-center text-sm text-blue-600">
              <Info className="w-4 h-4 ml-1" />
              מקור תעריף: {pricing.rate_source_name || pricing.rate_source}
            </div>
          </div>
        )}

        {loadingPricing && (
          <div className="bg-gray-50 rounded-xl p-5 animate-pulse">
            <div className="h-20 bg-gray-200 rounded" />
          </div>
        )}

        {/* === VALIDATION ERRORS === */}
        {validationErrors.length > 0 && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <h4 className="text-red-800 font-medium mb-2 flex items-center">
              <AlertCircle className="w-4 h-4 ml-2" />
              שגיאות:
            </h4>
            <ul className="list-disc list-inside text-red-700 text-sm space-y-1">
              {validationErrors.map((err, i) => (
                <li key={i}>{err}</li>
              ))}
            </ul>
          </div>
        )}

        {/* === ERROR === */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
            {error}
          </div>
        )}

        {/* === ACTIONS === */}
        <div className="flex gap-3 pt-4 border-t">
          {onCancel && (
            <button
              type="button"
              onClick={onCancel}
              className="flex-1 py-3 px-6 bg-gray-100 text-gray-700 rounded-xl font-medium hover:bg-gray-200 transition-colors"
            >
              ביטול
            </button>
          )}
          
          <button
            type="button"
            onClick={handleSubmit}
            disabled={!isValid || submitting}
            className="flex-1 py-3 px-6 bg-green-600 text-white rounded-xl font-medium hover:bg-green-700 transition-colors flex items-center justify-center disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Send className="w-5 h-5 ml-2" />
            {submitting ? 'שולח...' : 'שלח לאישור'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default WorklogCreateEnhanced;

