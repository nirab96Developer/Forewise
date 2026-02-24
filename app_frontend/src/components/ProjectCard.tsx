// src/components/ProjectCard.tsx
import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Calendar, MapPin, CheckCircle, Clock, AlertCircle } from '../utils/icons';

// טיפוס לכרטיס פרויקט
interface ProjectCardProps {
  id: string;
  code: string;
  title: string;
  location: string;
  startDate: string;
  endDate?: string;
  status: 'planned' | 'in_progress' | 'completed' | 'delayed';
  progress?: number;
  description?: string;
  imageSrc?: string;
}

// מיפוי סטטוס לאייקון ולצבע
const statusConfig = {
  planned: { icon: Calendar, color: 'text-kkl-blue', text: 'מתוכנן' },
  in_progress: { icon: Clock, color: 'text-kkl-green', text: 'בביצוע' },
  completed: { icon: CheckCircle, color: 'text-green-600', text: 'הושלם' },
  delayed: { icon: AlertCircle, color: 'text-amber-500', text: 'בעיכוב' }
};

const ProjectCard: React.FC<ProjectCardProps> = ({
  id: _id, // לא בשימוש כרגע
  code,
  title,
  location,
  startDate,
  endDate,
  status,
  progress = 0,
  description,
  imageSrc
}) => {
  const navigate = useNavigate();
  const { icon: StatusIcon, color, text } = statusConfig[status];

  // פונקציה למעבר לדף פרטי הפרויקט
  const handleClick = () => {
    navigate(`/projects/${code}`);
  };

  return (
    <div 
      className="bg-white rounded-lg shadow-md hover:shadow-lg transition-all overflow-hidden cursor-pointer animate-fadeIn" 
      onClick={handleClick}
    >
      {/* תמונת פרויקט אם קיימת */}
      {imageSrc && (
        <div className="h-40 overflow-hidden">
          <img src={imageSrc} alt={title} className="w-full h-full object-cover" />
        </div>
      )}
      
      <div className="p-4">
        {/* כותרת ומיקום */}
        <h3 className="font-bold text-lg mb-1">{title}</h3>
        <div className="flex items-center text-gray-600 text-sm mb-3">
          <MapPin className="w-4 h-4 ml-1" />
          <span>{location}</span>
        </div>
        
        {/* סטטוס ותאריכים */}
        <div className="flex justify-between mb-3">
          <div className="flex items-center">
            <StatusIcon className={`w-4 h-4 ${color} ml-1`} />
            <span className={`text-sm ${color}`}>{text}</span>
          </div>
          
          <div className="text-sm text-gray-500">
            {startDate} {endDate ? ` - ${endDate}` : ''}
          </div>
        </div>
        
        {/* פס התקדמות */}
        {status === 'in_progress' && (
          <div className="mt-2 mb-3">
            <div className="w-full bg-gray-200 rounded-full h-2.5">
              <div 
                className="bg-kkl-green h-2.5 rounded-full" 
                style={{ width: `${progress}%` }}
              ></div>
            </div>
            <div className="text-xs text-right mt-1 text-gray-500">{progress}% הושלם</div>
          </div>
        )}
        
        {/* תיאור קצר */}
        {description && (
          <p className="text-gray-600 text-sm mt-2 line-clamp-2">{description}</p>
        )}
      </div>
    </div>
  );
};

export default ProjectCard;