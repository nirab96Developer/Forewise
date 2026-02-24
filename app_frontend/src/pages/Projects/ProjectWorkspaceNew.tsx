// @ts-nocheck
// Project Workspace - עיצוב קומפקטי עם נתונים אמיתיים
import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
import { 
  ArrowRight, Eye, Map, ClipboardList, Clock, 
  Loader2, AlertCircle, DollarSign, CheckCircle2, AlertTriangle,
  Calendar, User, TreeDeciduous, MapPin, ExternalLink, Package, 
  FileText, Plus, ChevronLeft
} from 'lucide-react';
import projectService from '../../services/projectService';
import workOrderService, { WorkOrder } from '../../services/workOrderService';
import workLogService, { WorkLog } from '../../services/workLogService';
import ProjectMap from '../../components/Map/ProjectMap';
import TreeLoader from '../../components/common/TreeLoader';
import { parseLocationMetadata, GeoFeature } from '../../services/locationService';

interface ProjectLocation {
  id: number;
  code: string;
  name: string;
  latitude?: number;
  longitude?: number;
  address?: string;
  metadata_json?: string;
}

interface Project {
  id: number;
  code: string;
  name: string;
  description?: string;
  status: string;
  region_id?: number;
  region_name?: string;
  area_id?: number;
  area_name?: string;
  allocated_budget?: number;
  spent_budget?: number;
  committed_budget?: number;
  manager_name?: string;
  planned_start_date?: string;
  planned_end_date?: string;
  location?: ProjectLocation;
  location_id?: number;
}

interface ProjectStats {
  budgetTotal: number;
  budgetSpent: number;
  budgetCommitted: number;
  budgetAvailable: number;
  budgetUsedPercent: number;
  activeOrders: number;
  pendingOrders: number;
  openReports: number;
  pendingReports: number;
}

const ProjectWorkspaceNew: React.FC = () => {
  const { code } = useParams<{ code: string }>();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const initialTab = searchParams.get('tab');
  const [project, setProject] = useState<Project | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'overview' | 'map' | 'orders' | 'worklogs'>(
    initialTab === 'worklogs' ? 'worklogs' : initialTab === 'orders' ? 'orders' : initialTab === 'map' ? 'map' : 'overview'
  );

  useEffect(() => {
    const tab = searchParams.get('tab');
    if (tab === 'worklogs' || tab === 'orders' || tab === 'map' || tab === 'overview') {
      setActiveTab(tab);
    }
  }, [searchParams]);
  
  // Real data states
  const [stats, setStats] = useState<ProjectStats>({
    budgetTotal: 0,
    budgetSpent: 0,
    budgetCommitted: 0,
    budgetAvailable: 0,
    budgetUsedPercent: 0,
    activeOrders: 0,
    pendingOrders: 0,
    openReports: 0,
    pendingReports: 0
  });
  const [workOrders, setWorkOrders] = useState<WorkOrder[]>([]);
  const [worklogs, setWorklogs] = useState<WorkLog[]>([]);

  useEffect(() => {
    loadProject();
  }, [code]);

  const loadProject = async () => {
    if (!code) {
      setError('קוד פרויקט חסר');
      setLoading(false);
      return;
    }

    setLoading(true);
    try {
      const data = await projectService.getProjectByCode(code);
      setProject(data);
      
      // Load real stats
      await loadStats(data.id, data);
    } catch (err) {
      console.error('Error loading project:', err);
      setError('שגיאה בטעינת פרויקט');
    }
    setLoading(false);
  };

  const loadStats = async (projectId: number, projectData: Project) => {
    try {
      // Fetch work orders for this project
      const ordersResponse = await workOrderService.getWorkOrders(1, 100, { project_id: projectId });
      const orders = ordersResponse.items || [];
      setWorkOrders(orders);
      
      // Fetch worklogs for this project
      const logsResponse = await workLogService.getWorkLogs({ project_id: projectId, page_size: 100 });
      const logs = logsResponse.work_logs || logsResponse.items || [];
      setWorklogs(logs);
      
      // Calculate stats
      const activeOrders = orders.filter(o => ['pending', 'approved', 'in_progress'].includes(o.status)).length;
      const pendingOrders = orders.filter(o => o.status === 'pending').length;
      const openReports = logs.filter(l => ['draft', 'pending', 'submitted'].includes(l.status)).length;
      const pendingReports = logs.filter(l => l.status === 'pending').length;
      
      const budgetTotal = projectData.allocated_budget || 0;
      const budgetSpent = projectData.spent_budget || 0;
      const budgetCommitted = projectData.committed_budget || 0;
      const budgetAvailable = budgetTotal - budgetSpent - budgetCommitted;
      const budgetUsedPercent = budgetTotal > 0 ? Math.round((budgetSpent / budgetTotal) * 100) : 0;
      
      setStats({
        budgetTotal,
        budgetSpent,
        budgetCommitted,
        budgetAvailable,
        budgetUsedPercent,
        activeOrders,
        pendingOrders,
        openReports,
        pendingReports
      });
    } catch (err) {
      console.error('Error loading stats:', err);
    }
  };

  if (loading) {
    return <TreeLoader fullScreen />;
  }

  if (error || !project) {
    return (
      <div className="min-h-screen flex items-center justify-center p-4">
        <div className="bg-white rounded-xl shadow-sm p-6 max-w-md text-center">
          <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-3" />
          <h2 className="text-lg font-bold mb-2">{error || 'פרויקט לא נמצא'}</h2>
          <button
            onClick={() => navigate('/projects')}
            className="mt-3 px-5 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
          >
            חזור לפרויקטים
          </button>
        </div>
      </div>
    );
  }

  const tabs = [
    { id: 'overview', label: 'סקירה', icon: Eye },
    { id: 'map', label: 'מפה', icon: Map },
    { id: 'orders', label: 'הזמנות', icon: ClipboardList, badge: stats.activeOrders },
    { id: 'worklogs', label: 'דיווחים', icon: Clock, badge: stats.openReports },
  ];

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col" dir="rtl">
      {/* Header + Tabs קבועים למעלה */}
      <div className="sticky top-0 z-20 bg-white shadow-sm">
        {/* Header קומפקטי */}
        <div className="border-b">
          <div className="max-w-7xl mx-auto px-3 sm:px-6 py-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 min-w-0">
                <button
                  onClick={() => navigate('/projects')}
                  className="text-green-600 hover:text-green-800 flex-shrink-0"
                >
                  <ArrowRight className="w-5 h-5" />
                </button>
                <div className="min-w-0">
                  <h1 className="text-base sm:text-lg font-bold text-gray-900 truncate">{project.name}</h1>
                  <p className="text-xs text-gray-500 truncate">#{project.code}</p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Tabs קומפקטיים - נשאר קבוע */}
        <div className="border-b overflow-x-auto scrollbar-hide">
          <div className="max-w-7xl mx-auto px-3 sm:px-6">
            <nav className="flex">
              {tabs.map((tab) => {
                const Icon = tab.icon;
                return (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id as any)}
                    className={`flex items-center gap-1.5 px-3 py-2 border-b-2 font-medium text-sm whitespace-nowrap transition-colors ${
                      activeTab === tab.id
                        ? 'border-green-600 text-green-600'
                        : 'border-transparent text-gray-500 hover:text-gray-700'
                    }`}
                  >
                    <Icon className="w-4 h-4" />
                    {tab.label}
                    {tab.badge !== undefined && tab.badge > 0 && (
                      <span className="bg-green-100 text-green-700 text-xs px-1.5 py-0.5 rounded-full">
                        {tab.badge}
                      </span>
                    )}
                  </button>
                );
              })}
            </nav>
          </div>
        </div>
      </div>

      {/* Content - גולל בנפרד */}
      <div className="flex-1 overflow-auto">
        <div className="max-w-7xl mx-auto px-3 sm:px-6 py-3">
          {activeTab === 'overview' && <OverviewTab project={project} stats={stats} />}
          {activeTab === 'map' && <MapTab project={project} />}
          {activeTab === 'orders' && <OrdersTab projectCode={project.code} projectId={project.id} orders={workOrders} />}
          {activeTab === 'worklogs' && <WorklogsTab projectCode={project.code} projectId={project.id} worklogs={worklogs} />}
        </div>
      </div>
    </div>
  );
};

// טאב סקירה - קומפקטי למובייל
const OverviewTab: React.FC<{ project: Project; stats: ProjectStats }> = ({ project, stats }) => {
  const paidPercent = stats.budgetTotal > 0 ? Math.round((stats.budgetSpent / stats.budgetTotal) * 100) : 0;
  const committedPercent = stats.budgetTotal > 0 ? Math.round((stats.budgetCommitted / stats.budgetTotal) * 100) : 0;

  return (
    <div className="space-y-3">
      {/* כרטיסי סטטיסטיקה - 2x2 */}
      <div className="grid grid-cols-2 gap-2">
        <StatCard 
          icon={<DollarSign className="w-4 h-4 text-green-600" />}
          label="תקציב"
          value={`${stats.budgetUsedPercent}%`}
          subtitle="נוצל"
          bgColor="bg-green-50"
        />
        <StatCard 
          icon={<Package className="w-4 h-4 text-blue-600" />}
          label="הזמנות"
          value={stats.activeOrders.toString()}
          subtitle={stats.pendingOrders > 0 ? `${stats.pendingOrders} ממתינות` : 'פעילות'}
          bgColor="bg-blue-50"
        />
        <StatCard 
          icon={<FileText className="w-4 h-4 text-orange-600" />}
          label="דיווחים"
          value={stats.openReports.toString()}
          subtitle={stats.pendingReports > 0 ? `${stats.pendingReports} ממתינים` : 'פתוחים'}
          bgColor="bg-orange-50"
        />
        <StatCard 
          icon={<CheckCircle2 className="w-4 h-4 text-purple-600" />}
          label="סטטוס"
          value={project.status === 'active' ? 'פעיל' : 'לא פעיל'}
          subtitle=""
          bgColor="bg-purple-50"
        />
      </div>

      {/* מצב תקציב - קומפקטי */}
      <div className="bg-white rounded-xl border p-4">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm font-medium text-gray-700">תקציב</span>
          <span className="text-lg font-bold">₪{stats.budgetTotal.toLocaleString()}</span>
        </div>
        
        <div className="h-2 bg-gray-100 rounded-full overflow-hidden flex">
          <div className="bg-green-500 h-full" style={{ width: `${paidPercent}%` }} />
          <div className="bg-yellow-400 h-full" style={{ width: `${committedPercent}%` }} />
        </div>
        
        <div className="flex justify-between mt-2 text-xs text-gray-500">
          <span>🟢 שולם {paidPercent}%</span>
          <span>🟡 מחוייב {committedPercent}%</span>
          <span>⚪ פנוי {100 - paidPercent - committedPercent}%</span>
        </div>
      </div>

      {/* פרטי פרויקט - קומפקטי */}
      <div className="bg-white rounded-xl border p-4">
        <h3 className="text-sm font-semibold mb-3 text-gray-800">פרטי הפרויקט</h3>
        <div className="grid grid-cols-2 gap-3 text-sm">
          <InfoItem icon={<Map className="w-3.5 h-3.5" />} label="מרחב" value={project.region_name || '-'} />
          <InfoItem icon={<MapPin className="w-3.5 h-3.5" />} label="אזור" value={project.area_name || '-'} />
          <InfoItem icon={<TreeDeciduous className="w-3.5 h-3.5" />} label="יער" value={project.name} />
          <InfoItem icon={<User className="w-3.5 h-3.5" />} label="מנהל" value={project.manager_name || '-'} />
          {project.planned_start_date && (
            <InfoItem 
              icon={<Calendar className="w-3.5 h-3.5" />} 
              label="תאריכים" 
              value={`${new Date(project.planned_start_date).toLocaleDateString('he-IL')}`} 
            />
          )}
        </div>
      </div>

    </div>
  );
};

// קומפוננטות עזר
const StatCard: React.FC<{ icon: React.ReactNode; label: string; value: string; subtitle: string; bgColor: string }> = 
  ({ icon, label, value, subtitle, bgColor }) => (
  <div className="bg-white rounded-xl border p-3">
    <div className={`w-8 h-8 ${bgColor} rounded-lg flex items-center justify-center mb-2`}>
      {icon}
    </div>
    <p className="text-xs text-gray-500">{label}</p>
    <p className="text-xl font-bold text-gray-900">{value}</p>
    {subtitle && <p className="text-xs text-gray-400">{subtitle}</p>}
  </div>
);

const InfoItem: React.FC<{ icon: React.ReactNode; label: string; value: string }> = ({ icon, label, value }) => (
  <div className="flex items-start gap-2">
    <div className="text-gray-400 mt-0.5">{icon}</div>
    <div className="min-w-0">
      <p className="text-xs text-gray-400">{label}</p>
      <p className="text-sm font-medium text-gray-900 truncate">{value}</p>
    </div>
  </div>
);

// טאב מפה
// Error Boundary for Google Maps crashes
class MapErrorBoundary extends React.Component<{children: React.ReactNode}, {hasError: boolean}> {
  constructor(props: any) { super(props); this.state = { hasError: false }; }
  static getDerivedStateFromError() { return { hasError: true }; }
  render() {
    if (this.state.hasError) {
      return (
        <div className="h-full flex flex-col items-center justify-center bg-gray-50 rounded-xl text-center p-8">
          <MapPin className="w-12 h-12 text-gray-300 mb-3" />
          <h3 className="text-lg font-medium text-gray-700 mb-1">המפה לא זמינה כרגע</h3>
          <p className="text-sm text-gray-500">ייתכן שיש בעיה בטעינת Google Maps</p>
        </div>
      );
    }
    return this.props.children;
  }
}

const MapTab: React.FC<{ project: Project }> = ({ project }) => {
  const [mapData, setMapData] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);
  const navigate = useNavigate();

  const location = project.location;
  const defaultLat = location?.latitude || 31.7683;
  const defaultLng = location?.longitude || 35.2137;

  useEffect(() => {
    const fetchAll = async () => {
      try {
        const token = localStorage.getItem('access_token');
        const headers = { 'Authorization': 'Bearer ' + token };
        
        // Only fetch project-specific data (fast, small responses)
        const [geoResp, forestResp] = await Promise.all([
          fetch('/api/v1/projects/' + project.id + '/geo', { headers }).then(r => r.ok ? r.json() : null).catch(() => null),
          fetch('/api/v1/projects/' + project.id + '/forest-map', { headers }).then(r => r.ok ? r.json() : null).catch(() => null),
        ]);

        // Only fetch area boundary if we need it (no forest = fallback mask)
        let areaGeom = null;
        const areaId = (project as any).area_id || geoResp?.area_id;
        if (areaId && !forestResp?.has_forest) {
          const areaResp = await fetch('/api/v1/geo/areas/boundaries?region_id=' + ((project as any).region_id || geoResp?.region_id || ''), { headers })
            .then(r => r.ok ? r.json() : null).catch(() => null);
          if (areaResp?.features) {
            const feat = areaResp.features.find((f: any) => f.properties.id === areaId);
            if (feat) areaGeom = feat;
          }
        }

        setMapData({ geo: geoResp, forest: forestResp, areaFeature: areaGeom });
      } catch (err) {
        console.error('Error fetching map data:', err);
      }
      setIsLoading(false);
    };
    if (project.id) fetchAll();
  }, [project.id]);

  if (isLoading) {
    return (
      <div className="h-[65vh] flex items-center justify-center bg-gray-50 rounded-xl">
        <TreeLoader size="md" />
      </div>
    );
  }

  // Project point
  const lat = mapData?.geo?.latitude || defaultLat;
  const lng = mapData?.geo?.longitude || defaultLng;

  // Build map layers
  const LazyLeafletMap = React.lazy(() => import('../../components/Map/LeafletMap'));
  
  // Forest polygon - show with border, no mask
  const forestGeom = mapData?.forest?.has_forest && mapData.forest.forest?.geojson_full;
  const forestPolygons = [];
  if (forestGeom) {
    const geom = forestGeom.geometry || forestGeom;
    if (geom && (geom.type === 'Polygon' || geom.type === 'MultiPolygon')) {
      forestPolygons.push({
        id: 999, name: mapData.forest.forest.name || 'שטח יער',
        geometry: geom,
        fillColor: '#10b981', strokeColor: '#047857',
        fillOpacity: 0.20, strokeWeight: 3,
      });
    }
  }

  // No nearby projects in project view - keep it clean and fast
  const nearbyPoints = [];

  // Main project point (gold, prominent)
  const projectPoint = {
    id: project.id, name: project.name, code: project.code,
    lat, lng,
    color: '#f59e0b',
    popupContent:
      '<div style="direction:rtl;padding:8px;min-width:160px">' +
      '<b style="font-size:14px;color:#047857">' + project.name + '</b><br>' +
      '<span style="color:#6b7280;font-size:11px">' + project.code + '</span><br>' +
      (project.region_name ? '<span style="color:#6b7280;font-size:11px">מרחב: ' + project.region_name + '</span><br>' : '') +
      (project.area_name ? '<span style="color:#6b7280;font-size:11px">אזור: ' + project.area_name + '</span>' : '') +
      '</div>',
  };

  const allPoints = [projectPoint, ...nearbyPoints];
  const allPolygons = [...forestPolygons];

  return (
    <div className="space-y-3">
      {/* Info bar */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        <div className="bg-gradient-to-r from-green-50 to-emerald-50 border border-green-200 rounded-xl p-3">
          <div className="flex items-center gap-2">
            <MapPin className="w-5 h-5 text-green-600" />
            <div>
              <p className="text-xs text-gray-500">מיקום</p>
              <p className="font-bold text-gray-900 text-sm">{lat.toFixed(4)}, {lng.toFixed(4)}</p>
            </div>
          </div>
        </div>
        {project.area_name && (
          <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-xl p-3">
            <div className="flex items-center gap-2">
              <Map className="w-5 h-5 text-blue-600" />
              <div>
                <p className="text-xs text-gray-500">אזור</p>
                <p className="font-bold text-gray-900 text-sm">{project.area_name}</p>
              </div>
            </div>
          </div>
        )}
        {project.region_name && (
          <div className="bg-gradient-to-r from-amber-50 to-orange-50 border border-amber-200 rounded-xl p-3">
            <div className="flex items-center gap-2">
              <TreeDeciduous className="w-5 h-5 text-amber-600" />
              <div>
                <p className="text-xs text-gray-500">מרחב</p>
                <p className="font-bold text-gray-900 text-sm">{project.region_name}</p>
              </div>
            </div>
          </div>
        )}
      </div>

      {mapData?.forest?.has_forest && mapData.forest.forest && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-3 flex items-center gap-3">
          <TreeDeciduous className="w-5 h-5 text-green-700" />
          <div>
            <span className="font-bold text-green-800 text-sm">{mapData.forest.forest.name}</span>
            {mapData.forest.forest.area_km2 && (
              <span className="text-green-600 text-xs mr-2">({mapData.forest.forest.area_km2} קמ״ר)</span>
            )}
          </div>
        </div>
      )}

      {/* Map */}
      <div className="rounded-xl overflow-hidden shadow-lg border-2 border-gray-200">
        <MapErrorBoundary>
          <React.Suspense fallback={<div className="h-[400px] flex items-center justify-center bg-gray-50"><Loader2 className="w-8 h-8 text-green-600 animate-spin" /></div>}>
            <LazyLeafletMap
              height="500px"
              center={[lat, lng]}
              zoom={forestPolygons.length > 0 ? 14 : 13}
              points={forestPolygons.length > 0 ? [projectPoint] : allPoints}
              polygons={allPolygons}
              fitBounds={true}
              mapType="street"
            />
          </React.Suspense>
        </MapErrorBoundary>
      </div>

      {/* Legend */}
      <div className="bg-white rounded-xl border border-gray-200 p-4">
        <div className="flex flex-wrap gap-5 text-sm">
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded-full bg-amber-500 border-2 border-white shadow" />
            <span className="text-gray-700">הפרויקט הנוכחי</span>
          </div>
          {nearbyPoints.length > 0 && (
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 rounded-full bg-gray-500 border-2 border-white shadow" />
              <span className="text-gray-700">פרויקטים באזור ({nearbyPoints.length})</span>
            </div>
          )}
          {forestPolygons.length > 0 && (
            <div className="flex items-center gap-2">
              <div className="w-4 h-3 bg-green-500/30 border-2 border-green-600 rounded" />
              <span className="text-gray-700">שטח יער</span>
            </div>
          )}
          {false && (
            <div className="flex items-center gap-2">
              <div className="w-4 h-3 bg-green-600/10 border-2 border-green-800 rounded" />
              <span className="text-gray-700">גבול אזור</span>
            </div>
          )}
          <a
            href={'https://www.google.com/maps?q=' + lat + ',' + lng}
            target="_blank" rel="noopener noreferrer"
            className="flex items-center gap-1 text-blue-600 hover:text-blue-800 mr-auto"
          >
            <ExternalLink className="w-4 h-4" />
            <span>Google Maps</span>
          </a>
        </div>
      </div>
    </div>
  );
};

// טאב הזמנות - נתונים אמיתיים
const OrdersTab: React.FC<{ projectCode: string; projectId: number; orders: WorkOrder[] }> = 
  ({ projectCode, projectId, orders }) => {
  const navigate = useNavigate();
  
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'pending': return 'bg-yellow-100 text-yellow-800';
      case 'approved': return 'bg-blue-100 text-blue-800';
      case 'in_progress': return 'bg-purple-100 text-purple-800';
      case 'completed': return 'bg-green-100 text-green-800';
      case 'cancelled': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };
  
  const getStatusLabel = (status: string) => {
    switch (status) {
      case 'pending': return 'ממתין';
      case 'approved': return 'מאושר';
      case 'in_progress': return 'בביצוע';
      case 'completed': return 'הושלם';
      case 'cancelled': return 'בוטל';
      default: return status;
    }
  };
  
  return (
    <div className="space-y-3">
      <div className="flex justify-between items-center">
        <h2 className="text-lg font-bold">הזמנות עבודה</h2>
        <button 
          onClick={() => navigate(`/work-orders/new?project=${projectId}`)}
          className="px-3 py-1.5 bg-green-600 text-white rounded-lg hover:bg-green-700 text-sm flex items-center gap-1"
        >
          <Plus className="w-4 h-4" />
          הזמנה חדשה
        </button>
      </div>
      
      {orders.length === 0 ? (
        <div className="bg-white rounded-xl border p-8 text-center">
          <ClipboardList className="w-12 h-12 text-gray-300 mx-auto mb-3" />
          <p className="text-gray-500">אין הזמנות לפרויקט זה</p>
        </div>
      ) : (
        <div className="space-y-2">
          {orders.map((order) => (
            <div 
              key={order.id}
              onClick={() => navigate(`/work-orders/${order.id}`)}
              className="bg-white rounded-xl border p-4 hover:shadow-md transition-shadow cursor-pointer"
            >
              <div className="flex items-start justify-between">
                <div className="min-w-0 flex-1">
                  <p className="font-medium text-gray-900 truncate">{order.title}</p>
                  <p className="text-sm text-gray-500 mt-1">
                    {order.supplier_name || 'ללא ספק'} • {new Date(order.work_start_date).toLocaleDateString('he-IL')}
                  </p>
                </div>
                <div className="flex items-center gap-2 flex-shrink-0">
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(order.status)}`}>
                    {getStatusLabel(order.status)}
                  </span>
                  <ChevronLeft className="w-4 h-4 text-gray-400" />
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

// טאב דיווחים - נתונים אמיתיים
const WorklogsTab: React.FC<{ projectCode: string; projectId: number; worklogs: WorkLog[] }> = 
  ({ projectCode, projectId, worklogs }) => {
  const navigate = useNavigate();
  const formatWorklogDate = (log: WorkLog) => {
    const rawDate = (log as any).report_date || (log as any).work_date || (log as any).created_at;
    if (!rawDate) return '-';
    const d = new Date(rawDate);
    return Number.isNaN(d.getTime()) ? '-' : d.toLocaleDateString('he-IL');
  };
  
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'draft': return 'bg-gray-100 text-gray-800';
      case 'pending': return 'bg-yellow-100 text-yellow-800';
      case 'submitted': return 'bg-blue-100 text-blue-800';
      case 'approved': return 'bg-green-100 text-green-800';
      case 'rejected': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };
  
  const getStatusLabel = (status: string) => {
    switch (status) {
      case 'draft': return 'טיוטה';
      case 'pending': return 'ממתין';
      case 'submitted': return 'הוגש';
      case 'approved': return 'מאושר';
      case 'rejected': return 'נדחה';
      default: return status;
    }
  };
  
  return (
    <div className="space-y-3">
      <div className="flex justify-between items-center">
        <h2 className="text-lg font-bold">דיווחי שעות</h2>
        <button
          onClick={() => navigate(`/projects/${projectCode}/workspace/work-logs/new?project_id=${projectId}&project_code=${projectCode}`)}
          className="px-3 py-1.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm flex items-center gap-1"
        >
          <Plus className="w-4 h-4" />
          דיווח חדש
        </button>
      </div>
      
      {worklogs.length === 0 ? (
        <div className="bg-white rounded-xl border p-8 text-center">
          <Clock className="w-12 h-12 text-gray-300 mx-auto mb-3" />
          <p className="text-gray-500">אין דיווחים לפרויקט זה</p>
        </div>
      ) : (
        <div className="space-y-2">
          {worklogs.map((log) => (
            <div 
              key={log.id}
              onClick={() => navigate(`/projects/${projectCode}/workspace/work-logs/${log.id}`)}
              className="bg-white rounded-xl border p-4 hover:shadow-md transition-shadow cursor-pointer"
            >
              <div className="flex items-start justify-between">
                <div className="min-w-0 flex-1">
                  <p className="font-medium text-gray-900">
                    דיווח #{log.report_number_formatted || log.report_number}
                  </p>
                  <p className="text-sm text-gray-500 mt-1">
                    {log.user_name || 'לא ידוע'} • {formatWorklogDate(log)} • {log.total_hours} שעות
                  </p>
                </div>
                <div className="flex items-center gap-2 flex-shrink-0">
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(log.status)}`}>
                    {getStatusLabel(log.status)}
                  </span>
                  <ChevronLeft className="w-4 h-4 text-gray-400" />
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default ProjectWorkspaceNew;
