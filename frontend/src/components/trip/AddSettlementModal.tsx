import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import toast from "react-hot-toast";
import { extractErrorMessage } from "../../api/client";
import * as settlementsApi from "../../api/settlements";
import type { TripMember } from "../../types";
import { Modal } from "../ui/Modal";

export function AddSettlementModal({
  open,
  onClose,
  tripId,
  currency,
  members,
  currentUserId,
}: {
  open: boolean;
  onClose: () => void;
  tripId: number;
  currency: string;
  members: TripMember[];
  currentUserId: number;
}) {
  const queryClient = useQueryClient();
  const active = members.filter((m) => m.status === "ACTIVE");
  const [payerId, setPayerId] = useState(currentUserId);
  const [receiverId, setReceiverId] = useState(() => active.find((m) => m.user.id !== currentUserId)?.user.id ?? currentUserId);
  const [amount, setAmount] = useState("");
  const [date, setDate] = useState(() => new Date().toISOString().slice(0, 10));
  const [note, setNote] = useState("");

  const mutation = useMutation({
    mutationFn: () =>
      settlementsApi.createSettlement(tripId, {
        payer_id: payerId,
        receiver_id: receiverId,
        amount,
        currency,
        date,
        note: note || undefined,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["settlements", tripId] });
      queryClient.invalidateQueries({ queryKey: ["balances", tripId] });
      queryClient.invalidateQueries({ queryKey: ["debts", tripId] });
      queryClient.invalidateQueries({ queryKey: ["trips"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      toast.success("Settlement recorded");
      setAmount("");
      setNote("");
      onClose();
    },
    onError: (err) => toast.error(extractErrorMessage(err)),
  });

  return (
    <Modal open={open} onClose={onClose} title="Record settlement">
      <form
        onSubmit={(e) => {
          e.preventDefault();
          if (payerId === receiverId) {
            toast.error("Payer and receiver must be different");
            return;
          }
          mutation.mutate();
        }}
        className="space-y-4"
      >
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="label">From (payer)</label>
            <select className="input" value={payerId} onChange={(e) => setPayerId(parseInt(e.target.value, 10))}>
              {active.map((m) => (
                <option key={m.user.id} value={m.user.id}>
                  {m.user.full_name}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="label">To (receiver)</label>
            <select className="input" value={receiverId} onChange={(e) => setReceiverId(parseInt(e.target.value, 10))}>
              {active.map((m) => (
                <option key={m.user.id} value={m.user.id}>
                  {m.user.full_name}
                </option>
              ))}
            </select>
          </div>
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="label">Amount ({currency})</label>
            <input required type="number" step="0.01" min="0.01" className="input" value={amount} onChange={(e) => setAmount(e.target.value)} />
          </div>
          <div>
            <label className="label">Date</label>
            <input required type="date" className="input" value={date} onChange={(e) => setDate(e.target.value)} />
          </div>
        </div>
        <div>
          <label className="label">Note (optional)</label>
          <input className="input" value={note} onChange={(e) => setNote(e.target.value)} />
        </div>
        <button type="submit" disabled={mutation.isPending} className="btn-primary w-full">
          {mutation.isPending ? "Saving…" : "Record settlement"}
        </button>
      </form>
    </Modal>
  );
}
