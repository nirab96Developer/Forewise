// src/components/Layout/PageContainer.tsx
// Container אחיד לכל הדפים - מבטיח spacing ומרווחים אחידים
import React from 'react';

interface PageContainerProps {
  children: React.ReactNode;
  /** כותרת הדף */
  title?: string;
  /** תיאור קצר מתחת לכותרת */
  subtitle?: string;
  /** אייקון לצד הכותרת */
  icon?: React.ReactNode;
  /** כפתורי פעולה בצד שמאל של הכותרת */
  actions?: React.ReactNode;
  /** האם להציג רקע אפור */
  grayBackground?: boolean;
  /** רוחב מקסימלי מותאם */
  maxWidth?: 'sm' | 'md' | 'lg' | 'xl' | '2xl' | '7xl' | 'full';
  /** padding נוסף */
  noPadding?: boolean;
}

const maxWidthClasses = {
  sm: 'max-w-sm',
  md: 'max-w-md',
  lg: 'max-w-lg',
  xl: 'max-w-xl',
  '2xl': 'max-w-2xl',
  '7xl': 'max-w-7xl',
  full: 'max-w-full',
};

export const PageContainer: React.FC<PageContainerProps> = ({
  children,
  title,
  subtitle,
  icon,
  actions,
  grayBackground = true,
  maxWidth = '7xl',
  noPadding = false,
}) => {
  return (
    <div className={`min-h-screen ${grayBackground ? 'bg-gray-50' : 'bg-white'}`} dir="rtl">
      <div className={`${maxWidthClasses[maxWidth]} mx-auto ${noPadding ? '' : 'px-6 py-6'}`}>
        {/* Header Section */}
        {(title || actions) && (
          <div className="mb-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                {icon && (
                  <div className="p-3 bg-gradient-to-br from-kkl-green to-green-600 rounded-xl text-white shadow-lg">
                    {icon}
                  </div>
                )}
                <div>
                  {title && (
                    <h1 className="text-2xl font-bold text-gray-900">{title}</h1>
                  )}
                  {subtitle && (
                    <p className="text-gray-500 mt-1">{subtitle}</p>
                  )}
                </div>
              </div>
              {actions && (
                <div className="flex items-center gap-3">
                  {actions}
                </div>
              )}
            </div>
          </div>
        )}
        
        {/* Content */}
        {children}
      </div>
    </div>
  );
};

export default PageContainer;

