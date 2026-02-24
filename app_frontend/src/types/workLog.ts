// src/types/workLog.ts
// הגדרות טיפוסים לדיווחי עבודה

export interface WorkLog {
    id: string;
    projectId: string;
    projectName: string;
    equipmentId: string;
    equipmentType: string;
    equipmentIdentifier: string;
    userId: string;
    userName: string;
    date: string;
    startTime: string;
    endTime: string;
    totalHours: number;
    status: WorkLogStatus;
    notes?: string;
    approvedBy?: string;
    approvedAt?: string;
    rejectionReason?: string;
    createdAt: string;
    updatedAt: string;
  }
  
export type WorkLogStatus = 
  | "DRAFT"      // טיוטה
  | "SUBMITTED"  // הוגש
  | "APPROVED"   // אושר
  | "REJECTED"   // נדחה
  | "INVOICED";  // חויב
  
  export interface WorkLogSummary {
    projectId: string;
    projectName: string;
    totalHours: number;
    equipmentHours: {[key: string]: number};
    dateRange: {
      startDate: string;
      endDate: string;
    };
    status: {
      DRAFT: number;
      SUBMITTED: number;
      APPROVED: number;
      REJECTED: number;
      INVOICED: number;
    };
  }
  
  export interface WorkLogFilter {
    projectId?: string;
    equipmentId?: string;
    userId?: string;
    dateFrom?: string;
    dateTo?: string;
    status?: WorkLogStatus;
  }
  
  export interface WorkLogApproval {
    id: string;
    workLogId: string;
    approverId: string;
    approverName: string;
    status: "approved" | "rejected";
    comments?: string;
    createdAt: string;
  }
  
  export interface StandardWorkLog {
    id: string;
    name: string;
    startTime: string;
    endTime: string;
    totalHours: number;
    breakDuration: number;
    isDefault: boolean;
    createdBy: string;
    createdAt: string;
    updatedAt: string;
  }
  
  // פונקציות עזר
export function getWorkLogStatusText(status: WorkLogStatus): string {
  switch (status) {
    case "DRAFT": return "טיוטה";
    case "SUBMITTED": return "הוגש";
    case "APPROVED": return "אושר";
    case "REJECTED": return "נדחה";
    case "INVOICED": return "חויב";
    default: return status;
  }
}
  
export function getWorkLogStatusColor(status: WorkLogStatus): string {
  switch (status) {
    case "DRAFT": return "bg-blue-100 text-blue-800";
    case "SUBMITTED": return "bg-yellow-100 text-yellow-800";
    case "APPROVED": return "bg-green-100 text-green-800";
    case "REJECTED": return "bg-red-100 text-red-800";
    case "INVOICED": return "bg-purple-100 text-purple-800";
    default: return "bg-gray-100 text-gray-800";
  }
}
  
  export function calculateHours(startTime: string, endTime: string): number {
    if (!startTime || !endTime) return 0;
    
    const start = new Date(`2000-01-01T${startTime}`);
    const end = new Date(`2000-01-01T${endTime}`);
    
    let diffHours = (end.getTime() - start.getTime()) / (1000 * 60 * 60);
    
    // במקרה של מעבר ליום הבא (סוף יום עבודה אחרי חצות)
    if (diffHours < 0) {
      diffHours += 24;
    }
    
    // עיגול לשתי ספרות אחרי הנקודה
    return Math.round(diffHours * 100) / 100;
  }