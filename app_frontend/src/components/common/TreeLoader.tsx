// src/components/common/TreeLoader.tsx
import React from 'react';

interface TreeLoaderProps {
  fullScreen?: boolean;
  size?: 'sm' | 'md' | 'lg';
}

import { ForewiseTree } from '../brand';

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
          <ForewiseTree width={s.svgW} height={s.svgH} />
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
