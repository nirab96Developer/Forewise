
// src/pages/WorkOrders/EditWorkOrder.tsx
import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowRight } from 'lucide-react';
import workOrderService, { WorkOrder, WorkOrderUpdate } from '../../services/workOrderService';
import projectService from '../../services/projectService';
import supplierService from '../../services/supplierService';
import UnifiedLoader from '../../components/common/UnifiedLoader';

interface Project {
  id: number;
  name: string;
  code: string;
}

interface Supplier {
  id: number;
  name: string;
}

const EditWorkOrder: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [formData, setFormData] = useState<WorkOrderUpdate>({});
  const [workOrder, setWorkOrder] = useState<WorkOrder | null>(null);
  const [projects, setProjects] = useState<Project[]>([]);
  const [suppliers, setSuppliers] = useState<Supplier[]>([]);
  const [loading, setLoading] = useState(false);
  const [loadingData, setLoadingData] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (id) {
      loadData();
    }
  }, [id]);

  const loadData = async () => {
    try {
      setLoadingData(true);
      
      // Load work order
      const order = await workOrderService.getWorkOrderById(parseInt(id!));
      setWorkOrder(order);
      
      // Load projects
      const projectsResponse = await projectService.getProjects({});
      setProjects(projectsResponse.projects || []);
      
      // Load suppliers
      const suppliersResponse = await supplierService.getSuppliers({});
      setSuppliers(suppliersResponse.suppliers || []);
      
      // Set form data
      setFormData({
        title: order.title,
        description: order.description,
        project_id: order.project_id,
        supplier_id: order.supplier_id,
        equipment_type: order.equipment_type,
        work_start_date: order.work_start_date,
        work_end_date: order.work_end_date,
        priority: order.priority,
        estimated_hours: order.estimated_hours,
        hourly_rate: order.hourly_rate,
      });
    } catch (error: any) {
      console.error('Error loading data:', error);
      setError('שגיאה בטעינת נתונים');
    } finally {
      setLoadingData(false);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: name === 'project_id' || name === 'supplier_id'
        ? (value ? parseInt(value) : undefined)
        : name === 'estimated_hours' || name === 'hourly_rate'
        ? (value ? parseFloat(value) : undefined)
        : value
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      await workOrderService.updateWorkOrder(parseInt(id!), formData);
      
      if ((window as any).showToast) {
        (window as any).showToast('הזמנת העבודה עודכנה בהצלחה!', 'success');
      } else {
        alert('הזמנת העבודה עודכנה בהצלחה!');
      }
      
      navigate(`/work-orders/${id}`);
    } catch (error: any) {
      console.error('Error updating work order:', error);
      const errorMessage = error.response?.data?.detail || error.response?.data?.message || 'שגיאה בעדכון הזמנת עבודה';
      setError(errorMessage);
      
      if ((window as any).showToast) {
        (window as any).showToast(errorMessage, 'error');
      } else {
        alert(errorMessage);
      }
    } finally {
      setLoading(false);
    }
  };

  if (loadingData) return <UnifiedLoader size="full" />;

  if (error && !workOrder) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="text-xl text-red-600 mb-4">{error}</div>
          <button 
            onClick={() => loadData()}
            className="bg-fw-green text-white px-4 py-2 rounded-lg hover:bg-green-700"
          >
            נסה שוב
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-3xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center mb-4">
            <button 
              onClick={() => navigate(`/work-orders/${id}`)}
              className="text-fw-green hover:text-green-700 flex items-center"
            >
              <ArrowRight className="w-4 h-4 ml-1" />
              חזרה לפרטי הזמנה
            </button>
          </div>
          <h1 className="text-3xl font-bold text-gray-900">עריכת הזמנת עבודה</h1>
        </div>

        {/* Form */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Title */}
            <div>
              <label htmlFor="title" className="block text-sm font-medium text-gray-700 mb-2">
                כותרת *
              </label>
              <input
                type="text"
                id="title"
                name="title"
                value={formData.title || ''}
                onChange={handleChange}
                required
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-fw-green focus:border-transparent"
              />
            </div>

            {/* Project */}
            <div>
              <label htmlFor="project_id" className="block text-sm font-medium text-gray-700 mb-2">
                פרויקט *
              </label>
              <select
                id="project_id"
                name="project_id"
                value={formData.project_id || ''}
                onChange={handleChange}
                required
                className="w-full pr-3 pl-10 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-fw-green focus:border-transparent"
              >
                <option value="">בחר פרויקט</option>
                {projects.map(project => (
                  <option key={project.id} value={project.id}>
                    {project.name} ({project.code})
                  </option>
                ))}
              </select>
            </div>

            {/* Supplier */}
            <div>
              <label htmlFor="supplier_id" className="block text-sm font-medium text-gray-700 mb-2">
                ספק
              </label>
              <select
                id="supplier_id"
                name="supplier_id"
                value={formData.supplier_id || ''}
                onChange={handleChange}
                className="w-full pr-3 pl-10 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-fw-green focus:border-transparent"
              >
                <option value="">בחר ספק (אופציונלי)</option>
                {suppliers.map(supplier => (
                  <option key={supplier.id} value={supplier.id}>
                    {supplier.name}
                  </option>
                ))}
              </select>
            </div>

            {/* Equipment Type */}
            <div>
              <label htmlFor="equipment_type" className="block text-sm font-medium text-gray-700 mb-2">
                סוג ציוד *
              </label>
              <input
                type="text"
                id="equipment_type"
                name="equipment_type"
                value={formData.equipment_type || ''}
                onChange={handleChange}
                required
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-fw-green focus:border-transparent"
              />
            </div>

            {/* Date Range */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label htmlFor="work_start_date" className="block text-sm font-medium text-gray-700 mb-2">
                  תאריך התחלה *
                </label>
                <input
                  type="date"
                  id="work_start_date"
                  name="work_start_date"
                  value={formData.work_start_date || ''}
                  onChange={handleChange}
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-fw-green focus:border-transparent"
                />
              </div>
              <div>
                <label htmlFor="work_end_date" className="block text-sm font-medium text-gray-700 mb-2">
                  תאריך סיום *
                </label>
                <input
                  type="date"
                  id="work_end_date"
                  name="work_end_date"
                  value={formData.work_end_date || ''}
                  onChange={handleChange}
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-fw-green focus:border-transparent"
                />
              </div>
            </div>

            {/* Priority */}
            <div>
              <label htmlFor="priority" className="block text-sm font-medium text-gray-700 mb-2">
                עדיפות
              </label>
              <select
                id="priority"
                name="priority"
                value={formData.priority || 'medium'}
                onChange={handleChange}
                className="w-full pr-3 pl-10 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-fw-green focus:border-transparent"
              >
                <option value="low">נמוכה</option>
                <option value="medium">בינונית</option>
                <option value="high">גבוהה</option>
              </select>
            </div>

            {/* Estimated Hours */}
            <div>
              <label htmlFor="estimated_hours" className="block text-sm font-medium text-gray-700 mb-2">
                שעות משוערות
              </label>
              <input
                type="number"
                id="estimated_hours"
                name="estimated_hours"
                value={formData.estimated_hours || ''}
                onChange={handleChange}
                min="0"
                step="0.5"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-fw-green focus:border-transparent"
              />
            </div>

            {/* Hourly Rate */}
            <div>
              <label htmlFor="hourly_rate" className="block text-sm font-medium text-gray-700 mb-2">
                תעריף לשעה (ש"ח)
              </label>
              <input
                type="number"
                id="hourly_rate"
                name="hourly_rate"
                value={formData.hourly_rate || ''}
                onChange={handleChange}
                min="0"
                step="0.01"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-fw-green focus:border-transparent"
              />
            </div>

            {/* Description */}
            <div>
              <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-2">
                תיאור העבודה
              </label>
              <textarea
                id="description"
                name="description"
                value={formData.description || ''}
                onChange={handleChange}
                rows={4}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-fw-green focus:border-transparent"
              />
            </div>

            {/* Error Message */}
            {error && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                <p className="text-red-600 text-sm">{error}</p>
              </div>
            )}

            {/* Submit Button */}
            <div className="flex gap-4">
              <button
                type="button"
                onClick={() => navigate(`/work-orders/${id}`)}
                className="flex-1 bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded-lg"
              >
                ביטול
              </button>
              <button
                type="submit"
                disabled={loading}
                className="flex-1 bg-fw-green hover:bg-green-700 text-white px-4 py-2 rounded-lg disabled:opacity-50"
              >
                {loading ? 'מעדכן...' : 'עדכן'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default EditWorkOrder;


















