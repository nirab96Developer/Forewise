// src/routes/index.tsx
// קובץ נתיבים - מבוסס על הרשאות מה-DB
// Permission codes: DOMAIN.ACTION (e.g., PROJECTS.VIEW, WORKLOGS.CREATE)

import React, { Suspense, lazy } from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import ProtectedRoute from "../components/common/ProtectedRoute";
import { PageSuspenseLoader } from "../components/common/UnifiedLoader";
import { PERMISSIONS } from "../utils/permissions";

// ========================================
// LAZY IMPORTS
// ========================================

// Auth
const Login = lazy(() => import("../pages/Login/Login"));
const ForgotPassword = lazy(() => import("../pages/Login/ForgotPassword"));
const ResetPassword = lazy(() => import("../pages/Login/ResetPassword"));
const OTP = lazy(() => import("../pages/OTP/OTP"));
const SupplierPortal = lazy(() => import("../pages/SupplierPortal/SupplierPortal"));

// Dashboard
const Dashboard = lazy(() => import("../pages/Dashboard/Dashboard"));

// Projects
const Projects = lazy(() => import("../pages/Projects/ProjectsClean"));
// ProjectPage replaced by ProjectWorkspace - using redirect
const ProjectWorkspace = lazy(() => import("../pages/Projects/ProjectWorkspaceNew"));
const NewProject = lazy(() => import("../pages/Projects/NewProject"));
const EditProject = lazy(() => import("../pages/Projects/EditProject"));

// Work Orders
const WorkOrders = lazy(() => import("../pages/WorkOrders/WorkOrders"));
const NewWorkOrder = lazy(() => import("../pages/WorkOrders/NewWorkOrder"));
const EditWorkOrder = lazy(() => import("../pages/WorkOrders/EditWorkOrder"));
const WorkOrderDetail = lazy(() => import("../pages/WorkOrders/WorkOrderDetail"));
const OrderCoordination = lazy(() => import("../pages/WorkOrders/OrderCoordination"));

// Work Logs (global /work-logs redirects to projects - but kept for project context)
const WorkLogs = lazy(() => import("../pages/WorkLogs/WorkLogs"));
const WorklogCreateNew = lazy(() => import("../pages/WorkLogs/WorklogCreateNew"));
const WorklogDetail = lazy(() => import("../pages/WorkLogs/WorklogDetail"));
const WorklogApproval = lazy(() => import("../pages/WorkLogs/WorklogApproval"));

// Equipment
const EquipmentScan = lazy(() => import("../pages/Equipment/EquipmentScan"));
const EquipmentDetail = lazy(() => import("../pages/Equipment/EquipmentDetail"));
const EquipmentRequestsStatus = lazy(() => import("../pages/Equipment/EquipmentRequestsStatus"));
const EquipmentBalances = lazy(() => import("../pages/Equipment/EquipmentBalances"));
const EquipmentInventory = lazy(() => import("../pages/Equipment/EquipmentInventory"));

// Suppliers
const Suppliers = lazy(() => import("../pages/Suppliers/Suppliers"));
const NewSupplier = lazy(() => import("../pages/Suppliers/NewSupplier"));
const EditSupplier = lazy(() => import("../pages/Suppliers/EditSupplier"));
const AddSupplierEquipment = lazy(() => import("../pages/Suppliers/AddSupplierEquipment"));
const UpdateSupplierEquipmentRate = lazy(() => import("../pages/Suppliers/UpdateSupplierEquipmentRate"));

// Invoices & Reports
const Invoices = lazy(() => import("../pages/Invoices/Invoices"));
const PricingReports = lazy(() => import("../pages/Reports/PricingReports"));

// Notifications & Support
const Notifications = lazy(() => import("../pages/Notifications/Notifications"));
const SupportTicket = lazy(() => import("../pages/Support/Support"));
const ActivityLog = lazy(() => import("../pages/ActivityLog/ActivityLogNew"));

// Settings (EquipmentTypes, PricingOverrides, SettingsPlaceholder removed - redirects to catalog)
const SystemSettings = lazy(() => import("../pages/Settings/SystemSettings"));
const SupplierSettings = lazy(() => import("../pages/Settings/SupplierSettings"));
const ConstraintReasons = lazy(() => import("../pages/Settings/ConstraintReasons"));
const FairRotation = lazy(() => import("../pages/Settings/FairRotation"));
const EquipmentCatalog = lazy(() => import("../pages/Settings/EquipmentCatalog"));
const WorkHours = lazy(() => import("../pages/Settings/WorkHours"));
const Budgets = lazy(() => import("../pages/Settings/Budgets"));
const BudgetDetail = lazy(() => import("../pages/Settings/BudgetDetail"));
const RolesPermissions = lazy(() => import("../pages/Settings/RolesPermissions"));

// Regions & Areas
const RegionDetail = lazy(() => import("../pages/Regions/RegionDetail"));
const NewRegion = lazy(() => import("../pages/Regions/NewRegion"));
const EditRegion = lazy(() => import("../pages/Regions/EditRegion"));
const AreaDetail = lazy(() => import("../pages/Areas/AreaDetail"));
const NewArea = lazy(() => import("../pages/Areas/NewArea"));

// Admin & Users (AdminPanel removed - using settings pages instead)
const Users = lazy(() => import("../pages/Users/Users"));
const NewUser = lazy(() => import("../pages/Users/NewUser"));
const EditUser = lazy(() => import("../pages/Users/EditUser"));

// Geography
const Regions = lazy(() => import("../pages/Regions/Regions"));
const Areas = lazy(() => import("../pages/Areas/Areas"));
const Locations = lazy(() => import("../pages/Locations/LocationsClean"));
const ForestMap = lazy(() => import("../pages/Map/ForestMap"));

// ========================================
// Loading Component - Using UnifiedLoader
// ========================================

// ========================================
// Route Guard Wrapper
// ========================================
interface GuardedProps {
  children: React.ReactNode;
  permission?: string;
}

const Guarded: React.FC<GuardedProps> = ({ children, permission }) => (
  <ProtectedRoute requiredPermission={permission}>
    {children}
  </ProtectedRoute>
);

// ========================================
// Main Routes Component
// ========================================
interface AppRoutesProps {
  setGlobalLoading: (loading: boolean) => void;
}

const AppRoutes: React.FC<AppRoutesProps> = ({ setGlobalLoading }) => {
  return (
    <Suspense fallback={<PageSuspenseLoader />}>
      <Routes>
        {/* ============================================
              AUTH ROUTES (Public)
          ============================================ */}
        <Route path="/login" element={<Login setGlobalLoading={setGlobalLoading} />} />
        <Route path="/forgot-password" element={<ForgotPassword />} />
        <Route path="/reset-password" element={<ResetPassword />} />
        <Route path="/otp" element={<OTP setGlobalLoading={setGlobalLoading} />} />
        {/* Supplier Portal - External landing page (no auth required) */}
        <Route path="/supplier-portal" element={<SupplierPortal />} />
        <Route path="/supplier-portal/:token" element={<SupplierPortal />} />
        {/* Alternative supplier landing URL */}
        <Route path="/supplier-landing/:token" element={<SupplierPortal />} />

        {/* ============================================
              DASHBOARD
          ============================================ */}
        <Route path="/" element={<Guarded permission={PERMISSIONS.DASHBOARD_VIEW}><Dashboard /></Guarded>} />

        {/* ============================================
              PROJECTS
          ============================================ */}
        <Route path="/projects" element={<Guarded permission={PERMISSIONS.PROJECTS_VIEW}><Projects /></Guarded>} />
        {/* Project detail redirects to workspace (pretty design) */}
        <Route path="/projects/:code" element={<Navigate to="workspace" replace />} />
        <Route path="/projects/:code/workspace" element={<Guarded permission={PERMISSIONS.PROJECTS_VIEW}><ProjectWorkspace /></Guarded>} />
        <Route path="/projects/:code/tasks/new" element={<Guarded permission={PERMISSIONS.PROJECTS_VIEW}><ProjectWorkspace /></Guarded>} />
        <Route path="/projects/:code/equipment/balances" element={<Guarded permission={PERMISSIONS.EQUIPMENT_VIEW}><EquipmentBalances /></Guarded>} />
        {/* Project Work Logs - in project context (under workspace) */}
        <Route path="/projects/:code/workspace/work-logs" element={<Guarded permission={PERMISSIONS.WORKLOGS_VIEW}><WorkLogs /></Guarded>} />
        <Route path="/projects/:code/workspace/work-logs/new" element={<Guarded permission={PERMISSIONS.WORKLOGS_CREATE}><WorklogCreateNew /></Guarded>} />
        <Route path="/projects/:code/workspace/work-logs/approvals" element={<Guarded permission={PERMISSIONS.WORKLOGS_APPROVE}><WorklogApproval /></Guarded>} />
        <Route path="/projects/:code/workspace/work-logs/:id" element={<Guarded permission={PERMISSIONS.WORKLOGS_VIEW}><WorklogDetail /></Guarded>} />
        {/* Project Work Orders - in project context (under workspace) */}
        <Route path="/projects/:code/workspace/work-orders" element={<Guarded permission={PERMISSIONS.WORK_ORDERS_VIEW}><WorkOrders /></Guarded>} />
        <Route path="/projects/:code/workspace/work-orders/new" element={<Guarded permission={PERMISSIONS.WORK_ORDERS_CREATE}><NewWorkOrder /></Guarded>} />
        <Route path="/projects/:code/workspace/work-orders/:id" element={<Guarded permission={PERMISSIONS.WORK_ORDERS_VIEW}><WorkOrderDetail /></Guarded>} />
        {/* Legacy project work-logs/work-orders routes - redirect to workspace */}
        <Route path="/projects/:code/work-logs" element={<Navigate to="../workspace/work-logs" replace />} />
        <Route path="/projects/:code/work-logs/new" element={<Navigate to="../workspace/work-logs/new" replace />} />
        <Route path="/projects/:code/work-logs/approvals" element={<Navigate to="../workspace/work-logs/approvals" replace />} />
        <Route path="/projects/:code/work-orders" element={<Navigate to="../workspace/work-orders" replace />} />
        <Route path="/projects/:code/work-orders/new" element={<Navigate to="../workspace/work-orders/new" replace />} />

        {/* Project create/edit - redirect to settings (organization) */}
        <Route path="/projects/new" element={<Navigate to="/settings/organization/projects/new" replace />} />
        <Route path="/projects/:code/edit" element={<Navigate to="/settings/organization/projects/:code/edit" replace />} />

        {/* Legacy project routes */}
        <Route path="/projects/:projectCode/workspace" element={<Navigate to="/projects" replace />} />
        <Route path="/projects/:projectId/report-hours" element={<Navigate to="/projects" replace />} />
        <Route path="/projects/:projectId/equipment/balances" element={<Navigate to="/projects" replace />} />

        {/* ============================================
              WORK ORDERS - Only individual pages (list is in project context)
          ============================================ */}
        {/* /work-orders list removed - access through project */}
        <Route path="/work-orders" element={<Navigate to="/projects" replace />} />
        <Route path="/work-orders/new" element={<Guarded permission={PERMISSIONS.WORK_ORDERS_CREATE}><NewWorkOrder /></Guarded>} />
        <Route path="/work-orders/:id" element={<Guarded permission={PERMISSIONS.WORK_ORDERS_VIEW}><WorkOrderDetail /></Guarded>} />
        <Route path="/work-orders/:id/edit" element={<Guarded permission={PERMISSIONS.WORK_ORDERS_UPDATE}><EditWorkOrder /></Guarded>} />
        <Route path="/order-coordination" element={<Guarded permission={PERMISSIONS.WORK_ORDERS_COORDINATE}><OrderCoordination /></Guarded>} />

        {/* ============================================
              WORK LOGS - Only approvals (reporting is in project context)
          ============================================ */}
        {/* Work Logs global page removed - reporting should be inside project workspace */}
        <Route path="/work-logs" element={<Navigate to="/projects" replace />} />
        <Route path="/work-logs/new" element={<Navigate to="/projects" replace />} />
        <Route path="/work-logs/:id" element={<Navigate to="/projects" replace />} />
        <Route path="/work-logs/approvals" element={<Navigate to="/projects" replace />} />

        {/* Legacy worklog routes */}
        <Route path="/worklogs" element={<Navigate to="/projects" replace />} />
        <Route path="/worklogs/new" element={<Navigate to="/projects" replace />} />
        <Route path="/worklogs/standard" element={<Navigate to="/projects" replace />} />
        <Route path="/worklogs/create" element={<Navigate to="/projects" replace />} />
        <Route path="/work-logs/create" element={<Navigate to="/projects" replace />} />
        <Route path="/work-logs/create-new" element={<Navigate to="/projects" replace />} />
        <Route path="/work-logs/standard" element={<Navigate to="/projects" replace />} />
        <Route path="/work-logs/manual" element={<Navigate to="/projects" replace />} />
        <Route path="/work-logs/storage" element={<Navigate to="/projects" replace />} />
        <Route path="/work-logs/approve" element={<Navigate to="/projects" replace />} />
        <Route path="/work-logs/approval" element={<Navigate to="/projects" replace />} />

        {/* ============================================
              EQUIPMENT - סריקה וזיהוי ציוד
          ============================================ */}
        <Route path="/equipment" element={<Navigate to="/equipment/inventory" replace />} />
        <Route path="/equipment/inventory" element={<Guarded permission={PERMISSIONS.EQUIPMENT_VIEW}><EquipmentInventory /></Guarded>} />
        <Route path="/equipment/scan" element={<Guarded permission={PERMISSIONS.EQUIPMENT_SCAN}><EquipmentScan /></Guarded>} />
        <Route path="/equipment/requests" element={<Guarded permission={PERMISSIONS.EQUIPMENT_REQUEST}><EquipmentRequestsStatus /></Guarded>} />
        <Route path="/equipment/:id" element={<Guarded permission={PERMISSIONS.EQUIPMENT_VIEW}><EquipmentDetail /></Guarded>} />

        {/* ============================================
              SUPPLIERS
          ============================================ */}
        <Route path="/suppliers" element={<Guarded permission={PERMISSIONS.SUPPLIERS_VIEW}><Suppliers /></Guarded>} />
        <Route path="/suppliers/new" element={<Guarded permission={PERMISSIONS.SUPPLIERS_CREATE}><NewSupplier /></Guarded>} />
        <Route path="/suppliers/:id" element={<Guarded permission={PERMISSIONS.SUPPLIERS_VIEW}><EditSupplier /></Guarded>} />
        <Route path="/suppliers/:id/edit" element={<Guarded permission={PERMISSIONS.SUPPLIERS_UPDATE}><EditSupplier /></Guarded>} />
        <Route path="/suppliers/:supplierId/add-equipment" element={<Guarded permission={PERMISSIONS.SUPPLIERS_UPDATE}><AddSupplierEquipment /></Guarded>} />
        <Route path="/suppliers/equipment/:equipmentId/update-rate" element={<Guarded permission={PERMISSIONS.SUPPLIERS_UPDATE}><UpdateSupplierEquipmentRate /></Guarded>} />

        {/* ============================================
              INVOICES & REPORTS
          ============================================ */}
        <Route path="/invoices" element={<Guarded permission={PERMISSIONS.INVOICES_VIEW}><Invoices /></Guarded>} />
        <Route path="/reports" element={<Navigate to="/reports/pricing" replace />} />
        <Route path="/reports/pricing" element={<Guarded permission={PERMISSIONS.REPORTS_VIEW}><PricingReports /></Guarded>} />

        {/* ============================================
              NOTIFICATIONS & SUPPORT
          ============================================ */}
        <Route path="/notifications" element={<Guarded permission={PERMISSIONS.DASHBOARD_VIEW}><Notifications /></Guarded>} />
        <Route path="/support" element={<Guarded permission={PERMISSIONS.DASHBOARD_VIEW}><SupportTicket /></Guarded>} />
        <Route path="/activity-log" element={<Guarded permission={PERMISSIONS.DASHBOARD_VIEW}><ActivityLog /></Guarded>} />

        {/* ============================================
              SETTINGS - ADMIN Only
          ============================================ */}
        <Route path="/settings" element={<Guarded permission={PERMISSIONS.SYSTEM_SETTINGS}><SystemSettings /></Guarded>} />
        <Route path="/settings/budgets" element={<Guarded permission={PERMISSIONS.SYSTEM_SETTINGS}><Budgets /></Guarded>} />
        <Route path="/settings/budgets/:id" element={<Guarded permission={PERMISSIONS.SYSTEM_SETTINGS}><BudgetDetail /></Guarded>} />
        {/* Equipment catalog - קטלוג כלים עם מחירים */}
        <Route path="/settings/equipment-catalog" element={<Guarded permission={PERMISSIONS.SYSTEM_SETTINGS}><EquipmentCatalog /></Guarded>} />
        {/* equipment-types and pricing-overrides removed - pricing is in equipment catalog */}
        <Route path="/settings/equipment-types" element={<Navigate to="/settings/equipment-catalog" replace />} />
        <Route path="/settings/pricing-overrides" element={<Navigate to="/settings/equipment-catalog" replace />} />
        <Route path="/settings/default-pricing" element={<Navigate to="/settings/equipment-catalog" replace />} />
        <Route path="/settings/constraint-reasons" element={<Guarded permission={PERMISSIONS.SYSTEM_SETTINGS}><ConstraintReasons /></Guarded>} />
        <Route path="/settings/fair-rotation" element={<Guarded permission={PERMISSIONS.SYSTEM_SETTINGS}><FairRotation /></Guarded>} />
        <Route path="/settings/work-hours" element={<Guarded permission={PERMISSIONS.SYSTEM_SETTINGS}><WorkHours /></Guarded>} />
        <Route path="/settings/suppliers" element={<Guarded permission={PERMISSIONS.SYSTEM_SETTINGS}><SupplierSettings /></Guarded>} />
        <Route path="/settings/suppliers/:id" element={<Guarded permission={PERMISSIONS.SYSTEM_SETTINGS}><SupplierSettings /></Guarded>} />

        {/* Settings - Organization (מרחבים/אזורים/פרויקטים) */}
        <Route path="/settings/organization/projects" element={<Guarded permission={PERMISSIONS.SYSTEM_SETTINGS}><Projects /></Guarded>} />
        <Route path="/settings/organization/projects/new" element={<Guarded permission={PERMISSIONS.PROJECTS_CREATE}><NewProject /></Guarded>} />
        <Route path="/settings/organization/projects/:code/edit" element={<Guarded permission={PERMISSIONS.PROJECTS_UPDATE}><EditProject /></Guarded>} />
        <Route path="/settings/organization/regions" element={<Guarded permission={PERMISSIONS.SYSTEM_SETTINGS}><Regions /></Guarded>} />
        <Route path="/settings/organization/regions/new" element={<Guarded permission={PERMISSIONS.SYSTEM_SETTINGS}><NewRegion /></Guarded>} />
        <Route path="/settings/organization/regions/:id" element={<Guarded permission={PERMISSIONS.SYSTEM_SETTINGS}><RegionDetail /></Guarded>} />
        <Route path="/settings/organization/regions/:id/edit" element={<Guarded permission={PERMISSIONS.SYSTEM_SETTINGS}><EditRegion /></Guarded>} />
        <Route path="/settings/organization/areas" element={<Guarded permission={PERMISSIONS.SYSTEM_SETTINGS}><Areas /></Guarded>} />
        <Route path="/settings/organization/areas/new" element={<Guarded permission={PERMISSIONS.SYSTEM_SETTINGS}><NewArea /></Guarded>} />
        <Route path="/settings/organization/areas/:id" element={<Guarded permission={PERMISSIONS.SYSTEM_SETTINGS}><AreaDetail /></Guarded>} />

        {/* Legacy settings routes */}
        <Route path="/settings/pricing" element={<Navigate to="/settings/pricing-overrides" replace />} />
        <Route path="/settings/supplier-equipment" element={<Navigate to="/settings/suppliers" replace />} />
        <Route path="/settings/equipment-categories" element={<Navigate to="/settings/equipment-catalog" replace />} />

        {/* ============================================
              ADMIN - Under Settings
          ============================================ */}
        {/* AdminPanel removed - redirect to users list */}
        <Route path="/settings/admin" element={<Navigate to="/settings/admin/users" replace />} />
        <Route path="/settings/admin/roles" element={<Guarded permission={PERMISSIONS.ROLES_MANAGE}><RolesPermissions /></Guarded>} />
        <Route path="/settings/admin/users" element={<Guarded permission={PERMISSIONS.USERS_VIEW}><Users /></Guarded>} />
        <Route path="/settings/admin/users/new" element={<Guarded permission={PERMISSIONS.USERS_CREATE}><NewUser /></Guarded>} />
        <Route path="/settings/admin/users/:id/edit" element={<Guarded permission={PERMISSIONS.USERS_UPDATE}><EditUser /></Guarded>} />
        <Route path="/settings/admin/activity-log" element={<Guarded permission={PERMISSIONS.SYSTEM_ACTIVITY_LOG}><ActivityLog /></Guarded>} />

        {/* Legacy admin routes - redirect to settings/admin */}
        <Route path="/admin" element={<Navigate to="/settings/admin" replace />} />
        <Route path="/admin/roles" element={<Navigate to="/settings/admin/roles" replace />} />
        <Route path="/admin/users" element={<Navigate to="/settings/admin/users" replace />} />
        <Route path="/admin/users/new" element={<Navigate to="/settings/admin/users/new" replace />} />
        <Route path="/admin/users/:id/edit" element={<Navigate to="/settings/admin/users/:id/edit" replace />} />
        <Route path="/admin/activity-log" element={<Navigate to="/settings/admin/activity-log" replace />} />
        <Route path="/admin-panel" element={<Navigate to="/settings/admin" replace />} />
        <Route path="/users/new" element={<Navigate to="/settings/admin/users/new" replace />} />
        <Route path="/users/:id/edit" element={<Navigate to="/settings/admin/users" replace />} />

        {/* ============================================
              GEOGRAPHY - Redirect to settings
          ============================================ */}
        <Route path="/regions" element={<Navigate to="/settings/organization/regions" replace />} />
        <Route path="/regions/:id" element={<Guarded permission={PERMISSIONS.SYSTEM_SETTINGS}><RegionDetail /></Guarded>} />
        <Route path="/regions/:id/edit" element={<Guarded permission={PERMISSIONS.SYSTEM_SETTINGS}><EditRegion /></Guarded>} />
        <Route path="/areas" element={<Navigate to="/settings/organization/areas" replace />} />
        <Route path="/areas/new" element={<Navigate to="/settings/organization/areas/new" replace />} />
        <Route path="/areas/:id" element={<Guarded permission={PERMISSIONS.SYSTEM_SETTINGS}><AreaDetail /></Guarded>} />
        <Route path="/locations" element={<Guarded permission={PERMISSIONS.AREAS_VIEW}><Locations /></Guarded>} />
        <Route path="/map" element={<Guarded permission={PERMISSIONS.DASHBOARD_VIEW}><ForestMap /></Guarded>} />

        {/* ============================================
              FALLBACK
          ============================================ */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Suspense>
  );
};

export default AppRoutes;
