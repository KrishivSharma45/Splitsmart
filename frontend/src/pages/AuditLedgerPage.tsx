import { useMutation, useQuery } from "@tanstack/react-query";
import { useState } from "react";
import toast from "react-hot-toast";
import * as auditApi from "../api/audit";
import { extractErrorMessage } from "../api/client";
import { AuditLogTable } from "../components/audit/AuditLogTable";
import { VerifyBanner } from "../components/audit/VerifyBanner";
import { PageSpinner } from "../components/ui/Spinner";
import type { AuditVerifyResponse } from "../types";

const EVENT_TYPES = [
  "",
  "USER_REGISTERED",
  "USER_LOGIN",
  "USER_LOGOUT",
  "PASSWORD_CHANGED",
  "TRIP_CREATED",
  "TRIP_UPDATED",
  "TRIP_ARCHIVED",
  "MEMBER_ADDED",
  "MEMBER_REMOVED",
  "ROLE_CHANGED",
  "EXPENSE_CREATED",
  "EXPENSE_UPDATED",
  "EXPENSE_VOIDED",
  "SETTLEMENT_CREATED",
  "SETTLEMENT_CANCELLED",
  "REPORT_GENERATED",
  "AUDIT_VERIFICATION_RUN",
];

export function AuditLedgerPage() {
  const [eventType, setEventType] = useState("");
  const [lastResult, setLastResult] = useState<AuditVerifyResponse | null>(null);
  const { data: records, isLoading } = useQuery({
    queryKey: ["my-audit", eventType],
    queryFn: () => auditApi.listMyAuditLog(eventType || undefined),
  });

  const verifyMutation = useMutation({
    mutationFn: () => auditApi.verifyGlobalAudit(),
    onSuccess: (result) => {
      setLastResult(result);
      if (result.status === "COMPROMISED") {
        toast.error("Integrity compromised — see the affected record below.");
      } else {
        toast.success("Audit chain verified: VALID");
      }
    },
    onError: (err) => toast.error(extractErrorMessage(err)),
  });

  return (
    <div>
      <div className="mb-6 flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="font-serif text-3xl text-ink">Audit Ledger</h1>
          <p className="mt-1 text-sm text-ink-faint">
            Your account's events plus every trip you belong to — one cryptographically chained sequence.
          </p>
        </div>
        <select className="input w-auto" value={eventType} onChange={(e) => setEventType(e.target.value)}>
          {EVENT_TYPES.map((t) => (
            <option key={t} value={t}>
              {t || "All event types"}
            </option>
          ))}
        </select>
      </div>

      <div className="mb-6">
        <VerifyBanner result={lastResult} isRunning={verifyMutation.isPending} onRun={() => verifyMutation.mutate()} />
      </div>

      {isLoading ? <PageSpinner /> : <AuditLogTable records={records ?? []} />}
    </div>
  );
}
