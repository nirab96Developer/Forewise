// src/components/common/Skeleton.tsx
// קומפוננטות Skeleton לטעינה

import React from 'react';

interface SkeletonProps {
  className?: string;
  width?: string | number;
  height?: string | number;
  rounded?: 'none' | 'sm' | 'md' | 'lg' | 'full';
}

// Skeleton בסיסי
export const Skeleton: React.FC<SkeletonProps> = ({ 
  className = '', 
  width, 
  height,
  rounded = 'md'
}) => {
  const roundedClasses = {
    none: 'rounded-none',
    sm: 'rounded-sm',
    md: 'rounded-md',
    lg: 'rounded-lg',
    full: 'rounded-full'
  };

  return (
    <div 
      className={`animate-pulse bg-gray-200 ${roundedClasses[rounded]} ${className}`}
      style={{ width, height }}
    />
  );
};

// Skeleton לכרטיס
export const CardSkeleton: React.FC<{ className?: string }> = ({ className = '' }) => (
  <div className={`bg-white rounded-xl p-6 shadow-sm border border-gray-100 ${className}`}>
    <div className="flex items-center gap-4 mb-4">
      <Skeleton width={48} height={48} rounded="lg" />
      <div className="flex-1">
        <Skeleton height={20} className="mb-2 w-3/4" />
        <Skeleton height={14} className="w-1/2" />
      </div>
    </div>
    <Skeleton height={12} className="mb-2" />
    <Skeleton height={12} className="w-4/5" />
  </div>
);

// Skeleton לטבלה
export const TableRowSkeleton: React.FC<{ columns?: number }> = ({ columns = 5 }) => (
  <tr className="border-b border-gray-100">
    {Array.from({ length: columns }).map((_, i) => (
      <td key={i} className="px-4 py-3">
        <Skeleton height={16} className={i === 0 ? 'w-20' : 'w-full'} />
      </td>
    ))}
  </tr>
);

export const TableSkeleton: React.FC<{ rows?: number; columns?: number }> = ({ 
  rows = 5, 
  columns = 5 
}) => (
  <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
    {/* Header */}
    <div className="bg-gray-50 px-4 py-3 border-b border-gray-100">
      <div className="flex gap-4">
        {Array.from({ length: columns }).map((_, i) => (
          <Skeleton key={i} height={14} className="flex-1" />
        ))}
      </div>
    </div>
    {/* Rows */}
    <table className="w-full">
      <tbody>
        {Array.from({ length: rows }).map((_, i) => (
          <TableRowSkeleton key={i} columns={columns} />
        ))}
      </tbody>
    </table>
  </div>
);

// Skeleton לסטטיסטיקות (KPI Cards)
export const StatsSkeleton: React.FC<{ count?: number }> = ({ count = 4 }) => (
  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
    {Array.from({ length: count }).map((_, i) => (
      <div key={i} className="bg-white rounded-xl p-4 shadow-sm border border-gray-100">
        <div className="flex items-center gap-3">
          <Skeleton width={40} height={40} rounded="lg" />
          <div className="flex-1">
            <Skeleton height={24} className="mb-1 w-16" />
            <Skeleton height={12} className="w-20" />
          </div>
        </div>
      </div>
    ))}
  </div>
);

// Skeleton לדשבורד מלא
export const DashboardSkeleton: React.FC = () => (
  <div className="p-6 space-y-6">
    {/* Header */}
    <div className="flex justify-between items-center">
      <div>
        <Skeleton height={28} className="w-48 mb-2" />
        <Skeleton height={16} className="w-32" />
      </div>
      <Skeleton width={120} height={40} rounded="lg" />
    </div>
    
    {/* Stats */}
    <StatsSkeleton count={4} />
    
    {/* Main content */}
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <div className="lg:col-span-2">
        <TableSkeleton rows={5} columns={4} />
      </div>
      <div>
        <CardSkeleton />
        <div className="mt-4">
          <CardSkeleton />
        </div>
      </div>
    </div>
  </div>
);

// Skeleton לטופס
export const FormSkeleton: React.FC<{ fields?: number }> = ({ fields = 5 }) => (
  <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100 space-y-4">
    {Array.from({ length: fields }).map((_, i) => (
      <div key={i}>
        <Skeleton height={14} className="w-24 mb-2" />
        <Skeleton height={40} rounded="lg" />
      </div>
    ))}
    <div className="flex gap-3 pt-4">
      <Skeleton width={100} height={42} rounded="lg" />
      <Skeleton width={80} height={42} rounded="lg" />
    </div>
  </div>
);

export default Skeleton;
