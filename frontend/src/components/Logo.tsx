export function Logo({ size = 28 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
      <rect width="24" height="24" rx="6" fill="#17160F" />
      <path
        d="M12 5l6 2.5v4c0 4-2.6 6.7-6 7.5-3.4-.8-6-3.5-6-7.5v-4z"
        stroke="#F2EEE6"
        strokeWidth="1.4"
        strokeLinejoin="round"
      />
    </svg>
  );
}

export function Wordmark({ className = "" }: { className?: string }) {
  return (
    <span className={`font-serif text-lg text-ink ${className}`}>
      SplitSmart<span className="text-ink-faint">.</span>
    </span>
  );
}
