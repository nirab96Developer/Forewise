// src/components/common/TreeLoader.tsx
import React from 'react';

interface TreeLoaderProps {
  fullScreen?: boolean;
  size?: 'sm' | 'md' | 'lg';
}

const ForewiseTree: React.FC<{ id: string; width: number; height: number }> = ({ id, width, height }) => (
  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 100" width={width} height={height}>
    <defs>
      <linearGradient id={`${id}_t`} x1="0%" y1="0%" x2="100%" y2="0%">
        <stop offset="0%" stopColor="#1565c0"/>
        <stop offset="100%" stopColor="#0097a7"/>
      </linearGradient>
      <linearGradient id={`${id}_m`} x1="0%" y1="0%" x2="100%" y2="0%">
        <stop offset="0%" stopColor="#0097a7"/>
        <stop offset="50%" stopColor="#2e7d32"/>
        <stop offset="100%" stopColor="#66bb6a"/>
      </linearGradient>
      <linearGradient id={`${id}_b`} x1="0%" y1="0%" x2="100%" y2="0%">
        <stop offset="0%" stopColor="#2e7d32"/>
        <stop offset="40%" stopColor="#66bb6a"/>
        <stop offset="100%" stopColor="#8B5e3c"/>
      </linearGradient>
    </defs>
    <path d="M46 20 Q60 9 74 20" stroke={`url(#${id}_t)`} strokeWidth="5.5" fill="none" strokeLinecap="round"/>
    <path d="M30 47 Q42 34 60 43 Q78 34 90 47" stroke={`url(#${id}_m)`} strokeWidth="5.5" fill="none" strokeLinecap="round"/>
    <path d="M14 74 Q28 60 46 69 Q60 76 74 69 Q92 60 106 74" stroke={`url(#${id}_b)`} strokeWidth="5.5" fill="none" strokeLinecap="round"/>
    <line x1="60" y1="76" x2="60" y2="90" stroke="#8B5e3c" strokeWidth="3.5" strokeLinecap="round"/>
    <circle cx="60" cy="95" r="5" fill="#8B5e3c"/>
  </svg>
);

const TreeLoader: React.FC<TreeLoaderProps> = ({ fullScreen = false, size = 'md' }) => {
  const sizes = {
    sm: { ring: 'w-10 h-10', svgW: 20, svgH: 17, container: 'py-8' },
    md: { ring: 'w-16 h-16', svgW: 28, svgH: 24, container: 'py-16' },
    lg: { ring: 'w-20 h-20', svgW: 36, svgH: 30, container: 'py-24' },
  };

  const s = sizes[size];

  const content = (
    <div className="flex flex-col items-center justify-center">
      <div className="relative">
        <div
          className={`${s.ring} rounded-full border-[3px] border-emerald-200 border-t-emerald-500 animate-spin`}
          style={{ animationDuration: '0.8s' }}
        />
        <div className={`absolute inset-0 ${s.ring} rounded-full bg-emerald-400/10 animate-pulse`} />
        <div className="absolute inset-0 flex items-center justify-center">
          <ForewiseTree id="tl" width={s.svgW} height={s.svgH} />
        </div>
      </div>
    </div>
  );

  if (fullScreen) {
    return (
      <div className="fixed inset-0 bg-white/90 backdrop-blur-sm flex items-center justify-center z-50">
        {content}
      </div>
    );
  }

  return (
    <div className={`flex items-center justify-center ${s.container} min-h-[200px]`}>
      {content}
    </div>
  );
};

export default TreeLoader;
