import { useEffect, useState } from 'react';
import { fetchFindings, type PaginatedFindings } from '../api/client';
import FindingsTable from '../components/FindingsTable';

export default function Findings() {
  const [data, setData] = useState<PaginatedFindings | null>(null);
  const [page, setPage] = useState(1);
  const [priority, setPriority] = useState('');
  const [status, setStatus] = useState('');
  const [issueType, setIssueType] = useState('');

  useEffect(() => {
    const params: Record<string, string> = { page: String(page), per_page: '20' };
    if (priority) params.priority = priority;
    if (status) params.status = status;
    if (issueType) params.issue_type = issueType;
    fetchFindings(params).then(setData).catch(() => {});
  }, [page, priority, status, issueType]);

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold text-gray-800">Findings</h1>

      {/* Filters */}
      <div className="flex flex-wrap gap-3 items-center">
        <select
          value={priority}
          onChange={(e) => { setPriority(e.target.value); setPage(1); }}
          className="border rounded px-3 py-1.5 text-sm bg-white"
        >
          <option value="">All Priorities</option>
          <option value="high">High</option>
          <option value="medium">Medium</option>
          <option value="low">Low</option>
        </select>

        <select
          value={status}
          onChange={(e) => { setStatus(e.target.value); setPage(1); }}
          className="border rounded px-3 py-1.5 text-sm bg-white"
        >
          <option value="">All Statuses</option>
          <option value="new">New</option>
          <option value="previously_identified">Recurring</option>
          <option value="resolved">Resolved</option>
        </select>

        <select
          value={issueType}
          onChange={(e) => { setIssueType(e.target.value); setPage(1); }}
          className="border rounded px-3 py-1.5 text-sm bg-white"
        >
          <option value="">All Issue Types</option>
          <option value="outdated_info">Outdated Info</option>
          <option value="incorrect_fact">Incorrect Fact</option>
          <option value="missing_update">Missing Update</option>
          <option value="misleading_language">Misleading Language</option>
          <option value="incomplete_info">Incomplete Info</option>
        </select>

        {data && (
          <span className="text-sm text-gray-500 ml-auto">
            {data.total} finding{data.total !== 1 ? 's' : ''}
          </span>
        )}
      </div>

      {/* Table */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        {data ? (
          <FindingsTable findings={data.items} />
        ) : (
          <div className="text-center py-12 text-gray-400">Loading...</div>
        )}
      </div>

      {/* Pagination */}
      {data && data.pages > 1 && (
        <div className="flex items-center justify-center gap-2">
          <button
            disabled={page <= 1}
            onClick={() => setPage(page - 1)}
            className="px-3 py-1 rounded border text-sm disabled:opacity-40"
          >
            Prev
          </button>
          <span className="text-sm text-gray-600">
            Page {data.page} / {data.pages}
          </span>
          <button
            disabled={page >= data.pages}
            onClick={() => setPage(page + 1)}
            className="px-3 py-1 rounded border text-sm disabled:opacity-40"
          >
            Next
          </button>
        </div>
      )}
    </div>
  );
}
