// src/components/common/DatePicker.tsx
import React, { useState, useRef, useEffect } from "react";
import { Calendar as CalendarIcon, ChevronLeft, ChevronRight, X } from "lucide-react";

// טיפוסים מיוצאים לשימוש בקומפוננטות אחרות
export type DatePickerSize = "sm" | "md" | "lg";
export type DatePickerVariant = "outline" | "filled" | "underline";

export interface DatePickerProps {
  value?: Date | null;
  onChange?: (date: Date | null) => void;
  label?: string;
  placeholder?: string;
  size?: DatePickerSize;
  variant?: DatePickerVariant;
  error?: string;
  helperText?: string;
  clearable?: boolean;
  disabled?: boolean;
  required?: boolean;
  minDate?: Date;
  maxDate?: Date;
  format?: string;
  className?: string;
  name?: string;
  id?: string;
  autoFocus?: boolean;
  disabledDates?: Date[];
  firstDayOfWeek?: 0 | 1; // 0 = ראשון, 1 = שני
}

// שמות חודשים בעברית
const MONTHS_IN_HEBREW = [
  "ינואר", "פברואר", "מרץ", "אפריל", "מאי", "יוני",
  "יולי", "אוגוסט", "ספטמבר", "אוקטובר", "נובמבר", "דצמבר"
];

// שמות ימים בעברית
// const DAYS_IN_HEBREW = ["ראשון", "שני", "שלישי", "רביעי", "חמישי", "שישי", "שבת"];

// שמות ימים מקוצרים בעברית
const SHORT_DAYS_IN_HEBREW = ["א", "ב", "ג", "ד", "ה", "ו", "ש"];

const DatePicker: React.FC<DatePickerProps> = ({
  value = null,
  onChange,
  label,
  placeholder = "בחר תאריך...",
  size = "md",
  variant = "outline",
  error,
  helperText,
  clearable = true,
  disabled = false,
  required = false,
  minDate,
  maxDate,
  format = "dd/MM/yyyy",
  className = "",
  name: _name,
  id,
  autoFocus = false,
  disabledDates = [],
  firstDayOfWeek = 0,
}) => {
  // מצבים פנימיים
  const [isOpen, setIsOpen] = useState(false);
  const [currentMonth, setCurrentMonth] = useState(value || new Date());
  const [hoveredDate, setHoveredDate] = useState<Date | null>(null);
  
  // שימוש ב-refs לניהול ממשק משתמש
  const containerRef = useRef<HTMLDivElement>(null);
  const calendarRef = useRef<HTMLDivElement>(null);

  // יצירת מטריצת הימים לחודש הנוכחי
  const getDaysInMonth = (year: number, month: number) => {
    // השגת התאריך האחרון בחודש
    const lastDay = new Date(year, month + 1, 0);
    return lastDay.getDate();
  };

  // בניית מטריצת ימים לתצוגת לוח השנה
  const buildCalendarDays = () => {
    const year = currentMonth.getFullYear();
    const month = currentMonth.getMonth();
    
    // מציאת היום הראשון בחודש
    const firstDayOfMonth = new Date(year, month, 1);
    let dayOfWeek = firstDayOfMonth.getDay();
    
    // התאמה ליום הראשון בשבוע
    if (firstDayOfWeek === 1) { // אם השבוע מתחיל ביום שני
      dayOfWeek = dayOfWeek === 0 ? 6 : dayOfWeek - 1;
    }
    
    const daysInMonth = getDaysInMonth(year, month);
    
    // בניית המטריצה
    const days: Array<Date | null> = [];
    
    // ימים מהחודש הקודם
    for (let i = 0; i < dayOfWeek; i++) {
      const prevMonthDate = new Date(year, month, -dayOfWeek + i + 1);
      days.push(prevMonthDate);
    }
    
    // ימים בחודש הנוכחי
    for (let i = 1; i <= daysInMonth; i++) {
      days.push(new Date(year, month, i));
    }
    
    // חישוב כמה ימים להוסיף מהחודש הבא כדי להשלים את הטבלה
    const remainingDays = (6 - ((dayOfWeek + daysInMonth - 1) % 7)) % 7;
    
    // ימים מהחודש הבא
    for (let i = 1; i <= remainingDays; i++) {
      const nextMonthDate = new Date(year, month + 1, i);
      days.push(nextMonthDate);
    }
    
    // חלוקה לשבועות
    const weeks: Array<Array<Date | null>> = [];
    for (let i = 0; i < days.length; i += 7) {
      weeks.push(days.slice(i, i + 7));
    }
    
    return weeks;
  };

  // טיפול בסגירת הלוח כשלוחצים מחוץ לרכיב
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        containerRef.current &&
        !containerRef.current.contains(event.target as Node)
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

  // בדיקה אם תאריך מסוים מושבת
  const isDateDisabled = (date: Date): boolean => {
    // בדיקה אם התאריך הוא מחוץ לטווח המותר
    if (minDate && date < new Date(minDate.setHours(0, 0, 0, 0))) {
      return true;
    }
    if (maxDate && date > new Date(maxDate.setHours(23, 59, 59, 999))) {
      return true;
    }
    
    // בדיקה אם התאריך נמצא ברשימת התאריכים המושבתים
    return disabledDates.some(disabledDate => 
      date.getDate() === disabledDate.getDate() &&
      date.getMonth() === disabledDate.getMonth() &&
      date.getFullYear() === disabledDate.getFullYear()
    );
  };

  // פורמט תאריך מותאם
  const formatDate = (date: Date | null): string => {
    if (!date) return "";
    
    const day = date.getDate().toString().padStart(2, "0");
    const month = (date.getMonth() + 1).toString().padStart(2, "0");
    const year = date.getFullYear();
    
    if (format === "dd/MM/yyyy") {
      return `${day}/${month}/${year}`;
    } else if (format === "MM/dd/yyyy") {
      return `${month}/${day}/${year}`;
    } else if (format === "yyyy-MM-dd") {
      return `${year}-${month}-${day}`;
    } else if (format === "hebrew") {
      return `${day} ב${MONTHS_IN_HEBREW[date.getMonth()]} ${year}`;
    }
    
    return `${day}/${month}/${year}`;
  };

  // טיפול בבחירת תאריך
  const handleDateSelect = (date: Date) => {
    if (isDateDisabled(date)) return;
    
    if (onChange) {
      onChange(date);
    }
    setIsOpen(false);
  };

  // טיפול בניקוי התאריך
  const handleClear = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (onChange) {
      onChange(null);
    }
  };

  // חודש קודם
  const goToPreviousMonth = () => {
    setCurrentMonth(new Date(currentMonth.getFullYear(), currentMonth.getMonth() - 1));
  };

  // חודש הבא
  const goToNextMonth = () => {
    setCurrentMonth(new Date(currentMonth.getFullYear(), currentMonth.getMonth() + 1));
  };

  // יצירת מערך ימי השבוע לפי סדר מותאם
  const getWeekDays = () => {
    let days = [...SHORT_DAYS_IN_HEBREW];
    if (firstDayOfWeek === 1) {
      // העברת יום ראשון לסוף אם השבוע מתחיל ביום שני
      days = [...days.slice(1), days[0]];
    }
    return days;
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
    <div className={`${className}`} ref={containerRef}>
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

      {/* שדה תאריך */}
      <div
        className={`
          relative ${variantStyles[variant]} ${sizeStyles[size]} ${errorStyle}
          ${disabled ? "opacity-60 cursor-not-allowed bg-gray-100" : "cursor-pointer"}
          transition-all duration-200
        `}
        onClick={() => !disabled && setIsOpen(!isOpen)}
        tabIndex={disabled ? -1 : 0}
        onFocus={() => autoFocus && !disabled && setIsOpen(true)}
        aria-haspopup="true"
        aria-expanded={isOpen}
        aria-disabled={disabled}
      >
        <div className="flex items-center justify-between">
          {/* תצוגת התאריך הנבחר */}
          <div className="flex-grow truncate">
            {value ? (
              <span>{formatDate(value)}</span>
            ) : (
              <span className="text-gray-400">{placeholder}</span>
            )}
          </div>

          {/* כפתורי ניקוי ואיקון לוח שנה */}
          <div className="flex items-center gap-1">
            {clearable && value && !disabled && (
              <button
                type="button"
                className="p-1 text-gray-400 hover:text-gray-600 focus:outline-none"
                onClick={handleClear}
                aria-label="נקה תאריך"
              >
                <X size={16} />
              </button>
            )}
            <CalendarIcon size={18} className="text-gray-400" />
          </div>
        </div>

        {/* לוח השנה הנפתח */}
        {isOpen && (
          <div
            ref={calendarRef}
            className="absolute right-0 z-10 mt-1 bg-white border border-gray-200 rounded-lg shadow-lg"
          >
            <div className="p-3">
              {/* כותרת החודש וניווט */}
              <div className="flex justify-between items-center mb-4">
                <button
                  className="p-1 rounded-full hover:bg-gray-100 focus:outline-none"
                  onClick={(e) => {
                    e.stopPropagation();
                    goToPreviousMonth();
                  }}
                  aria-label="חודש קודם"
                >
                  <ChevronRight size={20} />
                </button>
                <h3 className="text-base font-medium">
                  {MONTHS_IN_HEBREW[currentMonth.getMonth()]} {currentMonth.getFullYear()}
                </h3>
                <button
                  className="p-1 rounded-full hover:bg-gray-100 focus:outline-none"
                  onClick={(e) => {
                    e.stopPropagation();
                    goToNextMonth();
                  }}
                  aria-label="חודש הבא"
                >
                  <ChevronLeft size={20} />
                </button>
              </div>

              {/* ימי השבוע */}
              <div className="grid grid-cols-7 mb-2">
                {getWeekDays().map((day, index) => (
                  <div
                    key={index}
                    className="text-center text-sm font-medium text-gray-500 py-1"
                  >
                    {day}
                  </div>
                ))}
              </div>

              {/* לוח הימים */}
              <div className="grid grid-cols-7 gap-1">
                {buildCalendarDays().flat().map((date, index) => {
                  if (!date) return <div key={`empty-${index}`} className="h-8" />;

                  const isOtherMonth = date.getMonth() !== currentMonth.getMonth();
                  const isToday = date.toDateString() === new Date().toDateString();
                  const isSelected = value && date.toDateString() === value.toDateString();
                  const isDisabled = isDateDisabled(date);
                  const isHovered = hoveredDate && date.toDateString() === hoveredDate.toDateString();

                  return (
                    <button
                      key={date.toISOString()}
                      className={`
                        h-8 w-8 flex items-center justify-center rounded-full text-sm 
                        focus:outline-none transition-colors
                        ${isOtherMonth ? "text-gray-300" : "text-gray-700"}
                        ${isToday && !isSelected ? "border border-blue-500" : ""}
                        ${isSelected ? "bg-blue-500 text-white" : ""}
                        ${isHovered && !isSelected && !isDisabled ? "bg-gray-100" : ""}
                        ${isDisabled ? "text-gray-300 cursor-not-allowed line-through" : "hover:bg-gray-100"}
                      `}
                      onClick={(e) => {
                        e.stopPropagation();
                        if (!isDisabled) handleDateSelect(date);
                      }}
                      onMouseEnter={() => setHoveredDate(date)}
                      onMouseLeave={() => setHoveredDate(null)}
                      disabled={isDisabled}
                      type="button"
                    >
                      {date.getDate()}
                    </button>
                  );
                })}
              </div>

              {/* קיצורי דרך */}
              <div className="mt-4 pt-3 border-t border-gray-200 flex justify-between text-sm text-blue-600">
                <button
                  className="hover:underline focus:outline-none"
                  onClick={(e) => {
                    e.stopPropagation();
                    const today = new Date();
                    if (!isDateDisabled(today)) {
                      handleDateSelect(today);
                    }
                  }}
                  type="button"
                >
                  היום
                </button>
                <button
                  className="hover:underline focus:outline-none"
                  onClick={(e) => {
                    e.stopPropagation();
                    setIsOpen(false);
                  }}
                  type="button"
                >
                  סגור
                </button>
              </div>
            </div>
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

export default DatePicker;