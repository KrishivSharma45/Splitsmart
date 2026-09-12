import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import toast from "react-hot-toast";
import * as auditApi from "../../api/audit";
import { extractErrorMessage } from "../../api/client";
import type { AuditVerifyResponse, Trip } from "../../types";
import { AuditLogTable } from "../audit/AuditLogTable";
import { VerifyBanner } from "../audit/VerifyBanner";

export function TripAuditTab({ trip }: { trip: Trip }) {
  const queryClient = useQueryClient();
  const [lastResult, setLastResult] = useState<AuditVerifyResponse | null>(null);
  const { data: records, isLoading } = useQuery({
    queryKey: ["trip-audit", trip.id],
    queryFn: () => auditApi.listTripAuditLog(trip.id),
  });

  const verifyMutation = useMutation({
    mutationFn: () => auditApi.verifyTripAudit(trip.id),
    onSuccess: (result) => {
      queryClient.invalidateQueries({ queryKey: ["trip-audit", trip.id] });
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
      <p className="mb-4 text-xs text-ink-faint">
        Events for this trip, part of SplitSmart's single global ledger. Verification checks the entire ledger's
        integrity, not just this trip's events.
      </p>
      <div className="mb-6">
        <VerifyBanner result={lastResult} isRunning={verifyMutation.isPending} onRun={() => verifyMutation.mutate()} />
      </div>
      {isLoading ? null : <AuditLogTable records={records ?? []} />}
    </div>
  );
}
