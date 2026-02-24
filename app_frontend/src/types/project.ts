// src/types/project.ts
// הגדרות טיפוסים לפרויקטים

export interface Project {
    id: string;
    name: string;
    description?: string;
    areaId: string;
    areaName: string;
    subAreaId: string;
    subAreaName: string;
    startDate: string;
    endDate: string;
    budget?: number;
    contacts: ProjectContact[];
    forestType?: string;
    status: ProjectStatus;
    notes?: string;
    files?: ProjectFile[];
    equipmentNeeded: boolean;
    createdBy: string;
    createdAt: string;
    updatedAt: string;
  }
  
  export type ProjectStatus = 
    | "planning"   // בתכנון
    | "active"     // פעיל
    | "completed"  // הושלם
    | "cancelled"; // בוטל
  
  export interface ProjectContact {
    id: string;
    name: string;
    role: string;
    email: string;
    phone: string;
  }
  
  export interface ProjectFile {
    id: string;
    name: string;
    path: string;
    type: string;
    size: number;
    uploadedBy: string;
    uploadedAt: string;
  }
  
  export interface Area {
    id: string;
    name: string;
    subAreas: SubArea[];
  }
  
  export interface SubArea {
    id: string;
    name: string;
    areaId: string;
  }
  
  export interface ProjectTask {
    id: string;
    projectId: string;
    title: string;
    description?: string;
    assignedTo?: string;
    startDate?: string;
    endDate?: string;
    status: "not_started" | "in_progress" | "completed" | "delayed";
    priority: "low" | "medium" | "high" | "urgent";
    notes?: string;
    createdBy: string;
    createdAt: string;
    updatedAt: string;
  }
  
  export interface ProjectEquipment {
    projectId: string;
    equipmentId: string;
    startDate: string;
    endDate: string;
    status: "requested" | "approved" | "in_use" | "returned";
    requestedBy: string;
    approvedBy?: string;
  }
  
  export interface ProjectBudgetItem {
    id: string;
    projectId: string;
    category: string;
    description: string;
    amount: number;
    spent: number;
    remaining: number;
    createdAt: string;
    updatedAt: string;
  }
  
  // פונקציות עזר
  export function getProjectStatusText(status: ProjectStatus): string {
    switch (status) {
      case "planning": return "בתכנון";
      case "active": return "פעיל";
      case "completed": return "הושלם";
      case "cancelled": return "בוטל";
      default: return status;
    }
  }
  
  export function getProjectStatusColor(status: ProjectStatus): string {
    switch (status) {
      case "planning": return "bg-blue-100 text-blue-800";
      case "active": return "bg-green-100 text-green-800";
      case "completed": return "bg-purple-100 text-purple-800";
      case "cancelled": return "bg-red-100 text-red-800";
      default: return "bg-gray-100 text-gray-800";
    }
  }