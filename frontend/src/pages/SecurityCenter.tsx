import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import toast from "react-hot-toast";
import * as auditApi from "../api/audit";
import { extractErrorMessage } from "../api/client";
import * as securityApi from "../api/security";
import { AuditLogTable } from "../components/audit/AuditLogTable";
import { VerifyBanner } from "../components/audit/VerifyBanner";
import { Badge } from "../components/ui/Badge";
import { Card } from "../components/ui/Card";
import { PageSpinner } from "../components/ui/Spinner";
import type { AuditVerifyResponse } from "../types";
import { formatDateTime } from "../utils/format";

export function SecurityCenter() {
  const queryClient = useQueryClient();
  const [lastResult, setLastResult] = useState<AuditVerifyResponse | null>(null);
  const { data, isLoading } = useQuery({ queryKey: ["security-overview"], queryFn: securityApi.getSecurityOverview });

  const verifyMutation = useMutation({
    mutationFn: () => auditApi.verifyGlobalAudit(),
    onSuccess: (result) => {
      setLastResult(result);
      queryClient.invalidateQueries({ queryKey: ["security-overview"] });
      if (result.status === "COMPROMISED") {
        toast.error("Integrity compromised — see the affected record below.");
      } else {
        toast.success("Audit chain verified: VALID");
      }
    },
    onError: (err) => toast.error(extractErrorMessage(err)),
  });

  if (isLoading || !data) return <PageSpinner />;

  const displayResult =
    lastResult ??
    ({
      status: data.audit_chain_status,
      records_checked: data.total_audit_events,
      broken_links: data.integrity_violations,
      affected_record: null,
      affected_records: [],
      verified_at: data.last_verification_at ?? new Date().toISOString(),
      scope: "global_ledger",
    } as AuditVerifyResponse);

  return (
    <div>
      <h1 className="font-serif text-3xl text-ink">Security Center</h1>
      <p className="mt-1 text-sm text-ink-faint">
        Live status pulled straight from the backend verification service — never faked.
      </p>

      <div className="mt-6 grid grid-cols-2 gap-4 md:grid-cols-4">
        <Card>
          <div className="flex items-center gap-2">
            <span className={`h-2 w-2 rounded-full ${data.database_status === "CONNECTED" ? "bg-accent-green" : "bg-accent-red"}`} />
            <span className="text-sm text-ink">Database</span>
          </div>
          <div className="mt-2 font-serif text-lg text-ink">{data.database_status}</div>
        </Card>
        <Card>
          <div className="flex items-center gap-2">
            <span className={`h-2 w-2 rounded-full ${data.audit_chain_status === "VALID" ? "bg-accent-green" : "bg-accent-red"}`} />
            <span className="text-sm text-ink">Audit ledger</span>
          </div>
          <div className="mt-2 font-serif text-lg text-ink">{data.audit_chain_status === "VALID" ? "VERIFIED" : "COMPROMISED"}</div>
        </Card>
        <Card>
          <div className="text-sm text-ink">Audit events</div>
          <div className="mt-2 font-serif text-lg text-ink">{data.total_audit_events}</div>
        </Card>
        <Card>
          <div className="text-sm text-ink">Integrity violations</div>
          <div className={`mt-2 font-serif text-lg ${data.integrity_violations > 0 ? "text-accent-red" : "text-ink"}`}>
            {data.integrity_violations}
          </div>
        </Card>
      </div>

      <div className="mt-6">
        <VerifyBanner result={displayResult} isRunning={verifyMutation.isPending} onRun={() => verifyMutation.mutate()} />
      </div>

      <div className="mt-6 grid grid-cols-1 gap-4 md:grid-cols-2">
        <Card>
          <div className="text-xs uppercase text-ink-faint">Active users (24h)</div>
          <div className="mt-1 font-serif text-2xl text-ink">{data.active_users_24h}</div>
        </Card>
        <Card>
          <div className="text-xs uppercase text-ink-faint">Failed logins (24h)</div>
          <div className={`mt-1 font-serif text-2xl ${data.failed_logins_24h > 0 ? "text-accent-amber" : "text-ink"}`}>
            {data.failed_logins_24h}
          </div>
        </Card>
      </div>

      <div className="mt-8 grid grid-cols-1 gap-8 lg:grid-cols-2">
        <div>
          <h2 className="mb-3 font-serif text-lg text-ink">Your recent authentication activity</h2>
          <Card className="p-0">
            {data.recent_security_events.length === 0 ? (
              <div className="p-5 text-sm text-ink-faint">No security events recorded.</div>
            ) : (
              <ul className="divide-y divide-line">
                {data.recent_security_events.map((e) => (
                  <li key={e.id} className="px-5 py-3">
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-ink">{e.event_type.replace(/_/g, " ")}</span>
                      <Badge tone="amber">{e.ip_address ?? "unknown IP"}</Badge>
                    </div>
                    <div className="mt-0.5 text-xs text-ink-faint">{formatDateTime(e.created_at)}</div>
                  </li>
                ))}
              </ul>
            )}
          </Card>
        </div>

        <div>
          <h2 className="mb-3 font-serif text-lg text-ink">Recent audit events</h2>
          <AuditLogTable records={data.recent_audit_events} />
        </div>
      </div>
    </div>
  );
}
