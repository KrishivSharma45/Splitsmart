import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import toast from "react-hot-toast";
import { extractErrorMessage } from "../../api/client";
import * as tripsApi from "../../api/trips";
import type { TripRole } from "../../types";
import { Modal } from "../ui/Modal";

export function AddMemberModal({ open, onClose, tripId }: { open: boolean; onClose: () => void; tripId: number }) {
  const queryClient = useQueryClient();
  const [email, setEmail] = useState("");
  const [role, setRole] = useState<TripRole>("MEMBER");

  const mutation = useMutation({
    mutationFn: () => tripsApi.addMember(tripId, email, role),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["members", tripId] });
      queryClient.invalidateQueries({ queryKey: ["trip", tripId] });
      toast.success("Member added");
      setEmail("");
      onClose();
    },
    onError: (err) => toast.error(extractErrorMessage(err)),
  });

  return (
    <Modal open={open} onClose={onClose} title="Add member">
      <form
        onSubmit={(e) => {
          e.preventDefault();
          mutation.mutate();
        }}
        className="space-y-4"
      >
        <div>
          <label className="label">Email</label>
          <input
            required
            type="email"
            className="input"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="member@example.com"
          />
          <p className="mt-1 text-xs text-ink-faint">The person must already have a SplitSmart account.</p>
        </div>
        <div>
          <label className="label">Role</label>
          <select className="input" value={role} onChange={(e) => setRole(e.target.value as TripRole)}>
            <option value="MEMBER">Member</option>
            <option value="ADMIN">Admin</option>
          </select>
        </div>
        <button type="submit" disabled={mutation.isPending} className="btn-primary w-full">
          {mutation.isPending ? "Adding…" : "Add member"}
        </button>
      </form>
    </Modal>
  );
}
