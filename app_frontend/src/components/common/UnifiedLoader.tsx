// src/components/common/UnifiedLoader.tsx
import React from 'react';

interface UnifiedLoaderProps {
  size?: 'sm' | 'md' | 'lg' | 'full';
  message?: string;
  showLogo?: boolean;
  transparent?: boolean;
}

const sizeConfig = {
  sm:   { container: 'py-8',        svgW: 20, svgH: 17, ringSize: 'w-10 h-10', textSize: 'text-sm' },
  md:   { container: 'py-16',       svgW: 28, svgH: 24, ringSize: 'w-14 h-14', textSize: 'text-base' },
  lg:   { container: 'py-24',       svgW: 36, svgH: 30, ringSize: 'w-20 h-20', textSize: 'text-lg' },
  full: { container: 'min-h-screen', svgW: 44, svgH: 37, ringSize: 'w-24 h-24', textSize: 'text-xl' },
};

const TreeSVG: React.FC<{ id: string; width: number; height: number }> = ({ id, width, height }) => (
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

const UnifiedLoader: React.FC<UnifiedLoaderProps> = ({
  size = 'md',
  message,
  showLogo = true,
  transparent = false,
}) => {
  const config = sizeConfig[size];

  return (
    <div
      className={`
        flex items-center justify-center ${config.container}
        ${transparent ? 'bg-transparent' : 'bg-white/60 backdrop-blur-sm'}
        transition-all duration-300
      `}
    >
      <div className="flex flex-col items-center gap-4">
        <div className="relative">
          <div
            className={`${config.ringSize} rounded-full border-[3px] border-emerald-200 border-t-emerald-500 animate-spin`}
            style={{ animationDuration: '1s' }}
          />
          <div
            className={`absolute inset-0 ${config.ringSize} rounded-full bg-gradient-to-br from-emerald-400/20 to-green-500/20 animate-pulse`}
          />
          {showLogo && (
            <div className="absolute inset-0 flex items-center justify-center">
              <TreeSVG id="ul" width={config.svgW} height={config.svgH} />
            </div>
          )}
        </div>
        {message && (
          <p className={`${config.textSize} text-gray-600 font-medium animate-pulse`}>{message}</p>
        )}
      </div>
    </div>
  );
};

export const PageSuspenseLoader: React.FC = () => (
  <div className="flex items-center justify-center min-h-[60vh]">
    <div className="relative">
      <div className="w-16 h-16 rounded-full border-[3px] border-emerald-200 border-t-emerald-500 animate-spin" />
      <div className="absolute inset-0 flex items-center justify-center">
        <TreeSVG id="psl" width={28} height={24} />
      </div>
    </div>
  </div>
);

export const FullScreenLoader: React.FC<{ message?: string }> = ({ message }) => (
  <div className="fixed inset-0 bg-white/80 backdrop-blur-sm flex items-center justify-center z-50">
    <div className="flex flex-col items-center gap-4">
      <div className="relative">
        <div className="w-16 h-16 rounded-full border-[3px] border-emerald-200 border-t-emerald-500 animate-spin" />
        <div className="absolute inset-0 flex items-center justify-center">
          <TreeSVG id="fsl" width={28} height={24} />
        </div>
      </div>
      {message && <p className="text-base text-gray-600 font-medium">{message}</p>}
    </div>
  </div>
);

export const InlineLoader: React.FC<{ size?: number }> = ({ size = 20 }) => (
  <div className="inline-flex items-center justify-center">
    <div
      className="rounded-full border-2 border-emerald-200 border-t-emerald-500 animate-spin"
      style={{ width: size, height: size }}
    />
  </div>
);

export const ContentSkeleton: React.FC = () => (
  <div className="space-y-4 p-4 animate-pulse">
    <div className="h-8 bg-gray-200 rounded-lg w-1/3" />
    <div className="space-y-3">
      <div className="h-4 bg-gray-200 rounded w-full" />
      <div className="h-4 bg-gray-200 rounded w-5/6" />
      <div className="h-4 bg-gray-200 rounded w-4/6" />
    </div>
    <div className="grid grid-cols-3 gap-4">
      <div className="h-24 bg-gray-200 rounded-lg" />
      <div className="h-24 bg-gray-200 rounded-lg" />
      <div className="h-24 bg-gray-200 rounded-lg" />
    </div>
  </div>
);

export default UnifiedLoader;
