import type { AuditLog } from "../../types";
import { formatDateTime } from "../../utils/format";
import { Card } from "../ui/Card";
import { EmptyState } from "../ui/EmptyState";
import { HashText } from "../ui/HashText";

export function AuditLogTable({ records }: { records: AuditLog[] }) {
  if (records.length === 0) {
    return <EmptyState title="No audit events yet" description="Actions you take will appear here, chained and hashed." />;
  }

  return (
    <Card className="overflow-x-auto p-0">
      <table className="w-full min-w-[720px] text-left text-sm">
        <thead>
          <tr className="border-b border-line text-xs uppercase tracking-wide text-ink-faint">
            <th className="px-5 py-3 font-medium">Event</th>
            <th className="px-5 py-3 font-medium">Actor</th>
            <th className="px-5 py-3 font-medium">Entity</th>
            <th className="px-5 py-3 font-medium">Timestamp</th>
            <th className="px-5 py-3 font-medium">Hash</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-line">
          {records.map((r) => (
            <tr key={r.id}>
              <td className="px-5 py-3 text-ink">{r.event_type}</td>
              <td className="px-5 py-3 text-ink-soft">{r.actor?.full_name ?? "—"}</td>
              <td className="px-5 py-3 text-ink-soft">
                {r.entity_type}
                {r.entity_id ? ` #${r.entity_id}` : ""}
              </td>
              <td className="px-5 py-3 text-ink-soft">{formatDateTime(r.timestamp)}</td>
              <td className="px-5 py-3">
                <HashText hash={r.current_hash} />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </Card>
  );
}
