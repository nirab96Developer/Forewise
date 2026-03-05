# API Endpoints Map — כל ה-38 Routers (עדכני מרץ 2026)

**Base URL:** `https://forewise.co/api/v1`  
**Auth:** `Authorization: Bearer {access_token}`

---

## Auth & Identity

### `/auth`
| Method | Endpoint | תיאור | Auth Required |
|--------|----------|--------|---------------|
| POST | `/auth/login` | login username+password | ❌ |
| POST | `/auth/register` | יצירת משתמש | ❌ |
| POST | `/auth/refresh` | רענון access_token | ❌ |
| POST | `/auth/logout` | התנתקות | ✅ |
| POST | `/auth/request-otp` | בקשת OTP | ❌ |
| POST | `/auth/verify-otp-v2` | אימות OTP + device | ❌ |
| POST | `/auth/device-login` | כניסה עם device_token | ❌ |
| GET | `/auth/devices` | רשימת מכשירים | ✅ |
| DELETE | `/auth/devices/{device_id}` | ביטול מכשיר | ✅ |
| POST | `/auth/send-otp` | שליחת OTP למייל | ❌ |
| POST | `/auth/verify-otp` | אימות OTP (legacy) | ❌ |
| POST | `/auth/change-password` | שינוי סיסמה | ✅ |
| POST | `/auth/reset-password` | בקשת reset | ❌ |
| POST | `/auth/reset-password/confirm` | אישור reset | ❌ |
| POST | `/auth/2fa/setup` | הגדרת 2FA | ✅ |
| POST | `/auth/2fa/verify-setup` | אימות הגדרת 2FA | ✅ |
| POST | `/auth/2fa/disable` | ביטול 2FA | ✅ |
| POST | `/auth/biometric/register` | רישום biometric | ✅ |
| POST | `/auth/biometric/authenticate` | התחברות biometric | ❌ |
| GET | `/auth/sessions` | sessions פעילות | ✅ |
| DELETE | `/auth/sessions/{id}` | ביטול session | ✅ |
| GET | `/auth/status` | מצב auth | ✅ |
| POST | `/auth/admin/lock-account` | נעילת חשבון | ✅ ADMIN |

### `/users`
| Method | Endpoint | תיאור |
|--------|----------|--------|
| GET | `/users` | רשימת משתמשים |
| POST | `/users` | יצירת משתמש |
| GET | `/users/{id}` | פרטי משתמש |
| PUT | `/users/{id}` | עדכון משתמש |
| DELETE | `/users/{id}` | מחיקת משתמש |
| GET | `/users/me` | המשתמש הנוכחי |
| PUT | `/users/{id}/suspend` | **השהיית משתמש** — סיבה + scheduled_deletion_at |
| PUT | `/users/{id}/reactivate` | **החזרת משתמש** — ביטול השהייה |
| PUT | `/users/{id}/role` | **החלפת תפקיד** — שמירת previous_role_id |

---

## Geography

### `/regions`
| GET /regions | GET /regions/{id} | POST /regions | PUT /regions/{id} | DELETE /regions/{id} |

### `/areas`
| GET /areas | GET /areas/{id} | POST /areas | PUT /areas/{id} | GET /areas/statistics |

### `/locations`
| GET /locations | POST /locations | PUT /locations/{id} | DELETE /locations/{id} |

### `/departments`
| GET /departments | POST /departments | PUT /departments/{id} |

### `/geo`
| Method | Endpoint | תיאור |
|--------|----------|--------|
| GET | `/geo/layers/all` | כל שכבות המפה (regions+areas+projects) |
| GET | `/geo/projects/{id}/forest-polygon` | פוליגון יער לפרויקט |
| POST | `/geo/projects/{id}/link-polygon/{polygon_id}` | קישור פוליגון |
| POST | `/geo/projects/{id}/find-polygon` | מציאת פוליגון אוטומטית |

---

## Projects

### `/projects`
| Method | Endpoint | תיאור |
|--------|----------|--------|
| GET | `/projects` | רשימת פרויקטים — **role-filtered אוטומטי:** REGION_MANAGER→region, AREA_MANAGER→area, WORK_MANAGER→my_projects=true |
| POST | `/projects` | יצירת פרויקט |
| GET | `/projects/{id}` | פרטי פרויקט |
| PUT | `/projects/{id}` | עדכון פרויקט |
| DELETE | `/projects/{id}` | מחיקה (soft) |
| GET | `/projects/by-code/{code}` | לפי קוד (+ budget data) |
| GET | `/projects/code/{code}` | **Workspace endpoint** — מחזיר מידע מועשר: `manager` (WORK_MANAGER מ-project_assignments), `accountant` (ACCOUNTANT מ-area_id), `area_manager` (AREA_MANAGER מ-area_id), `region_name`, `area_name`, forest polygon centroid |
| GET | `/projects/statistics` | סטטיסטיקות |
| POST | `/projects/{id}/restore` | שחזור |
| GET | `/projects/{id}/forest-map` | מפת יער + `center_lat`/`center_lng` בFForestInfo |

**Response schema של `/projects/code/{code}`:**
```json
{
  "id": 127,
  "code": "YR-045",
  "name": "פרויקט דוגמה",
  "region_name": "מרחב הצפון",
  "area_name": "אזור עמק יזרעאל",
  "manager": { "id": 12, "full_name": "אבי לוי" },
  "accountant": { "id": 7, "full_name": "רחל כהן" },
  "area_manager": { "id": 3, "full_name": "דוד מזרחי" },
  "budget": { "total_amount": 50000, "committed_amount": 10000, "spent_amount": 15000, "available_amount": 25000 }
}
```

### `/project-assignments`
| GET | POST | PUT | DELETE | GET /my-assignments | GET /project/{id}/team |

---

## Work Orders

### `/work-orders`
| Method | Endpoint | תיאור |
|--------|----------|--------|
| GET | `/work-orders` | רשימת הזמנות |
| POST | `/work-orders` | יצירה |
| GET | `/work-orders/{id}` | פרטים |
| PUT | `/work-orders/{id}` | עדכון |
| DELETE | `/work-orders/{id}` | מחיקה |
| POST | `/work-orders/{id}/approve` | **אישור** DISTRIBUTING→APPROVED |
| PATCH | `/work-orders/{id}/approve` | alias |
| POST | `/work-orders/{id}/reject` | **דחייה** |
| POST | `/work-orders/{id}/start` | **התחלה** APPROVED→ACTIVE |
| POST | `/work-orders/{id}/close` | **סיום** ACTIVE→COMPLETED |
| POST | `/work-orders/{id}/cancel` | **ביטול** |
| POST | `/work-orders/{id}/send-to-supplier` | **שליחה לספק** + portal_token |
| POST | `/work-orders/{id}/resend-to-supplier` | שליחה מחדש |
| POST | `/work-orders/{id}/move-to-next-supplier` | Fair Rotation |
| POST | `/work-orders/{id}/restore` | שחזור |
| GET | `/work-orders/statistics` | סטטיסטיקות |

### `/worklogs`
| GET | POST | GET /{id} | PUT /{id} | POST /{id}/approve | GET /by-work-order/{id} |

### `/supplier-portal` (ללא auth!)
| Method | Endpoint | תיאור |
|--------|----------|--------|
| GET | `/supplier-portal/{token}` | פרטי הזמנה לספק |
| POST | `/supplier-portal/{token}/accept` | אישור הזמנה |
| POST | `/supplier-portal/{token}/reject` | דחיית הזמנה |
| GET | `/supplier-portal/{token}/status` | סטטוס נוכחי |

---

## Suppliers & Equipment

### `/suppliers`
| GET | POST | GET /{id} | PUT /{id} | DELETE /{id} | GET /{id}/equipment |

### `/supplier-rotations`
| GET | POST | GET /{id} | PUT /{id} | POST /distribute |

### `/equipment`
| GET | POST | GET /{id} | PUT /{id} | DELETE /{id} |
| POST /{id}/scan | POST /{id}/assign | POST /{id}/release | GET /statistics |

### `/equipment-categories`
| GET | POST | GET /{id} | PUT /{id} | GET /{id}/children |

### `/equipment-types`
| GET | POST | GET /{id} | PUT /{id} | POST /{id}/activate |

---

## Finance

### `/budgets`
| Method | Endpoint | תיאור |
|--------|----------|--------|
| GET | `/budgets` | רשימת תקציבים |
| POST | `/budgets` | יצירת תקציב |
| GET | `/budgets/{id}` | פרטים |
| PUT | `/budgets/{id}` | עדכון |
| DELETE | `/budgets/{id}` | מחיקה |
| GET | `/budgets/{id}/detail` | פירוט מלא |
| GET | `/budgets/{id}/committed` | מחויב |
| GET | `/budgets/{id}/spent` | הוצא |
| GET | `/budgets/statistics` | סטטיסטיקות |

### `/invoices`
| Method | Endpoint | תיאור |
|--------|----------|--------|
| GET | `/invoices` | רשימת חשבוניות |
| POST | `/invoices` | יצירה |
| GET | `/invoices/{id}` | פרטים |
| PUT | `/invoices/{id}` | עדכון |
| DELETE | `/invoices/{id}` | מחיקה |
| POST | `/invoices/{id}/approve` | אישור |
| GET | `/invoices/{id}/items` | פריטים |
| GET | `/invoices/summary/stats` | **סטטיסטיקות** — total/total_amount/balance_due/paid_amount/overdue_count |
| POST | `/invoices/generate-monthly` | **יצירת חשבונית חודשית** מ-APPROVED worklogs |
| GET | `/invoices/uninvoiced-suppliers` | ספקים עם worklogs לא ממוינים |

### `/system-rates`
| GET | POST | PUT /{id} | DELETE /{id} |

### `/pricing`
| Method | Endpoint | תיאור |
|--------|----------|--------|
| POST | `/pricing/compute-cost` | חישוב עלות דיווח |
| GET | `/pricing/rate-for-equipment-type/{id}` | תעריף לסוג כלי |
| GET | `/pricing/simulate-days` | סימולציית עלות לימים |
| GET | `/pricing/reports/by-project` | דוח עלויות לפי פרויקט + `unverified_count` + **`worklogs_detail`** |
| GET | `/pricing/reports/by-supplier` | דוח עלויות לפי ספק |
| GET | `/pricing/reports/by-equipment-type` | דוח עלויות לפי סוג כלי |

**`worklogs_detail` per project item** (מרץ 2026):
```json
{
  "worklog_id": 45,
  "report_date": "2026-02-20",
  "work_hours": 8.5,
  "cost_before_vat": 1275.0,
  "cost_with_vat": 1487.25,
  "hourly_rate_snapshot": 150.0,
  "supplier_name": "חברת מחפרים בע\"מ",
  "equipment_license_plate": "12-345-67",
  "equipment_type": "מחפר",
  "status": "APPROVED",
  "is_verified": true
}
```

### `/budget-transfers` (**חדש**)
| Method | Endpoint | תיאור |
|--------|----------|--------|
| POST | `/budget-transfers/request` | בקשת העברת תקציב |
| POST | `/budget-transfers/{id}/approve` | אישור העברה (מלא/חלקי) |
| POST | `/budget-transfers/{id}/reject` | דחיית העברה |
| GET | `/budget-transfers` | רשימת בקשות (per role) |

### `/settings/equipment-rates` (**חדש**)
| Method | Endpoint | תיאור |
|--------|----------|--------|
| GET | `/settings/equipment-rates` | תעריפים לפי equipment_type |
| POST | `/settings/equipment-rates` | יצירת סוג ציוד חדש |
| PATCH | `/settings/equipment-rates/{id}` | עדכון תעריף + רישום היסטוריה |
| GET | `/settings/equipment-rates/{id}/history` | היסטוריית שינויי תעריף |


---

## Dashboard

| Method | Endpoint | תיאור |
|--------|----------|--------|
| GET | `/dashboard/statistics` | KPIs כלליים |
| GET | `/dashboard/projects` | פרויקטים לדשבורד |
| GET | `/dashboard/map` | נתוני מפה |
| GET | `/dashboard/summary` | סיכום מנהלים |
| GET | `/dashboard/alerts` | התראות מערכת |
| GET | `/dashboard/financial-summary` | סיכום פיננסי |
| GET | `/dashboard/live-counts` | ספירות חיות |
| GET | `/dashboard/my-tasks` | משימות שלי |

---

## Misc

| Router | Endpoints עיקריים |
|--------|------------------|
| `/notifications` | GET, POST, PUT /{id}/read, POST /read-all |
| `/activity-logs` | GET, GET /{id} |
| `/activity-types` | GET, POST, PUT /{id} |
| `/reports` | GET, POST, GET /{id}, POST /{id}/run |
| `/support-tickets` | GET, POST, GET /{id}, POST /{id}/comments |
| `/roles` | GET, POST, GET /{id}, PUT /{id} |
| `/permissions` | GET, POST, GET /{id} |
| `/role-assignments` | GET, POST, DELETE /{id} |
| `/admin/*` | Admin operations |
| `/ws` | WebSocket connection |

---

## Response Status Codes

| Code | מצב |
|------|-----|
| 200 | הצלחה |
| 201 | נוצר בהצלחה |
| 204 | מחיקה הצליחה |
| 400 | שגיאת ולידציה |
| 401 | לא מאומת |
| 403 | אין הרשאה |
| 404 | לא נמצא (גם עבור unauthorized by-id) |
| 409 | כפילות (Duplicate) |
| 422 | Pydantic validation error |
| 429 | Too Many Requests |
| 500 | שגיאת שרת |
