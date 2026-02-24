import React from "react";
import { TreeDeciduous } from "lucide-react";

// טיפוסים מיוצאים לשימוש בקומפוננטות אחרות
export type LoadingScreenType = "home" | "projects" | "project" | "login" | "default";

export interface LoadingScreenProps {
  username: string;
  type?: LoadingScreenType;
}

// טיפוסים פנימיים
type MessageMap = {
  [K in LoadingScreenType]: string;
};

// הודעות קבועות
const LOADING_MESSAGES: MessageMap = {
  home: "טוען את הדף הראשי...",
  login: "ברוך הבא,",
  projects: "טוען את הפרויקטים שלך...",
  project: "טוען את פרטי הפרויקט...",
  default: "טוען..."
};

const SUB_MESSAGES: MessageMap = {
  home: "מכין את התצוגה הראשית...",
  login: "מכינים את המערכת עבורך...",
  projects: "מכין את הנתונים עבורך...",
  project: "מכין את פרטי הפרויקט...",
  default: "אנא המתן..."
};

const LoadingScreen: React.FC<LoadingScreenProps> = ({
  username,
  type = "default",
}) => {
  // פונקציה לעיבוד שם המשתמש
  const formatUsername = (userStr: string): string => {
    try {
      // בודק אם זה JSON
      if (userStr.includes('{') && userStr.includes('}')) {
        const userData = JSON.parse(userStr);
        return userData.name || userStr;
      }
      return userStr;
    } catch {
      return userStr;
    }
  };

  // פונקציות חכמות עם טיפוסים מדויקים
  const getLoadingMessage = (): string => {
    const message = LOADING_MESSAGES[type];
    const formattedName = formatUsername(username);
    return type === "login" ? `${message} ${formattedName}` : message;
  };

  const getSubMessage = (): string => {
    return SUB_MESSAGES[type];
  };

  return (
    <div
      className="fixed inset-0 bg-gradient-to-r from-green-100 via-green-200 to-blue-200
                 backdrop-blur-md flex flex-col items-center justify-center z-50 transition-all duration-500"
    >
      {/* אנימציית טעינה */}
      <div className="relative mb-8">
        <div className="w-16 h-16 border-4 border-t-green-500 border-b-blue-500 rounded-full animate-spin"></div>
        <TreeDeciduous
          size={48}
          className="text-green-500 absolute inset-0 m-auto animate-pulse"
        />
      </div>

      {/* הודעות */}
      <div className="text-center text-gray-700">
        <h2 className="text-2xl font-medium mb-2" role="status">
          {getLoadingMessage()}
        </h2>
        <p className="text-lg opacity-80">
          {getSubMessage()}
        </p>
      </div>
    </div>
  );
};

// הגדרות ברירת מחדל
LoadingScreen.defaultProps = {
  type: "default" as LoadingScreenType
};

export default LoadingScreen;
