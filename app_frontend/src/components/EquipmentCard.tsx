// src/components/EquipmentCard.tsx
import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Truck, Calendar, CheckCircle, AlertCircle, XCircle } from '../utils/icons';

// טיפוס לכרטיס ציוד
interface EquipmentCardProps {
  id: string;
  name: string;
  type: string;
  status: 'available' | 'in_use' | 'maintenance' | 'out_of_order';
  lastMaintenance?: string;
  currentProject?: string;
  image?: string;
}

// מיפוי סטטוס לאייקון ולצבע
const statusConfig = {
  available: { icon: CheckCircle, color: 'text-kkl-green', text: 'זמין' },
  in_use: { icon: Truck, color: 'text-kkl-blue', text: 'בשימוש' },
  maintenance: { icon: AlertCircle, color: 'text-amber-500', text: 'בתחזוקה' },
  out_of_order: { icon: XCircle, color: 'text-red-500', text: 'לא תקין' }
};

const EquipmentCard: React.FC<EquipmentCardProps> = ({
  id,
  name,
  type,
  status,
  lastMaintenance,
  currentProject,
  image
}) => {
  const navigate = useNavigate();
  const { icon: StatusIcon, color, text } = statusConfig[status];

  // פונקציה למעבר לדף פרטי הציוד
  const handleClick = () => {
    navigate(`/equipment/${id}`);
  };

  return (
    <div 
      className="bg-white rounded-lg shadow-md hover:shadow-lg transition-all p-4 cursor-pointer animate-fadeIn" 
      onClick={handleClick}
    >
      <div className="flex items-start">
        {/* תמונת הציוד */}
        <div className="w-24 h-24 rounded-md overflow-hidden bg-gray-100 flex items-center justify-center ml-3">
          {image ? (
            <img src={image} alt={name} className="w-full h-full object-cover" />
          ) : (
            <Truck className="w-12 h-12 text-gray-400" />
          )}
        </div>

        {/* פרטי הציוד */}
        <div className="flex-1">
          <h3 className="font-bold text-lg mb-1">{name}</h3>
          <p className="text-gray-600 text-sm mb-2">{type}</p>
          
          {/* סטטוס */}
          <div className="flex items-center mb-2">
            <StatusIcon className={`w-4 h-4 ${color} ml-1`} />
            <span className={`text-sm ${color}`}>{text}</span>
          </div>

          {/* מידע נוסף */}
          {lastMaintenance && (
            <div className="flex items-center text-sm text-gray-500 mb-1">
              <Calendar className="w-4 h-4 ml-1" />
              <span>תחזוקה אחרונה: {lastMaintenance}</span>
            </div>
          )}
          
          {currentProject && (
            <div className="text-sm text-kkl-blue mt-2">
              בשימוש בפרויקט: {currentProject}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default EquipmentCard;