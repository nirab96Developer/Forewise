// src/components/DebugButton.tsx
// Floating debug button component

import React from 'react';
import { Bug } from 'lucide-react';
import { debugLogger } from '../utils/debug';

interface DebugButtonProps {
  onClick: () => void;
  errorCount: number;
}

const DebugButton: React.FC<DebugButtonProps> = ({ onClick, errorCount }) => {
  return (
    <button
      onClick={onClick}
      className="fixed bottom-4 left-4 z-40 p-3 bg-gray-800 hover:bg-gray-700 text-white rounded-full shadow-lg transition-all group"
      title="Debug Panel (Ctrl+Shift+D or F12)"
    >
      <Bug className="w-5 h-5" />
      {errorCount > 0 && (
        <span className="absolute -top-1 -right-1 w-5 h-5 bg-red-500 rounded-full flex items-center justify-center text-xs font-bold animate-pulse">
          {errorCount > 9 ? '9+' : errorCount}
        </span>
      )}
      <span className="absolute left-full ml-2 px-2 py-1 bg-gray-800 text-white text-xs rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap">
        Debug Panel ({debugLogger.getLogs().length} logs)
      </span>
    </button>
  );
};

export default DebugButton;




