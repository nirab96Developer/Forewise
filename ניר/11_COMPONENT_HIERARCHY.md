# Component Hierarchy — היררכיית רכיבים

## עץ רכיבים ראשי

```mermaid
flowchart TD
    subgraph ROOT["React App"]
        MAIN["main.tsx\nBrowserRouter\nAuthProvider\nApp"]
        APP["App.tsx\n- isLoggedIn state\n- Navigation (if logged)\n- AppRoutes\n- ToastProvider\n- DebugPanel\n- HumanSupportChat"]
    end

    subgraph NAV["Navigation"]
        NAVIGATION["Navigation.tsx\n- role-based menu (menuConfig)\n- sidebar mobile/desktop\n- user avatar + logout\n- notification bell"]
    end

    subgraph ROUTE_TREE["Route Tree (routes/index.tsx)"]
        PUBLIC_R["Public Routes\n/login → Login\n/otp → OTP\n/forgot-password → ForgotPassword\n/reset-password → ResetPassword\n/supplier-portal/:token → SupplierPortal\n/supplier-landing/:token → SupplierPortal"]
        
        GUARDED_R["Guarded Routes (ProtectedRoute)"]
        
        GUARDED_R --> DASH_ROUTE["/ → Dashboard\nrequiredPermission: DASHBOARD.VIEW"]
        GUARDED_R --> PROJ_ROUTES["Projects\n/projects → ProjectsClean\n/projects/:code/workspace → ProjectWorkspaceNew\n/projects/new → NewProject\n/projects/:code/edit → EditProject"]
        GUARDED_R --> WO_ROUTES["Work Orders\n/work-orders → WorkOrders\n/work-orders/new → NewWorkOrder\n/work-orders/:id → WorkOrderDetail\n/work-orders/:id/edit → EditWorkOrder\n/order-coordination → OrderCoordination"]
        GUARDED_R --> WL_ROUTES["Work Logs\n/work-logs → WorkLogs\n/work-logs/new → WorklogCreateNew\n/work-logs/:id → WorklogDetail\n/work-logs/approvals → WorklogApproval"]
        GUARDED_R --> SUPP_ROUTES["Suppliers\n/suppliers → Suppliers\n/suppliers/new → NewSupplier\n/suppliers/:id → EditSupplier\n/suppliers/:id/equipment/add → AddSupplierEquipment"]
        GUARDED_R --> EQ_ROUTES["Equipment\n/equipment → EquipmentInventory\n/equipment/:id → EquipmentDetail\n/equipment/scan → EquipmentScan\n/equipment/balances → EquipmentBalances\n/equipment/requests → EquipmentRequestsStatus"]
        GUARDED_R --> GEO_ROUTES["Geography\n/regions → Regions\n/regions/:id → RegionDetail\n/areas → Areas\n/areas/:id → AreaDetail\n/locations → LocationsClean\n/map → ForestMap"]
        GUARDED_R --> FIN_ROUTES["Finance\n/invoices → Invoices\n/budgets → Budgets\n/budgets/:id → BudgetDetail"]
        GUARDED_R --> USER_ROUTES["Users\n/users → Users\n/users/new → NewUser\n/users/:id/edit → EditUser"]
        GUARDED_R --> OTHER_ROUTES["Other\n/notifications → Notifications\n/activity-log → ActivityLogNew\n/support → Support\n/reports → PricingReports\n/settings → SystemSettings\n/settings/roles → RolesPermissions\n/settings/fair-rotation → FairRotation\n..."]
    end

    MAIN --> APP
    APP --> NAV
    APP --> ROUTE_TREE
```

---

## ProjectWorkspaceNew — מבנה פנימי

```mermaid
flowchart TD
    PWS["ProjectWorkspaceNew.tsx\n/projects/:code/workspace"]
    
    PWS --> HEADER["Header Bar\n- שם פרויקט\n- קוד\n- סטטוס badge\n- כפתורי עריכה"]
    
    PWS --> TABS["Tabs Component\n(common/Tabs.tsx)"]
    
    TABS --> TAB1["Tab: סקירה\n- תקציב summary\n- מנהל + אזור\n- תאריכים\n- תיאור"]
    TABS --> TAB2["Tab: הזמנות עבודה\n- WorkOrders list\n- status filter\n- create new WO"]
    TABS --> TAB3["Tab: דיווחי שעות\n- Worklogs list\n- total hours\n- approve actions"]
    TABS --> TAB4["Tab: מפה\n- ForestMap component\n- project location_geom\n- Leaflet polygon"]
    TABS --> TAB5["Tab: ציוד\n- Equipment assigned\n- scan history"]
    
    HEADER --> ACTIONS["Actions dropdown\n- ערוך פרויקט\n- הקצה ציוד\n- צור דוח"]
```

---

## Dashboard — ניתוב לפי Role

```mermaid
flowchart TD
    DASH["Dashboard.tsx\n(route: '/')"]
    
    DASH --> CHECK["Check user role\n(from AuthContext)"]
    
    CHECK -->|"ADMIN"| ADMIN_D["AdminDashboard.tsx\n- כל הסטטיסטיקות\n- projects/suppliers/budget\n- system alerts"]
    CHECK -->|"REGION_MANAGER"| REG_D["RegionManagerDashboard.tsx\n- פרויקטים במרחב\n- budget overview\n- WO status"]
    CHECK -->|"AREA_MANAGER"| AREA_D["AreaManagerDashboard.tsx\n- פרויקטים באזור\n- worklogs pending"]
    CHECK -->|"WORK_MANAGER"| WORK_D["WorkManagerDashboard.tsx\n- הזמנות שלי\n- create WO\n- project list"]
    CHECK -->|"ACCOUNTANT"| ACCT_D["AccountantDashboard.tsx\n- invoices\n- budgets\n- financial KPIs"]
    CHECK -->|"ORDER_COORDINATOR"| COORD_D["OrderCoordinatorDashboard.tsx\n- pending WOs\n- supplier status\n- send actions"]
    CHECK -->|"FIELD_WORKER"| FIELD_D["FieldWorkerDashboard.tsx\n- today's tasks\n- worklog entry\n- equipment scan"]
    CHECK -->|"SUPPLIER"| SUPP_D["SupplierManagerDashboard.tsx\n- orders received\n- portal links"]
    CHECK -->|"VIEWER"| VIEW_D["ViewerDashboard.tsx\n- read-only stats"]
```

---

## ProtectedRoute — auth flow

```mermaid
flowchart TD
    PR["ProtectedRoute.tsx\nProps: requiredPermission?"]
    
    PR --> CHECK_AUTH{"isAuthenticated?\nlocalStorage OR sessionStorage"}
    CHECK_AUTH -->|"No"| REDIRECT_LOGIN["Navigate to /login\n+ state.from = current path"]
    CHECK_AUTH -->|"Yes"| CHECK_USER{"user data valid?"}
    CHECK_USER -->|"No"| REDIRECT_LOGIN
    CHECK_USER -->|"Yes"| CHECK_PERM{"requiredPermission?"}
    CHECK_PERM -->|"No permission needed"| RENDER["✅ Render children"]
    CHECK_PERM -->|"Check permission"| PERM_CHECK{"hasPermission(required)\nOR role===ADMIN"}
    PERM_CHECK -->|"Allowed"| RENDER
    PERM_CHECK -->|"Denied"| FORBIDDEN["403 Forbidden\n'אין הרשאה' component\n+ חזור אחורה button"]
    
    subgraph FIRST_RENDER["First Render"]
        LOADING["Loading spinner\n(TreeLoader)\nwhile checking"]
    end
```

---

## ForestMap — שכבות גיאוגרפיות

```mermaid
flowchart TD
    FM["ForestMap.tsx\n/map route"]
    
    FM --> API_CALL["GET /api/v1/geo/layers/all"]
    API_CALL --> LAYERS_DATA["Response:\n- regions: GeoJSON features\n- areas: GeoJSON features\n- projects: [{lat,lng,code,geo_validation_status}]"]
    
    FM --> LEAFLET["LeafletMap.tsx\n- OpenStreetMap tiles\n- Satellite toggle"]
    
    LEAFLET --> POLY_LAYER["Polygon Layer\n- regions (colored by region)\n- areas (colored by index)\n- opacity varies by user scope"]
    
    LEAFLET --> POINT_LAYER["Point Layer\n- green circle = regular project\n- yellow star = 'שלי' project\n- ⚠️ warning for NEAR (≤3km from border)"]
    
    LEAFLET --> TOOLTIPS["Popup on click:\n- שם פרויקט\n- קוד | מרחב\n- NEAR warning + distance\n- 'פתח פרויקט' button"]
    
    FM --> SIDEBAR["Sidebar\n- שכבות toggles\n- מרחבים filter\n- מקרא\n- selected project card"]
    
    FM --> GEO_VALID["Geo Validation (3km rule):\nINSIDE ✅ = within area polygon\nNEAR ⚠️ = 0-3000m outside\nFAR ❌ = >3000m (data issue)"]
```

---

## Toast System

```mermaid
flowchart LR
    TOAST_PROVIDER["ToastProvider\n(in App.tsx)"]
    
    ANY_PAGE["כל דף"] -->|"(window as any).showToast\n(message, type)"| TOAST_PROVIDER
    
    TOAST_PROVIDER --> TOAST_UI["Toast Component\n- success (ירוק)\n- error (אדום)\n- warning (כתום)\n- info (כחול)\n- auto-dismiss 4s\n- manual close X"]
```

---

## Navigation Menu Structure (by role)

```
ADMIN:
  🏠 דשבורד
  🌲 פרויקטים
  📋 הזמנות עבודה
  ⏰ דיווחי שעות
  👷 ספקים
  🚜 ציוד
  💰 חשבוניות
  📊 תקציבים
  🗺️ מפה
  👥 משתמשים
  ⚙️ הגדרות

WORK_MANAGER:
  🏠 דשבורד
  🌲 פרויקטים שלי
  📋 הזמנות עבודה
  ⏰ דיווחי שעות
  🗺️ מפה

ORDER_COORDINATOR:
  🏠 דשבורד
  📋 תיאום הזמנות
  👷 ספקים
  🗺️ מפה

ACCOUNTANT:
  🏠 דשבורד
  💰 חשבוניות
  📊 תקציבים
  📈 דוחות
```
