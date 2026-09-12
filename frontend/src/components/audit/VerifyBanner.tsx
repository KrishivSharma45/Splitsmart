import type { AuditVerifyResponse } from "../../types";
import { formatDateTime } from "../../utils/format";

export function VerifyBanner({
  result,
  isRunning,
  onRun,
}: {
  result: AuditVerifyResponse | null | undefined;
  isRunning: boolean;
  onRun: () => void;
}) {
  const isValid = result?.status === "VALID";
  const isCompromised = result?.status === "COMPROMISED";

  return (
    <div
      className={`card flex flex-wrap items-center justify-between gap-4 border p-5 ${
        isCompromised ? "border-accent-red/40 bg-accent-red/5" : isValid ? "border-accent-green/30" : ""
      }`}
    >
      <div>
        <div className="flex items-center gap-2">
          <span className={`h-2 w-2 rounded-full ${isCompromised ? "bg-accent-red" : isValid ? "bg-accent-green" : "bg-ink-faint"}`} />
          <span className="font-serif text-lg text-ink">
            {isCompromised ? "INTEGRITY COMPROMISED" : isValid ? "INTEGRITY VERIFIED" : "Not verified yet"}
          </span>
        </div>
        {result ? (
          <p className="mt-1 text-xs text-ink-faint">
            {result.records_checked} records checked · {result.broken_links} broken link{result.broken_links === 1 ? "" : "s"}
            {isCompromised && result.affected_record !== null && ` · first affected record #${result.affected_record}`}
            {" · "}
            {formatDateTime(result.verified_at)}
          </p>
        ) : (
          <p className="mt-1 text-xs text-ink-faint">Run verification to walk the ledger from genesis and confirm every hash.</p>
        )}
      </div>
      <button onClick={onRun} disabled={isRunning} className="btn-secondary">
        {isRunning ? "Verifying…" : "Run verification"}
      </button>
    </div>
  );
}
