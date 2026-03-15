
import React, { useState, useEffect } from "react";
import { useParams, Link } from "react-router-dom";
import {
  ArrowRight,
  AlertCircle,
  Search,
  Package,
  CheckCircle,
  Clock,
  TrendingUp,
} from "lucide-react";
import equipmentService, { Equipment } from "../../services/equipmentService";
import UnifiedLoader from "../../components/common/UnifiedLoader";

interface EquipmentBalance {
  id: number;
  name: string;
  code: string;
  type: string;
  status: string;
  supplier_name?: string;
  current_value?: number;
  purchase_price?: number;
  location?: string;
  last_maintenance_date?: string;
  next_maintenance_date?: string;
}

const EquipmentBalances: React.FC = () => {
  const { code } = useParams();
  const [equipment, setEquipment] = useState<EquipmentBalance[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [typeFilter, setTypeFilter] = useState("all");

  useEffect(() => {
    fetchEquipment();
  }, []);

  const fetchEquipment = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await equipmentService.getEquipment({ page_size: 200 });
      const items = response.items || response.equipment || [];
      setEquipment(
        items.map((item: Equipment) => ({
          id: item.id,
          name: item.name,
          code: item.code,
          type: item.type,
          status: item.status,
          supplier_name: item.supplier_name,
          current_value: item.current_value,
          purchase_price: item.purchase_price,
          location: typeof item.location === "string" ? item.location : (item.location as any)?.name || "",
          last_maintenance_date: item.last_maintenance_date,
          next_maintenance_date: item.next_maintenance_date,
        }))
      );
    } catch (err: any) {
      console.error("Error fetching equipment:", err);
      setError("שגיאה בטעינת נתוני ציוד");
    } finally {
      setLoading(false);
    }
  };

  const filteredEquipment = equipment.filter((item) => {
    const matchesSearch =
      !searchTerm ||
      item.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      item.code.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (item.supplier_name || "").toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = statusFilter === "all" || item.status === statusFilter;
    const matchesType = typeFilter === "all" || item.type === typeFilter;
    return matchesSearch && matchesStatus && matchesType;
  });

  const types = [...new Set(equipment.map((e) => e.type).filter(Boolean))];

  const totalValue = filteredEquipment.reduce((sum, e) => sum + (e.current_value || 0), 0);
  const totalPurchase = filteredEquipment.reduce((sum, e) => sum + (e.purchase_price || 0), 0);
  const activeCount = filteredEquipment.filter((e) => e.status === "active" || e.status === "פעיל").length;
  const maintenanceCount = filteredEquipment.filter(
    (e) => e.status === "maintenance" || e.status === "תחזוקה"
  ).length;

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat("he-IL", { style: "currency", currency: "ILS", maximumFractionDigits: 0 }).format(value);
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "active":
      case "פעיל":
        return "bg-green-100 text-green-800";
      case "maintenance":
      case "תחזוקה":
        return "bg-yellow-100 text-yellow-800";
      case "inactive":
      case "לא פעיל":
        return "bg-red-100 text-red-800";
      default:
        return "bg-gray-100 text-gray-800";
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case "active":
        return "פעיל";
      case "maintenance":
        return "תחזוקה";
      case "inactive":
        return "לא פעיל";
      default:
        return status;
    }
  };

  if (loading) return <UnifiedLoader size="full" />;

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="bg-white rounded-xl shadow-sm p-8 max-w-md text-center">
          <AlertCircle className="w-12 h-12 text-red-400 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-gray-900 mb-2">שגיאה</h3>
          <p className="text-gray-500 mb-4">{error}</p>
          <button onClick={fetchEquipment} className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700">
            נסה שוב
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 pt-6 pb-8 px-4 " dir="rtl">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          {code && (
            <Link to={`/projects/${code}`} className="text-green-600 hover:text-green-700 flex items-center text-sm mb-4">
              <ArrowRight className="w-4 h-4 ml-1" />
              חזרה לפרויקט
            </Link>
          )}
          <h1 className="text-2xl font-bold text-gray-900">יתרות ציוד</h1>
          <p className="text-gray-500 mt-1">סיכום מצב ושווי ציוד</p>
        </div>

        {/* Summary Cards */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <div className="bg-white rounded-xl shadow-sm p-4">
            <div className="flex items-center gap-2 text-gray-500 text-sm mb-1">
              <Package className="w-4 h-4" />
              סה"כ פריטים
            </div>
            <div className="text-2xl font-bold text-gray-900">{filteredEquipment.length}</div>
          </div>
          <div className="bg-white rounded-xl shadow-sm p-4">
            <div className="flex items-center gap-2 text-green-600 text-sm mb-1">
              <CheckCircle className="w-4 h-4" />
              פעילים
            </div>
            <div className="text-2xl font-bold text-green-700">{activeCount}</div>
          </div>
          <div className="bg-white rounded-xl shadow-sm p-4">
            <div className="flex items-center gap-2 text-yellow-600 text-sm mb-1">
              <Clock className="w-4 h-4" />
              בתחזוקה
            </div>
            <div className="text-2xl font-bold text-yellow-700">{maintenanceCount}</div>
          </div>
          <div className="bg-white rounded-xl shadow-sm p-4">
            <div className="flex items-center gap-2 text-blue-600 text-sm mb-1">
              <TrendingUp className="w-4 h-4" />
              שווי נוכחי
            </div>
            <div className="text-xl font-bold text-blue-700">{formatCurrency(totalValue)}</div>
            {totalPurchase > 0 && (
              <div className="text-xs text-gray-400 mt-1">רכישה: {formatCurrency(totalPurchase)}</div>
            )}
          </div>
        </div>

        {/* Filters */}
        <div className="bg-white rounded-xl shadow-sm p-4 mb-6">
          <div className="flex flex-wrap gap-4">
            <div className="relative flex-1 min-w-[200px]">
              <Search className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
              <input
                type="text"
                placeholder="חיפוש לפי שם, קוד או ספק..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pr-10 pl-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent text-sm"
              />
            </div>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="pr-3 pl-10 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent text-sm min-w-[130px]"
            >
              <option value="all">כל הסטטוסים</option>
              <option value="active">פעיל</option>
              <option value="פעיל">פעיל (HE)</option>
              <option value="maintenance">תחזוקה</option>
              <option value="תחזוקה">תחזוקה (HE)</option>
              <option value="inactive">לא פעיל</option>
            </select>
            {types.length > 0 && (
              <select
                value={typeFilter}
                onChange={(e) => setTypeFilter(e.target.value)}
                className="pr-3 pl-10 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent text-sm min-w-[130px]"
              >
                <option value="all">כל הסוגים</option>
                {types.map((t) => (
                  <option key={t} value={t}>{t}</option>
                ))}
              </select>
            )}
          </div>
        </div>

        {/* Table */}
        <div className="bg-white rounded-xl shadow-sm overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 border-b">
                <tr>
                  <th className="text-right px-4 py-3 font-medium text-gray-600">קוד</th>
                  <th className="text-right px-4 py-3 font-medium text-gray-600">שם</th>
                  <th className="text-right px-4 py-3 font-medium text-gray-600">סוג</th>
                  <th className="text-right px-4 py-3 font-medium text-gray-600">סטטוס</th>
                  <th className="text-right px-4 py-3 font-medium text-gray-600">ספק</th>
                  <th className="text-right px-4 py-3 font-medium text-gray-600">מיקום</th>
                  <th className="text-right px-4 py-3 font-medium text-gray-600">מחיר רכישה</th>
                  <th className="text-right px-4 py-3 font-medium text-gray-600">שווי נוכחי</th>
                  <th className="text-right px-4 py-3 font-medium text-gray-600">תחזוקה הבאה</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {filteredEquipment.map((item) => (
                  <tr key={item.id} className="hover:bg-gray-50 transition-colors">
                    <td className="px-4 py-3">
                      <Link to={`/equipment/${item.id}`} className="text-green-600 hover:text-green-700 font-medium">
                        {item.code}
                      </Link>
                    </td>
                    <td className="px-4 py-3 font-medium text-gray-900">{item.name}</td>
                    <td className="px-4 py-3 text-gray-600">{item.type}</td>
                    <td className="px-4 py-3">
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(item.status)}`}>
                        {getStatusText(item.status)}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-gray-600">{item.supplier_name || "-"}</td>
                    <td className="px-4 py-3 text-gray-600">{item.location || "-"}</td>
                    <td className="px-4 py-3 text-gray-600">
                      {item.purchase_price ? formatCurrency(item.purchase_price) : "-"}
                    </td>
                    <td className="px-4 py-3 font-medium text-gray-900">
                      {item.current_value ? formatCurrency(item.current_value) : "-"}
                    </td>
                    <td className="px-4 py-3 text-gray-600">
                      {item.next_maintenance_date
                        ? new Date(item.next_maintenance_date).toLocaleDateString("he-IL")
                        : "-"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {filteredEquipment.length === 0 && (
            <div className="text-center py-12">
              <Package className="w-12 h-12 text-gray-300 mx-auto mb-3" />
              <h3 className="text-lg font-medium text-gray-900 mb-1">לא נמצא ציוד</h3>
              <p className="text-gray-500">נסה לשנות את מסנני החיפוש</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default EquipmentBalances;
