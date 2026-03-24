
// src/pages/Settings/SystemSettings.tsx
// הגדרות מערכת - מסך ראשי עם ניווט לכל ההגדרות
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Settings, Users, Truck, Wrench, MapPin, FileText, 
  ChevronLeft, Shield, Building2, Layers,
  DollarSign, Receipt, Cog, Clock
} from 'lucide-react';
import api from '../../services/api';

// Types
interface SettingsCategory {
  id: string;
  title: string;
  description: string;
  icon: React.ReactNode;
  color: string;
  items: SettingsItem[];
}

interface SettingsItem {
  id: string;
  title: string;
  description: string;
  icon: React.ReactNode;
  path: string;
  badge?: string;
}

// Settings Categories Data - Simplified, no duplicates
const settingsCategories: SettingsCategory[] = [
  {
    id: 'users',
    title: 'ניהול משתמשים',
    description: 'הוספה, עריכה והרשאות משתמשים',
    icon: <Users className="w-6 h-6" />,
    color: 'bg-blue-500',
    items: [
      {
        id: 'users-list',
        title: 'רשימת משתמשים',
        description: 'צפייה ועריכת כל המשתמשים במערכת',
        icon: <Users className="w-5 h-5" />,
        path: '/settings/admin/users',
      },
      {
        id: 'roles',
        title: 'תפקידים והרשאות',
        description: 'ניהול תפקידים והרשאות גישה',
        icon: <Shield className="w-5 h-5" />,
        path: '/settings/admin/roles',
      },
    ],
  },
  {
    id: 'suppliers',
    title: 'ספקים וציוד',
    description: 'ניהול ספקים, ציוד, תמחור, סבב הוגן ואילוצים',
    icon: <Truck className="w-6 h-6" />,
    color: 'bg-kkl-green',
    items: [
      {
        id: 'suppliers-list',
        title: 'ספקים וציוד',
        description: 'רשימת ספקים, ציוד, מספרי רישוי, תעריפים',
        icon: <Truck className="w-5 h-5" />,
        path: '/settings/suppliers',
      },
    ],
  },
  {
    id: 'budgets',
    title: 'תקציבים וניהול חשבונות',
    description: 'ניהול תקציבים, חשבוניות ודוחות כספיים',
    icon: <DollarSign className="w-6 h-6" />,
    color: 'bg-orange-500',
    items: [
      {
        id: 'budgets-list',
        title: 'תקציבים',
        description: 'ניהול תקציבי פרויקטים וניצול',
        icon: <DollarSign className="w-5 h-5" />,
        path: '/settings/budgets',
      },
      {
        id: 'invoices',
        title: 'חשבוניות',
        description: 'צפייה וניהול חשבוניות ספקים',
        icon: <Receipt className="w-5 h-5" />,
        path: '/invoices',
      },
      {
        id: 'pricing-reports',
        title: 'דוחות תמחור',
        description: 'דוחות תמחור ועלויות',
        icon: <FileText className="w-5 h-5" />,
        path: '/reports/pricing',
      },
    ],
  },
  {
    id: 'organization',
    title: 'ארגון - מרחבים, אזורים ופרויקטים',
    description: 'ניהול מבנה ארגוני ופרויקטים',
    icon: <MapPin className="w-6 h-6" />,
    color: 'bg-purple-500',
    items: [
      {
        id: 'regions',
        title: 'מרחבים',
        description: 'ניהול מרחבי Forewise',
        icon: <Building2 className="w-5 h-5" />,
        path: '/settings/organization/regions',
      },
      {
        id: 'areas',
        title: 'אזורים',
        description: 'ניהול אזורים בתוך מרחבים',
        icon: <MapPin className="w-5 h-5" />,
        path: '/settings/organization/areas',
      },
      {
        id: 'projects-management',
        title: 'ניהול פרויקטים',
        description: 'יצירה ועריכת פרויקטים',
        icon: <Building2 className="w-5 h-5" />,
        path: '/settings/organization/projects',
      },
    ],
  },
  {
    id: 'system',
    title: 'כללי מערכת',
    description: 'הגדרות כלליות ופרמטרים תפעוליים',
    icon: <Cog className="w-6 h-6" />,
    color: 'bg-gray-600',
    items: [
      {
        id: 'work-hours',
        title: 'זמני עבודה',
        description: 'שעות תקן, חריגות ומנוחה',
        icon: <Clock className="w-5 h-5" />,
        path: '/settings/work-hours',
      },
    ],
  },
  {
    id: 'reports',
    title: 'דוחות וייצוא',
    description: 'תבניות דוחות והגדרות ייצוא',
    icon: <FileText className="w-6 h-6" />,
    color: 'bg-cyan-500',
    items: [
      {
        id: 'report-templates',
        title: 'תבניות דוחות',
        description: 'עריכת תבניות PDF וייצוא',
        icon: <FileText className="w-5 h-5" />,
        path: '/reports',
      },
    ],
  },
];

const SystemSettings: React.FC = () => {
  const navigate = useNavigate();
  const [expandedCategory, setExpandedCategory] = useState<string | null>('users');
  const [counts, setCounts] = useState<any>({});

  useEffect(() => {
    loadCounts();
  }, []);

  const loadCounts = async () => {
    try {
      const res = await api.get('/dashboard/live-counts');
      setCounts(res.data || {});
    } catch (err) {
      console.error('Error loading counts:', err);
    }
  };

  // Badge map: item id → { value, color }
  const getBadge = (itemId: string): { text: string; color: string } | null => {
    const c = counts;
    const badges: Record<string, { text: string; color: string } | null> = {
      'users-list': c.users_active ? { text: `${c.users_active} פעילים`, color: 'bg-blue-100 text-blue-700' } : null,
      'roles': c.roles ? { text: `${c.roles} תפקידים · ${c.permissions} הרשאות`, color: 'bg-purple-100 text-purple-700' } : null,
      'suppliers-list': c.suppliers_active ? { text: `${c.suppliers_active} ספקים פעילים`, color: 'bg-green-100 text-green-700' } : null,
      'supplier-equipment': c.equipment_total ? { text: `${c.equipment_total} כלים`, color: 'bg-orange-100 text-orange-700' } : null,
      'budgets-list': c.budgets_total ? { text: `${c.budgets_total} תקציבים${c.budgets_overrun > 0 ? ' · ⚠' + c.budgets_overrun + ' חריגות' : ''}`, color: c.budgets_overrun > 0 ? 'bg-red-100 text-red-700' : 'bg-green-100 text-green-700' } : null,
      'invoices': c.wo_pending > 0 ? { text: `${c.wo_pending} ממתינים`, color: 'bg-red-100 text-red-700' } : null,
      'regions': c.regions ? { text: `${c.regions} מרחבים`, color: 'bg-purple-100 text-purple-700' } : null,
      'areas': c.areas ? { text: `${c.areas} אזורים`, color: 'bg-indigo-100 text-indigo-700' } : null,
      'projects-management': c.projects_active ? { text: `${c.projects_active} פרויקטים`, color: 'bg-green-100 text-green-700' } : null,
      'equipment-catalog': c.equipment_total ? { text: `${c.equipment_total} כלים`, color: 'bg-orange-100 text-orange-700' } : null,
      'fair-rotation': null,
      'constraint-reasons': null,
      'report-templates': c.rates ? { text: `${c.rates} תעריפים`, color: 'bg-cyan-100 text-cyan-700' } : null,
    };
    return badges[itemId] || null;
  };

  // Category-level badges
  const getCategoryBadge = (categoryId: string): string => {
    const c = counts;
    switch (categoryId) {
      case 'users': return c.users_active ? `${c.users_active} משתמשים` : '';
      case 'suppliers': return c.suppliers_active ? `${c.suppliers_active} ספקים · ${c.equipment_total || 0} כלים` : '';
      case 'budgets': {
        const parts = [];
        if (c.budgets_total) parts.push(`${c.budgets_total} תקציבים`);
        if (c.invoices_total) parts.push(`${c.invoices_total} חשבוניות`);
        if (c.invoices_pending > 0) parts.push(`${c.invoices_pending} ממתינות`);
        if (c.budgets_overrun > 0) parts.push(`⚠ ${c.budgets_overrun} חריגות`);
        return parts.join(' · ');
      }
      case 'organization': return `${c.regions || 0} מרחבים · ${c.areas || 0} אזורים · ${c.projects_active || 0} פרויקטים`;
      case 'system': return '';
      case 'reports': return '';
      default: return '';
    }
  };

  const handleCategoryClick = (categoryId: string) => {
    setExpandedCategory(expandedCategory === categoryId ? null : categoryId);
  };

  const handleItemClick = (path: string) => {
    navigate(path);
  };

  return (
    <div className="min-h-screen bg-kkl-bg" dir="rtl">
      <div className="max-w-5xl mx-auto px-4 py-6">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-12 h-12 bg-kkl-green rounded-xl flex items-center justify-center">
              <Settings className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-kkl-text">הגדרות מערכת</h1>
              <p className="text-gray-500">ניהול הגדרות, ספקים, כלים ופרמטרים</p>
            </div>
          </div>
        </div>

        {/* Categories Grid */}
        <div className="space-y-4">
          {settingsCategories.map((category) => (
            <div 
              key={category.id}
              className="bg-white rounded-xl shadow-sm border border-kkl-border overflow-hidden"
            >
              {/* Category Header */}
              <button
                onClick={() => handleCategoryClick(category.id)}
                className="w-full px-5 py-4 flex items-center justify-between hover:bg-gray-50 transition-colors"
              >
                <div className="flex items-center gap-4">
                  <div className={`w-12 h-12 ${category.color} rounded-xl flex items-center justify-center text-white`}>
                    {category.icon}
                  </div>
                  <div className="text-right">
                    <h2 className="text-lg font-semibold text-kkl-text">{category.title}</h2>
                    <p className="text-sm text-gray-500">{category.description}</p>
                  </div>
                  {getCategoryBadge(category.id) && (
                    <span className={`mr-auto ml-4 px-3 py-1 text-xs font-medium rounded-full ${
                      getCategoryBadge(category.id).includes('⚠') ? 'bg-red-100 text-red-700' : 'bg-gray-100 text-gray-600'
                    }`}>
                      {getCategoryBadge(category.id)}
                    </span>
                  )}
                </div>
                <ChevronLeft 
                  className={`w-5 h-5 text-gray-400 transition-transform ${
                    expandedCategory === category.id ? 'rotate-90' : ''
                  }`} 
                />
              </button>

              {/* Category Items */}
              {expandedCategory === category.id && (
                <div className="border-t border-kkl-border bg-gray-50 p-4">
                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                    {category.items.map((item) => (
                      <button
                        key={item.id}
                        onClick={() => handleItemClick(item.path)}
                        className="bg-white p-4 rounded-lg border border-kkl-border hover:border-kkl-green hover:shadow-md transition-all text-right group"
                      >
                        <div className="flex items-start gap-3">
                          <div className="w-10 h-10 bg-kkl-green-light rounded-lg flex items-center justify-center text-kkl-green group-hover:bg-kkl-green group-hover:text-white transition-colors">
                            {item.icon}
                          </div>
                          <div className="flex-1 min-w-0">
                            <h3 className="font-medium text-kkl-text group-hover:text-kkl-green transition-colors">
                              {item.title}
                            </h3>
                            <p className="text-xs text-gray-500 mt-1 line-clamp-2">
                              {item.description}
                            </p>
                          </div>
                          {getBadge(item.id) && (
                            <span className={`px-2 py-0.5 text-xs font-medium rounded-full whitespace-nowrap ${getBadge(item.id)?.color || 'bg-gray-100 text-gray-600'}`}>
                              {getBadge(item.id)?.text}
                            </span>
                          )}
                        </div>
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>

        {/* Quick Stats - from live counts */}
        <div className="mt-8 grid grid-cols-2 sm:grid-cols-4 gap-4">
          <div className="bg-white rounded-xl border border-kkl-border p-4 text-center">
            <div className="text-2xl font-bold text-kkl-green">{counts.users_active || 0}</div>
            <div className="text-sm text-gray-500">משתמשים</div>
          </div>
          <div className="bg-white rounded-xl border border-kkl-border p-4 text-center">
            <div className="text-2xl font-bold text-kkl-green">{counts.regions || 0}</div>
            <div className="text-sm text-gray-500">מרחבים</div>
          </div>
          <div className="bg-white rounded-xl border border-kkl-border p-4 text-center">
            <div className="text-2xl font-bold text-kkl-green">{counts.equipment_total || 0}</div>
            <div className="text-sm text-gray-500">כלים במערכת</div>
          </div>
          <div className="bg-white rounded-xl border border-kkl-border p-4 text-center">
            <div className="text-2xl font-bold text-kkl-green">{counts.suppliers_active || 0}</div>
            <div className="text-sm text-gray-500">ספקים פעילים</div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SystemSettings;

