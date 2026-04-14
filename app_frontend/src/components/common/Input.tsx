// src/components/common/Input.tsx
import React, { InputHTMLAttributes, forwardRef } from 'react';
import { Eye, EyeOff } from 'lucide-react';

type InputVariant = 'default' | 'error' | 'success';
type InputSize = 'sm' | 'md' | 'lg';

interface InputProps extends Omit<InputHTMLAttributes<HTMLInputElement>, 'size'> {
  variant?: InputVariant;
  size?: InputSize;
  label?: string;
  error?: string;
  helperText?: string;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
  isPassword?: boolean;
  fullWidth?: boolean;
}

const Input = forwardRef<HTMLInputElement, InputProps>(({
  variant = 'default',
  size = 'md',
  label,
  error,
  helperText,
  leftIcon,
  rightIcon,
  isPassword = false,
  fullWidth = false,
  className = '',
  type,
  ...props
}, ref) => {
  const [showPassword, setShowPassword] = React.useState(false);
  const [isFocused, setIsFocused] = React.useState(false);

  const inputType = isPassword ? (showPassword ? 'text' : 'password') : type;

  const getVariantClasses = (): string => {
    switch (variant) {
      case 'error':
        return 'border-red-300 focus:border-red-500 focus:ring-red-500 bg-red-50/50';
      case 'success':
        return 'border-fw-green focus:border-fw-green focus:ring-fw-green bg-green-50/50';
      default:
        return 'border-gray-200 focus:border-fw-green focus:ring-fw-green hover:border-gray-300';
    }
  };

  const getSizeClasses = (): string => {
    switch (size) {
      case 'sm':
        return 'py-1 px-3 text-sm';
      case 'md':
        return 'py-2 px-3 text-sm';
      case 'lg':
        return 'py-3 px-4 text-base';
      default:
        return 'py-2 px-3 text-sm';
    }
  };

  const widthClass = fullWidth ? 'w-full' : '';
  const focusClass = isFocused ? 'ring-2 ring-opacity-50' : '';

  return (
    <div className={`${widthClass}`}>
      {label && (
        <label className="block text-sm font-semibold text-gray-700 mb-2">
          {label}
        </label>
      )}
      <div className="relative">
        {leftIcon && (
          <div className="absolute inset-y-0 right-0 pr-3 flex items-center pointer-events-none">
            <div className="text-gray-400">{leftIcon}</div>
          </div>
        )}
        <input
          ref={ref}
          type={inputType}
          className={`
            block w-full rounded-xl border-2 transition-all duration-200 
            placeholder:text-gray-400 text-gray-900
            touch-manipulation shadow-sm hover:shadow-md
            ${getVariantClasses()}
            ${getSizeClasses()}
            ${focusClass}
            ${leftIcon ? 'pr-10' : ''}
            ${rightIcon || isPassword ? 'pl-10' : ''}
            ${className}
          `}
          onFocus={() => setIsFocused(true)}
          onBlur={() => setIsFocused(false)}
          {...props}
        />
        {(rightIcon || isPassword) && (
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center">
            {isPassword ? (
              <button
                type="button"
                className="text-gray-400 hover:text-gray-600 focus:outline-none"
                onClick={() => setShowPassword(!showPassword)}
              >
                {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
              </button>
            ) : (
              <div className="text-gray-400">{rightIcon}</div>
            )}
          </div>
        )}
      </div>
      {error && (
        <p className="mt-1 text-sm text-red-600">{error}</p>
      )}
      {helperText && !error && (
        <p className="mt-1 text-sm text-gray-500">{helperText}</p>
      )}
    </div>
  );
});

Input.displayName = 'Input';

export default Input;
