// @ts-nocheck
import React, { useEffect, useState } from "react";
import { CheckCircle, XCircle, Clock, Calendar, User } from "lucide-react";
import workLogService from "../../services/workLogService";

const WorklogApproval: React.FC = () => {
    const [worklogs, setWorklogs] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [filter, setFilter] = useState<string>("pending");

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
        <div className="min-h-screen bg-gray-50 pt-20 pb-8 px-4 md:pr-72" dir="rtl">
            <div className="max-w-7xl mx-auto">
                <h1 className="text-2xl font-bold text-gray-900 mb-6">אישור דיווחים</h1>

                {/* Filters */}
                <div className="mb-6 flex gap-2">
                    <button
                        onClick={() => setFilter("pending")}
                        className={`px-4 py-2 rounded-lg ${filter === "pending" ? "bg-yellow-100 text-yellow-800" : "bg-white text-gray-700"}`}
                    >
                        ממתינים לאישור
                    </button>
                    <button
                        onClick={() => setFilter("approved")}
                        className={`px-4 py-2 rounded-lg ${filter === "approved" ? "bg-green-100 text-green-800" : "bg-white text-gray-700"}`}
                    >
                        מאושרים
                    </button>
                    <button
                        onClick={() => setFilter("rejected")}
                        className={`px-4 py-2 rounded-lg ${filter === "rejected" ? "bg-red-100 text-red-800" : "bg-white text-gray-700"}`}
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
                        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-600 mx-auto"></div>
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
                                    <span className={`px-3 py-1 rounded-full text-sm ${worklog.status === 'approved' ? 'bg-green-100 text-green-800' :
                                            worklog.status === 'rejected' ? 'bg-red-100 text-red-800' :
                                                'bg-yellow-100 text-yellow-800'
                                        }`}>
                                        {worklog.status === 'approved' ? 'מאושר' :
                                            worklog.status === 'rejected' ? 'נדחה' :
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

                                {worklog.status === 'pending' && (
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
