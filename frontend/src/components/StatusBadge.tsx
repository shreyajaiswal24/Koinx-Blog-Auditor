const colors: Record<string, string> = {
  new: 'bg-yellow-400 text-black',
  previously_identified: 'bg-sky-300 text-black',
  resolved: 'bg-green-300 text-black',
  completed: 'bg-green-500 text-white',
  ignored: 'bg-gray-400 text-white',
};

const labels: Record<string, string> = {
  new: 'New',
  previously_identified: 'Recurring',
  resolved: 'Resolved',
  completed: 'Completed',
  ignored: 'Ignored',
};

export default function StatusBadge({ status }: { status: string }) {
  return (
    <span className={`inline-block px-2 py-0.5 rounded text-xs font-semibold ${colors[status] ?? 'bg-gray-300 text-black'}`}>
      {labels[status] ?? status}
    </span>
  );
}
