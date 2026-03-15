// src/components/common/Loader.tsx
import React from 'react';

interface LoaderProps {
  size?: 'sm' | 'md' | 'lg';
  color?: 'blue' | 'gray' | 'green' | 'red';
  className?: string;
}

const Loader: React.FC<LoaderProps> = ({ size = 'md', className = '' }) => {
  const sizeMap = { sm: 16, md: 24, lg: 32 };
  const px = sizeMap[size];
  const svgW = px;
  const svgH = Math.round(px * 0.84);

  return (
    <span
      className={`inline-flex items-center justify-center animate-pulse ${className}`}
      style={{ width: px, height: px }}
    >
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 100" width={svgW} height={svgH}>
        <defs>
          <linearGradient id="lo_t" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#1565c0"/>
            <stop offset="100%" stopColor="#0097a7"/>
          </linearGradient>
          <linearGradient id="lo_m" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#0097a7"/>
            <stop offset="50%" stopColor="#2e7d32"/>
            <stop offset="100%" stopColor="#66bb6a"/>
          </linearGradient>
          <linearGradient id="lo_b" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#2e7d32"/>
            <stop offset="40%" stopColor="#66bb6a"/>
            <stop offset="100%" stopColor="#8B5e3c"/>
          </linearGradient>
        </defs>
        <path d="M46 20 Q60 9 74 20" stroke="url(#lo_t)" strokeWidth="5.5" fill="none" strokeLinecap="round"/>
        <path d="M30 47 Q42 34 60 43 Q78 34 90 47" stroke="url(#lo_m)" strokeWidth="5.5" fill="none" strokeLinecap="round"/>
        <path d="M14 74 Q28 60 46 69 Q60 76 74 69 Q92 60 106 74" stroke="url(#lo_b)" strokeWidth="5.5" fill="none" strokeLinecap="round"/>
        <line x1="60" y1="76" x2="60" y2="90" stroke="#8B5e3c" strokeWidth="3.5" strokeLinecap="round"/>
        <circle cx="60" cy="95" r="5" fill="#8B5e3c"/>
      </svg>
    </span>
  );
};

export default Loader;
