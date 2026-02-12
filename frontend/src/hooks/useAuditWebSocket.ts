import { useEffect, useRef, useState, useCallback } from 'react';

export interface AuditEvent {
  event: string;
  total_posts?: number;
  current?: number;
  total?: number;
  post_title?: string;
  findings_in_post?: number;
  total_findings?: number;
  error?: string;
}

export function useAuditWebSocket() {
  const [events, setEvents] = useState<AuditEvent[]>([]);
  const [latest, setLatest] = useState<AuditEvent | null>(null);
  const [connected, setConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const ws = new WebSocket(`${protocol}//${window.location.host}/ws/audit`);

    ws.onopen = () => setConnected(true);
    ws.onclose = () => {
      setConnected(false);
      // Reconnect after 2 seconds
      setTimeout(connect, 2000);
    };
    ws.onmessage = (msg) => {
      const data: AuditEvent = JSON.parse(msg.data);
      setLatest(data);
      setEvents((prev) => [...prev, data]);
    };

    wsRef.current = ws;
  }, []);

  const clearEvents = useCallback(() => {
    setEvents([]);
    setLatest(null);
  }, []);

  useEffect(() => {
    connect();
    return () => {
      wsRef.current?.close();
    };
  }, [connect]);

  return { events, latest, connected, clearEvents };
}
