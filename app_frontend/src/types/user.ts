// src/types/user.ts
// הגדרות טיפוסים למשתמשים

export interface User {
    id: string;
    username: string;
    email: string;
    firstName: string;
    lastName: string;
    role: UserRole;
    department?: string;
    position?: string;
    phone?: string;
    avatar?: string;
    isActive: boolean;
    lastLogin?: string;
    permissions: Permission[];
    preferences?: UserPreferences;
    createdAt: string;
    updatedAt: string;
  }
  
  export type UserRole = 
    | "admin"           // מנהל מערכת
    | "manager"         // מנהל
    | "area_manager"    // מנהל אזורי
    | "project_manager" // מנהל פרויקטים
    | "field_worker"    // מנהל עבודה (legacy)
    | "equipment_manager" // מנהל ציוד
    | "finance"         // כספים
    | "viewer";         // מנהל מרחב (legacy)
  
  export interface Permission {
    resource: string;
    actions: ("view" | "create" | "edit" | "delete" | "approve")[];
  }
  
  export interface UserPreferences {
    language: "he" | "en";
    theme: "light" | "dark" | "system";
    notifications: {
      email: boolean;
      inApp: boolean;
      sms: boolean;
    };
    dashboardLayout?: string;
  }
  
  export interface AuthState {
    user: User | null;
    token: string | null;
    isAuthenticated: boolean;
    loading: boolean;
    error: string | null;
  }
  
  export interface LoginCredentials {
    username: string;
    password: string;
  }
  
  export interface LoginResponse {
    user: User;
    token: string;
    expiresIn: number;
  }
  
  export interface UserActivity {
    id: string;
    userId: string;
    action: string;
    resource: string;
    resourceId?: string;
    details?: string;
    ipAddress?: string;
    createdAt: string;
  }
  
  // פונקציות עזר
  export function getUserFullName(user: User): string {
    return `${user.firstName} ${user.lastName}`;
  }
  
  export function getUserRoleText(role: UserRole): string {
    switch (role) {
      case "admin": return "מנהל מערכת";
      case "manager": return "מנהל";
      case "area_manager": return "מנהל אזור";
      case "project_manager": return "מנהל פרויקטים";
      case "field_worker": return "מנהל עבודה";
      case "equipment_manager": return "מנהל ציוד";
      case "finance": return "כספים";
      case "viewer": return "מנהל מרחב";
      default: return role;
    }
  }
  
  export function hasPermission(user: User, resource: string, action: "view" | "create" | "edit" | "delete" | "approve"): boolean {
    if (!user || !user.permissions) return false;
    
    // מנהל מערכת יכול לעשות הכל
    if (user.role === "admin") return true;
    
    const permission = user.permissions.find(p => p.resource === resource);
    return permission ? permission.actions.includes(action) : false;
  }