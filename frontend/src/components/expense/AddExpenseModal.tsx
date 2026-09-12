import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import toast from "react-hot-toast";
import { extractErrorMessage } from "../../api/client";
import * as expensesApi from "../../api/expenses";
import type { ExpenseCategory, SplitMethod, TripMember } from "../../types";
import { Modal } from "../ui/Modal";
import { buildParticipants, initialSplitRows, SplitEditor, type SplitRow } from "./SplitEditor";

const CATEGORIES: ExpenseCategory[] = ["FOOD", "TRANSPORT", "ACCOMMODATION", "SHOPPING", "ENTERTAINMENT", "BILLS", "OTHER"];
const SPLIT_METHODS: { value: SplitMethod; label: string }[] = [
  { value: "EQUAL", label: "Equal" },
  { value: "EXACT", label: "Exact amounts" },
  { value: "PERCENTAGE", label: "Percentage" },
  { value: "SHARES", label: "Shares" },
];

export function AddExpenseModal({
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
  const [description, setDescription] = useState("");
  const [amount, setAmount] = useState("");
  const [paidBy, setPaidBy] = useState(currentUserId);
  const [category, setCategory] = useState<ExpenseCategory>("FOOD");
  const [splitMethod, setSplitMethod] = useState<SplitMethod>("EQUAL");
  const [date, setDate] = useState(() => new Date().toISOString().slice(0, 10));
  const [notes, setNotes] = useState("");
  const [rows, setRows] = useState<SplitRow[]>(() => initialSplitRows(members));

  useEffect(() => {
    if (open) {
      setRows(initialSplitRows(members));
      setPaidBy(currentUserId);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open]);

  const mutation = useMutation({
    mutationFn: () =>
      expensesApi.createExpense(tripId, {
        description,
        amount,
        currency,
        paid_by: paidBy,
        category,
        split_method: splitMethod,
        date,
        notes: notes || undefined,
        participants: buildParticipants(rows, splitMethod),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["expenses", tripId] });
      queryClient.invalidateQueries({ queryKey: ["balances", tripId] });
      queryClient.invalidateQueries({ queryKey: ["debts", tripId] });
      queryClient.invalidateQueries({ queryKey: ["trips"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      toast.success("Expense recorded");
      resetAndClose();
    },
    onError: (err) => toast.error(extractErrorMessage(err)),
  });

  function resetAndClose() {
    setDescription("");
    setAmount("");
    setNotes("");
    onClose();
  }

  return (
    <Modal open={open} onClose={resetAndClose} title="Add expense" width="max-w-lg">
      <form
        onSubmit={(e) => {
          e.preventDefault();
          mutation.mutate();
        }}
        className="space-y-4"
      >
        <div>
          <label className="label">Description</label>
          <input required className="input" value={description} onChange={(e) => setDescription(e.target.value)} placeholder="Hotel" />
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

        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="label">Paid by</label>
            <select className="input" value={paidBy} onChange={(e) => setPaidBy(parseInt(e.target.value, 10))}>
              {members
                .filter((m) => m.status === "ACTIVE")
                .map((m) => (
                  <option key={m.user.id} value={m.user.id}>
                    {m.user.full_name}
                  </option>
                ))}
            </select>
          </div>
          <div>
            <label className="label">Category</label>
            <select className="input" value={category} onChange={(e) => setCategory(e.target.value as ExpenseCategory)}>
              {CATEGORIES.map((c) => (
                <option key={c} value={c}>
                  {c.charAt(0) + c.slice(1).toLowerCase()}
                </option>
              ))}
            </select>
          </div>
        </div>

        <div>
          <label className="label">Split method</label>
          <div className="flex gap-2">
            {SPLIT_METHODS.map((m) => (
              <button
                type="button"
                key={m.value}
                onClick={() => setSplitMethod(m.value)}
                className={`rounded-full border px-3 py-1.5 text-xs font-medium transition ${
                  splitMethod === m.value ? "border-ink bg-ink text-cream-soft" : "border-line text-ink-soft hover:bg-ink/5"
                }`}
              >
                {m.label}
              </button>
            ))}
          </div>
        </div>

        <div>
          <label className="label">Split between</label>
          <SplitEditor members={members} method={splitMethod} amount={amount} currency={currency} rows={rows} onChange={setRows} />
        </div>

        <div>
          <label className="label">Notes (optional)</label>
          <textarea className="input" rows={2} value={notes} onChange={(e) => setNotes(e.target.value)} />
        </div>

        <button type="submit" disabled={mutation.isPending} className="btn-primary w-full">
          {mutation.isPending ? "Saving…" : "Add expense"}
        </button>
      </form>
    </Modal>
  );
}
