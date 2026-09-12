export function Spinner({ className = "" }: { className?: string }) {
  return (
    <div
      className={`h-4 w-4 animate-spin rounded-full border-2 border-ink/20 border-t-ink ${className}`}
      role="status"
      aria-label="Loading"
    />
  );
}

export function PageSpinner() {
  return (
    <div className="flex h-64 items-center justify-center">
      <Spinner className="h-6 w-6" />
    </div>
  );
}
