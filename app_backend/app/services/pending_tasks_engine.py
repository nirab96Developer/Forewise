# app/services/pending_tasks_engine.py
"""
PendingTasksEngine - Central "what's waiting for me" per role+scope.
One endpoint, all roles, same dashboard layout, different content.
"""
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_


class PendingTasksEngine:

    def get_my_tasks(self, db: Session, user_id: int, role: str,
                     region_id: Optional[int] = None,
                     area_id: Optional[int] = None) -> Dict[str, Any]:
        return {
            "kpis": self._get_kpis(db, user_id, role, region_id, area_id),
            "actions": self._get_actions(role),
            "alerts": self._get_alerts(db, role),
            "role": role,
            "generated_at": datetime.utcnow().isoformat(),
        }

    def _get_kpis(self, db, user_id, role, region_id, area_id):
        h = {"WORK_MANAGER": self._kpis_wm, "ORDER_COORDINATOR": self._kpis_coord,
             "ACCOUNTANT": self._kpis_acct, "ADMIN": self._kpis_admin,
             "FIELD_WORKER": self._kpis_field,
             "AREA_MANAGER": self._kpis_mgr, "REGION_MANAGER": self._kpis_mgr}
        fn = h.get(role, self._kpis_default)
        if role in ("AREA_MANAGER", "REGION_MANAGER"):
            return fn(db, role, region_id, area_id)
        elif role in ("WORK_MANAGER", "FIELD_WORKER"):
            return fn(db, user_id)
        elif role == "ACCOUNTANT":
            return fn(db, region_id, area_id)
        else:
            return fn(db)

    def _kpis_wm(self, db, user_id):
        from app.models import WorkOrder, Worklog
        wo_active = db.query(func.count(WorkOrder.id)).filter(
            WorkOrder.status.in_(["ACCEPTED","IN_PROGRESS"]), WorkOrder.is_active==True).scalar() or 0
        drafts = db.query(func.count(Worklog.id)).filter(
            Worklog.status.in_(["draft","DRAFT",None,""]), Worklog.is_active==True).scalar() or 0
        submitted = db.query(func.count(Worklog.id)).filter(
            Worklog.status.in_(["submitted","SUBMITTED"]), Worklog.is_active==True).scalar() or 0
        return [
            {"id":"awaiting_scan","label":"ממתינות לסריקה","value":wo_active,"icon":"scan","color":"orange","link":"/work-orders?status=IN_PROGRESS"},
            {"id":"draft_worklogs","label":"דיווחים להשלמה","value":drafts,"icon":"clock","color":"blue","link":"/work-logs?status=draft"},
            {"id":"submitted","label":"נשלחו לאישור","value":submitted,"icon":"send","color":"green","link":"/work-logs"},
        ]

    def _kpis_coord(self, db):
        from app.models import WorkOrder
        no_sup = db.query(func.count(WorkOrder.id)).filter(
            WorkOrder.status.in_(["DRAFT","PENDING"]), WorkOrder.supplier_id==None, WorkOrder.is_active==True).scalar() or 0
        pending = db.query(func.count(WorkOrder.id)).filter(
            WorkOrder.status=="PENDING_SUPPLIER", WorkOrder.is_active==True).scalar() or 0
        active = db.query(func.count(WorkOrder.id)).filter(
            WorkOrder.status.in_(["IN_PROGRESS","ACCEPTED"]), WorkOrder.is_active==True).scalar() or 0
        return [
            {"id":"no_supplier","label":"ממתינות לשיבוץ ספק","value":no_sup,"icon":"users","color":"red","link":"/work-orders?status=PENDING"},
            {"id":"pending_supplier","label":"ממתינות לאישור ספק","value":pending,"icon":"clock","color":"orange","link":"/work-orders?status=PENDING_SUPPLIER"},
            {"id":"in_field","label":"בשטח עכשיו","value":active,"icon":"truck","color":"green","link":"/work-orders?status=IN_PROGRESS"},
        ]

    def _kpis_acct(self, db, region_id, area_id):
        from app.models import Worklog, WorkOrder, Project
        pending = db.query(func.count(Worklog.id)).filter(
            Worklog.status.in_(["submitted","SUBMITTED"]), Worklog.is_active==True).scalar() or 0
        approved = db.query(func.count(Worklog.id)).filter(
            Worklog.status.in_(["approved","APPROVED"]), Worklog.is_active==True).scalar() or 0
        completed = db.query(func.count(WorkOrder.id)).filter(
            WorkOrder.status.in_(["COMPLETED","APPROVED"]), WorkOrder.is_active==True).scalar() or 0
        return [
            {"id":"pending_approval","label":"דיווחים לאישור","value":pending,"icon":"clipboard","color":"red","link":"/work-logs/approvals"},
            {"id":"ready_invoice","label":"מוכנים לחשבונית","value":approved,"icon":"receipt","color":"orange","link":"/invoices"},
            {"id":"completed_wo","label":"הזמנות שהושלמו","value":completed,"icon":"check","color":"green","link":"/work-orders?status=COMPLETED"},
        ]

    def _kpis_mgr(self, db, role, region_id, area_id):
        from app.models import WorkOrder, Project
        # Scope: filter by region/area
        proj_scope = db.query(Project.id).filter(Project.is_active==True)
        if role == "REGION_MANAGER" and region_id:
            proj_scope = proj_scope.filter(Project.region_id == region_id)
        elif role == "AREA_MANAGER" and area_id:
            proj_scope = proj_scope.filter(Project.area_id == area_id)
        scoped_project_ids = [p[0] for p in proj_scope.all()]
        
        wo_base = db.query(func.count(WorkOrder.id)).filter(WorkOrder.is_active==True)
        if scoped_project_ids:
            wo_base_scoped = wo_base.filter(WorkOrder.project_id.in_(scoped_project_ids))
        else:
            wo_base_scoped = wo_base
            
        open_wo = wo_base_scoped.filter(
            WorkOrder.status.in_(["DRAFT","PENDING","PENDING_SUPPLIER","ACCEPTED","IN_PROGRESS"])).scalar() or 0
        stuck = wo_base_scoped.filter(
            WorkOrder.status.in_(["PENDING","PENDING_SUPPLIER"]),
            WorkOrder.created_at < datetime.utcnow() - timedelta(days=3)).scalar() or 0
        projects = len(scoped_project_ids)
        return [
            {"id":"open_wo","label":"הזמנות פתוחות","value":open_wo,"icon":"file","color":"blue","link":"/work-orders"},
            {"id":"stuck","label":"הזמנות תקועות","value":stuck,"icon":"alert","color":"red","link":"/work-orders?status=PENDING"},
            {"id":"projects","label":"פרויקטים פעילים","value":projects,"icon":"building","color":"green","link":"/projects"},
        ]

    def _kpis_admin(self, db):
        from app.models.support_ticket import SupportTicket
        from app.models import WorkOrder, User as U
        tickets = 0
        try:
            tickets = db.query(func.count(SupportTicket.id)).filter(
                SupportTicket.status.in_(["open","in_progress"]), SupportTicket.is_active==True).scalar() or 0
        except: pass
        stuck = db.query(func.count(WorkOrder.id)).filter(or_(WorkOrder.status==None, WorkOrder.status=="")).scalar() or 0
        users = db.query(func.count(U.id)).filter(U.is_active==True).scalar() or 0
        return [
            {"id":"tickets","label":"טיקטים פתוחים","value":tickets,"icon":"headphones","color":"red","link":"/support"},
            {"id":"stuck","label":"תהליכים תקועים","value":stuck,"icon":"alert","color":"orange","link":"/work-orders"},
            {"id":"users","label":"משתמשים פעילים","value":users,"icon":"users","color":"green","link":"/settings/admin/users"},
        ]

    def _kpis_field(self, db, user_id):
        from app.models import Worklog
        drafts = db.query(func.count(Worklog.id)).filter(
            Worklog.user_id==user_id, Worklog.status.in_(["draft","DRAFT",None,""])).scalar() or 0
        submitted = db.query(func.count(Worklog.id)).filter(
            Worklog.user_id==user_id, Worklog.status.in_(["submitted","SUBMITTED"])).scalar() or 0
        approved = db.query(func.count(Worklog.id)).filter(
            Worklog.user_id==user_id, Worklog.status.in_(["approved","APPROVED"])).scalar() or 0
        return [
            {"id":"drafts","label":"דיווחים להשלמה","value":drafts,"icon":"edit","color":"orange","link":"/work-logs/new"},
            {"id":"submitted","label":"ממתינים לאישור","value":submitted,"icon":"clock","color":"blue","link":"/work-logs"},
            {"id":"approved","label":"אושרו","value":approved,"icon":"check","color":"green","link":"/work-logs"},
        ]

    def _kpis_default(self, db):
        from app.models import Project
        total = db.query(func.count(Project.id)).filter(Project.is_active==True).scalar() or 0
        return [{"id":"projects","label":"פרויקטים","value":total,"icon":"building","color":"green","link":"/projects"}]

    def _get_actions(self, role):
        m = {
            "WORK_MANAGER": [
                {"id":"scan","label":"סרוק כלי","path":"/equipment/scan","icon":"qr-code"},
                {"id":"report","label":"צור דיווח","path":"/work-logs/new","icon":"plus"},
                {"id":"projects","label":"הפרויקטים שלי","path":"/projects","icon":"building"},
            ],
            "ORDER_COORDINATOR": [
                {"id":"coord","label":"תאם הזמנות","path":"/order-coordination","icon":"refresh"},
                {"id":"suppliers","label":"ספקים","path":"/suppliers","icon":"truck"},
                {"id":"rotation","label":"סבב הוגן","path":"/settings/fair-rotation","icon":"rotate"},
            ],
            "ACCOUNTANT": [
                {"id":"approve","label":"אשר דיווחים","path":"/work-logs/approvals","icon":"check"},
                {"id":"invoices","label":"חשבוניות","path":"/invoices","icon":"receipt"},
                {"id":"reports","label":"דוחות","path":"/reports/pricing","icon":"chart"},
            ],
            "ADMIN": [
                {"id":"tickets","label":"פניות תמיכה","path":"/support","icon":"headphones"},
                {"id":"users","label":"ניהול משתמשים","path":"/settings/admin/users","icon":"users"},
                {"id":"settings","label":"הגדרות","path":"/settings","icon":"settings"},
            ],
            "FIELD_WORKER": [
                {"id":"report","label":"דווח שעות","path":"/work-logs/new","icon":"clock"},
                {"id":"scan","label":"סרוק ציוד","path":"/equipment/scan","icon":"qr-code"},
                {"id":"projects","label":"פרויקטים","path":"/projects","icon":"building"},
            ],
            "AREA_MANAGER": [
                {"id":"projects","label":"פרויקטים","path":"/projects","icon":"building"},
                {"id":"approvals","label":"אישורים","path":"/work-logs/approvals","icon":"check"},
                {"id":"reports","label":"דוחות","path":"/reports/pricing","icon":"chart"},
            ],
            "REGION_MANAGER": [
                {"id":"projects","label":"פרויקטים","path":"/projects","icon":"building"},
                {"id":"areas","label":"אזורים","path":"/settings/organization/areas","icon":"map"},
                {"id":"reports","label":"דוחות","path":"/reports/pricing","icon":"chart"},
            ],
        }
        return m.get(role, m.get("FIELD_WORKER",[]))

    def _get_alerts(self, db, role):
        alerts = []
        from app.models import WorkOrder
        stuck = db.query(func.count(WorkOrder.id)).filter(
            WorkOrder.status.in_(["PENDING","PENDING_SUPPLIER"]),
            WorkOrder.created_at < datetime.utcnow() - timedelta(days=3),
            WorkOrder.is_active==True).scalar() or 0
        if stuck > 0:
            alerts.append({"id":"stuck","type":"warning","message":f"{stuck} הזמנות ממתינות יותר מ-3 ימים","link":"/work-orders?status=PENDING"})
        if role == "ADMIN":
            null_s = db.query(func.count(WorkOrder.id)).filter(or_(WorkOrder.status==None, WorkOrder.status=="")).scalar() or 0
            if null_s > 0:
                alerts.append({"id":"null_status","type":"error","message":f"{null_s} הזמנות ללא סטטוס","link":"/work-orders"})
            try:
                from app.models.support_ticket import SupportTicket
                t = db.query(func.count(SupportTicket.id)).filter(SupportTicket.status=="open", SupportTicket.is_active==True).scalar() or 0
                if t > 0:
                    alerts.append({"id":"tickets","type":"info","message":f"{t} פניות תמיכה פתוחות","link":"/support"})
            except: pass
        return alerts
