// src/components/common/Alert.tsx
import React, { useState } from 'react';
import { AlertCircle, CheckCircle, X, AlertTriangle, Info } from 'lucide-react';

type AlertVariant = 'info' | 'success' | 'warning' | 'error';

interface AlertProps {
  title?: string;
  children: React.ReactNode;
  variant?: AlertVariant;
  isDismissible?: boolean;
  className?: string;
}

const Alert: React.FC<AlertProps> = ({
  title,
  children,
  variant = 'info',
  isDismissible = false,
  className = ''
}) => {
  const [isVisible, setIsVisible] = useState(true);

  if (!isVisible) return null;

  // הגדרת סגנונות לפי הוריאנט
  const variantStyles = {
    info: 'bg-blue-50 text-blue-800 border-blue-200',
    success: 'bg-green-50 text-green-800 border-green-200',
    warning: 'bg-yellow-50 text-yellow-800 border-yellow-200',
    error: 'bg-red-50 text-red-800 border-red-200'
  };

  // בחירת איקון המתאים לוריאנט
  const getIcon = () => {
    switch (variant) {
      case 'info': return <Info className="w-5 h-5" />;
      case 'success': return <CheckCircle className="w-5 h-5" />;
      case 'warning': return <AlertTriangle className="w-5 h-5" />;
      case 'error': return <AlertCircle className="w-5 h-5" />;
      default: return <Info className="w-5 h-5" />;
    }
  };

  return (
    <div className={`flex items-start p-4 border rounded-lg ${variantStyles[variant]} ${className}`}>
      <div className="flex-shrink-0 ml-3">
        {getIcon()}
      </div>
      <div className="flex-1">
        {title && <h4 className="text-base font-medium mb-1">{title}</h4>}
        <div className="text-sm">{children}</div>
      </div>
      {isDismissible && (
        <button 
          onClick={() => setIsVisible(false)}
          className="flex-shrink-0 mr-3 focus:outline-none"
          aria-label="סגור"
        >
          <X className="w-5 h-5" />
        </button>
      )}
    </div>
  );
};

export default Alert;
