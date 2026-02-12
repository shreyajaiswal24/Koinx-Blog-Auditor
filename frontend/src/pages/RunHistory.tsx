import { useEffect, useState } from 'react';
import { fetchRuns, type Run } from '../api/client';

function formatDuration(start: number | null, end: number | null): string {
  if (!start || !end) return '—';
  const secs = Math.round(end - start);
  if (secs < 60) return `${secs}s`;
  const mins = Math.floor(secs / 60);
  const rem = secs % 60;
  return `${mins}m ${rem}s`;
}

export default function RunHistory() {
  const [runs, setRuns] = useState<Run[]>([]);

  useEffect(() => {
    fetchRuns().then(setRuns).catch(() => {});
  }, []);

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold text-gray-800">Run History</h1>

      <div className="bg-white rounded-lg shadow overflow-hidden">
        <table className="min-w-full text-sm">
          <thead>
            <tr className="bg-gray-100 text-left text-gray-600 uppercase text-xs">
              <th className="px-4 py-3">Run #</th>
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
          <div className="text-center text-gray-400 py-12">No audit runs yet.</div>
        )}
      </div>
    </div>
  );
}
