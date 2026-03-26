import React from "react";

interface Props {
  width?: number;
  height?: number;
  className?: string;
  id?: string;
}

let _counter = 0;

const ForewiseTree: React.FC<Props> = ({ width = 32, height = 27, className = "", id }) => {
  const uid = id || `fw${++_counter}`;
  return (
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 100" width={width} height={height} className={className}>
      <defs>
        <linearGradient id={`${uid}_t`} x1="0%" y1="0%" x2="100%" y2="0%">
          <stop offset="0%" stopColor="#1565c0" />
          <stop offset="100%" stopColor="#0097a7" />
        </linearGradient>
        <linearGradient id={`${uid}_m`} x1="0%" y1="0%" x2="100%" y2="0%">
          <stop offset="0%" stopColor="#0097a7" />
          <stop offset="50%" stopColor="#2e7d32" />
          <stop offset="100%" stopColor="#66bb6a" />
        </linearGradient>
        <linearGradient id={`${uid}_b`} x1="0%" y1="0%" x2="100%" y2="0%">
          <stop offset="0%" stopColor="#2e7d32" />
          <stop offset="40%" stopColor="#66bb6a" />
          <stop offset="100%" stopColor="#8B5e3c" />
        </linearGradient>
      </defs>
      <path d="M46 20 Q60 9 74 20" stroke={`url(#${uid}_t)`} strokeWidth="5.5" fill="none" strokeLinecap="round" />
      <path d="M30 47 Q42 34 60 43 Q78 34 90 47" stroke={`url(#${uid}_m)`} strokeWidth="5.5" fill="none" strokeLinecap="round" />
      <path d="M14 74 Q28 60 46 69 Q60 76 74 69 Q92 60 106 74" stroke={`url(#${uid}_b)`} strokeWidth="5.5" fill="none" strokeLinecap="round" />
      <line x1="60" y1="76" x2="60" y2="90" stroke="#8B5e3c" strokeWidth="3.5" strokeLinecap="round" />
      <circle cx="60" cy="95" r="5" fill="#8B5e3c" />
    </svg>
  );
};

export default ForewiseTree;
