import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import toast from "react-hot-toast";
import { extractErrorMessage } from "../../api/client";
import * as tripsApi from "../../api/trips";
import type { Trip, TripRole } from "../../types";
import { isAtLeast } from "../../utils/role";
import { Badge } from "../ui/Badge";
import { Card } from "../ui/Card";
import { PageSpinner } from "../ui/Spinner";
import { AddMemberModal } from "./AddMemberModal";

export function MembersTab({ trip, currentUserId }: { trip: Trip; currentUserId: number }) {
  const [addOpen, setAddOpen] = useState(false);
  const queryClient = useQueryClient();
  const { data: members, isLoading } = useQuery({
    queryKey: ["members", trip.id],
    queryFn: () => tripsApi.listMembers(trip.id),
  });

  const canManage = isAtLeast(trip.my_role, "ADMIN");
  const isOwner = trip.my_role === "OWNER";

  const removeMutation = useMutation({
    mutationFn: (userId: number) => tripsApi.removeMember(trip.id, userId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["members", trip.id] });
      queryClient.invalidateQueries({ queryKey: ["balances", trip.id] });
      toast.success("Member removed");
    },
    onError: (err) => toast.error(extractErrorMessage(err)),
  });

  const roleMutation = useMutation({
    mutationFn: ({ userId, role }: { userId: number; role: TripRole }) => tripsApi.changeMemberRole(trip.id, userId, role),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["members", trip.id] });
      toast.success("Role updated");
    },
    onError: (err) => toast.error(extractErrorMessage(err)),
  });

  if (isLoading) return <PageSpinner />;

  return (
    <div>
      <div className="mb-4 flex justify-end">
        {canManage && (
          <button onClick={() => setAddOpen(true)} className="btn-primary">
            Add member
          </button>
        )}
      </div>

      <Card className="p-0">
        <ul className="divide-y divide-line">
          {members?.map((m) => (
            <li key={m.id} className="flex items-center justify-between gap-4 px-5 py-3.5">
              <div className="flex items-center gap-3">
                <div className="flex h-8 w-8 items-center justify-center rounded-full bg-ink text-xs font-medium text-cream-soft">
                  {m.user.full_name.charAt(0).toUpperCase()}
                </div>
                <div>
                  <div className="text-sm text-ink">
                    {m.user.full_name} {m.user.id === currentUserId && <span className="text-ink-faint">(you)</span>}
                  </div>
                  <div className="text-xs text-ink-faint">{m.user.email}</div>
                </div>
              </div>
              <div className="flex items-center gap-3">
                {canManage && !(m.role === "OWNER" && !isOwner) ? (
                  <select
                    className="input w-auto py-1 text-xs"
                    value={m.role}
                    onChange={(e) => roleMutation.mutate({ userId: m.user.id, role: e.target.value as TripRole })}
                    disabled={roleMutation.isPending || (m.role === "OWNER" && !isOwner)}
                  >
                    <option value="MEMBER">Member</option>
                    <option value="ADMIN">Admin</option>
                    {isOwner && <option value="OWNER">Owner</option>}
                  </select>
                ) : (
                  <Badge tone={m.role === "OWNER" ? "amber" : "neutral"}>{m.role}</Badge>
                )}
                {(canManage || m.user.id === currentUserId) && (
                  <button
                    onClick={() => removeMutation.mutate(m.user.id)}
                    disabled={removeMutation.isPending}
                    className="text-xs text-accent-red hover:underline"
                  >
                    {m.user.id === currentUserId ? "Leave" : "Remove"}
                  </button>
                )}
              </div>
            </li>
          ))}
        </ul>
      </Card>

      <AddMemberModal open={addOpen} onClose={() => setAddOpen(false)} tripId={trip.id} />
    </div>
  );
}
