// src/hooks/useWebSocket.ts
import { useEffect, useRef, useState, useCallback } from 'react';

export interface WebSocketMessage {
  type: string;
  data: any;
  timestamp: string;
}

export interface UseWebSocketReturn {
  isConnected: boolean;
  lastMessage: WebSocketMessage | null;
  sendMessage: (message: any) => void;
  reconnect: () => void;
}

const MAX_RETRIES = 3;
const BASE_DELAY_MS = 1000;

export const useWebSocket = (url?: string): UseWebSocketReturn => {
  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);

  const wsRef             = useRef<WebSocket | null>(null);
  const retryCountRef     = useRef(0);
  const retryTimerRef     = useRef<ReturnType<typeof setTimeout> | null>(null);
  const destroyedRef      = useRef(false);   // true after unmount — prevents stale reconnects
  const connectingRef     = useRef(false);   // prevents duplicate connections

  // ── Build the correct WebSocket URL ────────────────────────────────────────
  const buildUrl = useCallback((): string | null => {
    if (url) return url;

    const token = localStorage.getItem('access_token');
    if (!token) return null;

    const proto = window.location.protocol === 'https:' ? 'wss' : 'ws';
    const host  = window.location.host;                    // e.g. forewise.co
    return `${proto}://${host}/api/v1/ws/notifications?token=${token}`;
  }, [url]);

  // ── Disconnect helper ───────────────────────────────────────────────────────
  const disconnect = useCallback(() => {
    if (retryTimerRef.current) {
      clearTimeout(retryTimerRef.current);
      retryTimerRef.current = null;
    }
    if (wsRef.current) {
      const ws = wsRef.current;
      wsRef.current = null;
      // Suppress further events before closing
      ws.onopen    = null;
      ws.onclose   = null;
      ws.onerror   = null;
      ws.onmessage = null;
      if (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING) {
        ws.close();
      }
    }
    setIsConnected(false);
    connectingRef.current = false;
  }, []);

  // ── Main connect function ───────────────────────────────────────────────────
  const connect = useCallback(() => {
    if (destroyedRef.current) return;
    if (connectingRef.current) return;          // already mid-connect
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    const wsUrl = buildUrl();
    if (!wsUrl) {
      // No token — user not logged in, don't bother
      return;
    }

    connectingRef.current = true;

    let ws: WebSocket;
    try {
      ws = new WebSocket(wsUrl);
    } catch (err) {
      connectingRef.current = false;
      return;
    }

    wsRef.current = ws;

    ws.onopen = () => {
      if (destroyedRef.current) { ws.close(); return; }
      retryCountRef.current = 0;
      connectingRef.current = false;
      setIsConnected(true);
    };

    ws.onmessage = (event) => {
      try {
        const message: WebSocketMessage = JSON.parse(event.data);
        setLastMessage(message);
      } catch {
        // ignore malformed frames
      }
    };

    ws.onerror = () => {
      // onerror is always followed by onclose — handle everything there
    };

    ws.onclose = () => {
      if (destroyedRef.current) return;       // component unmounted — stop

      wsRef.current     = null;
      connectingRef.current = false;
      setIsConnected(false);

      if (retryCountRef.current >= MAX_RETRIES) {
        // Give up — fall back to polling (handled in useNotifications)
        console.warn('[WS] Max retries reached — switching to polling');
        return;
      }

      retryCountRef.current += 1;
      const delay = BASE_DELAY_MS * Math.pow(2, retryCountRef.current - 1); // 1s, 2s, 4s
      console.log(`[WS] Retry ${retryCountRef.current}/${MAX_RETRIES} in ${delay}ms`);

      retryTimerRef.current = setTimeout(() => {
        if (!destroyedRef.current) connect();
      }, delay);
    };
  }, [buildUrl]);

  // ── Manual reconnect (resets counter) ─────────────────────────────────────
  const reconnect = useCallback(() => {
    retryCountRef.current = 0;
    disconnect();
    connect();
  }, [connect, disconnect]);

  // ── Send a message ─────────────────────────────────────────────────────────
  const sendMessage = useCallback((message: any) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
    }
  }, []);

  // ── Lifecycle: connect when mounted, disconnect on unmount ─────────────────
  useEffect(() => {
    destroyedRef.current  = false;
    retryCountRef.current = 0;

    const token = localStorage.getItem('access_token');
    if (token) {
      connect();
    }

    return () => {
      destroyedRef.current = true;
      disconnect();
    };
    // connect/disconnect are stable — only run this once on mount
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return { isConnected, lastMessage, sendMessage, reconnect };
};
