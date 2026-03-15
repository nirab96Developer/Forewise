// תצורת תפריט דינמי - תפריט שונה לכל role
import {
  Home,
  Building2,
  Settings,
  BarChart3,
  Activity,
  MapPin,
  Receipt,
  ClipboardList,
  RefreshCcw,
  Truck,
  ScanLine,
  FileText,
  Wallet,
  ClipboardCheck,
  BookOpen,
  LucideIcon
} from "lucide-react";
import { PERMISSIONS, hasPermission, normalizeRole, UserRole } from "../utils/permissions";

// ============================================================
// Menu Item Interface
// ============================================================
export interface MenuItem {
  id: string;
  icon: LucideIcon;
  label: string;
  path: string;
  permission: string;  // Permission code from DB (DOMAIN.ACTION)
  badge?: string;
  children?: MenuItem[];
  dividerAfter?: boolean;
}

// ============================================================
// All Available Menu Items - Pool
// כל פריט תפריט אפשרי במערכת
// ============================================================
const MENU_ITEM_POOL: Record<string, MenuItem> = {
  dashboard: {
    id: "dashboard",
    icon: Home,
    label: "ראשי",
    path: "/",
    permission: PERMISSIONS.DASHBOARD_VIEW,
  },
  projects: {
    id: "projects",
    icon: Building2,
    label: "הפרויקטים שלי",
    path: "/projects",
    permission: PERMISSIONS.PROJECTS_VIEW,
  },
  projectsRegion: {
    id: "projects",
    icon: Building2,
    label: "פרויקטים במרחב",
    path: "/projects",
    permission: PERMISSIONS.PROJECTS_VIEW,
  },
  projectsArea: {
    id: "projects",
    icon: Building2,
    label: "פרויקטים באזור",
    path: "/projects",
    permission: PERMISSIONS.PROJECTS_VIEW,
  },
  orderCoordination: {
    id: "order-coordination",
    icon: RefreshCcw,
    label: "תיאום הזמנות",
    path: "/order-coordination",
    permission: PERMISSIONS.WORK_ORDERS_COORDINATE,
  },
  suppliers: {
    id: "suppliers",
    icon: Truck,
    label: "ספקים",
    path: "/suppliers",
    permission: PERMISSIONS.SUPPLIERS_VIEW,
  },
  equipmentScan: {
    id: "equipment-scan",
    icon: ScanLine,
    label: "סריקת ציוד",
    path: "/equipment/scan",
    permission: PERMISSIONS.EQUIPMENT_SCAN,
  },
  workLogs: {
    id: "work-logs",
    icon: ClipboardList,
    label: "דיווחים",
    path: "/work-logs",
    permission: PERMISSIONS.WORKLOGS_VIEW,
  },
  invoices: {
    id: "invoices",
    icon: Receipt,
    label: "חשבוניות",
    path: "/invoices",
    permission: PERMISSIONS.INVOICES_VIEW,
  },
  reports: {
    id: "reports",
    icon: BarChart3,
    label: "דוחות",
    path: "/reports/pricing",
    permission: PERMISSIONS.REPORTS_VIEW,
  },
  map: {
    id: "map",
    icon: MapPin,
    label: "מפה",
    path: "/map",
    permission: PERMISSIONS.DASHBOARD_VIEW,
  },
  activityLog: {
    id: "activity-log",
    icon: Activity,
    label: "יומן פעילות",
    path: "/activity-log",
    permission: PERMISSIONS.DASHBOARD_VIEW,
  },
  equipment: {
    id: "equipment",
    icon: FileText,
    label: "ציוד",
    path: "/equipment/inventory",
    permission: PERMISSIONS.EQUIPMENT_VIEW,
  },
  workOrders: {
    id: "work-orders",
    icon: ClipboardCheck,
    label: "הזמנות עבודה",
    path: "/work-orders",
    permission: PERMISSIONS.WORK_ORDERS_VIEW,
  },
  budgets: {
    id: "budgets",
    icon: Wallet,
    label: "תקציבים",
    path: "/settings/budgets",
    permission: PERMISSIONS.BUDGETS_VIEW,
  },
  settings: {
    id: "settings",
    icon: Settings,
    label: "הגדרות מערכת",
    path: "/settings",
    permission: PERMISSIONS.SYSTEM_SETTINGS,
  },
  journal: {
    id: "journal",
    icon: BookOpen,
    label: "יומן אישי",
    path: "/my-journal",
    permission: PERMISSIONS.DASHBOARD_VIEW, // available to all logged-in users
  },
};

// ============================================================
// Role → Menu Items Mapping
// כל role מקבל תפריט ייחודי עם סדר ו-dividers מותאמים
// ============================================================
const ROLE_MENU_CONFIG: Record<UserRole, { items: string[]; dividerAfter?: string[] }> = {
  [UserRole.ADMIN]: {
    items: [
      "dashboard", "projects", "orderCoordination",
      "invoices", "reports", "map",
      "activityLog", "settings"
    ],
    dividerAfter: ["dashboard", "map", "settings"],
  },
  [UserRole.REGION_MANAGER]: {
    items: ["dashboard", "projectsRegion", "workOrders", "invoices", "budgets", "reports", "map", "journal"],
    dividerAfter: ["dashboard", "map"],
  },
  [UserRole.AREA_MANAGER]: {
    items: ["dashboard", "projectsArea", "workOrders", "budgets", "reports", "map", "journal"],
    dividerAfter: ["dashboard", "map"],
  },
  [UserRole.WORK_MANAGER]: {
    items: ["dashboard", "projects", "map", "journal"],
    dividerAfter: ["dashboard", "map"],
  },
  [UserRole.ORDER_COORDINATOR]: {
    items: ["dashboard", "orderCoordination", "suppliers", "map", "journal"],
    dividerAfter: ["dashboard", "map"],
  },
  [UserRole.ACCOUNTANT]: {
    items: ["dashboard", "invoices", "budgets", "reports", "journal"],
    dividerAfter: ["dashboard", "reports"],
  },
  [UserRole.SUPPLIER_MANAGER]: {
    items: ["dashboard", "settings", "journal"],
    dividerAfter: ["dashboard", "settings"],
  },
  [UserRole.FIELD_WORKER]: {
    items: ["dashboard", "projects", "journal"],
    dividerAfter: ["dashboard"],
  },
  [UserRole.SUPPLIER]: {
    items: [],  // Supplier uses /supplier-portal, no sidebar
    dividerAfter: [],
  },
  [UserRole.VIEWER]: {
    items: ["dashboard", "projects", "reports", "journal"],
    dividerAfter: ["dashboard", "reports"],
  },
  [UserRole.USER]: {
    items: ["dashboard", "projects", "journal"],
    dividerAfter: ["dashboard"],
  },
};

// ============================================================
// Backward compat: ALL_MENU_ITEMS (flat list of all unique items)
// ============================================================
export const ALL_MENU_ITEMS: MenuItem[] = [
  MENU_ITEM_POOL.dashboard,
  MENU_ITEM_POOL.projects,
  MENU_ITEM_POOL.orderCoordination,
  MENU_ITEM_POOL.suppliers,
  MENU_ITEM_POOL.invoices,
  MENU_ITEM_POOL.reports,
  MENU_ITEM_POOL.map,
  MENU_ITEM_POOL.activityLog,
  MENU_ITEM_POOL.settings,
];

// ============================================================
// Menu Functions
// ============================================================

/**
 * Get menu items for a specific role.
 * Returns role-specific items filtered by DB permissions.
 */
export function getMenuItemsForRole(userRole: string): MenuItem[] {
  const role = normalizeRole(userRole);
  const config = ROLE_MENU_CONFIG[role] || ROLE_MENU_CONFIG[UserRole.VIEWER];
  const dividerSet = new Set(config.dividerAfter || []);

  const result: MenuItem[] = [];
  for (const key of config.items) {
    const item = MENU_ITEM_POOL[key];
    if (!item) continue;
    if (!hasPermission(item.permission)) continue;
    result.push({
      ...item,
      dividerAfter: dividerSet.has(key) ? true : undefined,
    });
  }
  return result;
}

/**
 * Get default route for user role
 */
export function getDefaultRouteForRole(userRole: string): string {
  const role = normalizeRole(userRole);
  if (role === UserRole.SUPPLIER) return "/supplier-portal";
  return "/";
}

// ============================================================
// Dashboard Configuration
// ============================================================
export interface DashboardConfig {
  title: string;
  subtitle: string;
  showCalendar: boolean;
  showQuickActions: boolean;
  showStats: boolean;
  primaryWidget: string;
  widgets: string[];
  quickActions: QuickAction[];
}

export interface QuickAction {
  id: string;
  label: string;
  path: string;
  icon: string;
  permission: string;
}

export const DASHBOARD_CONFIG: Record<UserRole, DashboardConfig> = {
  [UserRole.ADMIN]: {
    title: "לוח בקרה - מנהל מערכת",
    subtitle: "סקירה כללית של המערכת",
    showCalendar: true,
    showQuickActions: true,
    showStats: true,
    primaryWidget: "system-overview",
    widgets: ["stats", "recent-activity", "alerts", "users"],
    quickActions: [
      { id: "new-user", label: "משתמש חדש", path: "/settings/admin/users/new", icon: "Users", permission: PERMISSIONS.USERS_CREATE },
      { id: "settings", label: "הגדרות", path: "/settings", icon: "Settings", permission: PERMISSIONS.SYSTEM_SETTINGS },
    ],
  },
  [UserRole.REGION_MANAGER]: {
    title: "לוח בקרה - מנהל מרחב",
    subtitle: "סקירת המרחב שלך",
    showCalendar: true,
    showQuickActions: true,
    showStats: true,
    primaryWidget: "region-overview",
    widgets: ["stats", "budget-summary", "projects-by-area", "reports"],
    quickActions: [
      { id: "projects", label: "פרויקטים", path: "/projects", icon: "Building2", permission: PERMISSIONS.PROJECTS_VIEW },
      { id: "reports", label: "דוחות", path: "/reports/pricing", icon: "BarChart3", permission: PERMISSIONS.REPORTS_VIEW },
    ],
  },
  [UserRole.AREA_MANAGER]: {
    title: "לוח בקרה - מנהל אזור",
    subtitle: "תפעול יומיומי",
    showCalendar: true,
    showQuickActions: true,
    showStats: true,
    primaryWidget: "area-overview",
    widgets: ["stats", "pending-approvals", "projects", "equipment-requests"],
    quickActions: [
      { id: "projects", label: "פרויקטים", path: "/projects", icon: "Building2", permission: PERMISSIONS.PROJECTS_VIEW },
    ],
  },
  [UserRole.WORK_MANAGER]: {
    title: "לוח בקרה - מנהל עבודה",
    subtitle: "הזמנות ואישורים",
    showCalendar: true,
    showQuickActions: true,
    showStats: true,
    primaryWidget: "daily-plan",
    widgets: ["calendar", "pending-approvals", "my-work-orders", "equipment-status"],
    quickActions: [
      { id: "projects", label: "פרויקטים", path: "/projects", icon: "Building2", permission: PERMISSIONS.PROJECTS_VIEW },
    ],
  },
  [UserRole.ORDER_COORDINATOR]: {
    title: "לוח בקרה - מתאם הזמנות",
    subtitle: "תיאום ספקים",
    showCalendar: false,
    showQuickActions: true,
    showStats: true,
    primaryWidget: "coordination-queue",
    widgets: ["awaiting-response", "expired-orders", "supplier-status"],
    quickActions: [
      { id: "coordination", label: "תיאום הזמנות", path: "/order-coordination", icon: "RefreshCcw", permission: PERMISSIONS.WORK_ORDERS_COORDINATE },
      { id: "suppliers", label: "ספקים", path: "/suppliers", icon: "Truck", permission: PERMISSIONS.SUPPLIERS_VIEW },
    ],
  },
  [UserRole.ACCOUNTANT]: {
    title: "לוח בקרה - חשבונות",
    subtitle: "חשבוניות ודוחות",
    showCalendar: false,
    showQuickActions: true,
    showStats: true,
    primaryWidget: "financial-overview",
    widgets: ["pending-invoices", "budget-summary", "cost-reports"],
    quickActions: [
      { id: "accountant-inbox", label: "תיבת נכנסים", path: "/accountant-inbox", icon: "FileText", permission: PERMISSIONS.WORKLOGS_APPROVE },
      { id: "invoices", label: "חשבוניות", path: "/invoices", icon: "Receipt", permission: PERMISSIONS.INVOICES_VIEW },
      { id: "reports", label: "דוחות", path: "/reports/pricing", icon: "BarChart3", permission: PERMISSIONS.REPORTS_VIEW },
    ],
  },
  [UserRole.SUPPLIER_MANAGER]: {
    title: "לוח בקרה - מנהל ספקים",
    subtitle: "ניהול ספקים",
    showCalendar: false,
    showQuickActions: true,
    showStats: true,
    primaryWidget: "suppliers-overview",
    widgets: ["suppliers-list", "equipment-status"],
    quickActions: [
      { id: "suppliers", label: "ספקים", path: "/suppliers", icon: "Truck", permission: PERMISSIONS.SUPPLIERS_VIEW },
    ],
  },
  [UserRole.FIELD_WORKER]: {
    title: "לוח בקרה - עובד שטח",
    subtitle: "דיווח שעות",
    showCalendar: false,
    showQuickActions: true,
    showStats: false,
    primaryWidget: "quick-report",
    widgets: ["my-worklogs", "worklog-status"],
    quickActions: [
      { id: "projects", label: "פרויקטים", path: "/projects", icon: "Building2", permission: PERMISSIONS.PROJECTS_VIEW },
      { id: "scan", label: "סריקת ציוד", path: "/equipment/scan", icon: "Search", permission: PERMISSIONS.EQUIPMENT_SCAN },
      { id: "report", label: "דיווח שעות", path: "/projects", icon: "Clock", permission: PERMISSIONS.WORKLOGS_CREATE },
    ],
  },
  [UserRole.SUPPLIER]: {
    title: "פורטל ספקים",
    subtitle: "הזמנות וחשבוניות",
    showCalendar: false,
    showQuickActions: true,
    showStats: false,
    primaryWidget: "supplier-orders",
    widgets: ["my-orders", "my-invoices"],
    quickActions: [],
  },
  [UserRole.VIEWER]: {
    title: "לוח בקרה",
    subtitle: "צפייה בלבד",
    showCalendar: false,
    showQuickActions: false,
    showStats: true,
    primaryWidget: "overview",
    widgets: ["stats", "projects-summary"],
    quickActions: [],
  },
  [UserRole.USER]: {
    title: "לוח בקרה",
    subtitle: "דיווח שעות",
    showCalendar: false,
    showQuickActions: true,
    showStats: false,
    primaryWidget: "quick-report",
    widgets: ["my-worklogs"],
    quickActions: [
      { id: "projects", label: "פרויקטים", path: "/projects", icon: "Building2", permission: PERMISSIONS.PROJECTS_VIEW },
    ],
  },
};

export function getDashboardConfig(userRole: string): DashboardConfig {
  const role = normalizeRole(userRole);
  return DASHBOARD_CONFIG[role] || DASHBOARD_CONFIG[UserRole.VIEWER];
}

// ============================================================
// Route Permission Mapping
// ============================================================
export const ROUTE_PERMISSIONS: Record<string, string> = {
  // Projects
  "/projects": PERMISSIONS.PROJECTS_VIEW,
  "/projects/new": PERMISSIONS.PROJECTS_CREATE,
  "/projects/:code": PERMISSIONS.PROJECTS_VIEW,
  "/projects/:code/edit": PERMISSIONS.PROJECTS_UPDATE,
  "/projects/:code/workspace": PERMISSIONS.PROJECTS_VIEW,

  // Work Orders
  "/work-orders": PERMISSIONS.WORK_ORDERS_VIEW,
  "/work-orders/new": PERMISSIONS.WORK_ORDERS_CREATE,
  "/work-orders/:id": PERMISSIONS.WORK_ORDERS_VIEW,
  "/work-orders/:id/edit": PERMISSIONS.WORK_ORDERS_UPDATE,
  "/order-coordination": PERMISSIONS.WORK_ORDERS_COORDINATE,

  // Work Logs
  "/projects/:code/workspace/work-logs": PERMISSIONS.WORKLOGS_VIEW,
  "/projects/:code/workspace/work-logs/new": PERMISSIONS.WORKLOGS_CREATE,
  "/projects/:code/workspace/work-logs/:id": PERMISSIONS.WORKLOGS_VIEW,
  "/projects/:code/workspace/work-logs/approvals": PERMISSIONS.WORKLOGS_APPROVE,

  // Equipment
  "/equipment": PERMISSIONS.EQUIPMENT_VIEW,
  "/equipment/request": PERMISSIONS.EQUIPMENT_SCAN,
  "/equipment/requests": PERMISSIONS.EQUIPMENT_REQUEST,

  // Suppliers
  "/suppliers": PERMISSIONS.SUPPLIERS_VIEW,
  "/suppliers/new": PERMISSIONS.SUPPLIERS_CREATE,
  "/suppliers/:id": PERMISSIONS.SUPPLIERS_VIEW,

  // Invoices & Reports
  "/invoices": PERMISSIONS.INVOICES_VIEW,
  "/reports/pricing": PERMISSIONS.REPORTS_VIEW,

  // Admin
  "/admin": PERMISSIONS.SYSTEM_ADMIN,
  "/admin/users": PERMISSIONS.USERS_VIEW,
  "/admin/roles": PERMISSIONS.ROLES_VIEW,
  "/settings": PERMISSIONS.SYSTEM_SETTINGS,
};

export default {
  ALL_MENU_ITEMS,
  getMenuItemsForRole,
  getDefaultRouteForRole,
  getDashboardConfig,
  DASHBOARD_CONFIG,
  ROUTE_PERMISSIONS,
};
