// src/components/common/Tabs.tsx
import React, { useState } from 'react';

// טיפוסים לכל לשונית
interface TabItem {
  id: string;
  label: React.ReactNode;
  content: React.ReactNode;
  disabled?: boolean;
}

interface TabsProps {
  items: TabItem[];
  defaultTabId?: string;
  onChange?: (tabId: string) => void;
  className?: string;
  variant?: 'underline' | 'contained' | 'pills';
}

const Tabs: React.FC<TabsProps> = ({
  items,
  defaultTabId,
  onChange,
  className = '',
  variant = 'underline'
}) => {
  // בחירת הלשונית הראשונה או המסומנת כברירת מחדל
  const [activeTab, setActiveTab] = useState(defaultTabId || (items.length > 0 ? items[0].id : ''));

  // טיפול בשינוי לשונית
  const handleTabChange = (tabId: string) => {
    setActiveTab(tabId);
    if (onChange) {
      onChange(tabId);
    }
  };

  // סגנונות לפי סוג הלשוניות
  const getTabStyles = (tabId: string, disabled: boolean = false) => {
    const isActive = activeTab === tabId;
    const disabledClasses = disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer';
    
    switch(variant) {
      case 'contained':
        return `py-2 px-4 font-medium text-sm ${disabledClasses} ${
          isActive 
            ? 'bg-white text-blue-600 border-t border-r border-l rounded-t-lg' 
            : 'text-gray-500 hover:text-gray-700'
        }`;
      case 'pills':
        return `py-2 px-4 font-medium text-sm rounded-full transition ${disabledClasses} ${
          isActive 
            ? 'bg-blue-600 text-white' 
            : 'text-gray-700 hover:bg-gray-100'
        }`;
      case 'underline':
      default:
        return `py-3 px-6 font-medium text-sm ${disabledClasses} ${
          isActive 
            ? 'border-b-2 border-blue-600 text-blue-600' 
            : 'text-gray-500 hover:text-gray-700 hover:border-gray-300 border-b-2 border-transparent'
        }`;
    }
  };

  return (
    <div className={className}>
      {/* הלשוניות */}
      <div className={`flex ${variant === 'contained' ? 'border-b' : ''}`}>
        {items.map((tab) => (
          <button
            key={tab.id}
            className={getTabStyles(tab.id, tab.disabled)}
            onClick={() => !tab.disabled && handleTabChange(tab.id)}
            disabled={tab.disabled}
          >
            {tab.label}
          </button>
        ))}
      </div>
      
      {/* תוכן הלשונית הפעילה */}
      <div className="py-4">
        {items.find(tab => tab.id === activeTab)?.content}
      </div>
    </div>
  );
};

export default Tabs;