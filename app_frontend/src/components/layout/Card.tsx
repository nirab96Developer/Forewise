// src/components/Layout/Card.tsx
// כרטיס אחיד לכל המערכת
import React from 'react';

interface CardProps {
  children: React.ReactNode;
  /** כותרת הכרטיס */
  title?: string;
  /** תיאור */
  subtitle?: string;
  /** אייקון */
  icon?: React.ReactNode;
  /** פעולות בצד שמאל */
  actions?: React.ReactNode;
  /** האם להציג גבול */
  bordered?: boolean;
  /** padding מותאם */
  padding?: 'none' | 'sm' | 'md' | 'lg';
  /** hover effect */
  hoverable?: boolean;
  /** onClick handler */
  onClick?: () => void;
  /** className נוסף */
  className?: string;
}

const paddingClasses = {
  none: '',
  sm: 'p-4',
  md: 'p-6',
  lg: 'p-8',
};

export const Card: React.FC<CardProps> = ({
  children,
  title,
  subtitle,
  icon,
  actions,
  bordered = false,
  padding = 'md',
  hoverable = false,
  onClick,
  className = '',
}) => {
  return (
    <div 
      className={`
        bg-white rounded-xl shadow-sm
        ${bordered ? 'border border-gray-200' : ''}
        ${paddingClasses[padding]}
        ${hoverable ? 'hover:shadow-md transition-shadow cursor-pointer' : ''}
        ${className}
      `}
      onClick={onClick}
    >
      {/* Card Header */}
      {(title || actions) && (
        <div className={`flex items-center justify-between ${padding !== 'none' ? 'mb-4' : 'p-4 border-b border-gray-100'}`}>
          <div className="flex items-center gap-3">
            {icon && (
              <div className="p-2 bg-gray-100 rounded-lg text-gray-600">
                {icon}
              </div>
            )}
            <div>
              {title && (
                <h3 className="font-semibold text-gray-900">{title}</h3>
              )}
              {subtitle && (
                <p className="text-sm text-gray-500">{subtitle}</p>
              )}
            </div>
          </div>
          {actions && (
            <div className="flex items-center gap-2">
              {actions}
            </div>
          )}
        </div>
      )}
      
      {/* Card Content */}
      {children}
    </div>
  );
};

export default Card;

