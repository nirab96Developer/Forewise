
// Worklog Form - דיווח שעות תקן/לא תקן
import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams, useParams } from 'react-router-dom';
import { CheckCircle, XCircle, Calendar, Save, Building2, AlertCircle, Loader2, Plus, Trash2, Moon } from 'lucide-react';
import api from '../../services/api';
import { saveOfflineWorklog } from '../../utils/offlineStorage';
import { showToast } from '../../components/common/Toast';
import projectService from '../../services/projectService';

interface Project {
  id: number;
  name: string;
  code: string;
}

interface WorkOrder {
  id: number;
  equipment_type: string;
  status: string;
}

// סוגי פעילות לדיווח לא תקן
const ACTIVITY_TYPES = [
  { value: 'work', label: 'עבודה', percent: 100, color: 'bg-green-100 text-green-800' },
  { value: 'rest', label: 'מנוחה', percent: 0, color: 'bg-blue-100 text-blue-800' },
  { value: 'idle_0', label: 'בטלה 0%', percent: 0, color: 'bg-gray-100 text-gray-800' },
  { value: 'idle_50', label: 'בטלה 50%', percent: 50, color: 'bg-yellow-100 text-yellow-800' },
  { value: 'idle_100', label: 'בטלה 100%', percent: 100, color: 'bg-orange-100 text-orange-800' },
  { value: 'equipment_change', label: 'החלפת כלים 50%', percent: 50, color: 'bg-purple-100 text-purple-800' },
  { value: 'travel_50', label: 'נסיעות 50%', percent: 50, color: 'bg-indigo-100 text-indigo-800' },
  { value: 'travel_100', label: 'נסיעות 100%', percent: 100, color: 'bg-indigo-100 text-indigo-800' },
];

interface TimeSegment {
  id: number;
  type: string;
  start_time: string;
  end_time: string;
  notes: string;
}

const WorklogFormUnified: React.FC = () => {
  const navigate = useNavigate();
  const { code: urlProjectCode } = useParams<{ code: string }>();
  const [searchParams] = useSearchParams();
  const projectIdParam = searchParams.get('project_id');
  const equipmentIdParam = searchParams.get('equipment_id');
  const workOrderIdParam = searchParams.get('work_order_id');
  const projectCodeParam = urlProjectCode || searchParams.get('project_code');
  
  const [isNonStandard, setIsNonStandard] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  
  const [projects, setProjects] = useState<Project[]>([]);
  const [_workOrders, setWorkOrders] = useState<WorkOrder[]>([]);
  const [selectedProject, setSelectedProject] = useState<Project | null>(null);
  const [scannedEquipment, setScannedEquipment] = useState<{id: number; code: string; name: string} | null>(null);
  
  // Segments for non-standard reports
  const [segments, setSegments] = useState<TimeSegment[]>([
    { id: 1, type: 'work', start_time: '06:30', end_time: '12:00', notes: '' },
  ]);
  
  const [formData, setFormData] = useState({
    project_id: projectIdParam ? parseInt(projectIdParam) : 0,
    work_order_id: workOrderIdParam ? parseInt(workOrderIdParam) : null as number | null,
    equipment_id: equipmentIdParam ? parseInt(equipmentIdParam) : null as number | null,
    work_date: new Date().toISOString().split('T')[0],
    activity: '',
    description: '',
    notes: '',
    includes_guard: false,  // האם כולל שמירת כלים
  });

  // Load equipment if scanned
  useEffect(() => {
    if (!equipmentIdParam) return;
    
    const loadEquipment = async () => {
      try {
        const response = await api.get(`/equipment/${equipmentIdParam}`);
        if (response.data) {
          setScannedEquipment({
            id: response.data.id,
            code: response.data.code || response.data.license_plate,
            name: response.data.name || response.data.equipment_type || 'ציוד'
          });
        }
      } catch (err) {
        console.error('Error loading equipment:', err);
      }
    };
    loadEquipment();
  }, [equipmentIdParam]);

  // Load work order if provided
  useEffect(() => {
    if (!workOrderIdParam) return;
    
    const loadWorkOrder = async () => {
      try {
        const response = await api.get(`/work-orders/${workOrderIdParam}`);
        if (response.data?.project_id) {
          setFormData(prev => ({ ...prev, project_id: response.data.project_id }));
        }
      } catch (err) {
        console.error('Error loading work order:', err);
      }
    };
    loadWorkOrder();
  }, [workOrderIdParam]);

  // Load projects
  useEffect(() => {
    const loadProjects = async () => {
      try {
        const response = await projectService.getProjects({});
        const projectsList = response?.projects || response || [];
        setProjects(projectsList);
        
        if (projectCodeParam && projectsList.length > 0) {
          const project = projectsList.find((p: Project) => p.code === projectCodeParam);
          if (project) {
            setSelectedProject(project);
            setFormData(prev => ({ ...prev, project_id: project.id }));
          }
        }
        
        if (projectIdParam && projectsList.length > 0) {
          const project = projectsList.find((p: Project) => p.id === parseInt(projectIdParam));
          if (project) setSelectedProject(project);
        }
      } catch (err) {
        console.error('Error loading projects:', err);
      }
    };
    loadProjects();
  }, [projectIdParam, projectCodeParam]);

  // Load work orders when project selected
  useEffect(() => {
    if (!selectedProject) {
      setWorkOrders([]);
      return;
    }
    
    const loadWorkOrders = async () => {
      try {
        const response = await api.get('/work-orders', {
          params: { project_id: selectedProject.id, status: 'active' }
        });
        setWorkOrders(response.data?.items || response.data || []);
      } catch (err) {
        setWorkOrders([]);
      }
    };
    loadWorkOrders();
  }, [selectedProject]);

  const handleProjectChange = (projectId: number) => {
    const project = projects.find(p => p.id === projectId);
    setSelectedProject(project || null);
    setFormData(prev => ({ ...prev, project_id: projectId, work_order_id: null }));
  };

  // Add segment
  const addSegment = () => {
    const lastSegment = segments[segments.length - 1];
    const newSegment: TimeSegment = {
      id: Date.now(),
      type: 'work',
      start_time: lastSegment?.end_time || '06:30',
      end_time: '17:00',
      notes: ''
    };
    setSegments([...segments, newSegment]);
  };

  // Remove segment
  const removeSegment = (id: number) => {
    if (segments.length > 1) {
      setSegments(segments.filter(s => s.id !== id));
    }
  };

  // Update segment
  const updateSegment = (id: number, field: keyof TimeSegment, value: string) => {
    setSegments(segments.map(s => 
      s.id === id ? { ...s, [field]: value } : s
    ));
  };

  // Calculate hours for a segment
  const calculateSegmentHours = (start: string, end: string): number => {
    const startDate = new Date(`2000-01-01T${start}`);
    const endDate = new Date(`2000-01-01T${end}`);
    return Math.max(0, (endDate.getTime() - startDate.getTime()) / (1000 * 60 * 60));
  };

  // Calculate totals
  const calculateTotals = () => {
    if (!isNonStandard) {
      // תקן: קבוע - 9 שעות עבודה נטו + 1.5 שעות מנוחה = 10.5 שעות משמרת
      return {
        totalPresence: 10.5,
        totalBillable: 9,
        restHours: 1.5
      };
    }

    let totalPresence = 0;
    let totalBillable = 0;
    let restHours = 0;

    segments.forEach(seg => {
      const hours = calculateSegmentHours(seg.start_time, seg.end_time);
      totalPresence += hours;
      
      const actType = ACTIVITY_TYPES.find(a => a.value === seg.type);
      if (actType) {
        totalBillable += hours * (actType.percent / 100);
        if (seg.type === 'rest') {
          restHours += hours;
        }
      }
    });

    return { totalPresence, totalBillable, restHours };
  };

  const totals = calculateTotals();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!formData.project_id) {
      setError('יש לבחור פרויקט');
      return;
    }
    if (!formData.activity) {
      setError('יש לבחור פעילות — שדה חובה בשני סוגי הדיווח');
      return;
    }
    
    setLoading(true);
    setError(null);
    
    const payload = {
      project_id: formData.project_id,
      work_order_id: formData.work_order_id,
      equipment_id: formData.equipment_id,
      work_date: formData.work_date,
      is_standard: !isNonStandard,
      total_hours: totals.totalPresence,
      billable_hours: totals.totalBillable,
      break_hours: totals.restHours,
      activity_type: formData.activity,
      description: formData.description,
      notes: formData.notes,
      equipment_scanned: !!equipmentIdParam,
      segments: isNonStandard ? segments.map(s => ({
        type: s.type,
        start_time: s.start_time,
        end_time: s.end_time,
        hours: calculateSegmentHours(s.start_time, s.end_time),
        notes: s.notes
      })) : undefined
    };

    try {
      if (!navigator.onLine) {
        await saveOfflineWorklog(payload);
        showToast('✅ הדיווח נשמר במכשיר — יועלה כשיחזור חיבור', 'success', 6000);
        setTimeout(() => navigate('/projects'), 1500);
        return;
      }

      await api.post('/worklogs', payload);
      setSuccess(true);
      
      setTimeout(() => {
        if (selectedProject) {
          navigate(`/projects/${selectedProject.code}/workspace?tab=worklogs`);
        } else {
          navigate('/projects');
        }
      }, 1500);
      
    } catch (err: any) {
      // Network error — save offline
      if (!err.response) {
        await saveOfflineWorklog(payload);
        showToast('✅ הדיווח נשמר במכשיר — יועלה כשיחזור חיבור', 'success', 6000);
        setTimeout(() => navigate('/projects'), 1500);
      } else {
        console.error('Error submitting worklog:', err);
        setError(err.response?.data?.detail || 'שגיאה בשמירת הדיווח');
      }
    } finally {
      setLoading(false);
    }
  };

  if (success) {
    return (
      <div className="min-h-screen bg-gray-50 pt-6 pb-8 px-4  flex items-center justify-center" dir="rtl">
        <div className="text-center bg-white rounded-xl shadow-lg p-8 max-w-md">
          <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <CheckCircle className="w-8 h-8 text-green-600" />
          </div>
          <h2 className="text-xl font-bold text-gray-900 mb-2">הדיווח נשמר בהצלחה!</h2>
          <p className="text-gray-600">מעביר אותך בחזרה...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 pt-6 pb-8 px-4 " dir="rtl">
      <div className="max-w-3xl mx-auto">
        <h1 className="text-2xl font-bold text-gray-900 mb-6">דיווח שעות</h1>
        
        <form onSubmit={handleSubmit} className="bg-white rounded-xl shadow-sm p-6 space-y-5">
          
          {/* Error Message */}
          {error && (
            <div className="flex items-center gap-2 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
              <AlertCircle className="w-4 h-4 flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}
          
          {/* Scanned Equipment Info */}
          {scannedEquipment && (
            <div className="flex items-center gap-3 p-3 bg-green-50 border border-green-200 rounded-lg">
              <div className="w-10 h-10 bg-green-600 rounded-lg flex items-center justify-center">
                <CheckCircle className="w-5 h-5 text-white" />
              </div>
              <div className="flex-1">
                <div className="text-xs text-green-700">ציוד נסרק</div>
                <div className="font-semibold text-green-800">{scannedEquipment.name}</div>
                <div className="text-xs text-green-600">קוד: {scannedEquipment.code}</div>
              </div>
            </div>
          )}
          
          {/* Project Selection — locked when project_id/code comes from URL */}
          <div className="border border-gray-200 rounded-lg p-4">
            <label className="block text-sm font-medium text-gray-700 mb-2 flex items-center gap-1">
              <Building2 className="w-4 h-4" />
              פרויקט
            </label>
            {(projectIdParam || projectCodeParam) ? (
              /* Locked display when project comes from URL */
              <div>
                <div className="w-full p-2.5 border border-gray-200 bg-gray-50 rounded-lg text-sm flex items-center justify-between">
                  <span className="font-medium text-gray-800">
                    {projects.find(p => p.id === formData.project_id)?.name || '...'}
                  </span>
                  <span className="text-gray-400 text-xs">
                    {projects.find(p => p.id === formData.project_id)?.code || projectCodeParam}
                  </span>
                </div>
                <p className="text-xs text-gray-400 mt-1">הפרויקט נקבע אוטומטית</p>
              </div>
            ) : (
              <select
                value={formData.project_id || ''}
                onChange={(e) => handleProjectChange(parseInt(e.target.value))}
                className="w-full p-2.5 border border-gray-300 rounded-lg focus:border-green-500 focus:ring-1 focus:ring-green-200 text-sm"
                required
              >
                <option value="">בחר פרויקט</option>
                {projects.map(project => (
                  <option key={project.id} value={project.id}>
                    {project.name} ({project.code})
                  </option>
                ))}
              </select>
            )}
          </div>
          
          {/* תקן / לא תקן Toggle */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">סוג הדיווח</label>
            <div className="flex gap-2">
              <button
                type="button"
                onClick={() => setIsNonStandard(false)}
                className={`flex-1 flex items-center justify-center gap-1.5 py-2.5 px-3 rounded-lg text-sm font-medium transition-all ${
                  !isNonStandard
                    ? 'bg-green-600 text-white'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
              >
                <CheckCircle className="w-4 h-4" />
                תקן
              </button>
              <button
                type="button"
                onClick={() => setIsNonStandard(true)}
                className={`flex-1 flex items-center justify-center gap-1.5 py-2.5 px-3 rounded-lg text-sm font-medium transition-all ${
                  isNonStandard
                    ? 'bg-orange-500 text-white'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
              >
                <XCircle className="w-4 h-4" />
                לא תקן
              </button>
            </div>
          </div>

          {/* Date & Activity */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">
                <Calendar className="w-3.5 h-3.5 inline ml-1" />
                תאריך
              </label>
              <input
                type="date"
                value={formData.work_date}
                onChange={(e) => setFormData({ ...formData, work_date: e.target.value })}
                className="w-full p-2.5 border border-gray-300 rounded-lg text-sm"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">פעילות</label>
              <select
                value={formData.activity}
                onChange={(e) => setFormData({ ...formData, activity: e.target.value })}
                className="w-full p-2.5 border border-gray-300 rounded-lg text-sm"
                required
              >
                <option value="">בחר פעילות</option>
                <option value="planting">נטיעה</option>
                <option value="clearing">ניקוי</option>
                <option value="maintenance">תחזוקה</option>
                <option value="pruning">גיזום</option>
                <option value="transport">הסעה</option>
                <option value="supervision">פיקוח</option>
                <option value="other">אחר</option>
              </select>
            </div>
          </div>

          {/* תקן - Fixed Template Display */}
          {!isNonStandard && (
            <div className="p-4 bg-green-50 rounded-lg border border-green-200">
              <div className="text-center mb-3">
                <div className="text-sm text-green-700">דיווח תקן</div>
                <div className="text-2xl font-bold text-green-800">10.5 שעות</div>
                <div className="text-xs text-green-600">9 שעות עבודה נטו + 1.5 שעות מנוחה = 10.5 שעות משמרת</div>
              </div>
              <div className="grid grid-cols-3 gap-2 text-center text-sm">
                <div className="bg-white rounded-lg p-2">
                  <div className="text-xs text-gray-500">התחלה</div>
                  <div className="font-semibold">06:30</div>
                </div>
                <div className="bg-white rounded-lg p-2">
                  <div className="text-xs text-gray-500">מנוחה</div>
                  <div className="font-semibold">12:00-13:30</div>
                </div>
                <div className="bg-white rounded-lg p-2">
                  <div className="text-xs text-gray-500">סיום</div>
                  <div className="font-semibold">17:00</div>
                </div>
              </div>
            </div>
          )}

          {/* לא תקן - Segments */}
          {isNonStandard && (
            <div className="p-4 bg-orange-50 rounded-lg border border-orange-200 space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-orange-800">פירוט שעות</span>
                <button
                  type="button"
                  onClick={addSegment}
                  className="flex items-center gap-1 text-xs bg-orange-500 text-white px-2 py-1 rounded hover:bg-orange-600"
                >
                  <Plus className="w-3 h-3" />
                  הוסף שורה
                </button>
              </div>
              
              {segments.map((segment, idx) => (
                <div key={segment.id} className="bg-white rounded-lg p-3 border border-orange-200">
                  <div className="flex items-center gap-2 mb-2">
                    <span className="text-xs text-gray-500">#{idx + 1}</span>
                    {segments.length > 1 && (
                      <button
                        type="button"
                        onClick={() => removeSegment(segment.id)}
                        className="mr-auto text-red-400 hover:text-red-600"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    )}
                  </div>
                  
                  <div className="grid grid-cols-4 gap-2">
                    <div className="col-span-2">
                      <label className="block text-xs text-gray-500 mb-1.5">סוג פעילות</label>
                      <select
                        value={segment.type}
                        onChange={(e) => updateSegment(segment.id, 'type', e.target.value)}
                        className="w-full p-2 border border-gray-200 rounded text-sm"
                      >
                        {ACTIVITY_TYPES.map(type => (
                          <option key={type.value} value={type.value}>
                            {type.label}
                          </option>
                        ))}
                      </select>
                    </div>
                    <div>
                      <label className="block text-xs text-gray-500 mb-1.5">התחלה</label>
                      <input
                        type="time"
                        value={segment.start_time}
                        onChange={(e) => updateSegment(segment.id, 'start_time', e.target.value)}
                        className="w-full p-2 border border-gray-200 rounded text-sm"
                      />
                    </div>
                    <div>
                      <label className="block text-xs text-gray-500 mb-1.5">סיום</label>
                      <input
                        type="time"
                        value={segment.end_time}
                        onChange={(e) => updateSegment(segment.id, 'end_time', e.target.value)}
                        className="w-full p-2 border border-gray-200 rounded text-sm"
                      />
                    </div>
                  </div>
                  
                  <div className="mt-2 flex items-center justify-between text-xs">
                    <span className={`px-2 py-0.5 rounded ${ACTIVITY_TYPES.find(t => t.value === segment.type)?.color || 'bg-gray-100'}`}>
                      {ACTIVITY_TYPES.find(t => t.value === segment.type)?.label}
                    </span>
                    <span className="text-gray-600">
                      {calculateSegmentHours(segment.start_time, segment.end_time).toFixed(1)} שעות
                    </span>
                  </div>
                </div>
              ))}
              
              {/* Totals */}
              <div className="bg-orange-100 rounded-lg p-3 grid grid-cols-3 gap-2 text-center">
                <div>
                  <div className="text-xs text-orange-600">נוכחות</div>
                  <div className="font-bold text-orange-800">{totals.totalPresence.toFixed(1)}</div>
                </div>
                <div>
                  <div className="text-xs text-orange-600">לתשלום</div>
                  <div className="font-bold text-orange-800">{totals.totalBillable.toFixed(1)}</div>
                </div>
                <div>
                  <div className="text-xs text-orange-600">מנוחה</div>
                  <div className="font-bold text-orange-800">{totals.restHours.toFixed(1)}</div>
                </div>
              </div>
            </div>
          )}

          {/* Notes */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">הערות (אופציונלי)</label>
            <textarea
              value={formData.notes}
              onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
              placeholder="הערות נוספות..."
              className="w-full p-2.5 border border-gray-300 rounded-lg text-sm min-h-[80px]"
            />
          </div>

          {/* Guard Checkbox */}
          <div className="p-4 bg-indigo-50 border border-indigo-200 rounded-lg">
            <label className="flex items-center gap-3 cursor-pointer">
              <input
                type="checkbox"
                checked={formData.includes_guard}
                onChange={(e) => setFormData({ ...formData, includes_guard: e.target.checked })}
                className="w-5 h-5 rounded border-indigo-300 text-indigo-600 focus:ring-indigo-500"
              />
              <div className="flex items-center gap-2">
                <Moon className="w-5 h-5 text-indigo-600" />
                <div>
                  <span className="text-sm font-medium text-indigo-900">בוצעה שמירת כלים</span>
                  <p className="text-xs text-indigo-600">סמן אם הייתה לינת שטח/שמירה בתאריך זה</p>
                </div>
              </div>
            </label>
          </div>

          {/* Submit Button */}
          <div className="flex gap-3 pt-2">
            <button
              type="button"
              onClick={() => navigate(-1)}
              className="flex-1 py-2.5 px-4 border border-gray-300 text-gray-700 rounded-lg text-sm font-medium hover:bg-gray-50"
            >
              ביטול
            </button>
            <button
              type="submit"
              disabled={loading || !formData.project_id}
              className="flex-1 flex items-center justify-center gap-2 py-2.5 px-4 bg-green-600 text-white rounded-lg text-sm font-medium hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Save className="w-4 h-4" />
              )}
              שמור דיווח
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default WorklogFormUnified;
