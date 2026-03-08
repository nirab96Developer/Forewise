# SYSTEM MAP — Forewise (KKL Forest Management)
> מפה מלאה של המערכת: routes, דפים, API endpoints, טבלות DB
> עדכון אחרון: מרץ 2026

---

## תוכן עניינים
1. [דיאגרמת מערכת מלאה](#diagram)
2. [ניתוח לפי נושא](#by-topic)
3. [טבלת דפים](#page-table)
4. [Endpoints ללא דף פרונטאנד](#orphan-endpoints)

---

## דיאגרמת מערכת מלאה {#diagram}

```mermaid
flowchart TD
    subgraph AUTH["🔐 Auth & Identity"]
        direction TB
        L["/login\nLogin.tsx"] -->|POST /auth/login| A1[("users\notp_tokens\nsessions")]
        OTP["/otp\nOTP.tsx"] -->|POST /auth/verify-otp| A1
        CP["/change-password\nChangePassword.tsx"] -->|POST /auth/change-password| A1
        WS["/welcome\nWelcomeSplash.tsx"]:::noapi
        FP["/forgot-password\nForgotPassword.tsx"] -->|POST /auth/reset-password| A1
    end

    subgraph DASH["🏠 Dashboard"]
        direction TB
        D["/\nDashboard.tsx"] -->|GET /dashboard/summary\nGET /dashboard/my-tasks\nGET /dashboard/alerts| DB1[("projects\nwork_orders\nworklogs\nbudgets\nnotifications")]
    end

    subgraph PROJ["📁 פרויקטים"]
        direction TB
        PL["/projects\nProjectsClean.tsx"] -->|GET /projects\nGET /dashboard/projects| P1[("projects\nareas\nregions\nlocations")]
        PW["/projects/:code/workspace\nProjectWorkspaceNew.tsx"] -->|GET /projects/code/:code\nGET /work-orders\nGET /worklogs\nGET /budgets/summary\nGET /activity-logs| P2[("projects\nwork_orders\nworklogs\nbudgets\nactivity_logs")]
        NP["/settings/organization/projects/new\nNewProject.tsx"] -->|POST /projects| P1
        EP["/settings/organization/projects/:code/edit\nEditProject.tsx"] -->|PUT /projects/:id| P1
    end

    subgraph WO["📋 הזמנות עבודה"]
        direction TB
        OC["/order-coordination\nOrderCoordination.tsx"] -->|GET /work-orders\nPATCH /work-orders/:id/approve\nPOST /work-orders/:id/send-to-supplier| WO1[("work_orders\nactivity_logs\nnotifications")]
        NWO["/work-orders/new\nNewWorkOrder.tsx"] -->|POST /work-orders| WO1
        WOD["/work-orders/:id\nWorkOrderDetail.tsx"] -->|GET /work-orders/:id\nPATCH /work-orders/:id/approve\nPATCH /work-orders/:id/reject| WO1
    end

    subgraph WL["⏱️ דיווחי שעות"]
        direction TB
        WLC["/projects/:code/workspace/work-logs/new\nWorklogCreateNew.tsx"] -->|POST /worklogs\nPOST /worklogs/standard| WL1[("worklogs\nwork_orders\nequipment_scans")]
        WLA["/projects/:code/workspace/work-logs/approvals\nWorklogApproval.tsx"] -->|GET /worklogs/pending-approval\nPOST /worklogs/:id/approve\nPOST /worklogs/:id/reject| WL1
        AI["/accountant-inbox\nAccountantInbox.tsx"] -->|GET /worklogs\nGET /invoices/uninvoiced-suppliers| WL1
    end

    subgraph SUP["🏢 ספקים"]
        direction TB
        SL["/suppliers\nSuppliers.tsx"] -->|GET /suppliers| S1[("suppliers\nequipment\nequipment_types")]
        NS["/suppliers/new\nNewSupplier.tsx"] -->|POST /suppliers| S1
        ES["/suppliers/:id/edit\nEditSupplier.tsx"] -->|PUT /suppliers/:id| S1
        ASE["/suppliers/:id/add-equipment\nAddSupplierEquipment.tsx"] -->|POST /suppliers/:id/equipment| S1
        SP["/supplier-portal/:token\nSupplierPortal.tsx"] -->|GET /supplier-portal/:token\nPOST /supplier-portal/:token/accept\nPOST /supplier-portal/:token/reject| S2[("work_orders\nsuppliers\nequipment\nsupplier_rotations")]
    end

    subgraph EQ["🚜 ציוד"]
        direction TB
        EI["/equipment/inventory\nEquipmentInventory.tsx"] -->|GET /equipment\nGET /equipment-types| E1[("equipment\nequipment_types\nsuppliers")]
        ESC["/equipment/scan\nEquipmentScan.tsx"] -->|GET /equipment/by-code/:code\nPOST /equipment/:id/scan| E2[("equipment\nequipment_scans\nwork_orders")]
        ED["/equipment/:id\nEquipmentDetail.tsx"] -->|GET /equipment/:id\nPUT /equipment/:id| E1
        EQ2["/settings/equipment-catalog\nEquipmentCatalog.tsx"] -->|GET /equipment-types\nPOST /equipment-types| E1
    end

    subgraph INV["🧾 חשבוניות"]
        direction TB
        IL["/invoices\nInvoices.tsx"] -->|GET /invoices\nPOST /invoices/generate-monthly| I1[("invoices\ninvoice_items\nsuppliers\nprojects")]
        ID["/invoices/:id\nInvoiceDetail.tsx"] -->|GET /invoices/:id\nGET /invoices/:id/items\nPOST /invoices/:id/approve| I1
    end

    subgraph BUD["💰 תקציב"]
        direction TB
        BG["/settings/budgets\nBudgets.tsx"] -->|GET /budgets/summary\nGET /budgets\nPOST /budgets\nPATCH /budgets/:id| B1[("budgets\nprojects\nareas\nregions")]
        BT["/budget-transfers\nBudgetTransfers.tsx"] -->|GET /budget-transfers\nPOST /budget-transfers/request\nPOST /budget-transfers/:id/approve| B2[("budget_transfers\nbudgets")]
    end

    subgraph REP["📊 דוחות"]
        direction TB
        PR["/reports/pricing\nPricingReports.tsx"] -->|GET /reports\nGET /reports/export/excel?type=worklogs| R1[("reports\nworklogs\ninvoices")]
        XL["Excel Export"] -->|GET /reports/export/excel\n?type=worklogs|invoices|projects|equipment| R2[("worklogs\ninvoices\nprojects\nequipment")]
    end

    subgraph ORG["🏛️ ארגון / הגדרות"]
        direction TB
        RG["/settings/organization/regions\nRegions.tsx"] -->|GET /regions\nPOST /regions\nPUT /regions/:id| O1[("regions")]
        AR["/settings/organization/areas\nAreas.tsx"] -->|GET /areas\nPOST /areas\nPUT /areas/:id| O2[("areas\nregions")]
        LC["/locations\nLocationsClean.tsx"] -->|GET /locations| O3[("locations")]
        SS["/settings\nSystemSettings.tsx"] -->|GET /dashboard/live-counts\nGET /system-rates| O4[("multiple")]
        CR["/settings/constraint-reasons\nConstraintReasons.tsx"] -->|GET /supplier-constraint-reasons| O5[("supplier_constraint_reasons")]
        FR["/settings/fair-rotation\nFairRotation.tsx"] -->|GET /supplier-rotations| O6[("supplier_rotations")]
    end

    subgraph USERS["👤 משתמשים"]
        direction TB
        UL["/settings/admin/users\nUsers.tsx"] -->|GET /users| U1[("users\nroles")]
        NU["/settings/admin/users/new\nNewUser.tsx"] -->|POST /users| U1
        RP["/settings/admin/roles\nRolesPermissions.tsx"] -->|GET /roles\nGET /permissions| U2[("roles\npermissions\nrole_permissions")]
    end

    subgraph MISC["🔔 שונות"]
        direction TB
        NT["/notifications\nNotifications.tsx"] -->|GET /notifications\nPATCH /notifications/:id/read\nPATCH /notifications/read-all| N1[("notifications")]
        AL["/activity-log\nActivityLogNew.tsx"] -->|GET /activity-logs| N2[("activity_logs\nusers")]
        JR["/my-journal\nMyJournal.tsx"] -->|GET /activity-logs?user_id=me\nPOST /users/me/journal/note| N2
        MAP["/map\nForestMap.tsx"] -->|GET /geo/layers/all\nGET /geo/forest-polygons\nGET /dashboard/map| N3[("locations\nprojects\nregions\nareas")]
        SUP2["/support\nSupport.tsx"] -->|POST /support-tickets| N4[("support_tickets")]
    end

    subgraph WS_RT["⚡ Real-time"]
        WSC["WebSocket\n/ws/notifications"] -->|JWT auth via ?token=| N1
        NT -.->|subscribes| WSC
        D -.->|subscribes| WSC
    end
```

---

## ניתוח לפי נושא {#by-topic}

### 🔐 Auth — `/auth/*`
| Endpoint | Frontend | DB |
|----------|----------|----|
| POST `/auth/login` | Login.tsx | `users`, `sessions`, `otp_tokens` |
| POST `/auth/verify-otp` | OTP.tsx | `otp_tokens`, `users` |
| POST `/auth/logout` | Navbar (כל דף) | `sessions` |
| POST `/auth/change-password` | ChangePassword.tsx | `users` |
| POST `/auth/reset-password` | ForgotPassword.tsx | `users` |
| POST `/auth/webauthn/register/begin` | WelcomeSplash.tsx | `biometric_credentials` |
| POST `/auth/webauthn/login/complete` | Login.tsx (biometric) | `biometric_credentials`, `users` |

### 📁 פרויקטים — `/projects/*`
| Endpoint | Frontend | DB |
|----------|----------|----|
| GET `/projects` | ProjectsClean.tsx | `projects`, `areas`, `regions` |
| GET `/projects/code/:code` | ProjectWorkspaceNew.tsx | `projects`, `budgets`, `locations` |
| POST `/projects` | NewProject.tsx | `projects` |
| PUT `/projects/:id` | EditProject.tsx | `projects` |
| GET `/projects/:id/forest-map` | ProjectWorkspaceNew (מפה tab) | `locations`, GIS |

### 📋 הזמנות עבודה — `/work-orders/*`
| Endpoint | Frontend | DB |
|----------|----------|----|
| GET `/work-orders` | OrderCoordination.tsx, ProjectWorkspaceNew | `work_orders` |
| POST `/work-orders` | NewWorkOrder.tsx | `work_orders`, `budgets` |
| POST `/work-orders/:id/send-to-supplier` | OrderCoordination.tsx | `work_orders`, `notifications`, email |
| PATCH `/work-orders/:id/approve` | WorkOrderDetail.tsx | `work_orders`, `notifications` |
| POST `/work-orders/:id/move-to-next-supplier` | OrderCoordination.tsx | `supplier_rotations` |

### ⏱️ דיווחי שעות — `/worklogs/*`
| Endpoint | Frontend | DB |
|----------|----------|----|
| POST `/worklogs` / `/worklogs/standard` | WorklogCreateNew.tsx | `worklogs`, `equipment_scans` |
| GET `/worklogs/pending-approval` | WorklogApproval.tsx | `worklogs` |
| POST `/worklogs/:id/approve` | WorklogApproval.tsx | `worklogs`, `notifications` |
| POST `/worklogs/:id/reject` | WorklogApproval.tsx | `worklogs`, `notifications` |

### 🧾 חשבוניות — `/invoices/*`
| Endpoint | Frontend | DB |
|----------|----------|----|
| GET `/invoices` | Invoices.tsx | `invoices`, `suppliers`, `projects` |
| POST `/invoices/generate-monthly` | Invoices.tsx | `invoices`, `invoice_items`, `worklogs` |
| POST `/invoices/:id/approve` | InvoiceDetail.tsx | `invoices`, `budgets` |
| POST `/invoices/:id/mark-paid` | InvoiceDetail.tsx | `invoices` |
| GET `/invoices/uninvoiced-suppliers` | AccountantInbox.tsx | `worklogs`, `suppliers` |

### 💰 תקציב — `/budgets/*`
| Endpoint | Frontend | DB |
|----------|----------|----|
| GET `/budgets/summary` | Budgets.tsx | `budgets`, `projects`, `areas`, `regions` |
| POST `/budgets` | Budgets.tsx (modal) | `budgets` |
| GET `/budget-transfers` | BudgetTransfers.tsx | `budget_transfers`, `budgets` |
| POST `/budget-transfers/request` | BudgetTransfers.tsx | `budget_transfers`, `budgets` |

### 🗺️ מפה / GIS — `/geo/*`
| Endpoint | Frontend | DB |
|----------|----------|----|
| GET `/geo/layers/all` | ForestMap.tsx | `locations`, `projects`, `regions`, `areas` |
| GET `/geo/forest-polygons` | ForestMap.tsx | `locations` (PostGIS geom) |
| GET `/dashboard/map` | ForestMap.tsx | `projects`, `locations` |

---

## טבלת דפים {#page-table}

| דף | Route | קבצים קשורים | הערות / בעיות ידועות |
|----|-------|---------------|----------------------|
| דשבורד ראשי | `/` | `Dashboard.tsx` | תקין, קורא 5+ endpoints |
| כניסה | `/login` | `Login.tsx` | WebAuthn + OTP + biometric |
| OTP | `/otp` | `OTP.tsx` | מפנה ל-`/welcome` אחרי הצלחה |
| ברוכים הבאים | `/welcome` | `WelcomeSplash.tsx` | **אין API calls** — דף splash בלבד |
| שינוי סיסמה | `/change-password` | `ChangePassword.tsx` | תקין |
| פרויקטים | `/projects` | `ProjectsClean.tsx` | תקין |
| Workspace פרויקט | `/projects/:code/workspace` | `ProjectWorkspaceNew.tsx` | tabs לפי role |
| תיאום הזמנות | `/order-coordination` | `OrderCoordination.tsx` | **iOS: TypeError on import** (תוקן) |
| הזמנת עבודה חדשה | `/work-orders/new` | `NewWorkOrder.tsx` | navigate ל-project אחרי submit |
| פרטי הזמנה | `/work-orders/:id` | `WorkOrderDetail.tsx` | תקין |
| עריכת הזמנה | `/work-orders/:id/edit` | `EditWorkOrder.tsx` | קיים, לא בתפריט |
| דיווח שעות חדש | `/work-orders/:id/report-hours` | `WorklogCreateNew.tsx` | תלוי equipment scan |
| אישור דיווחים | `/projects/:code/workspace/work-logs/approvals` | `WorklogApproval.tsx` | רק AREA_MANAGER+ |
| תיבת נכנסות רואה חשבון | `/accountant-inbox` | `AccountantInbox.tsx` | לא בתפריט הצד |
| ציוד — מלאי | `/equipment/inventory` | `EquipmentInventory.tsx` | תקין |
| סריקת ציוד | `/equipment/scan` | `EquipmentScan.tsx` | QR + license plate |
| פרטי ציוד | `/equipment/:id` | `EquipmentDetail.tsx` | תקין |
| יתרות ציוד | `/projects/:code/equipment/balances` | `EquipmentBalances.tsx` | תקין |
| ספקים | `/suppliers` | `Suppliers.tsx` | תקין |
| ספק חדש | `/suppliers/new` | `NewSupplier.tsx` | תקין |
| עריכת ספק | `/suppliers/:id/edit` | `EditSupplier.tsx` | תקין |
| הוסף ציוד לספק | `/suppliers/:id/add-equipment` | `AddSupplierEquipment.tsx` | תקין |
| פורטל ספק | `/supplier-portal/:token` | `SupplierPortal.tsx` | **ציבורי**, ללא JWT |
| חשבוניות | `/invoices` | `Invoices.tsx` | Excel export + generate monthly |
| פרטי חשבונית | `/invoices/:id` | `InvoiceDetail.tsx` | approve/pay |
| תקציבים | `/settings/budgets` | `Budgets.tsx` | cards mobile + table desktop |
| העברות תקציב | `/budget-transfers` | `BudgetTransfers.tsx` | **לא בתפריט הצד** |
| דוחות תמחור | `/reports/pricing` | `PricingReports.tsx` | Excel export |
| מפה | `/map` | `ForestMap.tsx` | PostGIS polygons, Leaflet |
| התראות | `/notifications` | `Notifications.tsx` | + WebSocket real-time |
| יומן פעילות | `/activity-log` | `ActivityLogNew.tsx` | ADMIN בלבד |
| היומן שלי | `/my-journal` | `MyJournal.tsx` | כל התפקידים, מסונן ל-user |
| תמיכה | `/support` | `Support.tsx` | POST support-tickets |
| הגדרות מערכת | `/settings` | `SystemSettings.tsx` | live-counts dashboard |
| קטלוג ציוד | `/settings/equipment-catalog` | `EquipmentCatalog.tsx` | תקין |
| סיבות אילוץ | `/settings/constraint-reasons` | `ConstraintReasons.tsx` | תקין |
| רוטציה הוגנת | `/settings/fair-rotation` | `FairRotation.tsx` | supplier_rotations |
| שעות עבודה | `/settings/work-hours` | `WorkHours.tsx` | work_hour_settings |
| ספקים (הגדרות) | `/settings/suppliers` | `SupplierSettings.tsx` | תקין |
| פרויקטים (org) | `/settings/organization/projects` | `ProjectsClean.tsx` | שיתוף קובץ עם /projects |
| מרחבים | `/settings/organization/regions` | `Regions.tsx` | תקין |
| אזורים | `/settings/organization/areas` | `Areas.tsx` | תקין |
| מיקומים | `/locations` | `LocationsClean.tsx` | **לא בתפריט הצד** |
| משתמשים | `/settings/admin/users` | `Users.tsx` | ADMIN בלבד |
| תפקידים והרשאות | `/settings/admin/roles` | `RolesPermissions.tsx` | ADMIN בלבד |
| יומן מערכת | `/settings/admin/activity-log` | `ActivityLogNew.tsx` | שיתוף קובץ עם /activity-log |
| מצב סנכרון | `/pending-sync` | `PendingSync.tsx` | offline sync queue, לא בתפריט |

---

## Endpoints ללא דף פרונטאנד {#orphan-endpoints}

אלו endpoints קיימים ב-Backend אך אין להם דף ייעודי בפרונטאנד:

### ממשל / Admin
| Endpoint | הערה |
|----------|------|
| POST `/auth/admin/lock-account` | נקרא מ-Users.tsx ע"י כפתור inline |
| GET `/auth/admin/security-audit/:user_id` | אין דף audit מלא |
| GET `/auth/admin/login-attempts/:user_id` | אין UI |
| POST `/auth/admin/unlock-account` | נקרא inline |
| GET `/users/:id/activity` | אין דף "פעילות משתמש" |

### GIS / Geo
| Endpoint | הערה |
|----------|------|
| POST `/geo/forest-polygons/import` | ייבוא GeoJSON — אין UI, רק API |
| POST `/geo/forest-polygons/import-file` | אין UI |
| POST `/geo/projects/:id/link-polygon/:pid` | נקרא פנימית, אין UI |
| GET `/geo/regions/boundaries` | לא מוצג בנפרד |
| GET `/geo/areas/boundaries` | לא מוצג בנפרד |

### Dashboard / Reports
| Endpoint | הערה |
|----------|------|
| GET `/dashboard/work-manager-summary` | מוחזר כחלק מ-`/dashboard/my-tasks`, אין דף נפרד |
| GET `/dashboard/region-areas` | משמש כ-widget, אין דף נפרד |
| GET `/dashboard/financial-summary` | אין דף "סיכום פיננסי" נפרד |
| GET `/dashboard/monthly-costs` | משמש ב-Dashboard כ-chart |
| GET `/dashboard/hours` | אין דף "שעות עבודה" נפרד |

### הזמנות עבודה
| Endpoint | הערה |
|----------|------|
| POST `/work-orders/:id/resend-to-supplier` | אין כפתור UI |
| POST `/work-orders/:id/close` | זהה ל-complete, אין UI |
| GET `/worklogs/activity-codes` | נטען כ-dropdown, אין דף נפרד |
| POST `/worklogs/storage` | לא חשוף ב-UI (overnight/storage worklog) |

### ספקים / ציוד
| Endpoint | הערה |
|----------|------|
| GET `/suppliers/active` | נקרא פנימית, אין דף |
| GET `/equipment/maintenance-needed` | **אין דף תחזוקה** — נתונים מוחזרים אבל לא מוצגים |
| PUT `/equipment/:id/maintenance` | אין UI לתחזוקה |
| GET `/equipment-types/statistics` | אין דף stats |

### דיווחים מיוחדים
| Endpoint | הערה |
|----------|------|
| GET `/reports/export/excel?type=equipment` | אין כפתור export ב-`/equipment` |
| GET `/invoices/summary/stats` | כפול של `/invoices/statistics`, לא בשימוש |
| POST `/invoices/from-work-order/:id` | אין flow UI ישיר |

---

## סיכום — נקודות קריטיות

| נושא | סטטוס | פעולה מומלצת |
|------|--------|----------------|
| `forewise.service` כפול | ✅ תוקן — disabled | אין צורך |
| `[Errno 98]` | ✅ תוקן | אין צורך |
| N+1 queries `/areas` | ✅ תוקן | אין צורך |
| WebSocket `/ws/notifications` מחזיר 404 | ⚠️ חלקי | הנתיב הנכון הוא `/api/v1/ws/notifications` |
| דף תחזוקה ציוד | ❌ חסר | להוסיף tab "תחזוקה" ב-EquipmentDetail |
| `/accountant-inbox` | ⚠️ קיים, לא בתפריט | להוסיף ל-ACCOUNTANT sidebar |
| `/budget-transfers` | ⚠️ קיים, לא בתפריט | להוסיף ל-ADMIN / REGION_MANAGER sidebar |
| `/locations` | ⚠️ קיים, לא בתפריט | להוסיף להגדרות ארגון |
| GeoJSON import | ❌ אין UI | admin-only tool, נשאר API בלבד |
