export function StatTile({
  label,
  value,
  hint,
}: {
  label: string;
  value: React.ReactNode;
  hint?: React.ReactNode;
}) {
  return (
    <div>
      <div className="font-serif text-2xl text-ink">{value}</div>
      <div className="mt-1 text-xs uppercase tracking-wide text-ink-faint">{label}</div>
      {hint && <div className="mt-0.5 text-xs text-ink-soft">{hint}</div>}
    </div>
  );
}
