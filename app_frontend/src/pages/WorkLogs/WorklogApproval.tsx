
import React, { useEffect, useState } from "react";
import { CheckCircle, XCircle, Clock, Calendar, User } from "lucide-react";
import workLogService from "../../services/workLogService";
import { getUserRole, normalizeRole, UserRole } from "../../utils/permissions";

const WorklogApproval: React.FC = () => {
    const _role = normalizeRole(getUserRole());
    const canApprove = [UserRole.ADMIN, UserRole.AREA_MANAGER, UserRole.ACCOUNTANT].includes(_role);
    const [worklogs, setWorklogs] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [filter, setFilter] = useState<string>("SUBMITTED");

    useEffect(() => {
        loadWorklogs();
    }, [filter]);

    const loadWorklogs = async () => {
        try {
            setLoading(true);
            const data = await workLogService.getWorkLogs({
                status: filter === "all" ? undefined : filter,
                limit: 50
            });
            // Handle both response formats: { work_logs: [...] } or array
            const logs = data?.work_logs || (Array.isArray(data) ? data : []);
            setWorklogs(logs);
        } catch (error) {
            console.error("Error loading worklogs:", error);
            setWorklogs([]);
        } finally {
            setLoading(false);
        }
    };

    const handleApprove = async (id: number) => {
        try {
            await workLogService.approveWorkLog(id);
            loadWorklogs();
        } catch (error) {
            console.error("Error approving worklog:", error);
        }
    };

    const handleReject = async (id: number) => {
        const reason = prompt("סיבת דחייה:");
        if (!reason) return;
        try {
            await workLogService.rejectWorkLog(id, reason);
            loadWorklogs();
        } catch (error) {
            console.error("Error rejecting worklog:", error);
        }
    };

    return (
        <div className="min-h-screen bg-gray-50 pt-6 pb-8 px-4 " dir="rtl">
            <div className="max-w-7xl mx-auto">
                <h1 className="text-2xl font-bold text-gray-900 mb-6">אישור דיווחים</h1>

                {/* Filters */}
                <div className="mb-6 flex gap-2">
                    <button
                        onClick={() => setFilter("SUBMITTED")}
                        className={`px-4 py-2 rounded-lg ${filter === "SUBMITTED" ? "bg-yellow-100 text-yellow-800" : "bg-white text-gray-700"}`}
                    >
                        ממתינים לאישור
                    </button>
                    <button
                        onClick={() => setFilter("APPROVED")}
                        className={`px-4 py-2 rounded-lg ${filter === "APPROVED" ? "bg-green-100 text-green-800" : "bg-white text-gray-700"}`}
                    >
                        מאושרים
                    </button>
                    <button
                        onClick={() => setFilter("REJECTED")}
                        className={`px-4 py-2 rounded-lg ${filter === "REJECTED" ? "bg-red-100 text-red-800" : "bg-white text-gray-700"}`}
                    >
                        נדחו
                    </button>
                    <button
                        onClick={() => setFilter("all")}
                        className={`px-4 py-2 rounded-lg ${filter === "all" ? "bg-blue-100 text-blue-800" : "bg-white text-gray-700"}`}
                    >
                        הכל
                    </button>
                </div>

                {/* Worklogs List */}
                {loading ? (
                    <div className="bg-white rounded-xl shadow-sm p-12 text-center">
                        <div className="relative">
          <div className="w-14 h-14 rounded-full border-[3px] border-emerald-200 border-t-emerald-500 animate-spin" style={{animationDuration:'0.9s'}} />
          <div className="absolute inset-0 flex items-center justify-center">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 100" width="28" height="24">
                <defs>
                  <linearGradient id="wa1_t" x1="0%" y1="0%" x2="100%" y2="0%"><stop offset="0%" stopColor="#1565c0"/><stop offset="100%" stopColor="#0097a7"/></linearGradient>
                  <linearGradient id="wa1_m" x1="0%" y1="0%" x2="100%" y2="0%"><stop offset="0%" stopColor="#0097a7"/><stop offset="50%" stopColor="#2e7d32"/><stop offset="100%" stopColor="#66bb6a"/></linearGradient>
                  <linearGradient id="wa1_b" x1="0%" y1="0%" x2="100%" y2="0%"><stop offset="0%" stopColor="#2e7d32"/><stop offset="40%" stopColor="#66bb6a"/><stop offset="100%" stopColor="#8B5e3c"/></linearGradient>
                </defs>
                <path d="M46 20 Q60 9 74 20" stroke="url(#wa1_t)" strokeWidth="5.5" fill="none" strokeLinecap="round"/>
                <path d="M30 47 Q42 34 60 43 Q78 34 90 47" stroke="url(#wa1_m)" strokeWidth="5.5" fill="none" strokeLinecap="round"/>
                <path d="M14 74 Q28 60 46 69 Q60 76 74 69 Q92 60 106 74" stroke="url(#wa1_b)" strokeWidth="5.5" fill="none" strokeLinecap="round"/>
                <line x1="60" y1="76" x2="60" y2="90" stroke="#8B5e3c" strokeWidth="3.5" strokeLinecap="round"/>
                <circle cx="60" cy="95" r="5" fill="#8B5e3c"/>
              </svg>
          </div>
        </div>
                        <p className="text-gray-500 mt-4">טוען דיווחים...</p>
                    </div>
                ) : worklogs.length === 0 ? (
                    <div className="bg-white rounded-xl shadow-sm p-12 text-center">
                        <Clock className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                        <p className="text-gray-500">אין דיווחים {filter !== "all" ? `עם סטטוס "${filter}"` : ""}</p>
                    </div>
                ) : (
                    <div className="space-y-4">
                        {worklogs.map((worklog) => (
                            <div key={worklog.id} className="bg-white rounded-xl shadow-sm p-6">
                                <div className="flex justify-between items-start mb-4">
                                    <div>
                                        <h3 className="text-lg font-semibold">{worklog.project_name || "פרויקט לא ידוע"}</h3>
                                        <p className="text-sm text-gray-500">דיווח #{worklog.report_number || worklog.id}</p>
                                    </div>
                                    <span className={`px-3 py-1 rounded-full text-sm ${(worklog.status || '').toUpperCase() === 'APPROVED' ? 'bg-green-100 text-green-800' :
                                            (worklog.status || '').toUpperCase() === 'REJECTED' ? 'bg-red-100 text-red-800' :
                                                'bg-yellow-100 text-yellow-800'
                                        }`}>
                                        {(worklog.status || '').toUpperCase() === 'APPROVED' ? 'מאושר' :
                                            (worklog.status || '').toUpperCase() === 'REJECTED' ? 'נדחה' :
                                                'ממתין'}
                                    </span>
                                </div>

                                <div className="grid grid-cols-2 gap-4 text-sm mb-4">
                                    <div className="flex items-center gap-2">
                                        <Calendar className="w-4 h-4 text-gray-400" />
                                        <span>{worklog.report_date || worklog.work_date || '-'}</span>
                                    </div>
                                    <div className="flex items-center gap-2">
                                        <Clock className="w-4 h-4 text-gray-400" />
                                        <span>{worklog.total_hours || worklog.work_hours || '-'} שעות</span>
                                    </div>
                                    <div className="flex items-center gap-2">
                                        <User className="w-4 h-4 text-gray-400" />
                                        <span>{worklog.user_name || 'משתמש לא ידוע'}</span>
                                    </div>
                                </div>

                                {(worklog.activity_description || worklog.description) && (
                                    <p className="text-sm text-gray-600 mb-4">{worklog.activity_description || worklog.description}</p>
                                )}

                                {canApprove && ['PENDING', 'SUBMITTED'].includes((worklog.status || '').toUpperCase()) && (
                                    <div className="flex gap-3 pt-4 border-t">
                                        <button
                                            onClick={() => handleApprove(worklog.id)}
                                            className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
                                        >
                                            <CheckCircle className="w-5 h-5" />
                                            אשר
                                        </button>
                                        <button
                                            onClick={() => handleReject(worklog.id)}
                                            className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700"
                                        >
                                            <XCircle className="w-5 h-5" />
                                            דחה
                                        </button>
                                    </div>
                                )}
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
};

export default WorklogApproval;
