import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import toast from "react-hot-toast";
import { extractErrorMessage } from "../../api/client";
import * as settlementsApi from "../../api/settlements";
import type { Trip, TripMember } from "../../types";
import { formatDate, formatMoney } from "../../utils/format";
import { isAtLeast } from "../../utils/role";
import { Badge } from "../ui/Badge";
import { Card } from "../ui/Card";
import { EmptyState } from "../ui/EmptyState";
import { PageSpinner } from "../ui/Spinner";
import { AddSettlementModal } from "./AddSettlementModal";

export function SettlementsTab({ trip, members, currentUserId }: { trip: Trip; members: TripMember[]; currentUserId: number }) {
  const [addOpen, setAddOpen] = useState(false);
  const queryClient = useQueryClient();
  const { data: settlements, isLoading } = useQuery({
    queryKey: ["settlements", trip.id],
    queryFn: () => settlementsApi.listSettlements(trip.id),
  });

  const cancelMutation = useMutation({
    mutationFn: (id: number) => settlementsApi.cancelSettlement(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["settlements", trip.id] });
      queryClient.invalidateQueries({ queryKey: ["balances", trip.id] });
      queryClient.invalidateQueries({ queryKey: ["debts", trip.id] });
      toast.success("Settlement cancelled");
    },
    onError: (err) => toast.error(extractErrorMessage(err)),
  });

  const canManage = isAtLeast(trip.my_role, "ADMIN");

  return (
    <div>
      <div className="mb-4 flex justify-end">
        <button onClick={() => setAddOpen(true)} className="btn-primary">
          Record settlement
        </button>
      </div>

      {isLoading ? (
        <PageSpinner />
      ) : !settlements || settlements.length === 0 ? (
        <EmptyState title="No settlements yet" description="Record a payment once someone settles up." />
      ) : (
        <Card className="p-0">
          <ul className="divide-y divide-line">
            {settlements.map((s) => (
              <li key={s.id} className="flex items-center justify-between gap-4 px-5 py-3.5">
                <div>
                  <div className="flex items-center gap-2 text-sm text-ink">
                    <span>{s.payer.full_name}</span>
                    <span className="text-ink-faint">→</span>
                    <span>{s.receiver.full_name}</span>
                    {s.status === "CANCELLED" && <Badge tone="red">Cancelled</Badge>}
                  </div>
                  <div className="mt-0.5 text-xs text-ink-faint">
                    {formatDate(s.date)}
                    {s.note ? ` · ${s.note}` : ""}
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <span className="mono text-sm text-ink-soft">{formatMoney(s.amount, s.currency)}</span>
                  {s.status === "COMPLETED" && (canManage || s.created_by === currentUserId) && (
                    <button
                      onClick={() => cancelMutation.mutate(s.id)}
                      disabled={cancelMutation.isPending}
                      className="text-xs text-accent-red hover:underline"
                    >
                      Cancel
                    </button>
                  )}
                </div>
              </li>
            ))}
          </ul>
        </Card>
      )}

      <AddSettlementModal
        open={addOpen}
        onClose={() => setAddOpen(false)}
        tripId={trip.id}
        currency={trip.currency}
        members={members}
        currentUserId={currentUserId}
      />
    </div>
  );
}
