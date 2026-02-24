// src/components/common/Select.tsx
import React, { useState, useRef, useEffect } from "react";
import { ChevronDown, X, Check, Search } from "lucide-react";

// טיפוסים מיוצאים לשימוש בקומפוננטות אחרות
export type SelectSize = "sm" | "md" | "lg";
export type SelectVariant = "outline" | "filled" | "underline";

export interface SelectOption {
  value: string | number;
  label: string;
  disabled?: boolean;
  icon?: React.ReactNode;
  description?: string;
}

export interface SelectProps {
  options: SelectOption[];
  value?: string | number | null;
  onChange?: (value: string | number | null) => void;
  placeholder?: string;
  label?: string;
  size?: SelectSize;
  variant?: SelectVariant;
  error?: string;
  helperText?: string;
  clearable?: boolean;
  searchable?: boolean;
  disabled?: boolean;
  required?: boolean;
  className?: string;
  emptyMessage?: string;
  groupBy?: (option: SelectOption) => string;
  name?: string;
  id?: string;
  autoFocus?: boolean;
}

const Select: React.FC<SelectProps> = ({
  options,
  value = null,
  onChange,
  placeholder = "בחר אפשרות...",
  label,
  size = "md",
  variant = "outline",
  error,
  helperText,
  clearable = false,
  searchable = false,
  disabled = false,
  required = false,
  className = "",
  emptyMessage = "אין אפשרויות",
  groupBy,
  name: _name,
  id,
  autoFocus = false,
}) => {
  // מצבים פנימיים
  const [isOpen, setIsOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [highlightedIndex, setHighlightedIndex] = useState<number>(-1);
  
  // שימוש ב-refs לניהול ממשק משתמש
  const selectRef = useRef<HTMLDivElement>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const searchInputRef = useRef<HTMLInputElement>(null);

  // פונקציות עזר לנוחות השימוש
  const selectedOption = options.find((option) => option.value === value);
  
  // פילטור אפשרויות על-פי חיפוש
  const filteredOptions = options.filter((option) =>
    option.label.toLowerCase().includes(searchQuery.toLowerCase())
  );

  // קבוצות אופציות אם הוגדר groupBy
  const groupedOptions = groupBy
    ? filteredOptions.reduce<Record<string, SelectOption[]>>((groups, option) => {
        const groupKey = groupBy(option);
        if (!groups[groupKey]) {
          groups[groupKey] = [];
        }
        groups[groupKey].push(option);
        return groups;
      }, {})
    : null;

  // מטפל בסגירת התפריט כשלוחצים מחוץ לרכיב
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        selectRef.current &&
        !selectRef.current.contains(event.target as Node)
      ) {
        setIsOpen(false);
      }
    };

    if (isOpen) {
      document.addEventListener("mousedown", handleClickOutside);
    }

    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [isOpen]);

  // מתמקד בשדה החיפוש כשהתפריט נפתח
  useEffect(() => {
    if (isOpen && searchable && searchInputRef.current) {
      searchInputRef.current.focus();
    }
  }, [isOpen, searchable]);

  // מטפל בניווט מקלדת
  useEffect(() => {
    if (!isOpen) return;

    const handleKeyDown = (event: KeyboardEvent) => {
      switch (event.key) {
        case "ArrowDown":
          event.preventDefault();
          setHighlightedIndex((prevIndex) => 
            Math.min(prevIndex + 1, filteredOptions.length - 1)
          );
          break;
        case "ArrowUp":
          event.preventDefault();
          setHighlightedIndex((prevIndex) => 
            Math.max(prevIndex - 1, 0)
          );
          break;
        case "Enter":
          event.preventDefault();
          if (highlightedIndex >= 0) {
            handleSelect(filteredOptions[highlightedIndex].value);
          }
          break;
        case "Escape":
          event.preventDefault();
          setIsOpen(false);
          break;
      }
    };

    document.addEventListener("keydown", handleKeyDown);
    return () => {
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, [isOpen, highlightedIndex, filteredOptions]);

  // מעדכן את מיקום התפריט לפי גובה המסך
  useEffect(() => {
    if (isOpen && dropdownRef.current && selectRef.current) {
      const selectRect = selectRef.current.getBoundingClientRect();
      const dropdownHeight = dropdownRef.current.offsetHeight;
      const viewportHeight = window.innerHeight;
      
      // בדיקה אם יש מספיק מקום למטה או שעדיף לפתוח למעלה
      const shouldOpenUpward = selectRect.bottom + dropdownHeight > viewportHeight &&
                               selectRect.top > dropdownHeight;
      
      // עדכון סגנון
      if (shouldOpenUpward) {
        dropdownRef.current.style.bottom = "100%";
        dropdownRef.current.style.top = "auto";
      } else {
        dropdownRef.current.style.top = "100%";
        dropdownRef.current.style.bottom = "auto";
      }
    }
  }, [isOpen]);

  // טיפול בבחירת אפשרות
  const handleSelect = (optionValue: string | number) => {
    if (onChange) {
      onChange(optionValue);
    }
    setIsOpen(false);
    setSearchQuery("");
  };

  // טיפול בניקוי הבחירה
  const handleClear = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (onChange) {
      onChange(null);
    }
    setSearchQuery("");
  };

  // סגנונות גדלים שונים
  const sizeStyles = {
    sm: "py-1 px-2 text-sm",
    md: "py-2 px-3 text-base",
    lg: "py-3 px-4 text-lg",
  };

  // סגנונות וריאנטים שונים
  const variantStyles = {
    outline: "border border-gray-300 rounded-lg bg-white focus-within:border-blue-500 focus-within:ring-2 focus-within:ring-blue-500/20",
    filled: "border border-gray-200 bg-gray-50 rounded-lg focus-within:bg-white focus-within:border-blue-500",
    underline: "border-b-2 border-gray-200 focus-within:border-blue-500 rounded-none",
  };

  // סגנון שגיאה
  const errorStyle = error ? "border-red-500 focus-within:border-red-500 focus-within:ring-2 focus-within:ring-red-500/20" : "";

  return (
    <div className={`${className}`}>
      {/* תווית */}
      {label && (
        <label 
          htmlFor={id} 
          className="block text-sm font-medium text-gray-700 mb-1"
        >
          {label}
          {required && <span className="text-red-500 mr-1">*</span>}
        </label>
      )}

      {/* תיבת בחירה */}
      <div
        ref={selectRef}
        className={`
          relative ${variantStyles[variant]} ${sizeStyles[size]} ${errorStyle}
          ${disabled ? "opacity-60 cursor-not-allowed bg-gray-100" : "cursor-pointer"}
          transition-all duration-200
        `}
        onClick={() => !disabled && setIsOpen(!isOpen)}
        tabIndex={disabled ? -1 : 0}
        onFocus={() => autoFocus && !disabled && setIsOpen(true)}
        aria-expanded={isOpen}
        aria-disabled={disabled}
        role="combobox"
      >
        <div className="flex items-center justify-between">
          {/* תצוגת אפשרות נבחרת */}
          <div className="flex-grow truncate">
            {selectedOption ? (
              <div className="flex items-center">
                {selectedOption.icon && (
                  <span className="ml-2">{selectedOption.icon}</span>
                )}
                <span className="truncate">{selectedOption.label}</span>
              </div>
            ) : (
              <span className="text-gray-400">{placeholder}</span>
            )}
          </div>

          {/* כפתורי ניקוי ופתיחת תפריט */}
          <div className="flex items-center gap-1">
            {clearable && value && !disabled && (
              <button
                type="button"
                className="p-1 text-gray-400 hover:text-gray-600 focus:outline-none"
                onClick={handleClear}
                aria-label="נקה בחירה"
              >
                <X size={16} />
              </button>
            )}
            <ChevronDown 
              size={18} 
              className={`text-gray-400 transition-transform duration-200 ${isOpen ? 'rotate-180' : ''}`}
            />
          </div>
        </div>

        {/* תפריט נפתח */}
        {isOpen && (
          <div
            ref={dropdownRef}
            className="absolute right-0 left-0 z-10 mt-1 bg-white border border-gray-200 rounded-lg shadow-lg max-h-60 overflow-auto"
          >
            {/* שדה חיפוש */}
            {searchable && (
              <div className="sticky top-0 p-2 bg-white border-b">
                <div className="relative">
                  <input
                    ref={searchInputRef}
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="w-full p-2 pr-8 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
                    placeholder="חיפוש..."
                    onClick={(e) => e.stopPropagation()}
                  />
                  <Search 
                    size={16} 
                    className="absolute left-2 top-1/2 transform -translate-y-1/2 text-gray-400" 
                  />
                </div>
              </div>
            )}

            {/* רשימת אפשרויות */}
            {filteredOptions.length === 0 ? (
              <div className="p-3 text-center text-gray-500">{emptyMessage}</div>
            ) : groupedOptions ? (
              // אפשרויות מקובצות
              Object.entries(groupedOptions).map(([groupName, groupOptions]) => (
                <div key={groupName}>
                  <div className="sticky top-0 p-2 bg-gray-100 font-medium text-sm text-gray-600">
                    {groupName}
                  </div>
                  {groupOptions.map((option, _index) => (
                    <div
                      key={option.value}
                      className={`
                        p-2 flex items-center hover:bg-gray-50 
                        ${option.disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
                        ${value === option.value ? 'bg-blue-50 text-blue-700' : ''}
                        ${highlightedIndex === filteredOptions.indexOf(option) ? 'bg-gray-100' : ''}
                      `}
                      onClick={() => !option.disabled && handleSelect(option.value)}
                    >
                      <div className="flex-grow">
                        <div className="flex items-center">
                          {option.icon && <span className="ml-2">{option.icon}</span>}
                          {option.label}
                        </div>
                        {option.description && (
                          <p className="text-xs text-gray-500 mt-0.5">
                            {option.description}
                          </p>
                        )}
                      </div>
                      {value === option.value && (
                        <Check size={18} className="text-blue-600" />
                      )}
                    </div>
                  ))}
                </div>
              ))
            ) : (
              // אפשרויות רגילות
              filteredOptions.map((option, _index) => (
                <div
                  key={option.value}
                  className={`
                    p-2 flex items-center hover:bg-gray-50 
                    ${option.disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
                    ${value === option.value ? 'bg-blue-50 text-blue-700' : ''}
                    ${highlightedIndex === _index ? 'bg-gray-100' : ''}
                  `}
                  onClick={() => !option.disabled && handleSelect(option.value)}
                >
                  <div className="flex-grow">
                    <div className="flex items-center">
                      {option.icon && <span className="ml-2">{option.icon}</span>}
                      {option.label}
                    </div>
                    {option.description && (
                      <p className="text-xs text-gray-500 mt-0.5">
                        {option.description}
                      </p>
                    )}
                  </div>
                  {value === option.value && (
                    <Check size={18} className="text-blue-600" />
                  )}
                </div>
              ))
            )}
          </div>
        )}
      </div>

      {/* הודעות עזרה ושגיאה */}
      {(error || helperText) && (
        <div className="mt-1 text-sm">
          {error ? (
            <p className="text-red-600">{error}</p>
          ) : helperText ? (
            <p className="text-gray-500">{helperText}</p>
          ) : null}
        </div>
      )}
    </div>
  );
};

export default Select;