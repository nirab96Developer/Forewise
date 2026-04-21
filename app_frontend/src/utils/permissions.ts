// מערכת הרשאות - מבוססת על DB
// ============================================================
// ההרשאות מגיעות מה-Backend בתגובת ה-login
// הקוד הזה מספק פונקציות עזר לבדיקת הרשאות בפרונטנד
// ============================================================

// ============================================================
// Permission Codes — canonical form is lowercase "resource.action"
// matches Backend (app_backend/app/models/permission.py validator)
// ============================================================
export const PERMISSIONS = {
  // Dashboard
  DASHBOARD_VIEW: "dashboard.view",

  // Projects
  PROJECTS_VIEW: "projects.read",
  PROJECTS_CREATE: "projects.create",
  PROJECTS_UPDATE: "projects.update",
  PROJECTS_DELETE: "projects.delete",

  // Work Orders
  WORK_ORDERS_VIEW: "work_orders.read",
  WORK_ORDERS_CREATE: "work_orders.create",
  WORK_ORDERS_UPDATE: "work_orders.update",
  WORK_ORDERS_DELETE: "work_orders.delete",
  WORK_ORDERS_COORDINATE: "work_orders.distribute",
  WORK_ORDERS_APPROVE: "work_orders.approve",
  WORK_ORDERS_CANCEL: "work_orders.cancel",
  WORK_ORDERS_CLOSE: "work_orders.close",
  WORK_ORDERS_RESEND: "work_orders.update",
  WORK_ORDERS_ESCALATE: "work_orders.update",

  // Worklogs
  WORKLOGS_VIEW: "worklogs.read",
  WORKLOGS_CREATE: "worklogs.create",
  WORKLOGS_UPDATE: "worklogs.update",
  WORKLOGS_APPROVE: "worklogs.approve",
  WORKLOGS_SUBMIT: "worklogs.submit",

  // Equipment
  EQUIPMENT_VIEW: "equipment.read",
  EQUIPMENT_CREATE: "equipment.create",
  EQUIPMENT_UPDATE: "equipment.update",
  EQUIPMENT_REQUEST: "equipment.assign",
  EQUIPMENT_SCAN: "equipment.read",

  // Suppliers
  SUPPLIERS_VIEW: "suppliers.read",
  SUPPLIERS_CREATE: "suppliers.create",
  SUPPLIERS_UPDATE: "suppliers.update",
  SUPPLIERS_DELETE: "suppliers.delete",

  // Invoices
  INVOICES_VIEW: "invoices.read",
  INVOICES_CREATE: "invoices.create",
  INVOICES_UPDATE: "invoices.update",
  INVOICES_APPROVE: "invoices.approve",

  // Budgets
  BUDGETS_VIEW: "budgets.read",
  BUDGETS_CREATE: "budgets.create",
  BUDGETS_UPDATE: "budgets.update",
  BUDGETS_APPROVE: "budgets.approve",

  // Reports
  REPORTS_VIEW: "reports.read",
  REPORTS_EXPORT: "reports.read",

  // Users
  USERS_VIEW: "users.read",
  USERS_CREATE: "users.create",
  USERS_UPDATE: "users.update",
  USERS_DELETE: "users.delete",

  // Roles
  ROLES_VIEW: "roles.read",
  ROLES_MANAGE: "roles.manage_permissions",

  // Geography
  REGIONS_VIEW: "regions.read",
  REGIONS_MANAGE: "regions.update",
  AREAS_VIEW: "areas.read",
  AREAS_MANAGE: "areas.update",

  // Activity Log — frontend pseudo-permissions (no backend route uses them)
  ACTIVITY_LOG_MY: "activity_log.my",
  ACTIVITY_LOG_AREA: "activity_log.area",
  ACTIVITY_LOG_REGION: "activity_log.region",
  ACTIVITY_LOG_SYSTEM: "activity_log.system",

  // System
  SYSTEM_ADMIN: "system.admin",
  SYSTEM_SETTINGS: "system.settings",
  SYSTEM_ACTIVITY_LOG: "activity_log.system",
} as const;

export type PermissionCode = typeof PERMISSIONS[keyof typeof PERMISSIONS];

// ============================================================
// User Role Enum - תואם ל-DB
// ============================================================
export enum UserRole {
  ADMIN = "ADMIN",
  REGION_MANAGER = "REGION_MANAGER",
  AREA_MANAGER = "AREA_MANAGER",
  WORK_MANAGER = "WORK_MANAGER",
  ORDER_COORDINATOR = "ORDER_COORDINATOR",
  ACCOUNTANT = "ACCOUNTANT",
  // Legacy / compatibility only
  FIELD_WORKER = "FIELD_WORKER",
  SUPPLIER = "SUPPLIER",
  SUPPLIER_MANAGER = "SUPPLIER_MANAGER",
  VIEWER = "VIEWER",
  USER = "USER"  // Legacy
}

// ============================================================
// Permission Storage & Retrieval
// ============================================================

/**
 * Get user permissions from localStorage
 */
export function getUserPermissions(): string[] {
  try {
    const userStr = localStorage.getItem('user');
    if (!userStr) return [];
    
    const user = JSON.parse(userStr);
    return user.permissions || [];
  } catch {
    return [];
  }
}

/**
 * Get user role from localStorage
 */
export function getUserRole(): string {
  try {
    const userStr = localStorage.getItem('user');
    if (!userStr) return '';
    
    const user = JSON.parse(userStr);
    return user.role || '';
  } catch {
    return '';
  }
}

/**
 * Check if user has a specific permission.
 * Comparison is case-insensitive — Backend canonical form is lowercase
 * (`resource.action`) but legacy frontend code may still pass UPPERCASE
 * strings such as "WORK_ORDERS.VIEW". Both must match.
 */
export function hasPermission(permission: string): boolean {
  const role = getUserRole();

  // ADMIN bypass
  if (role === 'ADMIN') return true;

  if (!permission) return false;
  const target = permission.toLowerCase();

  const permissions = getUserPermissions();
  for (const p of permissions) {
    if (!p) continue;
    if (p.toLowerCase() === target) return true;
    // SYSTEM.ADMIN super-permission
    if (p.toLowerCase() === 'system.admin') return true;
  }

  return false;
}

/**
 * Check if user has any of the specified permissions
 */
export function hasAnyPermission(...permissions: string[]): boolean {
  return permissions.some(p => hasPermission(p));
}

/**
 * Check if user has all of the specified permissions
 */
export function hasAllPermissions(...permissions: string[]): boolean {
  return permissions.every(p => hasPermission(p));
}

// ============================================================
// Role Name Mapping
// ============================================================
export const ROLE_NAME_MAP: Record<string, UserRole> = {
  // עברית
  "מנהל מערכת": UserRole.ADMIN,
  "מנהל מרחב": UserRole.REGION_MANAGER,
  "מנהל אזור": UserRole.AREA_MANAGER,
  "מנהל עבודה": UserRole.WORK_MANAGER,
  "מתאם הזמנות": UserRole.ORDER_COORDINATOR,
  "מנהלת חשבונות": UserRole.ACCOUNTANT,
  "עובד שטח": UserRole.WORK_MANAGER,
  "ספק": UserRole.SUPPLIER,
  "צופה": UserRole.REGION_MANAGER,
  
  // אנגלית
  "admin": UserRole.ADMIN,
  "ADMIN": UserRole.ADMIN,
  "region_manager": UserRole.REGION_MANAGER,
  "REGION_MANAGER": UserRole.REGION_MANAGER,
  "area_manager": UserRole.AREA_MANAGER,
  "AREA_MANAGER": UserRole.AREA_MANAGER,
  "work_manager": UserRole.WORK_MANAGER,
  "WORK_MANAGER": UserRole.WORK_MANAGER,
  "order_coordinator": UserRole.ORDER_COORDINATOR,
  "ORDER_COORDINATOR": UserRole.ORDER_COORDINATOR,
  "accountant": UserRole.ACCOUNTANT,
  "ACCOUNTANT": UserRole.ACCOUNTANT,
  "field_worker": UserRole.WORK_MANAGER,
  "FIELD_WORKER": UserRole.WORK_MANAGER,
  "supplier": UserRole.SUPPLIER,
  "SUPPLIER": UserRole.SUPPLIER,
  "viewer": UserRole.REGION_MANAGER,
  "VIEWER": UserRole.REGION_MANAGER,
  "user": UserRole.WORK_MANAGER,
  "USER": UserRole.WORK_MANAGER,
};

export function normalizeRole(role: string): UserRole {
  if (!role) return UserRole.WORK_MANAGER;
  return ROLE_NAME_MAP[role] || UserRole.WORK_MANAGER;
}

// ============================================================
// Role Hierarchy
// ============================================================
export const ROLE_HIERARCHY: Record<UserRole, number> = {
  [UserRole.ADMIN]: 100,
  [UserRole.REGION_MANAGER]: 80,
  [UserRole.AREA_MANAGER]: 70,
  [UserRole.WORK_MANAGER]: 60,
  [UserRole.ORDER_COORDINATOR]: 55,
  [UserRole.ACCOUNTANT]: 50,
  [UserRole.SUPPLIER_MANAGER]: 45,
  [UserRole.FIELD_WORKER]: 30,
  [UserRole.SUPPLIER]: 25,
  [UserRole.VIEWER]: 10,
  [UserRole.USER]: 30
};

export function isHigherRole(role1: string, role2: string): boolean {
  const h1 = ROLE_HIERARCHY[normalizeRole(role1)] || 0;
  const h2 = ROLE_HIERARCHY[normalizeRole(role2)] || 0;
  return h1 > h2;
}

// ============================================================
// Display Names
// ============================================================
export function getRoleDisplayName(role: string): string {
  const r = normalizeRole(role);
  const names: Record<UserRole, string> = {
    [UserRole.ADMIN]: "מנהל מערכת",
    [UserRole.REGION_MANAGER]: "מנהל מרחב",
    [UserRole.AREA_MANAGER]: "מנהל אזור",
    [UserRole.WORK_MANAGER]: "מנהל עבודה",
    [UserRole.ORDER_COORDINATOR]: "מתאם הזמנות",
    [UserRole.ACCOUNTANT]: "מנהלת חשבונות",
    [UserRole.SUPPLIER_MANAGER]: "מנהל מערכת",
    [UserRole.FIELD_WORKER]: "מנהל עבודה",
    [UserRole.SUPPLIER]: "ספק",
    [UserRole.VIEWER]: "מנהל מרחב",
    [UserRole.USER]: "מנהל עבודה"
  };
  return names[r] || "משתמש";
}

export function getRoleDescription(role: string): string {
  const r = normalizeRole(role);
  const desc: Record<UserRole, string> = {
    [UserRole.ADMIN]: "גישה מלאה לכל המערכת",
    [UserRole.REGION_MANAGER]: "בקרה ותקציב - צפייה בלבד",
    [UserRole.AREA_MANAGER]: "תפעול יומיומי, אישור דיווחים",
    [UserRole.WORK_MANAGER]: "יצירת הזמנות, אישור דיווחים",
    [UserRole.ORDER_COORDINATOR]: "תיאום, הפצה ואישור הזמנות עבודה",
    [UserRole.ACCOUNTANT]: "כספים וחשבוניות בלבד",
    [UserRole.SUPPLIER_MANAGER]: "ניהול מערכת",
    [UserRole.FIELD_WORKER]: "עבודה שוטפת בפרויקטים",
    [UserRole.SUPPLIER]: "פורטל ספקים בלבד",
    [UserRole.VIEWER]: "בקרה ברמת מרחב",
    [UserRole.USER]: "עבודה שוטפת בפרויקטים"
  };
  return desc[r] || "";
}

// ============================================================
// Helper Functions
// ============================================================
export function isAdmin(): boolean {
  return getUserRole() === 'ADMIN';
}

export function isManager(): boolean {
  const role = normalizeRole(getUserRole());
  return [UserRole.ADMIN, UserRole.REGION_MANAGER, UserRole.AREA_MANAGER, UserRole.WORK_MANAGER].includes(role);
}

export function hasFinancialAccess(): boolean {
  const role = normalizeRole(getUserRole());
  return [UserRole.ADMIN, UserRole.ACCOUNTANT].includes(role);
}

export function canReportHours(): boolean {
  return hasPermission(PERMISSIONS.WORKLOGS_CREATE);
}

export function canApproveWorkLogs(): boolean {
  return hasPermission(PERMISSIONS.WORKLOGS_APPROVE);
}

export function canCreateWorkOrder(): boolean {
  return hasPermission(PERMISSIONS.WORK_ORDERS_CREATE);
}

export function canApproveInvoices(): boolean {
  return hasPermission(PERMISSIONS.INVOICES_APPROVE);
}

export function getHomeRouteForRole(role: string): string {
  if (normalizeRole(role) === UserRole.SUPPLIER) return "/supplier-portal";
  return "/";
}

// ============================================================
// Menu Permission Mapping (for backward compatibility)
// ============================================================
export const MENU_PERMISSIONS: Record<string, string> = {
  dashboard: PERMISSIONS.DASHBOARD_VIEW,
  projects: PERMISSIONS.PROJECTS_VIEW,
  projectWorkspace: PERMISSIONS.PROJECTS_VIEW,
  equipmentBalances: PERMISSIONS.EQUIPMENT_VIEW,
  workOrders: PERMISSIONS.WORK_ORDERS_VIEW,
  workOrderCreate: PERMISSIONS.WORK_ORDERS_CREATE,
  orderCoordination: PERMISSIONS.WORK_ORDERS_COORDINATE,
  workLogs: PERMISSIONS.WORKLOGS_VIEW,
  workLogCreate: PERMISSIONS.WORKLOGS_CREATE,
  workLogApproval: PERMISSIONS.WORKLOGS_APPROVE,
  equipment: PERMISSIONS.EQUIPMENT_VIEW,
  equipmentRequests: PERMISSIONS.EQUIPMENT_REQUEST,
  scanning: PERMISSIONS.EQUIPMENT_SCAN,
  suppliers: PERMISSIONS.SUPPLIERS_VIEW,
  invoices: PERMISSIONS.INVOICES_VIEW,
  reports: PERMISSIONS.REPORTS_VIEW,
  financialReports: PERMISSIONS.REPORTS_EXPORT,
  activityLog: PERMISSIONS.SYSTEM_ACTIVITY_LOG,
  settings: PERMISSIONS.SYSTEM_SETTINGS,
  users: PERMISSIONS.USERS_VIEW,
  roles: PERMISSIONS.ROLES_VIEW,
  admin: PERMISSIONS.SYSTEM_ADMIN,
  regions: PERMISSIONS.REGIONS_VIEW,
  areas: PERMISSIONS.AREAS_VIEW,
  locations: PERMISSIONS.AREAS_VIEW,
  support: PERMISSIONS.DASHBOARD_VIEW,
  notifications: PERMISSIONS.DASHBOARD_VIEW,
};

/**
 * Get menu items that user has access to
 */
export function getMenuItemsForRole(_userRole: string): string[] {
  const items: string[] = [];
  Object.entries(MENU_PERMISSIONS).forEach(([menuItem, permission]) => {
    if (hasPermission(permission)) {
      items.push(menuItem);
    }
  });
  return items;
}

// ============================================================
// Legacy Compatibility
// ============================================================
export const ACTION_PERMISSIONS = MENU_PERMISSIONS;
export const READ_ONLY_ROLES = {};

export default {
  PERMISSIONS,
  UserRole,
  ROLE_HIERARCHY,
  ROLE_NAME_MAP,
  MENU_PERMISSIONS,
  normalizeRole,
  hasPermission,
  hasAnyPermission,
  hasAllPermissions,
  getUserPermissions,
  getUserRole,
  getMenuItemsForRole,
  getRoleDisplayName,
  getRoleDescription,
  getHomeRouteForRole,
  isAdmin,
  isManager,
  hasFinancialAccess,
  canReportHours,
  canApproveWorkLogs,
  canCreateWorkOrder,
  canApproveInvoices,
  isHigherRole,
};
