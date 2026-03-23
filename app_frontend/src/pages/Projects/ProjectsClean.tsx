
// src/pages/Projects/ProjectsClean.tsx
// רשימת פרויקטים עם עיצוב נקי לבן וירוק

import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { 
  Plus, 
  Search, 
  Calendar, 
  MapPin, 
  User, 
  ChevronRight,
  Briefcase
} from 'lucide-react';
import projectService, { Project, ProjectFilters } from '../../services/projectService';
import api from '../../services/api';

const ProjectsClean: React.FC = () => {
  const navigate = useNavigate();
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterStatus, setFilterStatus] = useState('all');
  // Auto-enable "my projects only" for WORK_MANAGER — they should only see their assigned projects
  const _userRole = (() => { try { return JSON.parse(localStorage.getItem('user') || '{}').role || ''; } catch { return ''; } })();
  const [myProjectsOnly, setMyProjectsOnly] = useState(_userRole === 'WORK_MANAGER' || _userRole === 'FIELD_WORKER');
  const [error, setError] = useState<string | null>(null);

  // AbortController ref — cancels in-flight request when a newer one starts
  const abortRef = React.useRef<AbortController | null>(null);

  const fetchProjects = async () => {
    // Cancel any previous in-flight request
    abortRef.current?.abort();
    abortRef.current = new AbortController();
    const signal = abortRef.current.signal;

    setLoading(true);
    setError(null);
    try {
      const filters: ProjectFilters = {
        search: searchTerm || undefined,
        status: filterStatus !== 'all' ? filterStatus : undefined,
        my_projects: myProjectsOnly || undefined,
        page: 1,
        per_page: 50
      };
      const response = await projectService.getProjects(filters, signal);
      if (signal.aborted) return; // Stale response — discard
      setProjects(response.projects);
    } catch (error: any) {
      if (error?.name === 'AbortError' || error?.code === 'ERR_CANCELED') return;
      console.error('Error fetching projects:', error);
      setError('שגיאה בטעינת הפרויקטים. אנא נסה שוב.');
    } finally {
      if (!signal.aborted) setLoading(false);
    }
  };
  // Single effect: fetch immediately on mount, debounce on filter changes
  const isMountRef = React.useRef(true);
  useEffect(() => {
    if (isMountRef.current) {
      // First render — fetch immediately, no debounce
      isMountRef.current = false;
      fetchProjects();
      return;
    }
    // Filter changed — debounce 500ms
    const timeoutId = setTimeout(() => {
      fetchProjects();
    }, 500);
    return () => clearTimeout(timeoutId);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchTerm, filterStatus, myProjectsOnly]);

  // מיפוי סטטוסים בעברית + צבעים
  // A project is "בתכנון" if it's active but has no budget allocated
  const getEffectiveStatus = (project: Project): string => {
    const base = (project.status || 'active').toLowerCase();
    if (base === 'active') {
      const budget = (project as any).allocated_budget ?? (project as any).total_budget ?? 0;
      if (!budget || Number(budget) === 0) return 'planning';
    }
    return base;
  };

  const getStatusConfig = (project: Project) => {
    const effective = getEffectiveStatus(project);
    const configs: Record<string, { text: string; bg: string; textColor: string }> = {
      'active':    { text: 'פעיל',     bg: 'bg-green-100',  textColor: 'text-green-800'  },
      'planning':  { text: 'בתכנון',   bg: 'bg-yellow-100', textColor: 'text-yellow-800' },
      'completed': { text: 'הושלם',    bg: 'bg-blue-100',   textColor: 'text-blue-800'   },
      'on_hold':   { text: 'מושהה',    bg: 'bg-orange-100', textColor: 'text-orange-800' },
      'cancelled': { text: 'בוטל',     bg: 'bg-red-100',    textColor: 'text-red-800'    },
      'planned':   { text: 'בתכנון',   bg: 'bg-yellow-100', textColor: 'text-yellow-800' },
    };
    return configs[effective] || { text: 'פעיל', bg: 'bg-green-100', textColor: 'text-green-800' };
  };

  const filteredProjects = projects.filter(project => {
    const matchesSearch = !searchTerm || 
      project.name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      project.code?.toLowerCase().includes(searchTerm.toLowerCase());
    
    const effective = getEffectiveStatus(project);
    const matchesStatus = filterStatus === 'all' ||
      (filterStatus === 'active'    && effective === 'active') ||
      (filterStatus === 'planning'  && effective === 'planning') ||
      (filterStatus === 'completed' && effective === 'completed');
    
    return matchesSearch && matchesStatus;
  });

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center p-4">
        <div className="bg-red-50 border border-red-200 rounded-lg p-6 max-w-md w-full text-center">
          <p className="text-red-800">{error}</p>
          <button
            onClick={fetchProjects}
            className="mt-4 px-6 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
          >
            נסה שוב
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8 flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">פרויקטים</h1>
            <p className="text-gray-600 mt-2">ניהול וסקירת פרויקטים פעילים</p>
          </div>
          <button
            onClick={async () => {
              try {
                const res = await api.get('/reports/export/excel?type=projects', { responseType: 'blob' });
                const url = window.URL.createObjectURL(new Blob([res.data]));
                const a = document.createElement('a');
                a.href = url;
                a.download = `projects_${new Date().toISOString().slice(0,10)}.xlsx`;
                a.click();
                window.URL.revokeObjectURL(url);
              } catch {
                (window as any).showToast?.('שגיאה בייצוא Excel', 'error');
              }
            }}
            className="inline-flex items-center gap-2 rounded-lg border border-green-200 bg-green-50 px-4 py-2 text-sm font-medium text-green-700 hover:bg-green-100 transition-colors"
          >
            📊 ייצוא Excel
          </button>
        </div>

        {/* Search and Filter Bar */}
        <div className="bg-white rounded-lg border border-gray-200 p-6 mb-8">
          <div className="flex flex-col md:flex-row gap-4">
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
                <input
                  type="text"
                  placeholder="חיפוש לפי שם או קוד פרויקט..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full pr-10 pl-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500 transition-colors"
                />
              </div>
            </div>
            
            <div className="flex gap-3 items-center">
              {_userRole !== 'WORK_MANAGER' && _userRole !== 'FIELD_WORKER' && (
                <button
                  onClick={() => setMyProjectsOnly(!myProjectsOnly)}
                  className={`flex items-center gap-2 px-4 py-2 rounded-lg border font-medium transition-colors ${
                    myProjectsOnly 
                      ? 'bg-green-100 border-green-400 text-green-700' 
                      : 'bg-white border-gray-200 text-gray-600 hover:bg-gray-50'
                  }`}
                >
                  <User className="w-4 h-4" />
                  שלי
                </button>
              )}

              {_userRole !== 'WORK_MANAGER' && _userRole !== 'FIELD_WORKER' && (
                <select
                  value={filterStatus}
                  onChange={(e) => setFilterStatus(e.target.value)}
                  className="pr-4 pl-10 py-2 bg-white border border-gray-200 text-gray-700 rounded-lg hover:bg-gray-50 focus:ring-2 focus:ring-green-500 focus:border-green-500 transition-colors"
                >
                <option value="all">כל הפרויקטים</option>
                <option value="active">פעילים (מתוקצבים)</option>
                <option value="planning">בתכנון (לא מתוקצב)</option>
                <option value="completed">הושלמו</option>
                </select>
              )}

              {!['WORK_MANAGER', 'FIELD_WORKER'].includes(_userRole) && (
                <Link
                  to="/projects/new"
                  className="flex items-center gap-2 px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors font-medium"
                >
                  <Plus className="w-5 h-5" />
                  פרויקט חדש
                </Link>
              )}
            </div>
          </div>
        </div>

        {/* Projects Grid */}
        {loading ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
            {Array.from({ length: 6 }).map((_, i) => (
              <div key={i} className="animate-pulse bg-white rounded-2xl border border-gray-200 overflow-hidden" style={{ willChange: 'transform' }}>
                <div className="h-1.5 bg-gray-200 rounded-t-2xl" />
                <div className="p-5 space-y-3">
                  <div className="flex justify-between">
                    <div className="h-4 bg-gray-200 rounded w-3/5" />
                    <div className="h-4 bg-gray-200 rounded w-14" />
                  </div>
                  <div className="h-3 bg-gray-100 rounded w-full" />
                  <div className="h-3 bg-gray-100 rounded w-4/5" />
                  <div className="flex gap-3 pt-2">
                    <div className="h-3 bg-gray-100 rounded w-20" />
                    <div className="h-3 bg-gray-100 rounded w-20" />
                  </div>
                </div>
                <div className="h-10 bg-gray-50 border-t border-gray-100" />
              </div>
            ))}
          </div>
        ) : filteredProjects.length === 0 ? (
          <div className="bg-white rounded-2xl border border-gray-200 p-12 text-center">
            <Briefcase className="w-16 h-16 text-gray-300 mx-auto mb-4" />
            <h2 className="text-xl font-semibold text-gray-900 mb-2">
              {searchTerm || filterStatus !== 'all' ? 'לא נמצאו פרויקטים' : 'אין פרויקטים'}
            </h2>
            <p className="text-gray-600 mb-6">
              {searchTerm || filterStatus !== 'all'
                ? 'נסה לחפש במונחים אחרים או לשנות את הסינון'
                : 'התחל ביצירת פרויקט חדש'}
            </p>
            {!searchTerm && filterStatus === 'all' && (
              <Link
                to="/projects/new"
                className="inline-flex items-center gap-2 px-6 py-3 bg-green-600 text-white rounded-xl hover:bg-green-700 transition-colors font-medium"
              >
                <Plus className="w-5 h-5" />
                צור פרויקט ראשון
              </Link>
            )}
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
            {filteredProjects.map((project) => {
              const statusConfig = getStatusConfig(project);
              const effectiveStatus = getEffectiveStatus(project);
              const isActive = effectiveStatus === 'active';
              const isPlanning = effectiveStatus === 'planning';
              return (
              <div
                key={project.id}
                className={`bg-white rounded-2xl border-2 flex flex-col hover:shadow-lg transition-shadow duration-200 cursor-pointer group ${
                  isActive ? 'border-green-100 hover:border-green-300' : isPlanning ? 'border-yellow-100 hover:border-yellow-300' : 'border-gray-100 hover:border-gray-300'
                }`}
                style={{ willChange: 'transform' }}
                onClick={() => navigate(`/projects/${project.code}/workspace`)}
              >
                {/* Colored top strip */}
                <div className={`h-1.5 rounded-t-2xl ${isActive ? 'bg-green-500' : isPlanning ? 'bg-yellow-400' : 'bg-gray-300'}`} />

                {/* Card Body — grows to fill height */}
                <div className="flex flex-col flex-1 p-5">
                  {/* Header row: name + status badge */}
                  <div className="flex items-start justify-between gap-2 mb-2">
                    <div className="min-w-0">
                      <h3 className="text-base font-bold text-gray-900 group-hover:text-green-700 transition-colors leading-tight truncate">
                        {project.name}
                      </h3>
                      <span className="text-xs text-gray-400 font-mono">{project.code}</span>
                    </div>
                    <span className={`flex-shrink-0 px-2.5 py-0.5 rounded-full text-xs font-semibold ${statusConfig.bg} ${statusConfig.textColor}`}>
                      {statusConfig.text}
                    </span>
                  </div>

                  {/* Description — fixed 2 lines, fills space */}
                  {project.description && (
                    <p className="text-sm text-gray-500 line-clamp-2 mb-4 flex-1 leading-relaxed">
                      {project.description}
                    </p>
                  )}
                  {!project.description && <div className="flex-1" />}

                  {/* Metadata chips */}
                  <div className="flex flex-wrap gap-x-4 gap-y-1.5 text-xs text-gray-500 mb-4">
                    {project.manager_name && (
                      <span className="flex items-center gap-1">
                        <User className="w-3.5 h-3.5 text-gray-400" />
                        {project.manager_name}
                      </span>
                    )}
                    {(project.area_name || project.region_name) && (
                      <span className="flex items-center gap-1">
                        <MapPin className="w-3.5 h-3.5 text-gray-400" />
                        {project.area_name || project.region_name}
                      </span>
                    )}
                    {project.planned_start_date && (
                      <span className="flex items-center gap-1">
                        <Calendar className="w-3.5 h-3.5 text-gray-400" />
                        {new Date(project.planned_start_date).toLocaleDateString('he-IL')}
                      </span>
                    )}
                  </div>

                  {/* Progress bar (if available) */}
                  {project.progress_percentage !== undefined && project.progress_percentage !== null && (
                    <div className="mb-4">
                      <div className="flex justify-between text-xs text-gray-500 mb-1">
                        <span>התקדמות</span>
                        <span className="font-medium text-gray-700">{project.progress_percentage}%</span>
                      </div>
                      <div className="w-full bg-gray-100 rounded-full h-1.5">
                        <div
                          className="bg-green-500 h-1.5 rounded-full transition-all duration-500"
                          style={{ width: `${Math.min(100, project.progress_percentage)}%` }}
                        />
                      </div>
                    </div>
                  )}
                </div>

                {/* Card Footer — always at bottom */}
                <div className="px-5 py-3 border-t border-gray-100 bg-gray-50/70 rounded-b-2xl">
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-gray-400">לחץ לכניסה</span>
                    <ChevronRight className="w-5 h-5 text-gray-400 group-hover:text-green-600 transition-colors" />
                  </div>
                </div>
              </div>
            );
            })}
          </div>
        )}

        {/* Stats Summary */}
        {filteredProjects.length > 0 && (
          <div className="mt-8 bg-white rounded-lg border border-gray-200 p-6">
            <div className={`grid gap-6 ${['WORK_MANAGER','FIELD_WORKER'].includes(_userRole) ? 'grid-cols-2' : 'grid-cols-2 md:grid-cols-4'}`}>
              <div className="text-center">
                <p className="text-2xl font-bold text-gray-900">{filteredProjects.length}</p>
                <p className="text-sm text-gray-600 mt-1">סה"כ פרויקטים</p>
              </div>
              <div className="text-center">
                <p className="text-2xl font-bold text-green-600">
                  {filteredProjects.filter(p => getEffectiveStatus(p) === 'active').length}
                </p>
                <p className="text-sm text-gray-600 mt-1">פרויקטים פעילים</p>
              </div>
              {!['WORK_MANAGER','FIELD_WORKER'].includes(_userRole) && (
                <>
                  <div className="text-center">
                    <p className="text-2xl font-bold text-blue-600">
                      {filteredProjects.filter(p => (p.status || '').toLowerCase() === 'completed').length}
                    </p>
                    <p className="text-sm text-gray-600 mt-1">פרויקטים שהושלמו</p>
                  </div>
                  <div className="text-center">
                    <p className="text-2xl font-bold text-orange-600">
                      {Math.round(
                        filteredProjects.reduce((sum, p) => sum + (p.progress_percentage || 0), 0) /
                        (filteredProjects.length || 1)
                      )}%
                    </p>
                    <p className="text-sm text-gray-600 mt-1">התקדמות ממוצעת</p>
                  </div>
                </>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ProjectsClean;
