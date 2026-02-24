// src/components/common/EmptyState.tsx
// קומפוננט אחיד להצגת מצב ריק
import React from 'react';
import { LucideIcon, Inbox, Search, FileText, Building2, Users, Truck, ClipboardList } from 'lucide-react';

interface EmptyStateProps {
  icon?: LucideIcon;
  title: string;
  description?: string;
  actionLabel?: string;
  onAction?: () => void;
  variant?: 'default' | 'search' | 'projects' | 'worklogs' | 'workorders' | 'users' | 'equipment';
  size?: 'sm' | 'md' | 'lg';
}

const EmptyState: React.FC<EmptyStateProps> = ({
  icon: CustomIcon,
  title,
  description,
  actionLabel,
  onAction,
  variant = 'default',
  size = 'md'
}) => {
  // Choose icon based on variant if not provided
  const getDefaultIcon = (): LucideIcon => {
    switch (variant) {
      case 'search':
        return Search;
      case 'projects':
        return Building2;
      case 'worklogs':
        return FileText;
      case 'workorders':
        return ClipboardList;
      case 'users':
        return Users;
      case 'equipment':
        return Truck;
      default:
        return Inbox;
    }
  };

  const Icon = CustomIcon || getDefaultIcon();

  // Size classes
  const sizeClasses = {
    sm: {
      container: 'py-6',
      iconWrapper: 'w-12 h-12',
      icon: 'w-6 h-6',
      title: 'text-base',
      description: 'text-sm',
      button: 'px-4 py-2 text-sm'
    },
    md: {
      container: 'py-10',
      iconWrapper: 'w-16 h-16',
      icon: 'w-8 h-8',
      title: 'text-lg',
      description: 'text-sm',
      button: 'px-5 py-2.5 text-sm'
    },
    lg: {
      container: 'py-16',
      iconWrapper: 'w-20 h-20',
      icon: 'w-10 h-10',
      title: 'text-xl',
      description: 'text-base',
      button: 'px-6 py-3 text-base'
    }
  };

  const classes = sizeClasses[size];

  return (
    <div className={`text-center ${classes.container}`}>
      <div className={`${classes.iconWrapper} bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4`}>
        <Icon className={`${classes.icon} text-gray-400`} />
      </div>
      
      <h3 className={`${classes.title} font-semibold text-gray-900 mb-2`}>
        {title}
      </h3>
      
      {description && (
        <p className={`${classes.description} text-gray-500 max-w-sm mx-auto mb-4`}>
          {description}
        </p>
      )}
      
      {actionLabel && onAction && (
        <button
          onClick={onAction}
          className={`${classes.button} inline-flex items-center gap-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors font-medium`}
        >
          {actionLabel}
        </button>
      )}
    </div>
  );
};

export default EmptyState;

