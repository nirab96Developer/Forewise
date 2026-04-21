// src/strings/ui.ts
// Common UI labels (buttons, table headers, generic messages).

export const UI_TEXT = {
  // Actions
  save:    'שמור',
  cancel:  'בטל',
  submit:  'שלח',
  approve: 'אשר',
  reject:  'דחה',
  delete:  'מחק',
  edit:    'ערוך',
  refresh: 'רענן',
  search:  'חיפוש',
  back:    'חזור',
  next:    'הבא',
  prev:    'הקודם',
  close:   'סגור',
  confirm: 'אישור',
  retry:   'נסה שוב',
  more:    'עוד',
  details: 'פרטים',
  view:    'צפה',
  yes:     'כן',
  no:      'לא',
  open:    'פתח',
  loading: 'טוען...',
  saving:  'שומר...',
  sending: 'שולח...',

  // Common labels
  unknown:        'לא ידוע',
  notSpecified:   'לא צוין',
  none:           '—',
  total:          'סה"כ',
  date:           'תאריך',
  time:           'שעה',
  status:         'סטטוס',
  priority:       'עדיפות',
  notes:          'הערות',
  reason:         'סיבה',
  description:    'תיאור',
  name:           'שם',
  email:          'אימייל',
  phone:          'טלפון',
  username:       'שם משתמש',
  password:       'סיסמה',

  // Empty states
  noData:         'אין נתונים להצגה',
  noResults:      'לא נמצאו תוצאות',
  noPermission:   'אין לך הרשאה לפעולה זו',

  // System
  system:         'מערכת',
  user:           'משתמש',
  admin:          'מנהל מערכת',
};

export type UITextKey = keyof typeof UI_TEXT;
