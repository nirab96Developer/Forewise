
// src/pages/Dashboard/Dashboard.tsx
// מרכיב ראשי - דשבורד מותאם לפי תפקיד המשתמש
import React from "react";
import { useAuth } from "../../contexts/AuthContext";
import { normalizeRole, UserRole } from "../../utils/permissions";
import { Navigate } from "react-router-dom";

// דשבורדים לפי תפקיד
import DefaultDashboard from "./DefaultDashboard";
import AccountantDashboard from "./AccountantDashboard";
import AreaManagerDashboard from "./AreaManagerDashboard";
import RegionManagerDashboard from "./RegionManagerDashboard";
import AdminDashboard from "./AdminDashboard";
import WorkManagerDashboard from "./WorkManagerDashboard";
import OrderCoordinatorDashboard from "./OrderCoordinatorDashboard";

// Dashboard Component - דשבורד מותאם לפי תפקיד
const Dashboard: React.FC = () => {
  const { user } = useAuth();
  
  // נרמל את התפקיד
  const userRole = normalizeRole(user?.role || '');
  
  // Debug log
  
  // בחירת דשבורד לפי תפקיד
  switch (userRole) {
// הנהלה מערכתית
    case UserRole.ADMIN:
      return <AdminDashboard />;
    
// ניהול מרחבי/אזורי 
    case UserRole.REGION_MANAGER:
      return <RegionManagerDashboard />;
      
    case UserRole.AREA_MANAGER:
      return <AreaManagerDashboard />;
    
// ניהול תפעול וכספים
    case UserRole.WORK_MANAGER:
      return <WorkManagerDashboard />;
      
    case UserRole.ORDER_COORDINATOR:
      return <OrderCoordinatorDashboard />;
      
    case UserRole.ACCOUNTANT:
      return <AccountantDashboard />;
    
// ניהול ספקים
    case UserRole.SUPPLIER_MANAGER:
      return <AdminDashboard />;
    
// שטח וספקים
    case UserRole.FIELD_WORKER:
      return <WorkManagerDashboard />;
      
    case UserRole.SUPPLIER:
      // ספקים לא אמורים להתחבר לאפליקציה!
      // הם מקבלים לינק ישיר לפורטל החיצוני
      // אם ספק הגיע לכאן בטעות, ננקה את הסשן ונחזיר אותו לדף ההתחברות
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      localStorage.removeItem('user');
      window.dispatchEvent(new Event('storage'));
      return <Navigate to="/login" replace />;
    
// צפייה בלבד
    case UserRole.VIEWER:
      return <RegionManagerDashboard />;
      
    default:
      // משתמש לא מזוהה מקבל דשבורד כללי
      console.warn('[Dashboard] Unknown role, using default dashboard:', userRole);
      return <DefaultDashboard />;
  }
};

export default Dashboard;
