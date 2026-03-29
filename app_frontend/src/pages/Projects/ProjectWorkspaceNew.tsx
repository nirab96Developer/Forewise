
// Project Workspace - עיצוב קומפקטי עם נתונים אמיתיים
import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
import {
  ArrowRight, Eye, Map, ClipboardList, Clock,
  Loader2, AlertCircle, CheckCircle2,
  Calendar, User, TreeDeciduous, MapPin, ExternalLink, Package,
  FileText, Plus, Calculator, Activity,
  LogIn, CheckCircle, XCircle, Send, FilePlus, FileCheck, Info,
  Camera, X, ScanLine, Wrench, ShieldAlert, AlertTriangle
} from 'lucide-react';
import projectService from '../../services/projectService';
import workOrderService, { WorkOrder } from '../../services/workOrderService';
import workLogService, { WorkLog } from '../../services/workLogService';
import api from '../../services/api';
import TreeLoader from '../../components/common/TreeLoader';
// locationService available if needed

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
  manager?: { id: number; full_name: string };
  manager_name?: string;
  accountant?: { id: number; full_name: string } | null;
  area_manager?: { id: number; full_name: string } | null;
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

  // Role detection 
  const storedUser = (() => {
    try { return JSON.parse(localStorage.getItem('user') || '{}'); } catch { return {}; }
  })();
  const userRoleCode: string = (storedUser?.role?.code || storedUser?.role_code || '').toUpperCase();
  const currentUserId: number | undefined = storedUser?.id ? Number(storedUser.id) : undefined;

  const isWorkManager = userRoleCode === 'WORK_MANAGER';
  const isAdminUser = userRoleCode === 'ADMIN';

  const allowedTabs = ['overview', 'orders', 'worklogs', 'map'];

  type TabId = 'overview' | 'map' | 'orders' | 'worklogs' | 'activity' | 'budget' | 'documents';

  const resolveInitialTab = (): TabId => {
    if (initialTab && allowedTabs.includes(initialTab)) return initialTab as TabId;
    return 'overview';
  };

  const [project, setProject] = useState<Project | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<TabId>(resolveInitialTab());

  useEffect(() => {
    const tab = searchParams.get('tab');
    if (tab && allowedTabs.includes(tab)) setActiveTab(tab as TabId);
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
      const activeOrders = orders.filter(o => ['PENDING', 'APPROVED', 'APPROVED_AND_SENT', 'IN_PROGRESS', 'ACTIVE', 'SUPPLIER_ACCEPTED_PENDING_COORDINATOR'].includes(o.status?.toUpperCase())).length;
      const pendingOrders = orders.filter(o => o.status?.toUpperCase() === 'PENDING').length;
      const openReports = logs.filter(l => ['PENDING', 'SUBMITTED'].includes((l.status || '').toUpperCase())).length;
      const pendingReports = logs.filter(l => (l.status || '').toUpperCase() === 'PENDING').length;

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

  // Tabs per role 
  const tabs = (isWorkManager || isAdminUser)
    ? [
      { id: 'overview', label: 'סקירה', icon: Eye },
      { id: 'orders', label: 'הזמנות עבודה', icon: ClipboardList, badge: stats.activeOrders },
      { id: 'worklogs', label: 'כלים בפרויקט', icon: Wrench, badge: stats.openReports },
      { id: 'map', label: 'מפה', icon: Map },
    ]
    : /* All other roles — same 4 tabs */
    [
      { id: 'overview', label: 'סקירה', icon: Eye },
      { id: 'orders', label: 'הזמנות עבודה', icon: ClipboardList, badge: stats.activeOrders },
      { id: 'worklogs', label: 'כלים בפרויקט', icon: Wrench, badge: stats.openReports },
      { id: 'map', label: 'מפה', icon: Map },
    ];

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col" dir="rtl">
      {/* Header + Tabs קבועים למעלה */}
      <div className="sticky top-16 z-10 bg-white shadow-sm">
        {/* Header + Tabs in one row */}
        <div className="border-b overflow-x-auto scrollbar-hide">
          <nav className="flex items-center px-3 sm:px-6 min-w-max">
            <button
              onClick={() => navigate('/projects')}
              className="text-green-600 hover:text-green-800 flex-shrink-0 p-1 ml-2"
            >
              <ArrowRight className="w-5 h-5" />
            </button>
            <div className="flex items-baseline gap-1.5 ml-4 flex-shrink-0">
              <h1 className="text-sm sm:text-base font-bold text-gray-900 truncate max-w-[150px] sm:max-w-[200px]">{project.name}</h1>
              <span className="text-[10px] text-gray-400">#{project.code}</span>
            </div>
            <div className="w-px h-6 bg-gray-200 mx-3 flex-shrink-0" />
            {tabs.map((tab) => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id as any)}
                  className={`flex items-center gap-1.5 px-3 py-2.5 border-b-2 font-medium text-sm whitespace-nowrap transition-colors min-h-[44px] ${activeTab === tab.id
                      ? 'border-green-600 text-green-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700'
                    }`}
                >
                  <Icon className="w-4 h-4 flex-shrink-0" />
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

      {/* Content - גולל בנפרד */}
      <div className="flex-1 overflow-auto" style={{ isolation: 'isolate' }}>
        <div className="max-w-7xl mx-auto px-3 sm:px-6 py-3">
          {/* סקירה — זהה לכולם */}
          {activeTab === 'overview' && <OverviewTab project={project} stats={stats} currentUser={storedUser} />}

          {activeTab === 'map' && <MapTab project={project} userRole={userRoleCode} />}

          {/* הזמנות */}
          {activeTab === 'orders' && (
            <OrdersTab
              projectCode={project.code}
              projectId={project.id}
              projectName={project.name}
              orders={(isWorkManager || isAdminUser)
                ? workOrders.filter(o =>
                  Number((o as any).created_by) === Number(currentUserId) ||
                  Number((o as any).created_by_id) === Number(currentUserId) ||
                  Number((o as any).reporter_id) === Number(currentUserId)
                )
                : workOrders}
              isWorkManager={isWorkManager || isAdminUser}
              onSwitchToWorklogs={() => setActiveTab('worklogs')}
              onAfterScan={() => setActiveTab('worklogs')}
            />
          )}

          {/* כלים בפרויקט */}
          {activeTab === 'worklogs' && (
            <WorklogsTab
              projectCode={project.code}
              projectId={project.id}
              worklogs={(isWorkManager && !isAdminUser)
                ? worklogs.filter(l =>
                  Number((l as any).reporter_id) === Number(currentUserId) ||
                  Number((l as any).created_by) === Number(currentUserId) ||
                  Number((l as any).user_id) === Number(currentUserId)
                )
                : worklogs}
              isWorkManager={isWorkManager || isAdminUser}
              approvedOrders={workOrders.filter(o =>
                APPROVED_STATUSES.includes((o.status || '').toUpperCase())
              )}
            />
          )}

          {activeTab === 'budget' && <BudgetTab project={project} stats={stats} />}
          {activeTab === 'documents' && <DocumentsTab projectId={project.id} />}
          {activeTab === 'activity' && <ActivityLogTab projectId={project.id} />}
        </div>
      </div>
    </div>
  );
};

// טאב סקירה - קומפקטי למובייל
const OverviewTab: React.FC<{ project: Project; stats: ProjectStats; currentUser?: any }> = ({ project, stats, currentUser }) => {
  const userRoleCode = (currentUser?.role?.code || currentUser?.role_code || '').toUpperCase();
  const managerValue = userRoleCode === 'WORK_MANAGER'
    ? (currentUser?.full_name || currentUser?.name || project.manager_name || project.manager?.full_name || '-')
    : (project.manager_name || project.manager?.full_name || '-');
  const paidPercent = stats.budgetTotal > 0 ? Math.round((stats.budgetSpent / stats.budgetTotal) * 100) : 0;
  const committedPercent = stats.budgetTotal > 0 ? Math.round((stats.budgetCommitted / stats.budgetTotal) * 100) : 0;

  return (
    <div className="space-y-3">
      {/* כרטיסי סטטיסטיקה - 2x2 */}
      <div className="grid grid-cols-2 gap-2">
        <StatCard
          icon={<Calculator className="w-4 h-4 text-green-600" />}
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

      {/* מצב תקציב — מפורט */}
      <div className="bg-white rounded-xl border p-4">
        <div className="flex items-center justify-between mb-3">
          <span className="text-sm font-semibold text-gray-700">מצב תקציב</span>
          <span className="text-base font-bold text-gray-900">{stats.budgetTotal.toLocaleString()}</span>
        </div>

        {/* 4 שורות פירוט */}
        <div className="space-y-1.5 text-xs mb-3">
          <div className="flex justify-between">
            <span className="text-gray-500">תקציב כולל:</span>
            <span className="font-medium text-gray-800">{stats.budgetTotal.toLocaleString()}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-yellow-600"> מוקפא (הזמנות פתוחות):</span>
            <span className="font-medium text-yellow-700">{stats.budgetCommitted.toLocaleString()}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-green-600"> נוצל (חשבוניות שולמו):</span>
            <span className="font-medium text-green-700">{stats.budgetSpent.toLocaleString()}</span>
          </div>
          <div className="flex justify-between border-t border-gray-100 pt-1.5 mt-1.5">
            <span className="font-semibold text-gray-700">זמין:</span>
            <span className={`font-bold ${stats.budgetAvailable < 0 ? 'text-red-600' : 'text-green-700'}`}>
              {stats.budgetAvailable.toLocaleString()}
            </span>
          </div>
        </div>

        <div className="h-2 bg-gray-100 rounded-full overflow-hidden flex">
          <div className="bg-green-500 h-full transition-all" style={{ width: `${paidPercent}%` }} />
          <div className="bg-yellow-400 h-full transition-all" style={{ width: `${committedPercent}%` }} />
        </div>
        <div className="flex justify-between mt-1.5 text-xs text-gray-400">
          <span>נוצל {paidPercent}%</span>
          <span>מוקפא {committedPercent}%</span>
          <span>פנוי {Math.max(0, 100 - paidPercent - committedPercent)}%</span>
        </div>
      </div>

      {/* פרטי פרויקט - קומפקטי */}
      <div className="bg-white rounded-xl border p-4">
        <h3 className="text-sm font-semibold mb-3 text-gray-800">פרטי הפרויקט</h3>
        <div className="grid grid-cols-2 gap-3 text-sm">
          <InfoItem icon={<Map className="w-3.5 h-3.5" />} label="מרחב" value={project.region_name || '-'} />
          <InfoItem icon={<MapPin className="w-3.5 h-3.5" />} label="אזור" value={project.area_name || '-'} />
          <InfoItem icon={<TreeDeciduous className="w-3.5 h-3.5" />} label="יער" value={project.name} />
          <InfoItem icon={<User className="w-3.5 h-3.5" />} label="מנהל עבודה" value={managerValue} />
          <InfoItem icon={<User className="w-3.5 h-3.5" />} label="מנהל אזור" value={project.area_manager?.full_name || '-'} />
          <InfoItem icon={<Calculator className="w-3.5 h-3.5" />} label="מנהלת חשבונות אזורית" value={project.accountant?.full_name || '-'} />
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
class MapErrorBoundary extends React.Component<{ children: React.ReactNode }, { hasError: boolean }> {
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

const MapTab: React.FC<{ project: Project; userRole?: string }> = ({ project, userRole }) => {
  const [mapData, setMapData] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [showPolygonDrawer, setShowPolygonDrawer] = useState(false);
  const canEditPolygon = ['ADMIN', 'AREA_MANAGER', 'REGION_MANAGER'].includes(userRole || '');
  const LazyPolygonDrawer = React.lazy(() => import('../../components/map/PolygonDrawer'));

  const location = project.location;
  const defaultLat = location?.latitude || 31.7683;
  const defaultLng = location?.longitude || 35.2137;

  const loadMapData = async () => {
    try {
      const token = localStorage.getItem('access_token');
      const headers = { 'Authorization': 'Bearer ' + token };

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

  useEffect(() => {
    if (project.id) loadMapData();
  }, [project.id]);

  if (isLoading) {
    return (
      <div className="h-[65vh] flex items-center justify-center bg-gray-50 rounded-xl">
        <TreeLoader size="md" />
      </div>
    );
  }

  // Determine map center: prefer polygon centroid, fallback to project GPS point
  const hasForest = mapData?.forest?.has_forest && mapData.forest.forest;
  const forestCenterLat = hasForest ? mapData.forest.forest.center_lat : null;
  const forestCenterLng = hasForest ? mapData.forest.forest.center_lng : null;
  const projLat = mapData?.geo?.latitude || defaultLat;
  const projLng = mapData?.geo?.longitude || defaultLng;
  const lat = forestCenterLat ?? projLat;
  const lng = forestCenterLng ?? projLng;

  const wazeUrl = `https://waze.com/ul?ll=${lat},${lng}&navigate=yes`;
  const googleMapsUrl = `https://www.google.com/maps/dir/?api=1&destination=${lat},${lng}`;

  // Build map layers
  const LazyLeafletMap = React.lazy(() => import('../../components/Map/LeafletMap'));

  // Forest polygon layer
  const forestGeom = hasForest && mapData.forest.forest?.geojson_full;
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

  // Point marker: use centroid when has_forest (so it's inside the polygon),
  // fallback to project GPS point when no forest polygon exists
  const pointLat = hasForest ? (forestCenterLat ?? projLat) : projLat;
  const pointLng = hasForest ? (forestCenterLng ?? projLng) : projLng;

  const projectPoint = {
    id: project.id, name: project.name, code: project.code,
    lat: pointLat, lng: pointLng,
    color: '#f59e0b',
    popupContent:
      '<div style="direction:rtl;padding:8px;min-width:160px">' +
      '<b style="font-size:14px;color:#047857">' + project.name + '</b><br>' +
      '<span style="color:#6b7280;font-size:11px">' + project.code + '</span><br>' +
      (project.region_name ? '<span style="color:#6b7280;font-size:11px">מרחב: ' + project.region_name + '</span><br>' : '') +
      (project.area_name ? '<span style="color:#6b7280;font-size:11px">אזור: ' + project.area_name + '</span>' : '') +
      '</div>',
  };

  // Always show the orange point — at centroid when has_forest, at GPS when not
  const allPoints = [projectPoint];
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

      {/* Graceful fallback when polygon unavailable */}
      {mapData && !mapData.forest?.has_forest && (
        <div className="bg-gray-50 border border-gray-200 rounded-lg p-3 flex items-center gap-2 text-sm text-gray-500">
          <TreeDeciduous className="w-4 h-4 text-gray-400 flex-shrink-0" />
          <span>
            {mapData.forest?.reason === 'polygon_too_far'
              ? 'גבולות יער לא תואמים למיקום הפרויקט — מוצגת נקודת מיקום בלבד'
              : 'מיפוי שטח לא זמין לפרויקט זה — מוצגת נקודת מיקום בלבד'}
          </span>
        </div>
      )}

      {/* Edit polygon button */}
      {canEditPolygon && !showPolygonDrawer && (
        <button
          onClick={() => setShowPolygonDrawer(true)}
          className="flex items-center gap-2 px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg text-sm font-medium transition-colors mb-3"
        >
          <MapPin className="w-4 h-4" />
          ערוך גבולות יער
        </button>
      )}

      {/* Polygon Drawer */}
      {showPolygonDrawer && (
        <div className="mb-4 border-2 border-purple-300 rounded-xl overflow-hidden" style={{ height: 500 }}>
          <React.Suspense fallback={<div className="h-full flex items-center justify-center"><span className="text-gray-400">טוען...</span></div>}>
            <LazyPolygonDrawer
              projectId={project.id}
              projectName={project.name}
              existingGeoJSON={mapData?.forest?.has_forest ? mapData.forest.forest?.geojson_full : undefined}
              onSave={() => { setShowPolygonDrawer(false); loadMapData(); }}
              onClose={() => setShowPolygonDrawer(false)}
            />
          </React.Suspense>
        </div>
      )}

      {/* Navigation buttons */}
      <div className="flex gap-2 mb-3">
        <a href={wazeUrl} target="_blank" rel="noopener noreferrer"
          className="flex items-center gap-2 px-4 py-2.5 bg-[#33ccff]/10 border border-[#33ccff]/30 rounded-xl text-sm font-semibold text-[#05b5cc] hover:bg-[#33ccff]/20 transition-colors">
          <img src="https://www.waze.com/favicon.ico" alt="Waze" width="20" height="20" style={{borderRadius:'4px'}} />
          נווט עם Waze
        </a>
        <a href={googleMapsUrl} target="_blank" rel="noopener noreferrer"
          className="flex items-center gap-2 px-4 py-2.5 bg-[#4285f4]/10 border border-[#4285f4]/30 rounded-xl text-sm font-semibold text-[#4285f4] hover:bg-[#4285f4]/20 transition-colors">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none"><path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7z" fill="#EA4335" /><circle cx="12" cy="9" r="2.5" fill="#fff" /></svg>
          נווט עם Google Maps
        </a>
      </div>

      {/* Map */}
      <div className="rounded-xl overflow-hidden shadow-lg border-2 border-gray-200 isolate" style={{ isolation: 'isolate' }}>
        <MapErrorBoundary>
          <React.Suspense fallback={<div className="h-[400px] flex items-center justify-center bg-gray-50"><div className="relative flex items-center justify-center w-12 h-12"><div className="absolute inset-0 rounded-full border-4 border-emerald-200 border-t-emerald-500 animate-spin" style={{ animationDuration: '0.9s' }}></div><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 100" width="28" height="24"><defs><linearGradient id="pw_t" x1="0%" y1="0%" x2="100%" y2="0%"><stop offset="0%" style={{ stopColor: '#1565c0' }} /><stop offset="100%" style={{ stopColor: '#0097a7' }} /></linearGradient><linearGradient id="pw_m" x1="0%" y1="0%" x2="100%" y2="0%"><stop offset="0%" style={{ stopColor: '#0097a7' }} /><stop offset="50%" style={{ stopColor: '#2e7d32' }} /><stop offset="100%" style={{ stopColor: '#66bb6a' }} /></linearGradient><linearGradient id="pw_b" x1="0%" y1="0%" x2="100%" y2="0%"><stop offset="0%" style={{ stopColor: '#2e7d32' }} /><stop offset="40%" style={{ stopColor: '#66bb6a' }} /><stop offset="100%" style={{ stopColor: '#8B5e3c' }} /></linearGradient></defs><path d="M46 20 Q60 9 74 20" stroke="url(#pw_t)" strokeWidth="5.5" fill="none" strokeLinecap="round" /><path d="M30 47 Q42 34 60 43 Q78 34 90 47" stroke="url(#pw_m)" strokeWidth="5.5" fill="none" strokeLinecap="round" /><path d="M14 74 Q28 60 46 69 Q60 76 74 69 Q92 60 106 74" stroke="url(#pw_b)" strokeWidth="5.5" fill="none" strokeLinecap="round" /><line x1="60" y1="76" x2="60" y2="90" stroke="#8B5e3c" strokeWidth="3.5" strokeLinecap="round" /><circle cx="60" cy="95" r="5" fill="#8B5e3c" /></svg></div></div>}>
            <LazyLeafletMap
              height="500px"
              center={[lat, lng]}
              zoom={forestPolygons.length > 0 ? 14 : 13}
              points={allPoints}
              polygons={allPolygons}
              fitBounds={forestPolygons.length > 0}
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
          {!hasForest && (
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 rounded-full bg-amber-500 border-2 border-white shadow" />
              <span className="text-gray-700">מיקום פרויקט</span>
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
// helpers shared by OrdersTab + WorkOrderDetail 
const APPROVED_STATUSES = ['APPROVED', 'APPROVED_AND_SENT', 'COORDINATOR_APPROVED', 'ACTIVE', 'IN_PROGRESS', 'SUPPLIER_ACCEPTED_PENDING_COORDINATOR'];

function woStatusBadge(status: string): { label: string; cls: string } {
  const s = (status || '').toUpperCase();
  if (['PENDING', 'DISTRIBUTING'].includes(s))
    return { label: 'ממתין לתיאום', cls: 'bg-yellow-100 text-yellow-700' };
  if (['SENT_TO_SUPPLIER', 'SUPPLIER_ACCEPTED_PENDING_COORDINATOR'].includes(s))
    return { label: 'אצל הספק', cls: 'bg-blue-100 text-blue-700' };
  if (APPROVED_STATUSES.includes(s))
    return { label: 'אושר — ניתן לדווח', cls: 'bg-green-100 text-green-700' };
  if (s === 'COMPLETED')
    return { label: 'הושלם', cls: 'bg-gray-100 text-gray-500' };
  if (['REJECTED', 'CANCELLED'].includes(s))
    return { label: 'נדחה', cls: 'bg-red-100 text-red-700' };
  return { label: status || '—', cls: 'bg-gray-100 text-gray-600' };
}

function safeWODate(dateStr?: string | null, fallback?: string | null): string {
  const raw = dateStr || fallback;
  if (!raw) return '—';
  const d = new Date(raw);
  if (Number.isNaN(d.getTime()) || d.getFullYear() < 2000) return '—';
  return d.toLocaleDateString('he-IL');
}

// Scan Equipment Modal — 3 scenarios
type ScanPhase = 'input' | 'loading' | 'different_plate' | 'wrong_type' | 'done';
interface ScanResult {
  status: string;
  message: string;
  question?: string;
  equipment_id?: number;
  equipment_type?: string;
  old_project?: { wo_id: number; wo_number: string; project_name: string; remaining_hours: number } | null;
  ordered_type?: string;
  scanned_type?: string;
  admin_can_override?: boolean;
}

const ScanEquipmentModal: React.FC<{
  orderId: number;
  orderNumber: string | number;
  onClose: () => void;
  onScanned: (orderId: number, equipmentNum: string) => void;
}> = ({ orderId, orderNumber, onClose, onScanned }) => {
  const [value, setValue] = useState('');
  const [phase, setPhase] = useState<ScanPhase>('input');
  const [err, setErr] = useState('');
  const [scanResult, setScanResult] = useState<ScanResult | null>(null);
  const [adminReason, setAdminReason] = useState('');

  const handleScan = async () => {
    const trimmed = value.trim();
    if (!trimmed) { setErr('יש להזין מספר רישוי'); return; }
    setPhase('loading');
    setErr('');
    try {
      const res = await api.post(`/work-orders/${orderId}/scan-equipment`, { license_plate: trimmed });
      const data: ScanResult = res.data;
      setScanResult(data);

      if (data.status === 'ok') {
        onScanned(orderId, trimmed);
        setPhase('done');
        setTimeout(() => { onClose(); window.location.reload(); }, 1200);
      } else if (data.status === 'different_plate') {
        setPhase('different_plate');
      } else if (data.status === 'wrong_type') {
        setPhase('wrong_type');
      } else {
        setErr(data.message || 'שגיאה לא צפויה');
        setPhase('input');
      }
    } catch (e: any) {
      setErr(e?.response?.data?.detail || 'שגיאת שרת');
      setPhase('input');
    }
  };

  const handleConfirmDifferentPlate = async () => {
    if (!scanResult?.equipment_id) return;
    setPhase('loading');
    try {
      const res = await api.post(`/work-orders/${orderId}/confirm-equipment`, {
        equipment_id: scanResult.equipment_id,
      });
      if (res.data.status === 'ok') {
        onScanned(orderId, value.trim());
        setPhase('done');
        setTimeout(() => { onClose(); window.location.reload(); }, 1200);
      }
    } catch (e: any) {
      setErr(e?.response?.data?.detail || 'שגיאה באישור');
      setPhase('different_plate');
    }
  };

  const handleAdminOverride = async () => {
    if (!adminReason.trim()) { setErr('חובה לציין סיבה לאישור חריג'); return; }
    setPhase('loading');
    try {
      const res = await api.post(`/work-orders/${orderId}/admin-override-equipment`, {
        license_plate: value.trim(),
        reason: adminReason.trim(),
      });
      if (res.data.status === 'ok') {
        onScanned(orderId, value.trim());
        setPhase('done');
        setTimeout(() => { onClose(); window.location.reload(); }, 1200);
      }
    } catch (e: any) {
      setErr(e?.response?.data?.detail || 'שגיאה באישור חריג');
      setPhase('wrong_type');
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4" onClick={onClose}>
      <div className="bg-white rounded-xl shadow-xl w-full max-w-md" onClick={e => e.stopPropagation()}>
        {/* Header */}
        <div className={`p-4 rounded-t-xl flex items-center justify-between ${
          phase === 'wrong_type' ? 'bg-red-600' :
          phase === 'different_plate' ? 'bg-amber-500' :
          phase === 'done' ? 'bg-green-600' : 'bg-green-600'
        }`}>
          <div className="flex items-center gap-2">
            {phase === 'wrong_type' ? <ShieldAlert className="w-5 h-5 text-white" /> :
             phase === 'different_plate' ? <AlertTriangle className="w-5 h-5 text-white" /> :
             <Camera className="w-5 h-5 text-white" />}
            <h3 className="font-bold text-white">
              {phase === 'wrong_type' ? 'חריגת סוג כלי' :
               phase === 'different_plate' ? 'לוחית שונה' :
               phase === 'done' ? 'כלי אושר' :
               `סריקת כלי — דרישה #${orderNumber}`}
            </h3>
          </div>
          <button onClick={onClose} className="p-1 hover:bg-white/20 rounded-lg">
            <X className="w-4 h-4 text-white" />
          </button>
        </div>

        <div className="p-5 space-y-4">
          {/* ── Phase: Input ── */}
          {phase === 'input' && (
            <>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1.5">מספר רישוי</label>
                <input
                  autoFocus
                  type="text"
                  value={value}
                  onChange={e => { setValue(e.target.value); setErr(''); }}
                  onKeyDown={e => e.key === 'Enter' && handleScan()}
                  placeholder="לדוגמה: 12-345-67"
                  className="w-full px-3 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-400 focus:border-transparent text-lg font-mono tracking-wider"
                />
                {err && <p className="text-red-500 text-xs mt-1">{err}</p>}
              </div>
              <div className="flex items-center gap-2 bg-green-50 border border-green-100 rounded-lg p-3 text-sm text-green-700">
                <ScanLine className="w-4 h-4 flex-shrink-0" />
                <span>הזן את מספר הרישוי של הכלי שהגיע לאתר</span>
              </div>
              <div className="flex gap-2 pt-1">
                <button onClick={onClose} className="flex-1 py-2.5 border border-gray-200 rounded-lg text-gray-600 hover:bg-gray-50 text-sm font-medium">ביטול</button>
                <button
                  onClick={handleScan}
                  disabled={!value.trim()}
                  className="flex-1 py-2.5 bg-green-600 hover:bg-green-700 text-white rounded-lg text-sm font-medium disabled:opacity-50 flex items-center justify-center gap-1.5"
                >
                  <ScanLine className="w-4 h-4" /> סרוק
                </button>
              </div>
            </>
          )}

          {/* ── Phase: Loading ── */}
          {phase === 'loading' && (
            <div className="flex flex-col items-center py-8 gap-3">
              <Loader2 className="w-8 h-8 animate-spin text-green-600" />
              <p className="text-sm text-gray-500">בודק התאמה...</p>
            </div>
          )}

          {/* ── Phase: Done (Scenario A success) ── */}
          {phase === 'done' && (
            <div className="flex flex-col items-center py-6 gap-3">
              <CheckCircle className="w-12 h-12 text-green-500" />
              <p className="text-base font-medium text-green-700">{scanResult?.message || 'כלי אושר בהצלחה'}</p>
            </div>
          )}

          {/* ── Phase: Different Plate (Scenario B) ── */}
          {phase === 'different_plate' && scanResult && (
            <>
              <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 space-y-2">
                <div className="flex items-start gap-2">
                  <AlertTriangle className="w-5 h-5 text-amber-600 mt-0.5 flex-shrink-0" />
                  <div>
                    <p className="text-sm font-medium text-amber-800">{scanResult.message}</p>
                    <p className="text-sm text-amber-700 mt-1">{scanResult.question}</p>
                  </div>
                </div>
              </div>

              {scanResult.old_project && (
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 text-sm">
                  <p className="font-medium text-blue-800 mb-1">שים לב — הכלי נמצא בפרויקט אחר:</p>
                  <p className="text-blue-700">
                    פרויקט: {scanResult.old_project.project_name || `הזמנה #${scanResult.old_project.wo_number}`}
                  </p>
                  <p className="text-blue-700">
                    באישור — הכלי יוסר מהפרויקט הקודם ויתרת התקציב תשוחרר
                  </p>
                </div>
              )}

              {err && <p className="text-red-500 text-xs">{err}</p>}

              <div className="flex gap-2 pt-1">
                <button onClick={() => { setPhase('input'); setScanResult(null); setErr(''); }}
                  className="flex-1 py-2.5 border border-gray-200 rounded-lg text-gray-600 hover:bg-gray-50 text-sm font-medium">
                  חזרה
                </button>
                <button onClick={handleConfirmDifferentPlate}
                  className="flex-1 py-2.5 bg-amber-500 hover:bg-amber-600 text-white rounded-lg text-sm font-medium flex items-center justify-center gap-1.5">
                  <CheckCircle className="w-4 h-4" /> כן, שייך לפרויקט
                </button>
              </div>
            </>
          )}

          {/* ── Phase: Wrong Type (Scenario C) ── */}
          {phase === 'wrong_type' && scanResult && (
            <>
              <div className="bg-red-50 border border-red-200 rounded-lg p-4 space-y-2">
                <div className="flex items-start gap-2">
                  <XCircle className="w-5 h-5 text-red-600 mt-0.5 flex-shrink-0" />
                  <div>
                    <p className="text-sm font-bold text-red-800">סוג הכלי שנסרק שונה מההזמנה</p>
                    <div className="mt-2 text-sm text-red-700 space-y-1">
                      <p>סוג בהזמנה: <span className="font-medium">{scanResult.ordered_type}</span></p>
                      <p>סוג שנסרק: <span className="font-medium">{scanResult.scanned_type}</span></p>
                    </div>
                  </div>
                </div>
              </div>

              {scanResult.admin_can_override ? (
                <>
                  <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
                    <div className="flex items-center gap-2 mb-2">
                      <ShieldAlert className="w-4 h-4 text-yellow-700" />
                      <p className="text-sm font-medium text-yellow-800">אישור חריג (מנהל מערכת בלבד)</p>
                    </div>
                    <textarea
                      value={adminReason}
                      onChange={e => { setAdminReason(e.target.value); setErr(''); }}
                      placeholder="ציין סיבה לאישור חריגת סוג כלי..."
                      rows={2}
                      className="w-full px-3 py-2 border border-yellow-300 rounded-lg text-sm focus:ring-2 focus:ring-yellow-400"
                    />
                  </div>
                  {err && <p className="text-red-500 text-xs">{err}</p>}
                  <div className="flex gap-2 pt-1">
                    <button onClick={onClose}
                      className="flex-1 py-2.5 border border-gray-200 rounded-lg text-gray-600 hover:bg-gray-50 text-sm font-medium">
                      ביטול
                    </button>
                    <button onClick={handleAdminOverride}
                      disabled={!adminReason.trim()}
                      className="flex-1 py-2.5 bg-red-600 hover:bg-red-700 text-white rounded-lg text-sm font-medium disabled:opacity-50 flex items-center justify-center gap-1.5">
                      <ShieldAlert className="w-4 h-4" /> אשר חריגה
                    </button>
                  </div>
                </>
              ) : (
                <>
                  <div className="bg-gray-50 border border-gray-200 rounded-lg p-3 text-sm text-gray-600">
                    <p>הפעולה חסומה. פנה למנהל מערכת לאישור חריג.</p>
                  </div>
                  <button onClick={onClose}
                    className="w-full py-2.5 border border-gray-200 rounded-lg text-gray-600 hover:bg-gray-50 text-sm font-medium">
                    סגור
                  </button>
                </>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
};

// OrdersTab 
const OrdersTab: React.FC<{
  projectCode: string;
  projectId: number;
  projectName?: string;
  orders: WorkOrder[];
  isWorkManager?: boolean;
  onSwitchToWorklogs?: () => void;
  onAfterScan?: () => void;
}> = ({ projectCode: _projectCode, projectId, projectName, orders, isWorkManager, onSwitchToWorklogs: _onSwitchToWorklogs, onAfterScan }) => {
  const navigate = useNavigate();

  // localScans: orderId equipment number (persists within the session until reload)
  const [localScans, setLocalScans] = useState<Record<number, string>>({});
  // justScanned: orderId true, only set immediately after scan (for success banner)
  const [justScanned, setJustScanned] = useState<Record<number, boolean>>({});
  const [scanModal, setScanModal] = useState<{ orderId: number; orderNumber: string | number } | null>(null);

  const handleScanned = (orderId: number, equipmentNum: string) => {
    setLocalScans(prev => ({ ...prev, [orderId]: equipmentNum }));
    setJustScanned(prev => ({ ...prev, [orderId]: true }));
    // After scan — notify parent to switch tab and show toast
    setTimeout(() => {
      onAfterScan?.();
      (window as any).showToast?.(' כלי נסרק בהצלחה — עבר לכלים בשטח', 'success');
    }, 600);
  };

  const hasEquipmentScan = (order: WorkOrder) =>
    !!localScans[order.id] || !!(order as any).equipment_scan || !!(order as any).scanned_equipment_id;

  const getScanValue = (order: WorkOrder) =>
    localScans[order.id] || (order as any).equipment_scan || '';

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
          {orders.map((order) => {
            const isApproved = APPROVED_STATUSES.includes((order.status || '').toUpperCase());
            const isRejected = ['REJECTED', 'CANCELLED'].includes((order.status || '').toUpperCase());
            const displayDate = safeWODate((order as any).work_start_date, order.created_at);
            const scanned = hasEquipmentScan(order);
            const equipmentNum = getScanValue(order);
            void justScanned[order.id];

            // Status badge — for WM after scan: "כלי נסרק — ניתן לדווח"
            const { label: rawLabel, cls } = woStatusBadge(order.status);
            const label = (isWorkManager && isApproved && scanned) ? 'כלי נסרק — ניתן לדווח' : rawLabel;
            const badgeCls = (isWorkManager && isApproved && scanned) ? 'bg-green-100 text-green-700' : cls;

            return (
              <div key={order.id} className={`bg-white rounded-2xl shadow-sm border-2 overflow-hidden transition-all hover:shadow-md ${isRejected ? 'border-red-200' : isApproved ? 'border-green-200' : 'border-gray-200'
                }`}>
                {/* Card Header (always visible) — coordinator style */}
                <div className="px-4 py-3">
                  {/* Row 1: Order number + badges */}
                  <div className="flex flex-wrap items-center gap-2 mb-2">
                    <span className="text-xs text-gray-400 font-mono">#{(order as any).order_number || order.id}</span>
                    <span className={`px-2.5 py-0.5 rounded-full text-xs font-medium ${badgeCls}`}>{label}</span>
                    {(order as any).is_forced_selection && (
                      <span className="px-2 py-0.5 bg-orange-100 text-orange-700 rounded-full text-xs font-medium">אילוץ ספק</span>
                    )}
                  </div>

                  {/* Row 2: Main info grid — like coordinator */}
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-x-4 gap-y-1.5 text-sm">
                    <div className="flex items-center gap-1.5 text-gray-700">
                      <span className="text-gray-400 text-xs"></span>
                      <span className="truncate">{order.equipment_type || '—'}</span>
                    </div>
                    <div className="flex items-center gap-1.5 text-gray-700">
                      <span className="text-gray-400 text-xs"></span>
                      {order.supplier_name
                        ? <span className="truncate text-green-700 font-medium">{order.supplier_name}</span>
                        : <span className="text-gray-400 italic text-xs">טרם נבחר</span>
                      }
                    </div>
                    <div className="flex items-center gap-1.5 text-gray-700">
                      <span className="text-gray-400 text-xs"></span>
                      <span className="text-xs">{displayDate}</span>
                    </div>
                    <div className="flex items-center gap-1.5 text-gray-700">
                      <span className="text-gray-400 text-xs"></span>
                      <span>{(order as any).estimated_hours || '—'} שעות</span>
                    </div>
                  </div>
                </div>

                {/* Expanded details */}
                <div className="border-t border-gray-100 bg-gray-50/50 px-4 py-3">
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    {/* Left: Order details */}
                    <div>
                      <h4 className="text-xs font-semibold text-gray-500 mb-2">פרטי ההזמנה</h4>
                      <div className="space-y-1.5 text-sm">
                        <div><span className="text-gray-400">סוג ציוד: </span><span className="font-medium">{order.equipment_type || '—'}</span></div>
                        <div><span className="text-gray-400">ספק: </span><span className="font-medium text-green-700">{order.supplier_name || 'טרם נבחר'}</span></div>
                        {scanned && equipmentNum && (
                          <div><span className="text-gray-400">מס׳ כלי: </span><span className="font-medium text-green-700">{equipmentNum}</span></div>
                        )}
                        <div><span className="text-gray-400">מיקום: </span><span className="font-medium">{(order as any).location_name || (order as any).area_name || '—'}</span></div>
                        <div><span className="text-gray-400">תאריכי עבודה: </span><span className="font-medium">{displayDate}</span></div>
                        {(order as any).estimated_hours && (
                          <div><span className="text-gray-400">כמות שעות: </span><span className="font-medium">{(order as any).estimated_hours}</span></div>
                        )}
                        {(order as any).is_forced_selection && (order as any).constraint_notes && (
                          <div><span className="text-gray-400">סיבת אילוץ: </span><span className="text-orange-700">{(order as any).constraint_notes}</span></div>
                        )}
                      </div>
                    </div>

                    {/* Right: Actions */}
                    <div>
                      <h4 className="text-xs font-semibold text-gray-500 mb-2">פעולות</h4>
                      <div className="space-y-2">
                        <button
                          onClick={() => {
                            const wo = order as any;
                            const statusMap: Record<string, string> = {
                              'PENDING': 'ממתין', 'APPROVED': 'מאושר', 'APPROVED_AND_SENT': 'אושר ונשלח',
                              'IN_PROGRESS': 'בביצוע', 'COMPLETED': 'הושלם', 'REJECTED': 'נדחה',
                              'CANCELLED': 'בוטל', 'DISTRIBUTING': 'בהפצה', 'PENDING_SUPPLIER': 'ממתין לספק',
                            };
                            const statusHe = statusMap[(wo.status || '').toUpperCase()] || wo.status || '—';
                            const startDate = wo.work_start_date ? new Date(wo.work_start_date).toLocaleDateString('he-IL') : '—';
                            const endDate = wo.work_end_date ? new Date(wo.work_end_date).toLocaleDateString('he-IL') : '—';
                            const html = `<!DOCTYPE html><html dir="rtl" lang="he"><head><meta charset="UTF-8"><title>הזמנה #${wo.order_number || wo.id}</title><style>@media print{body{margin:0}}body{font-family:Arial,sans-serif;padding:30px;max-width:700px;margin:0 auto;color:#333}h1{color:#2d5016;border-bottom:3px solid #2d5016;padding-bottom:10px}table{width:100%;border-collapse:collapse;margin:20px 0}td{padding:10px 14px;border-bottom:1px solid #e0e0e0}td:first-child{font-weight:bold;color:#555;width:35%}td:last-child{color:#111}.badge{display:inline-block;padding:4px 14px;border-radius:20px;font-size:13px;font-weight:600}.status-approved{background:#dcfce7;color:#166534}.status-pending{background:#fef9c3;color:#854d0e}.status-rejected{background:#fee2e2;color:#991b1b}.footer{margin-top:40px;text-align:center;color:#999;font-size:12px;border-top:1px solid #eee;padding-top:15px}@media print{.no-print{display:none}}</style></head><body>` +
                              `<div class="no-print" style="text-align:center;margin-bottom:20px"><button onclick="window.print()" style="background:#2d5016;color:white;border:none;padding:10px 30px;border-radius:8px;font-size:14px;cursor:pointer"> הדפסה / שמירה כ-PDF</button></div>` +
                              `<h1>הזמנת עבודה #${wo.order_number || wo.id}</h1>` +
                              `<table><tr><td>סטטוס</td><td><span class="badge ${statusHe === 'מאושר' || statusHe === 'אושר ונשלח' ? 'status-approved' : statusHe === 'נדחה' || statusHe === 'בוטל' ? 'status-rejected' : 'status-pending'}">${statusHe}</span></td></tr>` +
                              `<tr><td>פרויקט</td><td>${projectName || '—'}</td></tr>` +
                              `<tr><td>סוג ציוד</td><td>${wo.equipment_type || '—'}</td></tr>` +
                              `<tr><td>ספק</td><td>${wo.supplier_name || 'ממתין לשיבוץ'}</td></tr>` +
                              `<tr><td>תאריך התחלה</td><td>${startDate}</td></tr>` +
                              `<tr><td>תאריך סיום</td><td>${endDate}</td></tr>` +
                              `<tr><td>שעות משוערות</td><td>${wo.estimated_hours || '—'}</td></tr>` +
                              `<tr><td>תעריף לשעה</td><td>${wo.hourly_rate ? '' + wo.hourly_rate : '—'}</td></tr>` +
                              `<tr><td>עלות כוללת</td><td>${wo.total_amount ? '' + Number(wo.total_amount).toLocaleString() : '—'}</td></tr>` +
                              `<tr><td>תיאור</td><td>${wo.description || '—'}</td></tr>` +
                              `</table>` +
                              `<div class="footer">Forewise — מערכת ניהול יערות | ${new Date().toLocaleDateString('he-IL')}</div>` +
                              `</body></html>`;
                            const blob = new Blob([html], { type: 'text/html;charset=utf-8' });
                            const url = URL.createObjectURL(blob);
                            window.open(url, '_blank');
                          }}
                          className="w-full flex items-center justify-center gap-2 py-2.5 bg-white border border-gray-200 hover:bg-gray-50 text-gray-700 rounded-xl text-sm font-medium transition-colors"
                        >
                          <Eye className="w-4 h-4" />
                          צפה בפרטים
                        </button>
                        {isApproved && !isRejected && !scanned && (
                          <button
                            onClick={() => setScanModal({ orderId: order.id, orderNumber: (order as any).order_number || order.id })}
                            className="w-full flex items-center justify-center gap-2 py-2.5 bg-green-600 hover:bg-green-700 text-white rounded-xl text-sm font-medium transition-colors"
                          >
                            <Camera className="w-4 h-4" />
                            הוספת כלי לפרויקט
                          </button>
                        )}
                        {isApproved && scanned && (
                          <div className="bg-green-50 border border-green-200 rounded-xl px-3 py-2 text-center text-xs text-green-700 font-medium">
                            כלי נסרק — עבור לטאב "כלים בפרויקט" לדיווח
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {scanModal && (
        <ScanEquipmentModal
          orderId={scanModal.orderId}
          orderNumber={scanModal.orderNumber}
          onClose={() => setScanModal(null)}
          onScanned={handleScanned}
        />
      )}
    </div>
  );
};

// WorklogsTab 
interface WorklogFormState {
  work_order_id: string;
  work_date: string;
  start_time: string;
  end_time: string;
  break_minutes: string;
  notes: string;
}

const EMPTY_FORM: WorklogFormState = {
  work_order_id: '',
  work_date: new Date().toISOString().split('T')[0],
  start_time: '07:00',
  end_time: '16:00',
  break_minutes: '0',
  notes: '',
};

const WorklogsTab: React.FC<{
  projectCode: string;
  projectId: number;
  worklogs: WorkLog[];
  isWorkManager?: boolean;
  approvedOrders?: WorkOrder[];
}> = ({ projectCode, projectId, worklogs, isWorkManager, approvedOrders = [] }) => {
  const navigate = useNavigate();
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState<WorklogFormState>(EMPTY_FORM);
  const [saving, setSaving] = useState(false);
  const [formErr, setFormErr] = useState('');

  const set = (field: keyof WorklogFormState, value: string) =>
    setForm(prev => ({ ...prev, [field]: value }));


  const calcHours = () => {
    try {
      const [sh, sm] = form.start_time.split(':').map(Number);
      const [eh, em] = form.end_time.split(':').map(Number);
      const mins = (eh * 60 + em) - (sh * 60 + sm) - Number(form.break_minutes || 0);
      return mins > 0 ? Math.round(mins / 6) / 10 : 0;
    } catch { return 0; }
  };

  const handleSubmit = async () => {
    if (!form.work_order_id) { setFormErr('יש לבחור הזמנה'); return; }
    if (!form.work_date) { setFormErr('יש לבחור תאריך'); return; }
    if (!form.start_time || !form.end_time) { setFormErr('יש להזין שעות'); return; }
    setSaving(true);
    setFormErr('');
    try {
      await api.post('/worklogs/', {
        work_order_id: Number(form.work_order_id),
        project_id: projectId,
        work_date: form.work_date,
        start_time: form.start_time,
        end_time: form.end_time,
        break_minutes: Number(form.break_minutes || 0),
        notes: form.notes,
        total_hours: calcHours(),
      });
      setShowForm(false);
      setForm(EMPTY_FORM);
      // Reload page to get updated worklogs list
      window.location.reload();
    } catch (e: any) {
      setFormErr(e?.response?.data?.detail || 'שגיאה בשמירת הדיווח');
    } finally {
      setSaving(false);
    }
  };

  const fmtDate = (log: WorkLog) => {
    const raw = (log as any).report_date || (log as any).work_date || (log as any).created_at;
    if (!raw) return '-';
    const d = new Date(raw);
    return Number.isNaN(d.getTime()) ? '-' : d.toLocaleDateString('he-IL');
  };

  const statusColor = (s: string) => ({
    draft: 'bg-gray-100 text-gray-800', pending: 'bg-yellow-100 text-yellow-800',
    submitted: 'bg-blue-100 text-blue-800', approved: 'bg-green-100 text-green-800',
    rejected: 'bg-red-100 text-red-800', invoiced: 'bg-indigo-100 text-indigo-800',
  }[s?.toLowerCase()] ?? 'bg-gray-100 text-gray-800');

  const statusLabel = (s: string) => ({
    draft: 'טיוטה', pending: 'ממתין', submitted: 'הוגש', approved: 'מאושר', rejected: 'נדחה', invoiced: 'חשבונית',
  }[s?.toLowerCase()] ?? s);


  return (
    <div className="space-y-3">
      {/* Header */}
      <div className="flex justify-between items-center">
        <h2 className="text-lg font-bold">דיווחי שעות</h2>
      </div>

      {/* Cannot report yet */}
      {isWorkManager && approvedOrders.length === 0 && (
        <div className="bg-amber-50 border border-amber-200 rounded-xl p-5 flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-amber-500 flex-shrink-0 mt-0.5" />
          <div>
            <p className="font-medium text-amber-800 text-sm">לא ניתן לדווח שעות עדיין</p>
            <p className="text-xs text-amber-600 mt-1">
              כדי לדווח שעות יש צורך בהזמנה מאושרת שהכלי שלה נסרק.
              עבור לטאב "הזמנות עבודה" וסרוק את כלי העבודה.
            </p>
          </div>
        </div>
      )}

      {/* Inline worklog form */}
      {showForm && (
        <div className="bg-white rounded-xl border shadow-sm overflow-hidden">
          <div className="bg-green-700 px-4 py-3 flex items-center justify-between">
            <span className="font-bold text-white text-sm">דיווח שעות חדש</span>
            <button onClick={() => setShowForm(false)} className="p-1 hover:bg-white/20 rounded-lg">
              <X className="w-4 h-4 text-white" />
            </button>
          </div>

          <div className="p-4 space-y-4" dir="rtl">
            {/* בחר הזמנה */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">הזמנה מאושרת</label>
              <select
                value={form.work_order_id}
                onChange={e => set('work_order_id', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-400 focus:border-transparent text-sm"
              >
                <option value="">בחר הזמנה...</option>
                {approvedOrders.map(o => (
                  <option key={o.id} value={o.id}>
                    דרישה #{(o as any).order_number || o.id} — {o.equipment_type || 'ציוד'} {(o as any).equipment_scan ? `(${(o as any).equipment_scan})` : ''}
                  </option>
                ))}
              </select>
            </div>

            {/* תאריך עבודה */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">תאריך עבודה</label>
              <input type="date" value={form.work_date} onChange={e => set('work_date', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-400 focus:border-transparent text-sm" />
            </div>

            {/* שעות */}
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">שעת התחלה</label>
                <input type="time" value={form.start_time} onChange={e => set('start_time', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-400 focus:border-transparent text-sm" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">שעת סיום</label>
                <input type="time" value={form.end_time} onChange={e => set('end_time', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-400 focus:border-transparent text-sm" />
              </div>
            </div>

            {/* הפסקות */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">הפסקות (דקות)</label>
              <input type="number" min="0" step="5" value={form.break_minutes} onChange={e => set('break_minutes', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-400 focus:border-transparent text-sm" placeholder="0" />
            </div>

            {/* סה"כ שעות */}
            {calcHours() > 0 && (
              <div className="bg-blue-50 rounded-lg px-3 py-2 text-sm text-blue-700 font-medium">
                סה״כ שעות עבודה: {calcHours()}
              </div>
            )}

            {/* הערות */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">הערות</label>
              <textarea rows={2} value={form.notes} onChange={e => set('notes', e.target.value)}
                placeholder="הערות לדיווח..."
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-400 focus:border-transparent text-sm resize-none" />
            </div>

            {formErr && <p className="text-red-500 text-sm">{formErr}</p>}

            <div className="flex gap-2 pt-1">
              <button onClick={() => setShowForm(false)}
                className="flex-1 py-2.5 border border-gray-200 rounded-lg text-gray-600 hover:bg-gray-50 text-sm font-medium">
                ביטול
              </button>
              <button onClick={handleSubmit} disabled={saving}
                className="flex-1 py-2.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-medium disabled:opacity-50 flex items-center justify-center gap-1.5">
                {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <CheckCircle className="w-4 h-4" />}
                שלח לאישור
              </button>
            </div>
          </div>
        </div>
      )}

      {/* כלים בפרויקט — Equipment cards from approved orders */}
      {approvedOrders.length > 0 && (
        <div className="space-y-3">
          {approvedOrders.map((order) => {
            const orderWorklogs = worklogs.filter(wl => (wl as any).work_order_id === order.id);
            const usedHours = orderWorklogs.reduce((sum: number, wl) => sum + (Number((wl as any).work_hours || wl.total_hours) || 0), 0);
            const estimatedHours = Number((order as any).estimated_hours) || 0;
            const remainingHours = Math.max(0, estimatedHours - usedHours);
            const licensePlate = (order as any).equipment_license_plate || (order as any).equipment_scan || '';

            return (
              <div key={`eq-${order.id}`} className="bg-white rounded-2xl border-2 border-green-100 shadow-sm overflow-hidden">
                {/* Header — like coordinator style */}
                <div className="px-4 py-3 flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <div className="w-9 h-9 bg-green-100 rounded-xl flex items-center justify-center">
                      <Wrench className="w-5 h-5 text-green-600" />
                    </div>
                    <div>
                      <p className="font-bold text-gray-900">{order.equipment_type || 'ציוד'}</p>
                      {licensePlate && <p className="text-xs text-green-700 font-mono font-bold">{licensePlate}</p>}
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-700">פעיל</span>
                    <span className="text-xs text-gray-400 font-mono">#{(order as any).order_number || order.id}</span>
                  </div>
                </div>

                {/* Details grid */}
                <div className="px-4 py-3 border-t border-gray-100">
                  <div className="grid grid-cols-2 sm:grid-cols-3 gap-x-4 gap-y-2 text-sm">
                    <div>
                      <span className="text-gray-400 text-xs block">סוג כלי</span>
                      <span className="font-medium text-gray-900">{order.equipment_type || '—'}</span>
                    </div>
                    <div>
                      <span className="text-gray-400 text-xs block">מספר כלי</span>
                      <span className="font-bold text-green-700">{licensePlate || '—'}</span>
                    </div>
                    <div>
                      <span className="text-gray-400 text-xs block">ספק</span>
                      <span className="font-medium text-gray-900">{order.supplier_name || '—'}</span>
                    </div>
                    <div>
                      <span className="text-gray-400 text-xs block">מיקום</span>
                      <span className="font-medium text-gray-900">{(order as any).location_name || (order as any).area_name || '—'}</span>
                    </div>
                    <div>
                      <span className="text-gray-400 text-xs block">תאריכי עבודה</span>
                      <span className="font-medium text-gray-900">{safeWODate((order as any).work_start_date, order.created_at)}</span>
                    </div>
                    <div>
                      <span className="text-gray-400 text-xs block">כמות שעות</span>
                      <span className="font-bold text-gray-900">{estimatedHours}</span>
                    </div>
                  </div>
                </div>

                {/* Hours balance */}
                {estimatedHours > 0 && (
                  <div className="px-4 py-3 border-t border-gray-100">
                    <div className="bg-blue-50 border border-blue-200 rounded-xl p-3">
                      <div className="flex justify-between items-center mb-2">
                        <span className="text-sm text-blue-700 font-semibold">יתרת שעות</span>
                        <span className="text-lg font-black text-blue-800">{remainingHours} / {estimatedHours}</span>
                      </div>
                      <div className="w-full bg-blue-200 rounded-full h-2.5">
                        <div
                          className={`h-2.5 rounded-full transition-all ${remainingHours < estimatedHours * 0.2 ? 'bg-red-500' : 'bg-blue-600'}`}
                          style={{ width: `${Math.min(100, estimatedHours > 0 ? (usedHours / estimatedHours) * 100 : 0)}%` }}
                        />
                      </div>
                      <div className="flex justify-between text-xs mt-1.5">
                        <span className="text-blue-600">דווח: {usedHours} שעות</span>
                        <span className={remainingHours < estimatedHours * 0.2 ? 'text-red-600 font-bold' : 'text-blue-600'}>
                          נותר: {remainingHours} שעות
                        </span>
                      </div>
                    </div>
                  </div>
                )}

                {/* Worklog history for this order */}
                {orderWorklogs.length > 0 && (
                  <div className="px-4 py-2 border-t border-gray-100">
                    <p className="text-xs font-semibold text-gray-500 mb-1.5">דיווחים ({orderWorklogs.length})</p>
                    <div className="space-y-1">
                      {orderWorklogs.slice(0, 3).map(log => (
                        <div key={log.id}
                          onClick={() => navigate(`/projects/${projectCode}/workspace/work-logs/${log.id}`)}
                          className="flex items-center justify-between text-xs bg-gray-50 rounded-lg px-3 py-2 hover:bg-gray-100 cursor-pointer"
                        >
                          <span className="text-gray-700">{fmtDate(log)} · {log.total_hours} שעות</span>
                          <span className={`px-1.5 py-0.5 rounded text-[10px] font-medium ${statusColor(log.status)}`}>
                            {statusLabel(log.status)}
                          </span>
                        </div>
                      ))}
                      {orderWorklogs.length > 3 && (
                        <p className="text-[10px] text-gray-400 text-center">+ עוד {orderWorklogs.length - 3} דיווחים</p>
                      )}
                    </div>
                  </div>
                )}

                {/* Actions */}
                <div className="px-4 py-3 border-t border-gray-100 bg-gray-50/50">
                  <div className="grid grid-cols-3 gap-2">
                    <button
                      onClick={() => navigate(`/projects/${projectCode}/workspace/work-logs/new?work_order_id=${order.id}&equipment_id=${(order as any).equipment_id || ''}&project_id=${projectId}`)}
                      className="flex items-center justify-center gap-2 py-2.5 bg-green-600 hover:bg-green-700 text-white rounded-xl text-sm font-medium transition-colors"
                    >
                      <Clock className="w-4 h-4" />
                      דיווח
                    </button>
                    <button
                      onClick={() => window.open(`/api/v1/work-orders/${order.id}/pdf`, '_blank')}
                      className="flex items-center justify-center gap-1.5 py-2.5 bg-white border border-gray-200 hover:bg-gray-50 text-gray-700 rounded-xl text-sm font-medium transition-colors"
                    >
                      <Eye className="w-4 h-4" />
                      פרטים
                    </button>
                    <button
                      onClick={async () => {
                        if (!confirm(`האם להסיר כלי מהפרויקט?\nהזמנה #${(order as any).order_number || order.id}\nיתרה תקציבית תשוחרר.`)) return;
                        try {
                          await api.post(`/work-orders/${order.id}/remove-equipment`);
                          window.location.reload();
                        } catch { /* error handled by interceptor */ }
                      }}
                      className="flex items-center justify-center gap-1.5 py-2.5 bg-white border border-red-200 hover:bg-red-50 text-red-600 rounded-xl text-xs font-medium transition-colors"
                    >
                      הסר כלי
                    </button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Empty state */}
      {approvedOrders.length === 0 && worklogs.length === 0 && !showForm && (
        <div className="bg-white rounded-xl border p-8 text-center">
          <Wrench className="w-12 h-12 text-gray-300 mx-auto mb-3" />
          <p className="text-gray-500">אין כלים פעילים בפרויקט</p>
          <p className="text-xs text-gray-400 mt-1">צור הזמנת עבודה וסרוק כלי כדי להתחיל</p>
        </div>
      )}
    </div>
  );
};

// 
// טאב יומן פעילות
// 
interface ActivityEntry {
  id: number;
  action: string;
  activity_type: string;
  description?: string;
  entity_type?: string;
  entity_id?: number;
  entity_name?: string;
  created_at: string;
  user_name?: string;
}

const ACTION_META: Record<string, { icon: React.FC<{ className?: string }>; label: string; color: string }> = {
  user_login: { icon: LogIn, label: 'כניסה למערכת', color: 'text-blue-500' },
  work_order_created: { icon: FilePlus, label: 'הזמנת עבודה נוצרה', color: 'text-green-600' },
  work_order_approved: { icon: FileCheck, label: 'הזמנת עבודה אושרה', color: 'text-emerald-600' },
  work_order_rejected: { icon: XCircle, label: 'הזמנת עבודה נדחתה', color: 'text-red-500' },
  work_order_sent: { icon: Send, label: 'הזמנה נשלחה לספק', color: 'text-purple-500' },
  worklog_created: { icon: FilePlus, label: 'דיווח שעות נוצר', color: 'text-blue-500' },
  worklog_approved: { icon: CheckCircle, label: 'דיווח שעות אושר', color: 'text-emerald-600' },
  worklog_rejected: { icon: XCircle, label: 'דיווח שעות נדחה', color: 'text-red-500' },
  invoice_created: { icon: FileText, label: 'חשבונית הופקה', color: 'text-orange-500' },
  invoice_approved: { icon: CheckCircle, label: 'חשבונית אושרה', color: 'text-emerald-600' },
  supplier_accepted: { icon: CheckCircle, label: 'ספק אישר הזמנה', color: 'text-green-500' },
  supplier_rejected: { icon: XCircle, label: 'ספק דחה הזמנה', color: 'text-red-500' },
};

function getActivityMeta(action: string) {
  const key = Object.keys(ACTION_META).find(k =>
    action?.toLowerCase().includes(k.replace(/_/g, '')) ||
    action?.toLowerCase() === k
  );
  return ACTION_META[key || ''] || { icon: Info, label: action || 'פעילות', color: 'text-gray-500' };
}

function formatActivityDate(iso: string) {
  try {
    const d = new Date(iso);
    const date = d.toLocaleDateString('he-IL', { day: '2-digit', month: '2-digit', year: 'numeric' });
    const time = d.toLocaleTimeString('he-IL', { hour: '2-digit', minute: '2-digit' });
    return { date, time };
  } catch {
    return { date: '', time: '' };
  }
}

const ActivityLogTab: React.FC<{ projectId: number }> = ({ projectId }) => {
  const [logs, setLogs] = useState<ActivityEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(false);
  const PAGE_SIZE = 20;

  useEffect(() => {
    setPage(1);
    setLogs([]);
    fetchLogs(1, true);
  }, [projectId]);

  const fetchLogs = async (pageNum: number, reset = false) => {
    try {
      setLoading(true);
      const resp = await api.get('/activity-logs/', {
        params: { project_id: projectId, limit: PAGE_SIZE, skip: (pageNum - 1) * PAGE_SIZE }
      });
      const data = resp.data;
      const items: ActivityEntry[] = Array.isArray(data) ? data : (data.items || []);
      const total: number = typeof data === 'object' && data.total !== undefined ? data.total : items.length;

      setLogs(prev => reset ? items : [...prev, ...items]);
      setHasMore((pageNum * PAGE_SIZE) < total);
      setError(null);
    } catch {
      setError('שגיאה בטעינת יומן הפעילות');
    } finally {
      setLoading(false);
    }
  };

  const loadMore = () => {
    const next = page + 1;
    setPage(next);
    fetchLogs(next);
  };

  if (loading && logs.length === 0) {
    return (
      <div className="flex items-center justify-center py-16">
        <div className="relative overflow-visible" style={{ padding: 4 }}>
          <div className="w-10 h-10 rounded-full border-[3px] border-emerald-200 border-t-emerald-500 animate-spin" style={{ animationDuration: '0.9s' }} />
          <div className="absolute inset-0 flex items-center justify-center">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 100" width="20" height="17">
              <defs>
                <linearGradient id="pw1_t" x1="0%" y1="0%" x2="100%" y2="0%"><stop offset="0%" stopColor="#1565c0" /><stop offset="100%" stopColor="#0097a7" /></linearGradient>
                <linearGradient id="pw1_m" x1="0%" y1="0%" x2="100%" y2="0%"><stop offset="0%" stopColor="#0097a7" /><stop offset="50%" stopColor="#2e7d32" /><stop offset="100%" stopColor="#66bb6a" /></linearGradient>
                <linearGradient id="pw1_b" x1="0%" y1="0%" x2="100%" y2="0%"><stop offset="0%" stopColor="#2e7d32" /><stop offset="40%" stopColor="#66bb6a" /><stop offset="100%" stopColor="#8B5e3c" /></linearGradient>
              </defs>
              <path d="M46 20 Q60 9 74 20" stroke="url(#pw1_t)" strokeWidth="5.5" fill="none" strokeLinecap="round" />
              <path d="M30 47 Q42 34 60 43 Q78 34 90 47" stroke="url(#pw1_m)" strokeWidth="5.5" fill="none" strokeLinecap="round" />
              <path d="M14 74 Q28 60 46 69 Q60 76 74 69 Q92 60 106 74" stroke="url(#pw1_b)" strokeWidth="5.5" fill="none" strokeLinecap="round" />
              <line x1="60" y1="76" x2="60" y2="90" stroke="#8B5e3c" strokeWidth="3.5" strokeLinecap="round" />
              <circle cx="60" cy="95" r="5" fill="#8B5e3c" />
            </svg>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-xl p-6 text-center text-red-600">
        <AlertCircle className="w-8 h-8 mx-auto mb-2" />
        {error}
      </div>
    );
  }

  if (logs.length === 0) {
    return (
      <div className="bg-white rounded-xl shadow-sm p-12 text-center">
        <Activity className="w-12 h-12 text-gray-300 mx-auto mb-4" />
        <p className="text-gray-500 font-medium">אין פעילות רשומה לפרויקט זה</p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-xl shadow-sm overflow-hidden">
      {/* Header */}
      <div className="px-5 py-4 border-b border-gray-100 flex items-center gap-2">
        <Activity className="w-5 h-5 text-green-600" />
        <h3 className="font-semibold text-gray-800">יומן פעילות בפרויקט</h3>
        <span className="text-xs text-gray-400 mr-auto">{logs.length} פעולות</span>
      </div>

      {/* Timeline */}
      <div className="divide-y divide-gray-50">
        {logs.map((entry, idx) => {
          const meta = getActivityMeta(entry.action || entry.activity_type);
          const Icon = meta.icon;
          const { date, time } = formatActivityDate(entry.created_at);
          const label = entry.description || meta.label;

          return (
            <div key={entry.id || idx} className="flex items-start gap-3 px-5 py-3 hover:bg-gray-50 transition-colors">
              {/* Icon */}
              <div className={`mt-0.5 flex-shrink-0 w-8 h-8 rounded-full bg-gray-50 flex items-center justify-center ${meta.color}`}>
                <Icon className="w-4 h-4" />
              </div>

              {/* Content */}
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-800 leading-snug">{label}</p>
                {entry.entity_name && (
                  <p className="text-xs text-gray-500 mt-0.5 truncate">{entry.entity_name}</p>
                )}
              </div>

              {/* Date */}
              <div className="text-left flex-shrink-0 text-xs text-gray-400 leading-snug">
                <div>{date}</div>
                <div>{time}</div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Load more */}
      {hasMore && (
        <div className="p-4 text-center border-t border-gray-100">
          <button
            onClick={loadMore}
            disabled={loading}
            className="px-5 py-2 text-sm text-green-600 hover:text-green-800 font-medium disabled:opacity-50"
          >
            {loading ? 'טוען...' : 'טען עוד'}
          </button>
        </div>
      )}
    </div>
  );
};

// BudgetTab 
const BudgetTab: React.FC<{ project: Project; stats: ProjectStats }> = ({ project, stats }) => {
  const paidPercent = stats.budgetTotal > 0 ? Math.round((stats.budgetSpent / stats.budgetTotal) * 100) : 0;
  const committedPercent = stats.budgetTotal > 0 ? Math.round((stats.budgetCommitted / stats.budgetTotal) * 100) : 0;
  const availablePercent = stats.budgetTotal > 0 ? Math.round((stats.budgetAvailable / stats.budgetTotal) * 100) : 0;

  return (
    <div className="space-y-4">
      {/* כותרת */}
      <div className="bg-white rounded-xl border p-5">
        <div className="flex items-center gap-2 mb-4">
          <Calculator className="w-5 h-5 text-green-600" />
          <h2 className="text-lg font-bold text-gray-900">ניצול תקציב — {project.name}</h2>
        </div>

        {/* Summary bar */}
        <div className="mb-4">
          <div className="flex justify-between text-sm mb-1">
            <span className="text-gray-500">תקציב כולל</span>
            <span className="font-bold text-gray-900">{stats.budgetTotal.toLocaleString()}</span>
          </div>
          <div className="h-4 bg-gray-100 rounded-full overflow-hidden flex">
            <div className="bg-green-500 h-full transition-all" style={{ width: `${paidPercent}%` }} title={`נוצל ${paidPercent}%`} />
            <div className="bg-yellow-400 h-full transition-all" style={{ width: `${committedPercent}%` }} title={`מוקפא ${committedPercent}%`} />
          </div>
          <div className="flex gap-4 mt-2 text-xs text-gray-500">
            <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded-full bg-green-500 inline-block" />נוצל {paidPercent}%</span>
            <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded-full bg-yellow-400 inline-block" />מוקפא {committedPercent}%</span>
            <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded-full bg-gray-200 inline-block" />זמין {availablePercent}%</span>
          </div>
        </div>

        {/* 4 פרטים */}
        <div className="divide-y divide-gray-50 text-sm">
          <div className="flex justify-between py-2">
            <span className="text-gray-500">תקציב כולל</span>
            <span className="font-semibold text-gray-800">{stats.budgetTotal.toLocaleString()}</span>
          </div>
          <div className="flex justify-between py-2">
            <span className="text-yellow-600"> מוקפא (הזמנות פתוחות)</span>
            <span className="font-semibold text-yellow-700">{stats.budgetCommitted.toLocaleString()}</span>
          </div>
          <div className="flex justify-between py-2">
            <span className="text-green-600"> נוצל (חשבוניות שולמו)</span>
            <span className="font-semibold text-green-700">{stats.budgetSpent.toLocaleString()}</span>
          </div>
          <div className="flex justify-between py-2 font-bold text-base">
            <span className="text-gray-700">זמין לשימוש</span>
            <span className={stats.budgetAvailable < 0 ? 'text-red-600' : 'text-green-700'}>
              {stats.budgetAvailable.toLocaleString()}
            </span>
          </div>
        </div>
      </div>

      {/* אזהרה אם תקציב חרג */}
      {stats.budgetAvailable < 0 && (
        <div className="bg-red-50 border border-red-200 rounded-xl p-4 flex items-center gap-3">
          <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0" />
          <p className="text-sm text-red-700 font-medium">חריגה מהתקציב של {Math.abs(stats.budgetAvailable).toLocaleString()}</p>
        </div>
      )}

      {/* כרטיסי סיכום */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {[
          { label: 'הזמנות פעילות', value: stats.activeOrders, color: 'text-blue-600', bg: 'bg-blue-50' },
          { label: 'ממתינות לאישור', value: stats.pendingOrders, color: 'text-yellow-600', bg: 'bg-yellow-50' },
          { label: 'דיווחים פתוחים', value: stats.openReports, color: 'text-orange-600', bg: 'bg-orange-50' },
          { label: 'דיווחים ממתינים', value: stats.pendingReports, color: 'text-purple-600', bg: 'bg-purple-50' },
        ].map(({ label, value, color, bg }) => (
          <div key={label} className={`${bg} rounded-xl p-4 text-center`}>
            <p className={`text-2xl font-bold ${color}`}>{value}</p>
            <p className="text-xs text-gray-500 mt-1">{label}</p>
          </div>
        ))}
      </div>
    </div>
  );
};

// DocumentsTab 
const DocumentsTab: React.FC<{ projectId: number }> = ({ projectId: _projectId }) => (
  <div className="bg-white rounded-xl border p-12 text-center">
    <FileText className="w-12 h-12 text-gray-300 mx-auto mb-3" />
    <p className="text-gray-500 font-medium">מסמכים</p>
    <p className="text-gray-400 text-sm mt-1">מודול המסמכים יפעיל בקרוב</p>
  </div>
);

export default ProjectWorkspaceNew;
