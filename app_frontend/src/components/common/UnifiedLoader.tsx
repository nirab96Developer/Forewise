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

import { ForewiseTree as TreeSVG } from '../brand';

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
              <TreeSVG width={config.svgW} height={config.svgH} />
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
        <TreeSVG width={28} height={24} />
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
          <TreeSVG width={28} height={24} />
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
