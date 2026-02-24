// @ts-nocheck
import React from "react";
import { useNavigate, useParams } from "react-router-dom";

const WorklogDetail: React.FC = () => {
    const navigate = useNavigate();
    const { id } = useParams();

    return (
        <div className="min-h-screen bg-gray-50 pt-20 pb-8 px-4 md:pr-72" dir="rtl">
            <div className="max-w-4xl mx-auto">
                <h1 className="text-2xl font-bold text-gray-900 mb-4">פרטי דיווח #{id}</h1>
                <div className="bg-white rounded-xl shadow-sm p-6">
                    <p className="text-gray-500">פרטים בטעינה...</p>
                    <button
                        onClick={() => navigate(-1)}
                        className="mt-4 px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200"
                    >
                        חזרה
                    </button>
                </div>
            </div>
        </div>
    );
};

export default WorklogDetail;
