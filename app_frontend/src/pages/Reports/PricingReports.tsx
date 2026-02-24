// @ts-nocheck
import React, { useState } from "react";
import { BarChart3, FileText, Download } from "lucide-react";

const PricingReports: React.FC = () => {
  const [loading] = useState(false);
  
  return (
    <div className="min-h-screen bg-gray-50 pt-20 pb-8 px-4 md:pr-72" dir="rtl">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-2xl font-bold text-gray-900 mb-6">דוחות תמחור</h1>
        
        <div className="bg-white rounded-xl shadow-sm p-12 text-center">
          <BarChart3 className="w-16 h-16 text-gray-300 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-gray-900 mb-2">אין דוחות זמינים</h3>
          <p className="text-gray-500 mb-6">דוחות תמחור יהיו זמינים לאחר צבירת נתונים</p>
          <div className="flex items-center justify-center gap-4 text-sm text-gray-600">
            <div className="flex items-center gap-2">
              <FileText className="w-4 h-4" />
              <span>0 דוחות</span>
            </div>
            <div className="flex items-center gap-2">
              <Download className="w-4 h-4" />
              <span>ייצוא Excel/PDF</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PricingReports;
