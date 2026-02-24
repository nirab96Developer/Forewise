// src/utils/date.ts
// פונקציות עזר לעבודה עם תאריכים

/**
 * פורמט תאריך לתצוגה בעברית
 * @param dateString תאריך כמחרוזת או אובייקט תאריך
 * @returns תאריך בפורמט DD/MM/YYYY
 */
export const formatDate = (dateString: string | Date | null | undefined): string => {
    if (!dateString) return '';
    
    const date = typeof dateString === 'string' ? new Date(dateString) : dateString;
    
    if (isNaN(date.getTime())) return '';
    
    const day = date.getDate().toString().padStart(2, '0');
    const month = (date.getMonth() + 1).toString().padStart(2, '0');
    const year = date.getFullYear();
    
    return `${day}/${month}/${year}`;
  };
  
  /**
   * פורמט תאריך עם שעה
   * @param dateString תאריך כמחרוזת או אובייקט תאריך
   * @returns תאריך ושעה בפורמט DD/MM/YYYY HH:MM
   */
  export const formatDateTime = (dateString: string | Date | null | undefined): string => {
    if (!dateString) return '';
    
    const date = typeof dateString === 'string' ? new Date(dateString) : dateString;
    
    if (isNaN(date.getTime())) return '';
    
    const formattedDate = formatDate(date);
    const hours = date.getHours().toString().padStart(2, '0');
    const minutes = date.getMinutes().toString().padStart(2, '0');
    
    return `${formattedDate} ${hours}:${minutes}`;
  };
  
  /**
   * בדיקה אם תאריך חל היום
   * @param dateString תאריך כמחרוזת או אובייקט תאריך
   * @returns האם התאריך הוא היום
   */
  export const isToday = (dateString: string | Date): boolean => {
    const date = typeof dateString === 'string' ? new Date(dateString) : dateString;
    const today = new Date();
    
    return date.getDate() === today.getDate() &&
           date.getMonth() === today.getMonth() &&
           date.getFullYear() === today.getFullYear();
  };
  
  /**
   * חישוב ימים עד לתאריך מסוים
   * @param targetDate תאריך יעד
   * @param fromDate תאריך התחלה (ברירת מחדל: היום)
   * @returns מספר הימים עד התאריך המבוקש
   */
  export const daysUntil = (
    targetDate: string | Date, 
    fromDate: string | Date = new Date()
  ): number => {
    const target = typeof targetDate === 'string' ? new Date(targetDate) : targetDate;
    const start = typeof fromDate === 'string' ? new Date(fromDate) : fromDate;
    
    // נקה את השעות כדי לקבל הפרש ימים מדויק
    const targetWithoutTime = new Date(target.getFullYear(), target.getMonth(), target.getDate());
    const startWithoutTime = new Date(start.getFullYear(), start.getMonth(), start.getDate());
    
    // חישוב ההפרש במילישניות וחלוקה למספר המילישניות ביום
    const differenceInTime = targetWithoutTime.getTime() - startWithoutTime.getTime();
    const differenceInDays = Math.ceil(differenceInTime / (1000 * 3600 * 24));
    
    return differenceInDays;
  };
  
  /**
   * קבלת חודש בעברית
   * @param month מספר החודש (0-11)
   * @returns שם החודש בעברית
   */
  export const getHebrewMonth = (month: number): string => {
    const hebrewMonths = [
      'ינואר', 'פברואר', 'מרץ', 'אפריל', 'מאי', 'יוני',
      'יולי', 'אוגוסט', 'ספטמבר', 'אוקטובר', 'נובמבר', 'דצמבר'
    ];
    
    return hebrewMonths[month];
  };
  
  /**
   * פורמט תאריך בסגנון עברי
   * @param dateString תאריך כמחרוזת או אובייקט תאריך
   * @returns תאריך בפורמט "DD ב[חודש] YYYY"
   */
  export const formatHebrewDate = (dateString: string | Date | null | undefined): string => {
    if (!dateString) return '';
    
    const date = typeof dateString === 'string' ? new Date(dateString) : dateString;
    
    if (isNaN(date.getTime())) return '';
    
    const day = date.getDate();
    const month = getHebrewMonth(date.getMonth());
    const year = date.getFullYear();
    
    return `${day} ב${month} ${year}`;
  };
  
  /**
   * יצירת תאריך ISO (YYYY-MM-DD) מתאריך
   * @param date תאריך
   * @returns מחרוזת בפורמט YYYY-MM-DD
   */
  export const toISODateString = (date: Date): string => {
    const year = date.getFullYear();
    const month = (date.getMonth() + 1).toString().padStart(2, '0');
    const day = date.getDate().toString().padStart(2, '0');
    
    return `${year}-${month}-${day}`;
  };
  
  /**
   * מחזיר את היום הראשון בחודש
   */
  export const getFirstDayOfMonth = (year: number, month: number): Date => {
    return new Date(year, month, 1);
  };
  
  /**
   * מחזיר את היום האחרון בחודש
   */
  export const getLastDayOfMonth = (year: number, month: number): Date => {
    return new Date(year, month + 1, 0);
  };
  
  /**
   * מחזיר את מספר הימים בחודש
   */
  export const getDaysInMonth = (year: number, month: number): number => {
    return new Date(year, month + 1, 0).getDate();
  };