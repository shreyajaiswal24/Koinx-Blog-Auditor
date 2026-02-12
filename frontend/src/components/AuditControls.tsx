import { useState } from 'react';
import { startAudit, getReportDownloadUrl } from '../api/client';

interface Props {
  isRunning: boolean;
  onStarted: () => void;
}

export default function AuditControls({ isRunning, onStarted }: Props) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleStart = async (postId?: number) => {
    setLoading(true);
    setError('');
    try {
      await startAudit(postId);
      onStarted();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Failed to start audit');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-wrap items-center gap-3">
      <button
        onClick={() => handleStart()}
        disabled={isRunning || loading}
        className="px-4 py-2 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {isRunning ? 'Audit Running...' : 'Run Full Audit'}
      </button>

      <a
        href={getReportDownloadUrl()}
        className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg font-medium hover:bg-gray-200"
        download
      >
        Download Excel
      </a>

      {error && <span className="text-red-600 text-sm">{error}</span>}
    </div>
  );
}
