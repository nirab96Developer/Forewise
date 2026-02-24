import React from 'react';

// הגדרת טיפוסים ספציפיים לכל קומפוננטה
interface BaseCardProps {
  children: React.ReactNode;
  className?: string;
}

interface CardHeaderProps extends BaseCardProps {}
interface CardTitleProps extends BaseCardProps {}
interface CardContentProps extends BaseCardProps {}

// הקומפוננטה הראשית - Card - סגנון Hillan מקצועי
export const Card: React.FC<BaseCardProps> = ({ 
  children, 
  className = '' 
}) => (
  <div className={`
    bg-white rounded-2xl border border-gray-100 
    shadow-lg hover:shadow-xl 
    transition-all duration-300 ease-out
    hover:scale-[1.01] hover:border-kkl-green/20
    ${className}
  `}>
    {children}
  </div>
);

// קומפוננטת Header
export const CardHeader: React.FC<CardHeaderProps> = ({ 
  children, 
  className = '' 
}) => (
  <div className={`
    p-6 border-b border-gray-100 
    bg-gradient-to-l from-gray-50/50 to-white
    ${className}
  `}>
    {children}
  </div>
);

// קומפוננטת Title
export const CardTitle: React.FC<CardTitleProps> = ({ 
  children, 
  className = '' 
}) => (
  <h3 className={`
    text-xl font-bold text-gray-900
    ${className}
  `}>
    {children}
  </h3>
);

// קומפוננטת Content
export const CardContent: React.FC<CardContentProps> = ({ 
  children, 
  className = '' 
}) => (
  <div className={`p-6 ${className}`}>
    {children}
  </div>
);

export default Card;
