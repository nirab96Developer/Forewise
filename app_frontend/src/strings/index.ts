// src/strings/index.ts
//
// Central, ONLY public façade for every user-visible string in the system.
//
// Golden rule:
//   Never render `{status}`, `{action}`, `{priority}` or any backend enum
//   directly. Always go through one of the helpers below. The fallback is
//   `'—'` (or `'לא ידוע'` where appropriate), never the raw English code.
//
// Usage:
//   import { getWorkOrderStatusLabel } from '@/strings';
//   <span>{getWorkOrderStatusLabel(order.status)}</span>
//
// Adding a new status?  ──→ edit only `./statuses.ts`.
// Adding a new activity? ──→ edit only `./activity.ts`.

export * from './statuses';
export * from './activity';
export * from './ui';
export * from './errors';

// ─── Imports for the helpers below ──────────────────────────────────────
import {
  WORK_ORDER_STATUS_LABELS, WORK_ORDER_STATUS_TONE,
  WORKLOG_STATUS_LABELS,    WORKLOG_STATUS_TONE,
  INVOICE_STATUS_LABELS,    INVOICE_STATUS_TONE,
  PROJECT_STATUS_LABELS,
  EQUIPMENT_STATUS_LABELS,
  EQUIPMENT_REQUEST_STATUS_LABELS,
  BUDGET_STATUS_LABELS,
  BUDGET_TRANSFER_STATUS_LABELS,
  SUPPORT_TICKET_STATUS_LABELS,
  SUPPLIER_RESPONSE_LABELS,
  PRIORITY_LABELS,
} from './statuses';
import { ACTIVITY_LABELS, ACTIVITY_ALIASES } from './activity';
import { UI_TEXT } from './ui';
import { ERROR_MESSAGES } from './errors';

// ─── Type ────────────────────────────────────────────────────────────────
export type Tone = 'success' | 'warning' | 'danger' | 'info' | 'attention' | 'neutral';

// Small helper: case-insensitive lookup with a guaranteed Hebrew fallback.
function lookup(map: Record<string, string>, raw: string | null | undefined, fallback = UI_TEXT.none): string {
  if (raw === null || raw === undefined) return fallback;
  const key = String(raw).trim();
  if (!key) return fallback;
  return map[key] || map[key.toUpperCase()] || map[key.toLowerCase()] || fallback;
}

// ─── Status helpers ─────────────────────────────────────────────────────
export const getWorkOrderStatusLabel  = (s: string | null | undefined) => lookup(WORK_ORDER_STATUS_LABELS,  s);
export const getWorklogStatusLabel    = (s: string | null | undefined) => lookup(WORKLOG_STATUS_LABELS,    s);
export const getInvoiceStatusLabel    = (s: string | null | undefined) => lookup(INVOICE_STATUS_LABELS,    s);
export const getProjectStatusLabel    = (s: string | null | undefined) => lookup(PROJECT_STATUS_LABELS,    s);
export const getEquipmentStatusLabel  = (s: string | null | undefined) => lookup(EQUIPMENT_STATUS_LABELS,  s);
export const getEquipmentRequestStatusLabel = (s: string | null | undefined) => lookup(EQUIPMENT_REQUEST_STATUS_LABELS, s);
export const getBudgetStatusLabel     = (s: string | null | undefined) => lookup(BUDGET_STATUS_LABELS,     s);
export const getBudgetTransferStatusLabel = (s: string | null | undefined) => lookup(BUDGET_TRANSFER_STATUS_LABELS, s);
export const getSupportTicketStatusLabel  = (s: string | null | undefined) => lookup(SUPPORT_TICKET_STATUS_LABELS,  s);
export const getSupplierResponseLabel = (s: string | null | undefined) => lookup(SUPPLIER_RESPONSE_LABELS, s);
export const getPriorityLabel         = (p: string | null | undefined) => lookup(PRIORITY_LABELS,          p, UI_TEXT.unknown);

// ─── Tone helpers (for badge styling) ───────────────────────────────────
export function getWorkOrderStatusTone(s: string | null | undefined): Tone {
  if (!s) return 'neutral';
  return WORK_ORDER_STATUS_TONE[String(s).toUpperCase()] || 'neutral';
}
export function getWorklogStatusTone(s: string | null | undefined): Tone {
  if (!s) return 'neutral';
  return WORKLOG_STATUS_TONE[String(s).toUpperCase()] || 'neutral';
}
export function getInvoiceStatusTone(s: string | null | undefined): Tone {
  if (!s) return 'neutral';
  return INVOICE_STATUS_TONE[String(s).toUpperCase()] || 'neutral';
}

/** Map a Tone to a Tailwind badge class triplet. Use everywhere instead of
 *  hand-rolled colour ladders so badges stay consistent across the system. */
export function toneClasses(tone: Tone): { bg: string; text: string; border: string; dot: string } {
  switch (tone) {
    case 'success':   return { bg: 'bg-green-100',   text: 'text-green-800',   border: 'border-green-200',   dot: 'bg-green-500' };
    case 'warning':   return { bg: 'bg-amber-100',   text: 'text-amber-800',   border: 'border-amber-200',   dot: 'bg-amber-500' };
    case 'danger':    return { bg: 'bg-red-100',     text: 'text-red-800',     border: 'border-red-200',     dot: 'bg-red-500' };
    case 'info':      return { bg: 'bg-blue-100',    text: 'text-blue-800',    border: 'border-blue-200',    dot: 'bg-blue-500' };
    case 'attention': return { bg: 'bg-purple-100',  text: 'text-purple-800',  border: 'border-purple-200',  dot: 'bg-purple-500' };
    case 'neutral':
    default:          return { bg: 'bg-gray-100',    text: 'text-gray-700',    border: 'border-gray-200',    dot: 'bg-gray-400' };
  }
}

// ─── Activity-log helper ────────────────────────────────────────────────
/**
 * Translate any backend activity action into a Hebrew label.
 * Accepts dotted lowercase, flat lowercase, SCREAMING_SNAKE — all variants
 * are normalised through `ACTIVITY_ALIASES`.
 */
export function getActivityLabel(action: string | null | undefined): string {
  if (!action) return UI_TEXT.system;
  const trimmed = String(action).trim();
  // Direct hit
  if (ACTIVITY_LABELS[trimmed]) return ACTIVITY_LABELS[trimmed];
  // Alias (case preserved — e.g. WORK_ORDER_DELETED)
  const aliased = ACTIVITY_ALIASES[trimmed];
  if (aliased && ACTIVITY_LABELS[aliased]) return ACTIVITY_LABELS[aliased];
  // Lowercase fallback
  const lower = trimmed.toLowerCase();
  if (ACTIVITY_LABELS[lower]) return ACTIVITY_LABELS[lower];
  const aliasedLower = ACTIVITY_ALIASES[lower];
  if (aliasedLower && ACTIVITY_LABELS[aliasedLower]) return ACTIVITY_LABELS[aliasedLower];
  // Last resort — never show the raw English code; show a neutral catch-all.
  return UI_TEXT.system;
}

// ─── Generic helpers ────────────────────────────────────────────────────
/** Re-export common UI text for ergonomic imports. */
export { UI_TEXT, ERROR_MESSAGES };
