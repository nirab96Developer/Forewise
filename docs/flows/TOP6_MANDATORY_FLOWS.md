# Top 6 Mandatory Flows

## 1) Login / Remember Me / Refresh / Logout

```mermaid
flowchart TD
  A[Login] --> B[/auth/login]
  B --> C{valid}
  C -- yes --> D[access+refresh]
  D --> E{remember_me}
  E --> F[storage policy]
  F --> G[auto refresh]
  G --> H[logout]
```

- access קצר, refresh לפי policy
- בלי 401-loop
- כשל refresh מנקה auth
- logout מנקה state
- trail אירועים נשמר

## 2) Forgot Password / Reset (single-use)

```mermaid
flowchart TD
  A[forgot] --> B[token]
  B --> C[token_hash only]
  C --> D[email link]
  D --> E[reset confirm]
  E --> F{valid+unused+unexpired}
  F --> G[password update + mark used]
```

- response גנרי
- hash-only
- single-use
- expiry קצר
- reuse נדחה

## 3) Work Order -> Supplier Portal -> Approve/Reject -> Active

```mermaid
flowchart LR
  A[work order] --> B[supplier distribution]
  B --> C[supplier portal]
  C --> D{approve/reject}
  D --> E[ACTIVE]
  D --> F[REJECTED]
```

- scope/token תקפים
- reject עם reason
- approve אטומי
- תנאי מעבר מבוקרים
- activity log חובה

## 4) Equipment Scan -> Daily Report -> Approval PDF

```mermaid
flowchart LR
  A[equipment scan] --> B[daily report]
  B --> C[approval]
  C --> D[pdf generated]
```

- scan קשור לציוד+משתמש
- תקן/לא תקן נשמר
- trail של reviewer
- PDF רק אחרי workflow תקין
- משמש ראיה תפעולית/חשבונאית

## 5) Accountant Inbox (Area-scoped) -> Approve/Reject -> Mark for Invoice

```mermaid
flowchart TD
  A[inbox] --> B[area scope filter]
  B --> C[review]
  C --> D{approve/reject}
  D --> E[mark for invoice]
```

- area scope חובה
- scope גם ב-list וגם by-id
- reject עם reason
- mark for invoice רק אחרי approve
- audit actor/time

## 6) Budget Reservation -> Release per Report -> Stop Early -> Release Remainder

```mermaid
flowchart LR
  A[reserve] --> B[approved report]
  B --> C[release]
  C --> D{stop early}
  D --> E[release remainder]
```

- reservation נועל מסגרת
- release לפי דיווחים מאושרים
- stop early משחרר יתרה
- מניעת חריגה
- תיעוד פיננסי מלא

