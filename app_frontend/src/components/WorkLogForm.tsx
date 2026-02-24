// src/components/WorkLogForm.tsx
// רכיב טופס לדיווח עבודה

import React, { useState, useEffect } from 'react';
import { Calendar, Clock, FileText, Save, X, Wrench } from 'lucide-react';
import workLogService, { WorkLogCreate } from '../services/workLogService';
import projectService from '../services/projectService';
import { getActivityTypes, ActivityType } from '../services/activityTypeService';

interface WorkLogFormProps {
  projectId?: number;
  onSuccess?: () => void;
  onCancel?: () => void;
}

const WorkLogForm: React.FC<WorkLogFormProps> = ({
  projectId,
  onSuccess,
  onCancel
}) => {
  const [formData, setFormData] = useState<WorkLogCreate>({
    project_id: projectId || 0,
    work_date: new Date().toISOString().split('T')[0],
    start_time: '06:30:00',
    end_time: '17:00:00',
    work_type: '',
    description: '',
    is_standard: false
  });

  const [projects, setProjects] = useState<any[]>([]);
  const [activityTypes, setActivityTypes] = useState<ActivityType[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadProjects();
    loadActivityTypes();
  }, []);

  const loadProjects = async () => {
    try {
      const data = await projectService.getProjects();
      setProjects(data.projects || []);
    } catch (err) {
      console.error('Error loading projects:', err);
    }
  };

  const loadActivityTypes = async () => {
    try {
      const data = await getActivityTypes();
      setActivityTypes(data);
    } catch (err) {
      console.error('Error loading activity types:', err);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: name === 'project_id' ? parseInt(value) : value
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      if (!formData.project_id) {
        setError('יש לבחור פרויקט');
        setLoading(false);
        return;
      }

      await workLogService.createWorkLog(formData);

      if (onSuccess) {
        onSuccess();
      }
    } catch (err: any) {
      console.error('Error creating work log:', err);
      setError(err.response?.data?.detail || 'שגיאה ביצירת דיווח עבודה');
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
          {error}
        </div>
      )}

      <div>
        <label htmlFor="project_id" className="block text-sm font-medium text-gray-700 mb-2">
          פרויקט *
        </label>
        <select
          id="project_id"
          name="project_id"
          value={formData.project_id}
          onChange={handleChange}
          required
          disabled={!!projectId}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-hillan-green focus:border-transparent"
        >
          <option value="">בחר פרויקט</option>
          {projects.map(project => (
            <option key={project.id} value={project.id}>
              {project.name}
            </option>
          ))}
        </select>
      </div>

      <div>
        <label htmlFor="work_date" className="block text-sm font-medium text-gray-700 mb-2">
          <Calendar className="inline w-4 h-4 mr-1" />
          תאריך *
        </label>
        <input
          type="date"
          id="work_date"
          name="work_date"
          value={formData.work_date}
          onChange={handleChange}
          required
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-hillan-green focus:border-transparent"
        />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label htmlFor="start_time" className="block text-sm font-medium text-gray-700 mb-2">
            <Clock className="inline w-4 h-4 mr-1" />
            שעת התחלה *
          </label>
          <input
            type="time"
            id="start_time"
            name="start_time"
            value={formData.start_time}
            onChange={handleChange}
            required
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-hillan-green focus:border-transparent"
          />
        </div>

        <div>
          <label htmlFor="end_time" className="block text-sm font-medium text-gray-700 mb-2">
            <Clock className="inline w-4 h-4 mr-1" />
            שעת סיום *
          </label>
          <input
            type="time"
            id="end_time"
            name="end_time"
            value={formData.end_time}
            onChange={handleChange}
            required
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-hillan-green focus:border-transparent"
          />
        </div>
      </div>

      <div>
        <label htmlFor="work_type" className="block text-sm font-medium text-gray-700 mb-2">
          <Wrench className="inline w-4 h-4 mr-1" />
          סוג פעולה *
        </label>
        <select
          id="work_type"
          name="work_type"
          value={formData.work_type}
          onChange={handleChange}
          required
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-kkl-green focus:border-transparent"
        >
          <option value="">בחר סוג פעולה</option>
          {activityTypes.map(type => (
            <option key={type.id} value={type.code}>
              {type.name}
            </option>
          ))}
        </select>
      </div>

      <div>
        <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-2">
          <FileText className="inline w-4 h-4 mr-1" />
          תיאור
        </label>
        <textarea
          id="description"
          name="description"
          value={formData.description}
          onChange={handleChange}
          rows={4}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-hillan-green focus:border-transparent"
        />
      </div>

      <div className="flex items-center">
        <input
          type="checkbox"
          id="is_standard"
          name="is_standard"
          checked={formData.is_standard}
          onChange={(e) => setFormData(prev => ({ ...prev, is_standard: e.target.checked }))}
          className="h-4 w-4 text-hillan-green focus:ring-hillan-green border-gray-300 rounded"
        />
        <label htmlFor="is_standard" className="mr-2 text-sm text-gray-700">
          דיווח תקן (10.5 שעות)
        </label>
      </div>

      <div className="flex gap-4">
        <button
          type="submit"
          disabled={loading}
          className="btn-primary flex-1 flex items-center justify-center gap-2"
        >
          <Save className="w-4 h-4" />
          {loading ? 'שומר...' : 'שמור'}
        </button>

        {onCancel && (
          <button
            type="button"
            onClick={onCancel}
            className="btn-secondary flex items-center justify-center gap-2"
          >
            <X className="w-4 h-4" />
            ביטול
          </button>
        )}
      </div>
    </form>
  );
};

export default WorkLogForm;













