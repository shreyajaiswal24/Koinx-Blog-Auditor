import { useEffect, useState } from 'react';
import { fetchRuns, startAudit, fetchAuditStatus, type Run } from '../api/client';
import { useNavigate } from 'react-router-dom';

const CATEGORY_OPTIONS = ['US Taxes', 'Canada Taxes'];

function formatDuration(start: number | null, end: number | null): string {
  if (!start || !end) return '—';
  const secs = Math.round(end - start);
  if (secs < 60) return `${secs}s`;
  const mins = Math.floor(secs / 60);
  const rem = secs % 60;
  return `${mins}m ${rem}s`;
}

export default function Audits() {
  const [runs, setRuns] = useState<Run[]>([]);
  const [showModal, setShowModal] = useState(false);
  const [category, setCategory] = useState(CATEGORY_OPTIONS[0]);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [isRunning, setIsRunning] = useState(false);
  const navigate = useNavigate();

  const loadRuns = () => {
    fetchRuns().then(setRuns).catch(() => {});
  };

  useEffect(() => {
    loadRuns();
    fetchAuditStatus().then((s) => setIsRunning(s.running)).catch(() => {});
  }, []);

  const handleStartAudit = async () => {
    setSubmitting(true);
    setError('');
    try {
      await startAudit(category);
      setShowModal(false);
      setIsRunning(true);
      navigate('/live');
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Failed to start audit');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-800">Audits</h1>
        <button
          onClick={() => setShowModal(true)}
          disabled={isRunning}
          className="px-5 py-2.5 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {isRunning ? 'Audit Running...' : 'Start Audit'}
        </button>
      </div>

      {/* Run history table */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <table className="min-w-full text-sm">
          <thead>
            <tr className="bg-gray-100 text-left text-gray-600 uppercase text-xs">
              <th className="px-4 py-3">Run #</th>
              <th className="px-4 py-3">Category</th>
              <th className="px-4 py-3">Started By</th>
              <th className="px-4 py-3">Started</th>
              <th className="px-4 py-3">Duration</th>
              <th className="px-4 py-3">Posts</th>
              <th className="px-4 py-3">Findings</th>
              <th className="px-4 py-3">API Calls</th>
              <th className="px-4 py-3">Tokens</th>
            </tr>
          </thead>
          <tbody>
            {runs.map((r) => (
              <tr key={r.id} className="border-b hover:bg-gray-50">
                <td className="px-4 py-3 font-medium">#{r.id}</td>
                <td className="px-4 py-3">
                  {r.category ? (
                    <span className="inline-block px-2.5 py-0.5 bg-blue-50 text-blue-700 text-xs font-medium rounded-full">
                      {r.category}
                    </span>
                  ) : (
                    <span className="text-gray-400">—</span>
                  )}
                </td>
                <td className="px-4 py-3 text-gray-600">{r.started_by || '—'}</td>
                <td className="px-4 py-3 text-gray-600">
                  {r.started_at ? new Date(r.started_at * 1000).toLocaleString() : '—'}
                </td>
                <td className="px-4 py-3 text-gray-600">
                  {formatDuration(r.started_at, r.completed_at)}
                </td>
                <td className="px-4 py-3">{r.total_posts}</td>
                <td className="px-4 py-3 font-semibold">{r.total_findings}</td>
                <td className="px-4 py-3 text-gray-600">{r.total_api_calls}</td>
                <td className="px-4 py-3 text-gray-600">{r.total_tokens.toLocaleString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {runs.length === 0 && (
          <div className="text-center text-gray-400 py-12">No audits yet.</div>
        )}
      </div>

      {/* Start Audit Modal */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          {/* Backdrop */}
          <div
            className="absolute inset-0 bg-black/50"
            onClick={() => setShowModal(false)}
          />

          {/* Modal content */}
          <div className="relative bg-white rounded-xl shadow-xl p-6 w-full max-w-md mx-4">
            <h2 className="text-lg font-semibold text-gray-800 mb-4">Start New Audit</h2>

            <div className="mb-5">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Category of Blogs
              </label>
              <select
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none bg-white"
              >
                {CATEGORY_OPTIONS.map((opt) => (
                  <option key={opt} value={opt}>
                    {opt}
                  </option>
                ))}
              </select>
            </div>

            {error && (
              <div className="bg-red-50 text-red-600 text-sm px-4 py-2.5 rounded-lg mb-4">
                {error}
              </div>
            )}

            <div className="flex justify-end gap-3">
              <button
                onClick={() => setShowModal(false)}
                className="px-4 py-2 text-gray-600 bg-gray-100 rounded-lg hover:bg-gray-200 font-medium transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleStartAudit}
                disabled={submitting}
                className="px-5 py-2 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {submitting ? 'Starting...' : 'Submit'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
