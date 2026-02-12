import { useEffect, useRef } from 'react';
import type { AuditEvent } from '../hooks/useAuditWebSocket';

function formatEvent(e: AuditEvent): string {
  switch (e.event) {
    case 'audit_started':
      return `Audit started — ${e.total_posts} posts to analyze`;
    case 'post_analyzed':
      return `[${e.current}/${e.total}] ${e.post_title} — ${e.findings_in_post} finding(s)${e.error ? ` (error: ${e.error})` : ''}`;
    case 'audit_complete':
      return `Audit complete — ${e.total_findings} total findings`;
    case 'audit_error':
      return `Error: ${e.error}`;
    case 'audit_finished':
      return 'Audit finished.';
    default:
      return JSON.stringify(e);
  }
}

export default function LiveLog({ events }: { events: AuditEvent[] }) {
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [events.length]);

  return (
    <div className="bg-gray-900 text-green-400 font-mono text-sm rounded-lg p-4 h-80 overflow-y-auto">
      {events.length === 0 && (
        <div className="text-gray-500">Waiting for audit events...</div>
      )}
      {events.map((e, i) => (
        <div key={i} className="py-0.5">
          {formatEvent(e)}
        </div>
      ))}
      <div ref={endRef} />
    </div>
  );
}
