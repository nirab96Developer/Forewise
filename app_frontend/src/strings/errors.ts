// src/strings/errors.ts
// Centralised error and validation messages.

export const ERROR_MESSAGES = {
  // Validation
  required:           'שדה חובה',
  invalid:            'ערך לא תקין',
  invalidEmail:       'כתובת מייל לא תקינה',
  invalidPhone:       'מספר טלפון לא תקין',
  invalidPlate:       'מספר רישוי לא תקין',
  passwordTooShort:   'סיסמה חייבת להכיל לפחות 8 תווים',
  passwordsMismatch:  'הסיסמאות לא תואמות',
  numberMustBePositive: 'הערך חייב להיות גדול מ-0',
  selectOption:       'יש לבחור אפשרות',

  // Network / API
  network:            'בעיית תקשורת — נסה שוב',
  serverError:        'שגיאת שרת — נסה שוב מאוחר יותר',
  unauthorized:       'אין הרשאה',
  forbidden:          'הפעולה אינה מורשית',
  notFound:           'לא נמצא',
  conflict:           'התרחש קונפליקט',
  timeout:            'הפעולה ארכה זמן רב מדי',

  // Auth
  invalidCredentials: 'שם משתמש או סיסמה שגויים',
  accountLocked:      'החשבון נעול זמנית. נסה שוב מאוחר יותר',
  sessionExpired:     'תוקף ההתחברות פג. אנא התחבר שוב',
  otpInvalid:         'קוד אימות שגוי',
  otpExpired:         'קוד אימות פג תוקף',

  // Generic fallbacks
  generic:            'אירעה שגיאה. אנא נסה שוב',
  unknown:            'שגיאה לא ידועה',
};

export type ErrorMessageKey = keyof typeof ERROR_MESSAGES;
