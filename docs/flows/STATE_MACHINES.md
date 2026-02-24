# State Machines

## Work Order

Statuses: `PENDING`, `APPROVED`, `ACTIVE`, `COMPLETED`, `REJECTED`, `CANCELLED`

```mermaid
stateDiagram-v2
  [*] --> PENDING
  PENDING --> APPROVED
  APPROVED --> ACTIVE
  ACTIVE --> COMPLETED
  PENDING --> REJECTED
  APPROVED --> CANCELLED
  ACTIVE --> CANCELLED
```

## Daily Work Report

Statuses: `draft`, `submitted`, `approved`, `rejected`, `processed`

```mermaid
stateDiagram-v2
  [*] --> draft
  draft --> submitted
  submitted --> approved
  submitted --> rejected
  approved --> processed
  rejected --> draft
```

## Approval Document (Operational)

Statuses: `Draft/Generated`, `PendingAccountant`, `Approved`, `Rejected`, `Invoiced`

```mermaid
stateDiagram-v2
  [*] --> DraftGenerated
  DraftGenerated --> PendingAccountant
  PendingAccountant --> Approved
  PendingAccountant --> Rejected
  Approved --> Invoiced
```

## Invoice

Statuses: `DRAFT`, `PENDING`, `APPROVED`, `PAID`, `CANCELLED`

```mermaid
stateDiagram-v2
  [*] --> DRAFT
  DRAFT --> PENDING
  PENDING --> APPROVED
  APPROVED --> PAID
  DRAFT --> CANCELLED
  PENDING --> CANCELLED
```

