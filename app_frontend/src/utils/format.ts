// src/utils/format.ts
// פונקציות עזר לפורמט של מספרים, טקסט וכו'

/**
 * פורמט מספר כמספר שלם עם פסיקים
 * @param num המספר לפורמט
 * @returns מחרוזת עם פסיקים (לדוגמה: 1,234,567)
 */
export const formatNumber = (num: number | null | undefined): string => {
    if (num === null || num === undefined) return '';
    return num.toLocaleString('he-IL');
  };
  
  /**
   * פורמט מספר עם מספר ספרות אחרי הנקודה
   * @param num המספר לפורמט
   * @param decimals מספר הספרות אחרי הנקודה
   * @returns מחרוזת מפורמטת (לדוגמה: 1,234.56)
   */
  export const formatDecimal = (
    num: number | null | undefined, 
    decimals: number = 2
  ): string => {
    if (num === null || num === undefined) return '';
    return num.toLocaleString('he-IL', { 
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals
    });
  };
  
  /**
   * פורמט מספר ככסף (₪)
   * @param amount הסכום לפורמט
   * @param decimals מספר הספרות אחרי הנקודה
   * @returns מחרוזת עם סמל השקל (לדוגמה: ₪1,234.56)
   */
  export const formatCurrency = (
    amount: number | null | undefined, 
    decimals: number = 2
  ): string => {
    if (amount === null || amount === undefined) return '';
    
    const formattedAmount = formatDecimal(amount, decimals);
    return `₪${formattedAmount}`;
  };
  
  /**
   * פורמט אחוזים
   * @param value הערך לפורמט (0.1 = 10%)
   * @param decimals מספר הספרות אחרי הנקודה
   * @returns מחרוזת עם סמל האחוז (לדוגמה: 10.5%)
   */
  export const formatPercent = (
    value: number | null | undefined, 
    decimals: number = 1
  ): string => {
    if (value === null || value === undefined) return '';
    
    // המרה לאחוזים (הכפלה ב-100)
    const percentValue = value * 100;
    
    return `${formatDecimal(percentValue, decimals)}%`;
  };
  
  /**
   * פורמט מספר שעות ודקות
   * @param hours מספר השעות
   * @returns מחרוזת בפורמט "X.Y שעות" או "X שעות Y דקות"
   */
  export const formatHours = (hours: number): string => {
    if (hours === Math.floor(hours)) {
      return `${hours} שעות`;
    }
    
    const wholeHours = Math.floor(hours);
    const minutes = Math.round((hours - wholeHours) * 60);
    
    if (minutes === 0) {
      return `${wholeHours} שעות`;
    } else if (wholeHours === 0) {
      return `${minutes} דקות`;
    } else {
      return `${wholeHours} שעות ו-${minutes} דקות`;
    }
  };
  
  /**
   * קיצור טקסט ארוך והוספת אליפסיס
   * @param text הטקסט לקיצור
   * @param maxLength האורך המקסימלי
   * @returns טקסט מקוצר עם אליפסיס (...) אם צריך
   */
  export const truncateText = (
    text: string | null | undefined, 
    maxLength: number = 50
  ): string => {
    if (!text) return '';
    
    if (text.length <= maxLength) {
      return text;
    }
    
    return `${text.substring(0, maxLength)}...`;
  };
  
  /**
   * המרת מחרוזת לאותיות גדולות בתחילת כל מילה
   * @param text המחרוזת להמרה
   * @returns מחרוזת עם אותיות גדולות בתחילת כל מילה
   */
  export const toTitleCase = (text: string | null | undefined): string => {
    if (!text) return '';
    
    return text
      .split(' ')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
      .join(' ');
  };
  
  /**
   * פורמט שם מלא (שם פרטי ושם משפחה)
   * @param firstName שם פרטי
   * @param lastName שם משפחה
   * @returns שם מלא מפורמט
   */
  export const formatFullName = (
    firstName: string | null | undefined, 
    lastName: string | null | undefined
  ): string => {
    const first = firstName || '';
    const last = lastName || '';
    
    if (!first && !last) return '';
    if (!first) return last;
    if (!last) return first;
    
    return `${first} ${last}`;
  };
  
  /**
   * פורמט מספר טלפון ישראלי
   * @param phone מספר הטלפון
   * @returns מחרוזת בפורמט XXX-XXXXXXX
   */
  export const formatPhoneNumber = (phone: string | null | undefined): string => {
    if (!phone) return '';
    
    // הסרת כל התווים שאינם ספרות
    const digitsOnly = phone.replace(/\D/g, '');
    
    // בדיקה אם יש מספיק ספרות
    if (digitsOnly.length < 9) return phone;
    
    // פורמט בהתאם לאורך (7, 9 או 10 ספרות)
    if (digitsOnly.length === 9) {
      // מספר סלולרי ללא 0 בהתחלה (לדוגמה 501234567)
      return `${digitsOnly.slice(0, 2)}-${digitsOnly.slice(2)}`;
    } else if (digitsOnly.length === 10) {
      // מספר סלולרי עם 0 בהתחלה (לדוגמה 0501234567)
      return `${digitsOnly.slice(0, 3)}-${digitsOnly.slice(3)}`;
    } else {
      // מספר אחר
      return phone;
    }
  };
  
  /**
   * פורמט מספר תעודת זהות ישראלית
   * @param id מספר תעודת הזהות
   * @returns מחרוזת בפורמט XXX-XXX-XXX
   */
  export const formatIdNumber = (id: string | null | undefined): string => {
    if (!id) return '';
    
    // הסרת כל התווים שאינם ספרות
    const digitsOnly = id.replace(/\D/g, '');
    
    // בדיקה אם יש 9 ספרות
    if (digitsOnly.length !== 9) return id;
    
    // פורמט XXX-XXX-XXX
    return `${digitsOnly.slice(0, 3)}-${digitsOnly.slice(3, 6)}-${digitsOnly.slice(6)}`;
  };
  
  /**
   * פורמט מספר רישוי
   * @param licensePlate מספר הרישוי
   * @returns מחרוזת מפורמטת
   */
  export const formatLicensePlate = (licensePlate: string | null | undefined): string => {
    if (!licensePlate) return '';
    
    // הסרת כל התווים שאינם ספרות
    const digitsOnly = licensePlate.replace(/\D/g, '');
    
    // בדיקה לפי מספר הספרות
    if (digitsOnly.length === 7) {
      // פורמט ישן: XX-XXX-XX
      return `${digitsOnly.slice(0, 2)}-${digitsOnly.slice(2, 5)}-${digitsOnly.slice(5)}`;
    } else if (digitsOnly.length === 8) {
      // פורמט חדש: XXX-XX-XXX
      return `${digitsOnly.slice(0, 3)}-${digitsOnly.slice(3, 5)}-${digitsOnly.slice(5)}`;
    } else {
      // פורמט אחר או לא תקין
      return licensePlate;
    }
  };