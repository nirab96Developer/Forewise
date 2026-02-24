// src/components/common/Button.tsx
import React, { ButtonHTMLAttributes } from 'react';

type ButtonVariant = 'primary' | 'secondary' | 'outline' | 'danger' | 'success' | 'link';
type ButtonSize = 'sm' | 'md' | 'lg';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  isLoading?: boolean;
  icon?: React.ReactNode;
  iconPosition?: 'left' | 'right';
  fullWidth?: boolean;
}

const Button: React.FC<ButtonProps> = ({
  children,
  variant = 'primary',
  size = 'md',
  isLoading = false,
  icon,
  iconPosition = 'right',
  fullWidth = false,
  className = '',
  disabled,
  ...props
}) => {
  // בחירת המחלקות המתאימות לפי הוריאנט - סגנון KKL/Hillan מקצועי
  const getVariantClasses = (): string => {
    switch (variant) {
      case 'primary':
        return 'bg-gradient-to-l from-kkl-green to-kkl-green-hover hover:shadow-lg hover:scale-[1.02] text-white focus:ring-kkl-green shadow-md';
      case 'secondary':
        return 'bg-gradient-to-l from-gray-50 to-gray-100 hover:from-gray-100 hover:to-gray-200 text-gray-800 focus:ring-gray-400 border border-gray-200 shadow-sm';
      case 'outline':
        return 'bg-white border-2 border-kkl-green hover:bg-kkl-green hover:text-white text-kkl-green focus:ring-kkl-green transition-all duration-200';
      case 'danger':
        return 'bg-gradient-to-l from-red-600 to-red-700 hover:shadow-lg hover:scale-[1.02] text-white focus:ring-red-500 shadow-md';
      case 'success':
        return 'bg-gradient-to-l from-success-green to-kkl-green hover:shadow-lg hover:scale-[1.02] text-white focus:ring-success-green shadow-md';
      case 'link':
        return 'bg-transparent hover:underline text-kkl-green hover:text-kkl-green-hover p-0 focus:ring-0';
      default:
        return 'bg-gradient-to-l from-kkl-green to-kkl-green-hover hover:shadow-lg hover:scale-[1.02] text-white focus:ring-kkl-green shadow-md';
    }
  };

  // בחירת המחלקות המתאימות לפי הגודל
  const getSizeClasses = (): string => {
    if (variant === 'link') return 'text-sm';
    
    switch (size) {
      case 'sm':
        return 'py-1 px-3 text-sm';
      case 'md':
        return 'py-2 px-4 text-sm';
      case 'lg':
        return 'py-3 px-6 text-base';
      default:
        return 'py-2 px-4 text-sm';
    }
  };

  const baseClasses = variant !== 'link' 
    ? 'rounded-xl font-semibold transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-opacity-50 active:scale-[0.97] touch-manipulation' 
    : 'font-semibold transition-all duration-200 focus:outline-none touch-manipulation';
  
  const widthClass = fullWidth ? 'w-full' : '';
  const disabledClass = disabled || isLoading ? 'opacity-60 cursor-not-allowed' : '';

  return (
    <button 
      className={`
        ${baseClasses}
        ${getVariantClasses()}
        ${getSizeClasses()}
        ${widthClass}
        ${disabledClass}
        ${className}
      `}
      disabled={disabled || isLoading}
      {...props}
    >
      {isLoading ? (
        <div className="flex items-center justify-center">
          <svg className="animate-spin h-4 w-4 text-current mr-2" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
          <span>טוען...</span>
        </div>
      ) : (
        <div className="flex items-center justify-center">
          {icon && iconPosition === 'right' && <span className="mr-2">{children}</span>}
          {icon && iconPosition === 'left' && icon}
          {!icon && children}
          {icon && iconPosition === 'right' && icon}
          {icon && iconPosition === 'left' && <span className="ml-2">{children}</span>}
        </div>
      )}
    </button>
  );
};

export default Button;
