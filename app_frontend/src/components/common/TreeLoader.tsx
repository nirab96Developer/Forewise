// src/components/common/TreeLoader.tsx
// לואדר אחיד עם עץ - משמש בכל האפליקציה
import React from 'react';
import { TreeDeciduous } from 'lucide-react';

interface TreeLoaderProps {
  fullScreen?: boolean;
  size?: 'sm' | 'md' | 'lg';
}

/**
 * TreeLoader - לואדר אחיד עם אייקון עץ
 * שימוש: <TreeLoader /> או <TreeLoader fullScreen />
 */
const TreeLoader: React.FC<TreeLoaderProps> = ({ fullScreen = false, size = 'md' }) => {
  const sizes = {
    sm: { ring: 'w-10 h-10', icon: 20, container: 'py-8' },
    md: { ring: 'w-16 h-16', icon: 28, container: 'py-16' },
    lg: { ring: 'w-20 h-20', icon: 36, container: 'py-24' },
  };
  
  const s = sizes[size];
  
  const content = (
    <div className="flex flex-col items-center justify-center">
      <div className="relative">
        {/* Spinning ring */}
        <div 
          className={`${s.ring} rounded-full border-[3px] border-emerald-200 border-t-emerald-500 animate-spin`}
          style={{ animationDuration: '0.8s' }}
        />
        {/* Pulsing glow */}
        <div className={`absolute inset-0 ${s.ring} rounded-full bg-emerald-400/10 animate-pulse`} />
        {/* Tree icon */}
        <div className="absolute inset-0 flex items-center justify-center">
          <TreeDeciduous size={s.icon} className="text-emerald-600" strokeWidth={1.5} />
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

