const colors: Record<string, string> = {
  high: 'bg-red-500 text-white',
  medium: 'bg-amber-400 text-black',
  low: 'bg-green-500 text-white',
};

export default function PriorityBadge({ priority }: { priority: string }) {
  return (
    <span className={`inline-block px-2 py-0.5 rounded text-xs font-semibold uppercase ${colors[priority] ?? 'bg-gray-300 text-black'}`}>
      {priority}
    </span>
  );
}
