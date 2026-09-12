type Tone = "neutral" | "green" | "amber" | "red";

const DOT_COLOR: Record<Tone, string> = {
  neutral: "bg-ink-faint",
  green: "bg-accent-green",
  amber: "bg-accent-amber",
  red: "bg-accent-red",
};

export function Badge({ tone = "neutral", children }: { tone?: Tone; children: React.ReactNode }) {
  return (
    <span className="badge">
      <span className={`h-1.5 w-1.5 rounded-full ${DOT_COLOR[tone]}`} />
      {children}
    </span>
  );
}
