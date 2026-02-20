import { useEffect, useState } from 'react';
import { fetchStats, fetchAuditStatus, type Stats } from '../api/client';
import StatsCards from '../components/StatsCards';
import AuditControls from '../components/AuditControls';

export default function Dashboard() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [running, setRunning] = useState(false);

  const load = () => {
    fetchStats().then(setStats).catch(() => {});
    fetchAuditStatus().then((s) => setRunning(s.running)).catch(() => {});
  };

  useEffect(() => {
    load();
    const id = setInterval(load, 5000);
    return () => clearInterval(id);
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-800">Dashboard</h1>
        <AuditControls isRunning={running} />
      </div>

      {stats ? (
        <StatsCards stats={stats} />
      ) : (
        <div className="text-gray-400">Loading stats...</div>
      )}

      {stats?.last_run && (
        <div className="bg-white rounded-lg shadow p-5">
          <h2 className="text-lg font-semibold text-gray-700 mb-3">Last Run</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div>
              <span className="text-gray-500">Run ID:</span>{' '}
              <span className="font-medium">#{stats.last_run.id}</span>
            </div>
            <div>
              <span className="text-gray-500">Posts:</span>{' '}
              <span className="font-medium">{stats.last_run.total_posts}</span>
            </div>
            <div>
              <span className="text-gray-500">Findings:</span>{' '}
              <span className="font-medium">{stats.last_run.total_findings}</span>
            </div>
            <div>
              <span className="text-gray-500">Started:</span>{' '}
              <span className="font-medium">
                {stats.last_run.started_at
                  ? new Date(stats.last_run.started_at * 1000).toLocaleString()
                  : '—'}
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
