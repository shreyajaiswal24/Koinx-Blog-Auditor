import type { Stats } from '../api/client';

interface CardProps {
  label: string;
  value: number;
  color: string;
}

function Card({ label, value, color }: CardProps) {
  return (
    <div className={`rounded-lg p-4 shadow ${color}`}>
      <div className="text-sm font-medium opacity-80">{label}</div>
      <div className="text-3xl font-bold mt-1">{value}</div>
    </div>
  );
}

export default function StatsCards({ stats }: { stats: Stats }) {
  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
      <Card label="Total Findings" value={stats.total_findings} color="bg-white text-gray-800" />
      <Card label="High Priority" value={stats.high} color="bg-red-50 text-red-700" />
      <Card label="Medium Priority" value={stats.medium} color="bg-amber-50 text-amber-700" />
      <Card label="Low Priority" value={stats.low} color="bg-green-50 text-green-700" />
      <Card label="New" value={stats.new} color="bg-yellow-50 text-yellow-700" />
      <Card label="Recurring" value={stats.previously_identified} color="bg-sky-50 text-sky-700" />
      <Card label="Resolved" value={stats.resolved} color="bg-emerald-50 text-emerald-700" />
      <Card label="Total Runs" value={stats.total_runs} color="bg-purple-50 text-purple-700" />
    </div>
  );
}
