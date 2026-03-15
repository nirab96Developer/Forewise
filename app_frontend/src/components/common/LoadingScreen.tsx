import React from 'react';

export type LoadingScreenType = 'home' | 'projects' | 'project' | 'login' | 'default';

export interface LoadingScreenProps {
  username: string;
  type?: LoadingScreenType;
}

type MessageMap = { [K in LoadingScreenType]: string };

const LOADING_MESSAGES: MessageMap = {
  home: 'טוען את הדף הראשי...',
  login: 'ברוך הבא,',
  projects: 'טוען את הפרויקטים שלך...',
  project: 'טוען את פרטי הפרויקט...',
  default: 'טוען...',
};

const SUB_MESSAGES: MessageMap = {
  home: 'מכין את התצוגה הראשית...',
  login: 'מכינים את המערכת עבורך...',
  projects: 'מכין את הנתונים עבורך...',
  project: 'מכין את פרטי הפרויקט...',
  default: 'אנא המתן...',
};

const LoadingScreen: React.FC<LoadingScreenProps> = ({ username, type = 'default' }) => {
  const formatUsername = (userStr: string): string => {
    try {
      if (userStr.includes('{') && userStr.includes('}')) {
        const userData = JSON.parse(userStr);
        return userData.name || userStr;
      }
      return userStr;
    } catch {
      return userStr;
    }
  };

  const getLoadingMessage = (): string => {
    const message = LOADING_MESSAGES[type];
    const formattedName = formatUsername(username);
    return type === 'login' ? `${message} ${formattedName}` : message;
  };

  return (
    <div className="fixed inset-0 bg-gradient-to-r from-green-100 via-green-200 to-blue-200 backdrop-blur-md flex flex-col items-center justify-center z-50 transition-all duration-500">
      {/* Animated ring + Forewise tree */}
      <div className="relative mb-8">
        <div className="w-20 h-20 border-4 border-t-green-500 border-b-blue-500 rounded-full animate-spin" />
        <div className="absolute inset-0 flex items-center justify-center animate-pulse">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 100" width="40" height="34">
            <defs>
              <linearGradient id="ls_t" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" stopColor="#1565c0"/>
                <stop offset="100%" stopColor="#0097a7"/>
              </linearGradient>
              <linearGradient id="ls_m" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" stopColor="#0097a7"/>
                <stop offset="50%" stopColor="#2e7d32"/>
                <stop offset="100%" stopColor="#66bb6a"/>
              </linearGradient>
              <linearGradient id="ls_b" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" stopColor="#2e7d32"/>
                <stop offset="40%" stopColor="#66bb6a"/>
                <stop offset="100%" stopColor="#8B5e3c"/>
              </linearGradient>
            </defs>
            <path d="M46 20 Q60 9 74 20" stroke="url(#ls_t)" strokeWidth="5.5" fill="none" strokeLinecap="round"/>
            <path d="M30 47 Q42 34 60 43 Q78 34 90 47" stroke="url(#ls_m)" strokeWidth="5.5" fill="none" strokeLinecap="round"/>
            <path d="M14 74 Q28 60 46 69 Q60 76 74 69 Q92 60 106 74" stroke="url(#ls_b)" strokeWidth="5.5" fill="none" strokeLinecap="round"/>
            <line x1="60" y1="76" x2="60" y2="90" stroke="#8B5e3c" strokeWidth="3.5" strokeLinecap="round"/>
            <circle cx="60" cy="95" r="5" fill="#8B5e3c"/>
          </svg>
        </div>
      </div>

      <div className="text-center text-gray-700">
        <h2 className="text-2xl font-medium mb-2" role="status">
          {getLoadingMessage()}
        </h2>
        <p className="text-lg opacity-80">{SUB_MESSAGES[type]}</p>
      </div>
    </div>
  );
};

LoadingScreen.defaultProps = { type: 'default' as LoadingScreenType };

export default LoadingScreen;
