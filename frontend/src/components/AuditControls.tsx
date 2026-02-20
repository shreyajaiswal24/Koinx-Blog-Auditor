import { getReportDownloadUrl } from '../api/client';
import { useNavigate } from 'react-router-dom';

interface Props {
  isRunning: boolean;
}

export default function AuditControls({ isRunning }: Props) {
  const navigate = useNavigate();

  return (
    <div className="flex flex-wrap items-center gap-3">
      <button
        onClick={() => navigate('/audits')}
        disabled={isRunning}
        className="px-4 py-2 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {isRunning ? 'Audit Running...' : 'Start New Audit'}
      </button>

      <a
        href={getReportDownloadUrl()}
        className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg font-medium hover:bg-gray-200"
        download
      >
        Download Excel
      </a>
    </div>
  );
}
