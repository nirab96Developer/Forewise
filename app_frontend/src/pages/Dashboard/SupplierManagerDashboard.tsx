import React from "react";
import { Truck } from "lucide-react";

const SupplierManagerDashboard: React.FC = () => (
  <div className="min-h-full bg-gray-50 p-5" dir="rtl">
    <div className="max-w-screen-xl mx-auto">
      <div className="bg-gradient-to-l from-green-700 to-green-800 rounded-2xl p-5 sm:p-6 text-white shadow-lg">
        <h1 className="text-xl font-extrabold flex items-center gap-2.5">
          <Truck className="w-6 h-6 text-green-300" />
          ניהול ספקים
        </h1>
        <p className="text-green-200 text-sm mt-1">סקירת ספקים וציוד</p>
      </div>
    </div>
  </div>
);

export default SupplierManagerDashboard;
