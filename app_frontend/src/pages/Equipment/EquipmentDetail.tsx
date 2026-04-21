
// src/pages/Equipment/EquipmentDetail.tsx
import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ArrowRight, Calendar, MapPin, Wrench, Clock } from 'lucide-react';
import equipmentService from '../../services/equipmentService';
import { getEquipmentStatusLabel } from '../../strings';

interface EquipmentDetail {
  id: number;
  name: string;
  type: string;
  status: string;
  location: string;
  last_maintenance: string;
  next_maintenance: string;
  description: string;
  specifications: string[];
  maintenance_history: Array<{
    date: string;
    description: string;
    technician: string;
  }>;
}

const EquipmentDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [equipment, setEquipment] = useState<EquipmentDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const numId = parseInt(id || '');
    if (id && !isNaN(numId) && numId > 0) {
      fetchEquipmentDetail(numId);
    } else {
      setLoading(false);
      setError('מזהה ציוד לא תקין');
    }
  }, [id]);

  const fetchEquipmentDetail = async (equipmentId: number) => {
    try {
      setLoading(true);
      setError(null);
      const data = await equipmentService.getEquipmentById(equipmentId);
      
      // Transform API response to component format
      const locationValue = typeof data.location === 'string' 
        ? data.location 
        : (data.location as any)?.name || data.location || 'ללא מיקום';
      
      const transformed: EquipmentDetail = {
        id: data.id,
        name: data.name || 'ללא שם',
        type: data.type || 'ללא סוג',
        status: data.status || 'ללא סטטוס',
        location: locationValue,
        last_maintenance: data.last_maintenance_date || 'לא מוגדר',
        next_maintenance: data.next_maintenance_date || 'לא מוגדר',
        description: 'ללא תיאור', // Description not in Equipment interface
        specifications: [], // Specifications not in Equipment interface
        maintenance_history: [] // Maintenance history not in Equipment interface
      };
      
      setEquipment(transformed);
    } catch (error) {
      console.error('Error fetching equipment detail:', error);
      setError('שגיאה בטעינת פרטי ציוד');
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    const upper = (status || '').toUpperCase();
    if (['ACTIVE', 'AVAILABLE', 'IN_USE', 'BUSY'].includes(upper)) return 'bg-green-100 text-green-800';
    if (['MAINTENANCE', 'RESERVED'].includes(upper))                return 'bg-yellow-100 text-yellow-800';
    if (['INACTIVE', 'OUT_OF_SERVICE', 'RETIRED'].includes(upper))  return 'bg-red-100 text-red-800';
    return 'bg-gray-100 text-gray-800';
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-xl">טוען פרטי ציוד...</div>
      </div>
    );
  }

  if (error || !equipment) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-xl text-red-600">{error || 'ציוד לא נמצא'}</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center mb-4">
            <Link to="/equipment" className="text-fw-green hover:text-green-700 flex items-center">
              <ArrowRight className="w-4 h-4 ml-1" />
              חזרה לרשימת ציוד
            </Link>
          </div>
          <div className="flex justify-between items-start">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">{equipment.name}</h1>
              <p className="text-gray-600 mt-2">{equipment.description}</p>
            </div>
            <span className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(equipment.status)}`}>
              {getEquipmentStatusLabel(equipment.status)}
            </span>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Info */}
          <div className="lg:col-span-2 space-y-6">
            {/* Basic Info */}
            <div className="bg-white rounded-lg shadow-md p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">פרטים בסיסיים</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="flex items-center">
                  <MapPin className="w-5 h-5 text-gray-500 ml-2" />
                  <div>
                    <span className="text-gray-600">מיקום:</span>
                    <span className="font-medium mr-2">{equipment.location}</span>
                  </div>
                </div>
                <div className="flex items-center">
                  <Wrench className="w-5 h-5 text-gray-500 ml-2" />
                  <div>
                    <span className="text-gray-600">סוג:</span>
                    <span className="font-medium mr-2">{equipment.type}</span>
                  </div>
                </div>
                <div className="flex items-center">
                  <Calendar className="w-5 h-5 text-gray-500 ml-2" />
                  <div>
                    <span className="text-gray-600">תחזוקה אחרונה:</span>
                    <span className="font-medium mr-2">{equipment.last_maintenance}</span>
                  </div>
                </div>
                <div className="flex items-center">
                  <Clock className="w-5 h-5 text-gray-500 ml-2" />
                  <div>
                    <span className="text-gray-600">תחזוקה הבאה:</span>
                    <span className="font-medium mr-2">{equipment.next_maintenance}</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Specifications */}
            <div className="bg-white rounded-lg shadow-md p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">מפרטים טכניים</h2>
              <ul className="space-y-2">
                {equipment.specifications.map((spec, index) => (
                  <li key={index} className="flex items-center">
                    <div className="w-2 h-2 bg-fw-green rounded-full ml-2"></div>
                    <span className="text-gray-700">{spec}</span>
                  </li>
                ))}
              </ul>
            </div>

            {/* Maintenance History */}
            <div className="bg-white rounded-lg shadow-md p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">היסטוריית תחזוקה</h2>
              <div className="space-y-4">
                {equipment.maintenance_history.map((maintenance, index) => (
                  <div key={index} className="border-l-4 border-fw-green pl-4 py-2">
                    <div className="flex justify-between items-start">
                      <div>
                        <p className="font-medium text-gray-900">{maintenance.description}</p>
                        <p className="text-sm text-gray-600">טכנאי: {maintenance.technician}</p>
                      </div>
                      <span className="text-sm text-gray-500">{maintenance.date}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Quick Actions */}
            <div className="bg-white rounded-lg shadow-md p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">פעולות מהירות</h3>
              <div className="space-y-3">
                <button className="w-full bg-fw-green hover:bg-green-700 text-white px-4 py-2 rounded-lg">
                  הזמן לתחזוקה
                </button>
                <button className="w-full bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg">
                  עדכן מיקום
                </button>
                <button className="w-full bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded-lg">
                  ערוך פרטים
                </button>
              </div>
            </div>

            {/* Status Info */}
            <div className="bg-white rounded-lg shadow-md p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">סטטוס נוכחי</h3>
              <div className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-gray-600">סטטוס:</span>
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(equipment.status)}`}>
                    {getEquipmentStatusLabel(equipment.status)}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">מיקום:</span>
                  <span className="font-medium">{equipment.location}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">זמין:</span>
                  <span className="text-green-600 font-medium">כן</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default EquipmentDetail;
