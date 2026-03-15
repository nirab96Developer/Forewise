// src/pages/Settings/Budgets.tsx
// ניהול תקציבים — היררכיה: מרחבים / אזורים / פרויקטים
import React, { useState, useEffect, useMemo } from "react";
import {
  DollarSign, Plus, ChevronDown, ChevronRight, Edit2,
  X, Loader2, CheckCircle, AlertCircle, Search
} from "lucide-react";
import api from "../../services/api";
import UnifiedLoader from "../../components/common/UnifiedLoader";

// ─── Types ───────────────────────────────────────────────────────────────────
interface BudgetItem {
  id: number;
  total_amount: number;
  committed_amount: number;
  spent_amount: number;
  remaining_amount?: number;
  project_id?: number | null;
  project_name?: string | null;
  project_code?: string | null;
  area_id?: number | null;
  area_name?: string | null;
  region_id?: number | null;
  region_name?: string | null;
  forest_name?: string | null;
  description?: string | null;
}

interface SummaryRegion {
  id: number; name: string; budget_id?: number | null;
  total_amount: number; committed_amount: number;
  spent_amount: number; remaining_amount: number; utilization_pct: number;
}
interface SummaryArea {
  id: number; name: string; region_id?: number; region_name?: string; budget_id?: number | null;
  total_amount: number; committed_amount: number;
  spent_amount: number; remaining_amount: number; utilization_pct: number;
}
interface SummaryProject {
  id: number; project_id: number; project_name: string; project_code?: string;
  forest_name?: string; area_id?: number; area_name?: string;
  region_id?: number; region_name?: string;
  total_amount: number; committed_amount: number;
  spent_amount: number; remaining_amount: number; utilization_pct: number;
}
interface BudgetSummary {
  regions: SummaryRegion[];
  areas: SummaryArea[];
  projects: SummaryProject[];
}

interface Region { id: number; name: string; }
interface Area   { id: number; name: string; region_id: number; }
interface Project {
  id: number; name: string; code: string;
  area_id?: number | null; area_name?: string | null;
  region_id?: number | null; region_name?: string | null;
  forest_name?: string | null;
  location?: { name?: string } | null;
}

type TabId = 'regions' | 'areas' | 'projects';

// ─── Helpers ─────────────────────────────────────────────────────────────────
const fmt = (n?: number | null) =>
  n != null ? `₪${Number(n).toLocaleString('he-IL')}` : '₪0';

const pct = (spent?: number | null, total?: number | null) => {
  if (!total || total <= 0) return 0;
  return Math.min(100, Math.round((Number(spent || 0) / Number(total)) * 100));
};

const pctColor = (p: number) =>
  p >= 90 ? 'bg-red-500' : p >= 70 ? 'bg-yellow-400' : 'bg-green-500';

const pctTextColor = (p: number) =>
  p >= 90 ? 'text-red-600' : p >= 70 ? 'text-yellow-600' : 'text-green-600';

function PctBar({ p }: { p: number }) {
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-2 bg-gray-100 rounded-full overflow-hidden">
        <div className={`h-full rounded-full ${pctColor(p)}`} style={{ width: `${p}%` }} />
      </div>
      <span className={`text-xs font-medium w-8 text-left ${pctTextColor(p)}`}>{p}%</span>
    </div>
  );
}

// ─── Edit Modal ───────────────────────────────────────────────────────────────
function EditBudgetModal({
  budget, onClose, onSaved,
}: { budget: BudgetItem; onClose: () => void; onSaved: () => void }) {
  const [amount, setAmount]  = useState(budget.total_amount?.toString() || '');
  const [desc, setDesc]      = useState(budget.description || '');
  const [saving, setSaving]  = useState(false);
  const [err, setErr]        = useState('');

  const handleSave = async () => {
    if (!amount || Number(amount) <= 0) { setErr('יש להזין סכום תקציב'); return; }
    setSaving(true); setErr('');
    try {
      await api.put(`/budgets/${budget.id}`, { total_amount: Number(amount), description: desc });
      onSaved();
    } catch (e: any) {
      setErr(e?.response?.data?.detail || 'שגיאה בשמירה');
    } finally { setSaving(false); }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4" onClick={onClose}>
      <div className="bg-white rounded-xl shadow-xl w-full max-w-md" onClick={e => e.stopPropagation()}>
        <div className="bg-orange-500 p-4 rounded-t-xl flex items-center justify-between">
          <h3 className="font-bold text-white">עריכת תקציב</h3>
          <button onClick={onClose} className="p-1 hover:bg-white/20 rounded-lg"><X className="w-4 h-4 text-white" /></button>
        </div>
        <div className="p-5 space-y-4">
          <p className="text-sm text-gray-600">
            {budget.project_name || budget.area_name || budget.region_name}
          </p>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">סכום תקציב (₪)</label>
            <input type="number" value={amount} onChange={e => setAmount(e.target.value)} min="0"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-400 text-sm" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">תיאור (אופציונלי)</label>
            <textarea value={desc} onChange={e => setDesc(e.target.value)} rows={2}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-400 text-sm resize-none" />
          </div>
          {err && <p className="text-red-500 text-sm">{err}</p>}
          <div className="flex gap-2">
            <button onClick={onClose} className="flex-1 py-2.5 border border-gray-200 rounded-lg text-gray-600 hover:bg-gray-50 text-sm">ביטול</button>
            <button onClick={handleSave} disabled={saving}
              className="flex-1 py-2.5 bg-orange-500 hover:bg-orange-600 text-white rounded-lg text-sm font-medium disabled:opacity-50 flex items-center justify-center gap-1.5">
              {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <CheckCircle className="w-4 h-4" />}
              שמור
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

// ─── New Budget Modal ─────────────────────────────────────────────────────────
function NewBudgetModal({
  regions, areas, projects, onClose, onSaved,
}: {
  regions: Region[]; areas: Area[]; projects: Project[];
  onClose: () => void; onSaved: () => void;
}) {
  const [level,     setLevel]     = useState<'region' | 'area' | 'project'>('project');
  const [regionId,  setRegionId]  = useState('');
  const [areaId,    setAreaId]    = useState('');
  const [projectId, setProjectId] = useState('');
  const [amount,    setAmount]    = useState('');
  const [desc,      setDesc]      = useState('');
  const [saving,    setSaving]    = useState(false);
  const [err,       setErr]       = useState('');

  const filteredAreas    = areas.filter(a => !regionId || a.region_id === Number(regionId));
  const filteredProjects = projects.filter(p =>
    (!regionId || p.region_id === Number(regionId)) &&
    (!areaId   || p.area_id   === Number(areaId))
  );

  const handleSave = async () => {
    if (!amount || Number(amount) <= 0) { setErr('יש להזין סכום תקציב'); return; }
    if (level === 'region' && !regionId)  { setErr('בחר מרחב'); return; }
    if (level === 'area'   && !areaId)    { setErr('בחר אזור'); return; }
    if (level === 'project'&& !projectId) { setErr('בחר פרויקט'); return; }
    setSaving(true); setErr('');
    try {
      const payload: Record<string, unknown> = {
        total_amount: Number(amount),
        description: desc || null,
      };
      if (level === 'region')  payload.region_id  = Number(regionId);
      if (level === 'area')    payload.area_id     = Number(areaId);
      if (level === 'project') payload.project_id  = Number(projectId);
      await api.post('/budgets/', payload);
      onSaved();
    } catch (e: any) {
      setErr(e?.response?.data?.detail || 'שגיאה ביצירת תקציב');
    } finally { setSaving(false); }
  };

  const selectedProject = projects.find(p => p.id === Number(projectId));

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4" onClick={onClose}>
      <div className="bg-white rounded-xl shadow-xl w-full max-w-lg" onClick={e => e.stopPropagation()}>
        <div className="bg-green-600 p-4 rounded-t-xl flex items-center justify-between">
          <h3 className="font-bold text-white">הקצאת תקציב חדש</h3>
          <button onClick={onClose} className="p-1 hover:bg-white/20 rounded-lg"><X className="w-4 h-4 text-white" /></button>
        </div>
        <div className="p-5 space-y-4">

          {/* שלב 1 — רמה */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">שלב 1 — בחר רמה</label>
            <div className="grid grid-cols-3 gap-2">
              {(['region', 'area', 'project'] as const).map(l => (
                <button key={l}
                  onClick={() => { setLevel(l); setRegionId(''); setAreaId(''); setProjectId(''); }}
                  className={`py-2 rounded-lg text-sm font-medium border transition-colors ${
                    level === l ? 'bg-green-600 text-white border-green-600' : 'border-gray-200 text-gray-600 hover:bg-gray-50'
                  }`}
                >
                  {l === 'region' ? 'מרחב' : l === 'area' ? 'אזור' : 'פרויקט'}
                </button>
              ))}
            </div>
          </div>

          {/* שלב 2 — dropdown מסונן */}
          <div className="space-y-3">
            <label className="block text-sm font-medium text-gray-700">שלב 2 — בחר {level === 'region' ? 'מרחב' : level === 'area' ? 'אזור' : 'פרויקט'}</label>

            {/* תמיד בוחרים מרחב קודם (אלא אם level = region) */}
            {(level === 'area' || level === 'project') && (
              <select value={regionId} onChange={e => { setRegionId(e.target.value); setAreaId(''); setProjectId(''); }}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-green-400">
                <option value="">— בחר מרחב —</option>
                {regions.map(r => <option key={r.id} value={r.id}>{r.name}</option>)}
              </select>
            )}

            {level === 'region' && (
              <select value={regionId} onChange={e => setRegionId(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-green-400">
                <option value="">— בחר מרחב —</option>
                {regions.map(r => <option key={r.id} value={r.id}>{r.name}</option>)}
              </select>
            )}

            {(level === 'area' || level === 'project') && regionId && (
              <select value={areaId} onChange={e => { setAreaId(e.target.value); setProjectId(''); }}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-green-400">
                <option value="">— בחר אזור —</option>
                {filteredAreas.map(a => <option key={a.id} value={a.id}>{a.name}</option>)}
              </select>
            )}

            {level === 'project' && areaId && (
              <select value={projectId} onChange={e => setProjectId(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-green-400">
                <option value="">— בחר פרויקט —</option>
                {filteredProjects.map(p => {
                  const forestName = p.location?.name || p.forest_name;
                  const label = forestName
                    ? `${p.name} — יער ${forestName} (${p.code})`
                    : `${p.name} (${p.code})`;
                  return (
                    <option key={p.id} value={p.id}>{label}</option>
                  );
                })}
              </select>
            )}

            {selectedProject && (
              <div className="bg-green-50 border border-green-200 rounded-lg p-3 text-sm text-green-700">
                🌳 {selectedProject.name}
                {(selectedProject.location?.name || selectedProject.forest_name) &&
                  ` — יער ${selectedProject.location?.name || selectedProject.forest_name}`}
                {` (${selectedProject.code})`}
                {selectedProject.area_name && ` • ${selectedProject.area_name}`}
              </div>
            )}
          </div>

          {/* שלב 3 — סכום */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">שלב 3 — סכום תקציב (₪)</label>
            <input type="number" value={amount} onChange={e => setAmount(e.target.value)} min="0" placeholder="לדוגמה: 500000"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-green-400" />
          </div>

          {/* שלב 4 — תיאור */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">שלב 4 — תיאור (אופציונלי)</label>
            <textarea value={desc} onChange={e => setDesc(e.target.value)} rows={2}
              placeholder="תיאור קצר להקצאת התקציב..."
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm resize-none focus:ring-2 focus:ring-green-400" />
          </div>

          {err && <p className="text-red-500 text-sm flex items-center gap-1"><AlertCircle className="w-3 h-3" />{err}</p>}

          <div className="flex gap-2 pt-1">
            <button onClick={onClose} className="flex-1 py-2.5 border border-gray-200 rounded-lg text-gray-600 hover:bg-gray-50 text-sm">ביטול</button>
            <button onClick={handleSave} disabled={saving}
              className="flex-1 py-2.5 bg-green-600 hover:bg-green-700 text-white rounded-lg text-sm font-medium disabled:opacity-50 flex items-center justify-center gap-1.5">
              {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <CheckCircle className="w-4 h-4" />}
              שמור
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

// ─── Main Component ───────────────────────────────────────────────────────────
const Budgets: React.FC = () => {
  const [budgets,  setBudgets]  = useState<BudgetItem[]>([]);
  const [regions,  setRegions]  = useState<Region[]>([]);
  const [areas,    setAreas]    = useState<Area[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [summary,  setSummary]  = useState<BudgetSummary | null>(null);
  const [loading,  setLoading]  = useState(true);
  const [tab,      setTab]      = useState<TabId>('regions');
  const [search,   setSearch]   = useState('');
  const [expandedRegions, setExpandedRegions] = useState<Set<number>>(new Set());
  const [editBudget,  setEditBudget]  = useState<BudgetItem | null>(null);
  const [showNew,     setShowNew]     = useState(false);

  const loadData = async () => {
    setLoading(true);
    try {
      const [bRes, rRes, aRes, pRes, sRes] = await Promise.allSettled([
        api.get('/budgets?page_size=500'),
        api.get('/regions'),
        api.get('/areas'),
        api.get('/projects?page_size=500&include_location=true'),
        api.get('/budgets/summary'),
      ]);
      if (bRes.status === 'fulfilled') setBudgets(bRes.value.data?.items || bRes.value.data || []);
      if (rRes.status === 'fulfilled') setRegions(rRes.value.data?.items || rRes.value.data || []);
      if (aRes.status === 'fulfilled') setAreas(aRes.value.data?.items   || aRes.value.data || []);
      if (pRes.status === 'fulfilled') setProjects(pRes.value.data?.items || pRes.value.data || []);
      if (sRes.status === 'fulfilled') setSummary(sRes.value.data || null);
    } catch { /* ignore */ }
    setLoading(false);
  };

  useEffect(() => { loadData(); }, []);

  // ── Aggregations ──────────────────────────────────────────────────────────

  const regionRows = useMemo(() => {
    // Prefer server-side summary (handles rollups correctly)
    if (summary && summary.regions.length > 0) {
      return summary.regions.map(sr => ({
        region: { id: sr.id, name: sr.name } as Region,
        total: sr.total_amount,
        spent: sr.spent_amount,
        committed: sr.committed_amount,
        budgets: sr.budget_id ? [{ id: sr.budget_id } as BudgetItem] : [],
      }));
    }
    // Fallback: client-side aggregation
    const map: Record<number, { region: Region; total: number; spent: number; committed: number; budgets: BudgetItem[] }> = {};
    regions.forEach(r => { map[r.id] = { region: r, total: 0, spent: 0, committed: 0, budgets: [] }; });
    budgets.forEach(b => {
      if (b.region_id && !b.area_id && !b.project_id) {
        const entry = map[b.region_id];
        if (entry) { entry.total += b.total_amount || 0; entry.spent += b.spent_amount || 0; entry.committed += b.committed_amount || 0; entry.budgets.push(b); }
      }
      if (b.project_id && b.region_id) {
        const entry = map[b.region_id];
        if (entry) { entry.total += b.total_amount || 0; entry.spent += b.spent_amount || 0; entry.committed += b.committed_amount || 0; }
      }
    });
    return Object.values(map).filter(r => r.total > 0 || r.budgets.length > 0);
  }, [budgets, regions, summary]);

  const areaRows = useMemo(() => {
    if (summary && summary.areas.length > 0) {
      return summary.areas.map(sa => ({
        area: { id: sa.id, name: sa.name, region_id: sa.region_id ?? 0 } as Area,
        region: sa.region_id ? { id: sa.region_id, name: sa.region_name || '' } as Region : undefined,
        total: sa.total_amount,
        spent: sa.spent_amount,
        committed: sa.committed_amount,
      }));
    }
    const map: Record<number, { area: Area; region?: Region; total: number; spent: number; committed: number }> = {};
    areas.forEach(a => { map[a.id] = { area: a, region: regions.find(r => r.id === a.region_id), total: 0, spent: 0, committed: 0 }; });
    budgets.forEach(b => {
      if (b.area_id && !b.project_id) {
        const e = map[b.area_id];
        if (e) { e.total += b.total_amount || 0; e.spent += b.spent_amount || 0; e.committed += b.committed_amount || 0; }
      }
      if (b.project_id && b.area_id) {
        const e = map[b.area_id];
        if (e) { e.total += b.total_amount || 0; e.spent += b.spent_amount || 0; e.committed += b.committed_amount || 0; }
      }
    });
    return Object.values(map).filter(a => a.total > 0);
  }, [budgets, areas, regions, summary]);

  const projectRows = useMemo(() => {
    if (summary && summary.projects.length > 0) {
      return summary.projects.map(sp => ({
        id: sp.id,
        total_amount: sp.total_amount,
        committed_amount: sp.committed_amount,
        spent_amount: sp.spent_amount,
        remaining_amount: sp.remaining_amount,
        project_id: sp.project_id,
        project_name: sp.project_name,
        project_code: sp.project_code,
        forest_name: sp.forest_name,
        area_id: sp.area_id,
        area_name: sp.area_name,
        region_id: sp.region_id,
        region_name: sp.region_name,
      } as BudgetItem));
    }
    return budgets.filter(b => !!b.project_id);
  }, [budgets, summary]);

  // ── Filter by search ──────────────────────────────────────────────────────
  const q = search.toLowerCase();
  const filteredRegionRows  = regionRows.filter(r  => !q || r.region.name.toLowerCase().includes(q));
  const filteredAreaRows    = areaRows.filter(a    => !q || a.area.name.toLowerCase().includes(q) || (a.region?.name || '').toLowerCase().includes(q));
  const filteredProjectRows = projectRows.filter(p => !q || (p.project_name || '').toLowerCase().includes(q) || (p.project_code || '').toLowerCase().includes(q) || (p.area_name || '').toLowerCase().includes(q) || (p.region_name || '').toLowerCase().includes(q));

  const toggleRegion = (id: number) =>
    setExpandedRegions(prev => { const s = new Set(prev); s.has(id) ? s.delete(id) : s.add(id); return s; });

  // ── Table header ──────────────────────────────────────────────────────────
  const TH: React.FC<{ children: React.ReactNode; className?: string }> =
    ({ children, className = '' }) => (
      <th className={`text-right text-xs font-semibold text-gray-500 uppercase tracking-wide px-4 py-3 ${className}`}>
        {children}
      </th>
    );

  if (loading) return <UnifiedLoader size="full" />;

  return (
    <div className="min-h-screen bg-gray-50 pt-16 sm:pt-0" dir="rtl">

      {/* ── Header ── */}
      <div className="bg-white border-b shadow-sm sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-3 sm:px-6 py-3 sm:py-4">
          <div className="flex items-center justify-between gap-3">
            <div className="flex items-center gap-2 sm:gap-3 min-w-0">
              <div className="w-9 h-9 sm:w-10 sm:h-10 bg-orange-100 rounded-xl flex items-center justify-center flex-shrink-0">
                <DollarSign className="w-5 h-5 text-orange-600" />
              </div>
              <div className="min-w-0">
                <h1 className="text-lg sm:text-xl font-bold text-gray-900 truncate">ניהול תקציבים</h1>
                <p className="text-xs sm:text-sm text-gray-500 hidden sm:block">היררכיה: מרחבים → אזורים → פרויקטים</p>
              </div>
            </div>
            <button
              onClick={() => setShowNew(true)}
              className="flex items-center gap-1.5 px-3 sm:px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg text-sm font-medium transition-colors flex-shrink-0 min-h-[44px]"
            >
              <Plus className="w-4 h-4 flex-shrink-0" />
              <span className="hidden sm:inline">הקצאת תקציב חדש</span>
              <span className="sm:hidden">+ תקציב</span>
            </button>
          </div>

          {/* Tabs + Search */}
          <div className="flex items-center justify-between mt-3 gap-2">
            <div className="flex gap-0.5 sm:gap-1 bg-gray-100 rounded-lg p-1 overflow-x-auto">
              {([['regions', 'מרחבים'], ['areas', 'אזורים'], ['projects', 'פרויקטים']] as [TabId, string][]).map(([id, label]) => (
                <button key={id} onClick={() => setTab(id)}
                  className={`px-3 sm:px-4 py-1.5 rounded-md text-sm font-medium transition-colors whitespace-nowrap ${tab === id ? 'bg-white shadow-sm text-orange-600' : 'text-gray-600 hover:text-gray-800'}`}>
                  {label}
                </button>
              ))}
            </div>
            <div className="relative flex-shrink-0">
              <Search className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                value={search} onChange={e => setSearch(e.target.value)}
                placeholder="חפש..."
                className="pr-9 pl-3 py-1.5 border border-gray-200 rounded-lg text-base w-32 sm:w-48 focus:outline-none focus:ring-2 focus:ring-orange-300"
                style={{ fontSize: '16px' }}
              />
            </div>
          </div>
        </div>
      </div>

      {/* ── Content ── */}
      <div className="max-w-7xl mx-auto px-3 sm:px-6 py-4 sm:py-6">

        {/* ══ Tab: מרחבים ══ */}
        {tab === 'regions' && (
          <>
          {/* Mobile: cards */}
          <div className="md:hidden space-y-3">
            {filteredRegionRows.length === 0 ? (
              <div className="text-center py-12 text-gray-400">אין נתוני תקציב</div>
            ) : filteredRegionRows.map(({ region, total, spent, committed }) => {
              const remaining = total - spent - committed;
              const p = pct(spent + committed, total);
              return (
                <div key={region.id} className="bg-white rounded-xl border shadow-sm p-4">
                  <div className="flex justify-between items-center mb-2">
                    <span className="font-bold text-gray-800">{region.name}</span>
                    <span className={`text-sm font-semibold ${p >= 90 ? 'text-red-600' : p >= 70 ? 'text-yellow-600' : 'text-green-600'}`}>{p}%</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2 mb-2">
                    <div className={`h-2 rounded-full ${pctColor(p)}`} style={{ width: `${p}%` }} />
                  </div>
                  <div className="flex justify-between text-xs text-gray-500">
                    <span>{fmt(spent)} נוצל</span>
                    <span className={remaining < 0 ? 'text-red-600 font-medium' : 'text-green-600 font-medium'}>{fmt(remaining)} נותר</span>
                  </div>
                  <div className="text-xs text-gray-400 mt-1">תקציב כולל: {fmt(total)}</div>
                </div>
              );
            })}
          </div>
          {/* Desktop: table */}
          <div className="hidden md:block bg-white rounded-xl shadow-sm border overflow-hidden">
            <table className="w-full">
              <thead className="bg-gray-50 border-b">
                <tr>
                  <TH className="w-8">{' '}</TH>
                  <TH>מרחב</TH>
                  <TH>תקציב כולל</TH>
                  <TH>מנוצל</TH>
                  <TH>נותר</TH>
                  <TH>% ניצול</TH>
                  <TH className="w-20">פעולות</TH>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50">
                {filteredRegionRows.length === 0 ? (
                  <tr><td colSpan={7} className="text-center py-12 text-gray-400">אין נתוני תקציב</td></tr>
                ) : filteredRegionRows.map(({ region, total, spent, committed, budgets: rBudgets }) => {
                  const remaining = total - spent - committed;
                  const p = pct(spent, total);
                  const isExpanded = expandedRegions.has(region.id);
                  const areaRowsForRegion = areaRows.filter(a => a.area.region_id === region.id && a.total > 0);
                  return (
                    <React.Fragment key={region.id}>
                      <tr className="hover:bg-orange-50/30 transition-colors">
                        <td className="px-4 py-3">
                          {areaRowsForRegion.length > 0 && (
                            <button onClick={() => toggleRegion(region.id)}
                              className="p-0.5 rounded hover:bg-gray-100">
                              {isExpanded
                                ? <ChevronDown className="w-4 h-4 text-gray-400" />
                                : <ChevronRight className="w-4 h-4 text-gray-400" />}
                            </button>
                          )}
                        </td>
                        <td className="px-4 py-3 font-semibold text-gray-800">{region.name}</td>
                        <td className="px-4 py-3 text-gray-700">{fmt(total)}</td>
                        <td className="px-4 py-3 text-gray-700">{fmt(spent)}</td>
                        <td className={`px-4 py-3 font-medium ${remaining < 0 ? 'text-red-600' : 'text-green-700'}`}>{fmt(remaining)}</td>
                        <td className="px-4 py-3 w-32"><PctBar p={p} /></td>
                        <td className="px-4 py-3">
                          {rBudgets[0] && (
                            <button onClick={() => setEditBudget(rBudgets[0])}
                              className="p-1.5 text-gray-400 hover:text-orange-600 hover:bg-orange-50 rounded-lg transition-colors">
                              <Edit2 className="w-4 h-4" />
                            </button>
                          )}
                        </td>
                      </tr>
                      {/* Expanded area rows */}
                      {isExpanded && areaRowsForRegion.map(({ area, total: at, spent: as_, committed: ac }) => {
                        const ar = at - as_ - ac;
                        const ap = pct(as_, at);
                        return (
                          <tr key={area.id} className="bg-orange-50/50">
                            <td />
                            <td className="px-4 py-2 pl-8 text-sm text-gray-600">↳ {area.name}</td>
                            <td className="px-4 py-2 text-sm text-gray-600">{fmt(at)}</td>
                            <td className="px-4 py-2 text-sm text-gray-600">{fmt(as_)}</td>
                            <td className={`px-4 py-2 text-sm font-medium ${ar < 0 ? 'text-red-500' : 'text-green-600'}`}>{fmt(ar)}</td>
                            <td className="px-4 py-2 w-32"><PctBar p={ap} /></td>
                            <td />
                          </tr>
                        );
                      })}
                    </React.Fragment>
                  );
                })}
              </tbody>
            </table>
          </div>
          </>
        )}

        {/* ══ Tab: אזורים ══ */}
        {tab === 'areas' && (
          <>
          {/* Mobile: cards */}
          <div className="md:hidden space-y-3">
            {filteredAreaRows.length === 0 ? (
              <div className="text-center py-12 text-gray-400">אין נתוני תקציב לאזורים</div>
            ) : filteredAreaRows.map(({ area, region, total, spent, committed }) => {
              const remaining = total - spent - committed;
              const p = pct(spent + committed, total);
              return (
                <div key={area.id} className="bg-white rounded-xl border shadow-sm p-4">
                  <div className="flex justify-between items-center mb-1">
                    <span className="font-bold text-gray-800">{area.name}</span>
                    <span className={`text-sm font-semibold ${p >= 90 ? 'text-red-600' : p >= 70 ? 'text-yellow-600' : 'text-green-600'}`}>{p}%</span>
                  </div>
                  {region && <div className="text-xs text-gray-400 mb-2">{region.name}</div>}
                  <div className="w-full bg-gray-200 rounded-full h-2 mb-2">
                    <div className={`h-2 rounded-full ${pctColor(p)}`} style={{ width: `${p}%` }} />
                  </div>
                  <div className="flex justify-between text-xs text-gray-500">
                    <span>{fmt(spent)} נוצל</span>
                    <span className={remaining < 0 ? 'text-red-600 font-medium' : 'text-green-600 font-medium'}>{fmt(remaining)} נותר</span>
                  </div>
                </div>
              );
            })}
          </div>
          {/* Desktop: table */}
          <div className="hidden md:block bg-white rounded-xl shadow-sm border overflow-hidden">
            <table className="w-full">
              <thead className="bg-gray-50 border-b">
                <tr>
                  <TH>מרחב</TH>
                  <TH>אזור</TH>
                  <TH>תקציב</TH>
                  <TH>מנוצל</TH>
                  <TH>נותר</TH>
                  <TH>% ניצול</TH>
                  <TH className="w-20">פעולות</TH>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50">
                {filteredAreaRows.length === 0 ? (
                  <tr><td colSpan={7} className="text-center py-12 text-gray-400">אין נתוני תקציב לאזורים</td></tr>
                ) : filteredAreaRows.map(({ area, region, total, spent, committed }) => {
                  const remaining = total - spent - committed;
                  const p = pct(spent, total);
                  const areaBudget = budgets.find(b => b.area_id === area.id && !b.project_id);
                  return (
                    <tr key={area.id} className="hover:bg-orange-50/30 transition-colors">
                      <td className="px-4 py-3 text-sm text-gray-500">{region?.name || '—'}</td>
                      <td className="px-4 py-3 font-semibold text-gray-800">{area.name}</td>
                      <td className="px-4 py-3 text-gray-700">{fmt(total)}</td>
                      <td className="px-4 py-3 text-gray-700">{fmt(spent)}</td>
                      <td className={`px-4 py-3 font-medium ${remaining < 0 ? 'text-red-600' : 'text-green-700'}`}>{fmt(remaining)}</td>
                      <td className="px-4 py-3 w-32"><PctBar p={p} /></td>
                      <td className="px-4 py-3">
                        {areaBudget && (
                          <button onClick={() => setEditBudget(areaBudget)}
                            className="p-1.5 text-gray-400 hover:text-orange-600 hover:bg-orange-50 rounded-lg transition-colors">
                            <Edit2 className="w-4 h-4" />
                          </button>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
          </>
        )}

        {/* ══ Tab: פרויקטים ══ */}
        {tab === 'projects' && (
          <>
          {/* Mobile: cards */}
          <div className="md:hidden space-y-3">
            {filteredProjectRows.length === 0 ? (
              <div className="text-center py-12 text-gray-400">אין נתוני תקציב לפרויקטים</div>
            ) : filteredProjectRows.map((b) => {
              const total = b.total_amount || 0;
              const spent = b.spent_amount || 0;
              const committed = b.committed_amount || 0;
              const remaining = total - spent - committed;
              const p = pct(spent + committed, total);
              return (
                <div key={b.id} className="bg-white rounded-xl border shadow-sm p-4">
                  <div className="flex justify-between items-start mb-1">
                    <div>
                      <span className="font-bold text-gray-800 text-sm">{b.project_name || '—'}</span>
                      {b.project_code && <span className="text-xs text-gray-400 mr-2">{b.project_code}</span>}
                    </div>
                    <span className={`text-sm font-semibold ${p >= 90 ? 'text-red-600' : p >= 70 ? 'text-yellow-600' : 'text-green-600'}`}>{p}%</span>
                  </div>
                  {(b.area_name || b.region_name) && (
                    <div className="text-xs text-gray-400 mb-2">{b.region_name}{b.area_name ? ` › ${b.area_name}` : ''}</div>
                  )}
                  <div className="w-full bg-gray-200 rounded-full h-2 mb-2">
                    <div className={`h-2 rounded-full ${pctColor(p)}`} style={{ width: `${p}%` }} />
                  </div>
                  <div className="flex justify-between text-xs text-gray-500">
                    <span>{fmt(spent)} נוצל</span>
                    <span className={remaining < 0 ? 'text-red-600 font-medium' : 'text-green-600 font-medium'}>{fmt(remaining)} נותר</span>
                  </div>
                  <div className="flex justify-between items-center mt-2">
                    <span className="text-xs text-gray-400">תקציב: {fmt(total)}</span>
                    <button onClick={() => setEditBudget(b)}
                      className="p-1.5 text-gray-400 hover:text-orange-600 hover:bg-orange-50 rounded-lg">
                      <Edit2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
          {/* Desktop: table */}
          <div className="hidden md:block bg-white rounded-xl shadow-sm border overflow-hidden">
            <table className="w-full">
              <thead className="bg-gray-50 border-b">
                <tr>
                  <TH>מרחב</TH>
                  <TH>אזור</TH>
                  <TH>שם פרויקט</TH>
                  <TH>קוד</TH>
                  <TH>תקציב</TH>
                  <TH>מנוצל</TH>
                  <TH>נותר</TH>
                  <TH>% ניצול</TH>
                  <TH className="w-20">פעולות</TH>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50">
                {filteredProjectRows.length === 0 ? (
                  <tr><td colSpan={9} className="text-center py-12 text-gray-400">אין נתוני תקציב לפרויקטים</td></tr>
                ) : filteredProjectRows.map((b) => {
                  const total     = b.total_amount     || 0;
                  const spent     = b.spent_amount     || 0;
                  const committed = b.committed_amount || 0;
                  const remaining = total - spent - committed;
                  const p = pct(spent, total);
                  return (
                    <tr key={b.id} className="hover:bg-orange-50/30 transition-colors">
                      <td className="px-4 py-3 text-sm text-gray-500">{b.region_name || '—'}</td>
                      <td className="px-4 py-3 text-sm text-gray-500">{b.area_name   || '—'}</td>
                      <td className="px-4 py-3 font-medium text-gray-800">{b.project_name || '—'}</td>
                      <td className="px-4 py-3 text-xs font-mono text-gray-500">{b.project_code || '—'}</td>
                      <td className="px-4 py-3 text-gray-700">{fmt(total)}</td>
                      <td className="px-4 py-3 text-gray-700">{fmt(spent)}</td>
                      <td className={`px-4 py-3 font-medium ${remaining < 0 ? 'text-red-600' : 'text-green-700'}`}>{fmt(remaining)}</td>
                      <td className="px-4 py-3 w-32"><PctBar p={p} /></td>
                      <td className="px-4 py-3">
                        <button onClick={() => setEditBudget(b)}
                          className="p-1.5 text-gray-400 hover:text-orange-600 hover:bg-orange-50 rounded-lg transition-colors">
                          <Edit2 className="w-4 h-4" />
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
          </>
        )}
      </div>

      {/* ── Modals ── */}
      {editBudget && (
        <EditBudgetModal
          budget={editBudget}
          onClose={() => setEditBudget(null)}
          onSaved={() => { setEditBudget(null); loadData(); }}
        />
      )}
      {showNew && (
        <NewBudgetModal
          regions={regions} areas={areas} projects={projects}
          onClose={() => setShowNew(false)}
          onSaved={() => { setShowNew(false); loadData(); }}
        />
      )}
    </div>
  );
};

export default Budgets;
