# System Flow Map

## Central Architecture Flow

```mermaid
flowchart LR
  Users[Users: Admin/Managers/Suppliers/Workers] --> FE[Frontend Web/PWA]
  SupplierPortal[Supplier Portal] --> FE
  Mobile[Mobile Usage] --> FE
  FE -->|HTTPS REST| API[Backend API]
  API -->|SQL| DB[(PostgreSQL/PostGIS)]
  API -->|SMTP| Mail[Mail Provider]
  API -->|Queue Optional| Workers[Workers/Celery]
  API -->|Cache Optional| Redis[(Redis)]
  API -->|PDF| Pdf[PDF Service]
  API --> Events[Activity Logs / Notifications]
```

## PNG Artifact

- `docs/diagrams/system-flow-map.png`

