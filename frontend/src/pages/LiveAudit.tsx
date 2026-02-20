import { useAuditWebSocket } from '../hooks/useAuditWebSocket';
import { fetchAuditStatus } from '../api/client';
import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import ProgressBar from '../components/ProgressBar';
import LiveLog from '../components/LiveLog';

export default function LiveAudit() {
  const { events, latest, connected } = useAuditWebSocket();
  const [running, setRunning] = useState(false);
  const [findingCount, setFindingCount] = useState(0);
  const navigate = useNavigate();

  useEffect(() => {
    fetchAuditStatus().then((s) => setRunning(s.running)).catch(() => {});
  }, []);

  useEffect(() => {
    if (!latest) return;
    if (latest.event === 'audit_started') {
      setRunning(true);
      setFindingCount(0);
    }
    if (latest.event === 'post_analyzed' && latest.findings_in_post) {
      setFindingCount((c) => c + latest.findings_in_post!);
    }
    if (latest.event === 'audit_complete' || latest.event === 'audit_finished') {
      setRunning(false);
      if (latest.total_findings !== undefined) {
        setFindingCount(latest.total_findings);
      }
    }
  }, [latest]);

  const current = latest?.current ?? 0;
  const total = latest?.total ?? latest?.total_posts ?? 0;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-800">Live Audit</h1>
        <div className="flex items-center gap-4">
          <span className={`w-2.5 h-2.5 rounded-full ${connected ? 'bg-green-500' : 'bg-red-500'}`} />
          <span className="text-sm text-gray-500">{connected ? 'Connected' : 'Disconnected'}</span>
        </div>
      </div>

      {/* Controls */}
      {!running && (
        <div>
          <button
            onClick={() => navigate('/audits')}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700"
          >
            Start New Audit
          </button>
        </div>
      )}
      {running && (
        <span className="text-sm text-gray-500 animate-pulse">Processing...</span>
      )}

      {/* Progress */}
      {total > 0 && (
        <div className="bg-white rounded-lg shadow p-5 space-y-4">
          <ProgressBar current={current} total={total} />
          <div className="flex gap-6 text-sm">
            <div>
              <span className="text-gray-500">Findings so far:</span>{' '}
              <span className="font-semibold text-blue-700">{findingCount}</span>
            </div>
          </div>
        </div>
      )}

      {/* Log */}
      <div className="bg-white rounded-lg shadow p-5">
        <h2 className="text-lg font-semibold text-gray-700 mb-3">Event Log</h2>
        <LiveLog events={events} />
      </div>
    </div>
  );
}
