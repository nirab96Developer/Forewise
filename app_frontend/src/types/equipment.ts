// src/types/equipment.ts
// הגדרות טיפוסים לציוד

export interface Equipment {
    id: string;
    type: string;
    model: string;
    identifier: string; // מספר רישוי / מזהה
    manufacturer: string;
    yearOfManufacture?: number;
    supplier: EquipmentSupplier;
    status: EquipmentStatus;
    location?: string;
    assignedTo?: string;
    lastMaintenance?: string;
    nextMaintenance?: string;
    specifications?: {[key: string]: string};
    notes?: string;
    images?: string[];
    documents?: string[];
    createdAt: string;
    updatedAt: string;
  }
  
  export interface EquipmentSupplier {
    id: string;
    name: string;
    contact: string;
    phone: string;
    email: string;
    address?: string;
    rating: number;
  }
  
  export type EquipmentStatus = 
    | "available"   // זמין
    | "in_use"      // בשימוש
    | "maintenance" // בתחזוקה
    | "repair"      // בתיקון
    | "reserved"    // שמור
    | "unavailable" // לא זמין
    | "retired";    // הוצא משימוש
  
  export interface EquipmentRequest {
    id: string;
    projectId: string;
    projectName: string;
    equipmentType: string;
    requestDate: string;
    startDate: string;
    endDate: string;
    status: EquipmentRequestStatus;
    supplier?: EquipmentSupplier;
    notes?: string;
    createdBy: string;
    rejectionReason?: string;
    workDays: number;
    createdAt: string;
    updatedAt: string;
  }
  
  export type EquipmentRequestStatus = 
    | "pending"    // ממתין לאישור
    | "approved"   // אושר
    | "rejected"   // נדחה
    | "completed"  // הושלם
    | "cancelled"; // בוטל
  
  export interface EquipmentCategory {
    id: string;
    name: string;
    description?: string;
    parentCategoryId?: string;
  }
  
  export interface EquipmentUsageLog {
    id: string;
    equipmentId: string;
    projectId: string;
    userId: string;
    startDate: string;
    endDate: string;
    hours: number;
    notes?: string;
    createdAt: string;
  }
  
  export interface EquipmentMaintenanceLog {
    id: string;
    equipmentId: string;
    maintenanceType: "routine" | "repair" | "inspection";
    date: string;
    performedBy: string;
    description: string;
    cost?: number;
    documents?: string[];
    createdAt: string;
  }