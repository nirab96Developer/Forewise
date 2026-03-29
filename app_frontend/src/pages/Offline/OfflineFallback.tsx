import React from "react";
import { WifiOff, RefreshCw, UploadCloud } from "lucide-react";
import { Link } from "react-router-dom";

const OfflineFallback: React.FC = () => {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 flex items-center justify-center p-4" dir="rtl">
      <div className="max-w-md w-full bg-white rounded-2xl shadow-xl border border-slate-200 p-8 text-center">
        <div className="w-16 h-16 bg-amber-100 rounded-full flex items-center justify-center mx-auto mb-4">
          <WifiOff className="w-8 h-8 text-amber-600" />
        </div>
        <h1 className="text-2xl font-bold text-slate-900 mb-2">אין חיבור לאינטרנט</h1>
        <p className="text-slate-600 leading-relaxed mb-6">
          המסך שניסית לפתוח דורש חיבור פעיל. אם עבדת קודם במערכת, אפשר להמשיך במסכים שכבר נשמרו במכשיר
          ולסנכרן פעולות ממתינות כשהחיבור יחזור.
        </p>

        <div className="space-y-3">
          <button
            type="button"
            onClick={() => window.location.reload()}
            className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-green-600 text-white rounded-xl font-medium hover:bg-green-700 transition-colors"
          >
            <RefreshCw className="w-4 h-4" />
            נסה שוב
          </button>

          <Link
            to="/pending-sync"
            className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-white text-slate-700 rounded-xl font-medium border border-slate-300 hover:bg-slate-50 transition-colors"
          >
            <UploadCloud className="w-4 h-4" />
            עבור לפריטים הממתינים לסנכרון
          </Link>
        </div>
      </div>
    </div>
  );
};

export default OfflineFallback;
