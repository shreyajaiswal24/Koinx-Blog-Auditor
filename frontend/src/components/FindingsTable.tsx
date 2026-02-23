import { useState } from 'react';
import type { Finding } from '../api/client';
import { updateFindingStatus } from '../api/client';
import PriorityBadge from './PriorityBadge';
import StatusBadge from './StatusBadge';

interface Props {
  findings: Finding[];
  onStatusChange?: () => void;
}

function SourceLink({ source }: { source: string }) {
  if (!source) return <span className="text-gray-400">—</span>;

  // If it's already a URL, link directly
  if (source.startsWith('http')) {
    return (
      <a
        href={source}
        target="_blank"
        rel="noopener noreferrer"
        className="text-blue-600 hover:underline font-medium"
        onClick={(e) => e.stopPropagation()}
      >
        {source}
      </a>
    );
  }

  // For IRS references like "Rev. Rul. 2023-14", "IRC §1091", "Notice 2014-21", etc.
  // Link to a Google search so the user can find the original source
  const searchUrl = `https://www.google.com/search?q=${encodeURIComponent(source + ' IRS site:irs.gov')}`;
  return (
    <a
      href={searchUrl}
      target="_blank"
      rel="noopener noreferrer"
      className="text-blue-600 hover:underline font-medium"
      onClick={(e) => e.stopPropagation()}
    >
      {source}
    </a>
  );
}

export default function FindingsTable({ findings, onStatusChange }: Props) {
  const [expandedId, setExpandedId] = useState<number | null>(null);
  const [updating, setUpdating] = useState<number | null>(null);

  const handleStatusChange = async (findingId: number, newStatus: string) => {
    setUpdating(findingId);
    try {
      await updateFindingStatus(findingId, newStatus);
      onStatusChange?.();
    } catch {
      // ignore
    } finally {
      setUpdating(null);
    }
  };

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full text-sm">
        <thead>
          <tr className="bg-gray-100 text-left text-gray-600 uppercase text-xs">
            <th className="px-4 py-3">Blog</th>
            <th className="px-4 py-3">Section</th>
            <th className="px-4 py-3">Issue Type</th>
            <th className="px-4 py-3">Priority</th>
            <th className="px-4 py-3">Status</th>
            <th className="px-4 py-3">Confidence</th>
          </tr>
        </thead>
        <tbody>
          {findings.map((f) => (
            <>
              <tr
                key={f.id}
                className="border-b hover:bg-gray-50 cursor-pointer"
                onClick={() => setExpandedId(expandedId === f.id ? null : f.id)}
              >
                <td className="px-4 py-3">
                  <a
                    href={f.blog_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-blue-600 hover:underline"
                    onClick={(e) => e.stopPropagation()}
                  >
                    {f.blog_title.length > 50 ? f.blog_title.slice(0, 50) + '...' : f.blog_title}
                  </a>
                </td>
                <td className="px-4 py-3 text-gray-600">{f.section_heading}</td>
                <td className="px-4 py-3">{f.issue_type.replace(/_/g, ' ')}</td>
                <td className="px-4 py-3"><PriorityBadge priority={f.priority} /></td>
                <td className="px-4 py-3"><StatusBadge status={f.status} /></td>
                <td className="px-4 py-3">{(f.confidence * 100).toFixed(0)}%</td>
              </tr>
              {expandedId === f.id && (
                <tr key={`${f.id}-detail`} className="bg-blue-50">
                  <td colSpan={6} className="px-6 py-4 space-y-3">
                    <div>
                      <div className="font-semibold text-gray-700 text-xs uppercase mb-1">Current Text</div>
                      <div className="text-gray-800 bg-white rounded p-3 border border-red-200 text-sm italic">"{f.exact_quote}"</div>
                    </div>
                    <div>
                      <div className="font-semibold text-gray-700 text-xs uppercase mb-1">Suggested Update</div>
                      <div className="text-gray-800 bg-white rounded p-3 border border-green-200 text-sm">{f.suggested_update}</div>
                    </div>
                    <div>
                      <div className="font-semibold text-gray-700 text-xs uppercase mb-1">Description</div>
                      <div className="text-gray-600 text-sm">{f.description}</div>
                    </div>
                    <div className="flex items-center gap-2 text-xs text-gray-500">
                      <span>Source:</span>
                      <SourceLink source={f.source} />
                      <span>| LLM Confidence: {(f.llm_confidence * 100).toFixed(0)}%</span>
                    </div>

                    {/* Action buttons */}
                    {f.status !== 'completed' && f.status !== 'ignored' && (
                      <div className="flex gap-2 pt-2 border-t border-blue-100">
                        <button
                          onClick={(e) => { e.stopPropagation(); handleStatusChange(f.id, 'completed'); }}
                          disabled={updating === f.id}
                          className="px-4 py-1.5 text-xs font-medium text-green-700 bg-green-50 border border-green-200 rounded-lg hover:bg-green-100 disabled:opacity-50 transition-colors"
                        >
                          {updating === f.id ? 'Updating...' : 'Mark Completed'}
                        </button>
                        <button
                          onClick={(e) => { e.stopPropagation(); handleStatusChange(f.id, 'ignored'); }}
                          disabled={updating === f.id}
                          className="px-4 py-1.5 text-xs font-medium text-gray-600 bg-gray-50 border border-gray-200 rounded-lg hover:bg-gray-100 disabled:opacity-50 transition-colors"
                        >
                          {updating === f.id ? 'Updating...' : 'Ignore'}
                        </button>
                      </div>
                    )}

                    {/* Already actioned */}
                    {f.status === 'completed' && (
                      <div className="text-xs text-green-600 font-medium pt-2 border-t border-blue-100">
                        Marked as completed
                      </div>
                    )}
                    {f.status === 'ignored' && (
                      <div className="text-xs text-gray-500 font-medium pt-2 border-t border-blue-100">
                        Ignored
                      </div>
                    )}
                  </td>
                </tr>
              )}
            </>
          ))}
        </tbody>
      </table>
      {findings.length === 0 && (
        <div className="text-center text-gray-400 py-12">No findings to display.</div>
      )}
    </div>
  );
}
