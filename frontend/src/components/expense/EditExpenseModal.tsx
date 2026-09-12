import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import toast from "react-hot-toast";
import { extractErrorMessage } from "../../api/client";
import * as expensesApi from "../../api/expenses";
import type { Expense, ExpenseCategory, SplitMethod, TripMember } from "../../types";
import { Modal } from "../ui/Modal";
import { buildParticipants, rowsFromExpense, SplitEditor, type SplitRow } from "./SplitEditor";

const CATEGORIES: ExpenseCategory[] = ["FOOD", "TRANSPORT", "ACCOMMODATION", "SHOPPING", "ENTERTAINMENT", "BILLS", "OTHER"];
const SPLIT_METHODS: { value: SplitMethod; label: string }[] = [
  { value: "EQUAL", label: "Equal" },
  { value: "EXACT", label: "Exact amounts" },
  { value: "PERCENTAGE", label: "Percentage" },
  { value: "SHARES", label: "Shares" },
];

export function EditExpenseModal({
  open,
  onClose,
  expense,
  members,
}: {
  open: boolean;
  onClose: () => void;
  expense: Expense;
  members: TripMember[];
}) {
  const queryClient = useQueryClient();
  const [description, setDescription] = useState(expense.description);
  const [amount, setAmount] = useState(expense.amount);
  const [paidBy, setPaidBy] = useState(expense.paid_by.id);
  const [category, setCategory] = useState<ExpenseCategory>(expense.category);
  const [splitMethod, setSplitMethod] = useState<SplitMethod>(expense.split_method);
  const [date, setDate] = useState(expense.date);
  const [notes, setNotes] = useState(expense.notes ?? "");
  const [rows, setRows] = useState<SplitRow[]>(() => rowsFromExpense(expense, members));
  const [splitTouched, setSplitTouched] = useState(false);

  useEffect(() => {
    if (open) {
      setDescription(expense.description);
      setAmount(expense.amount);
      setPaidBy(expense.paid_by.id);
      setCategory(expense.category);
      setSplitMethod(expense.split_method);
      setDate(expense.date);
      setNotes(expense.notes ?? "");
      setRows(rowsFromExpense(expense, members));
      setSplitTouched(false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open, expense.id]);

  const mutation = useMutation({
    mutationFn: () =>
      expensesApi.updateExpense(expense.id, {
        description,
        amount,
        paid_by: paidBy,
        category,
        split_method: splitMethod,
        date,
        notes: notes || undefined,
        participants: buildParticipants(rows, splitMethod),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["expense", expense.id] });
      queryClient.invalidateQueries({ queryKey: ["expenses", expense.trip_id] });
      queryClient.invalidateQueries({ queryKey: ["balances", expense.trip_id] });
      queryClient.invalidateQueries({ queryKey: ["debts", expense.trip_id] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      toast.success("Expense updated");
      onClose();
    },
    onError: (err) => toast.error(extractErrorMessage(err)),
  });

  return (
    <Modal open={open} onClose={onClose} title="Edit expense" width="max-w-lg">
      <form
        onSubmit={(e) => {
          e.preventDefault();
          mutation.mutate();
        }}
        className="space-y-4"
      >
        <div>
          <label className="label">Description</label>
          <input required className="input" value={description} onChange={(e) => setDescription(e.target.value)} />
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="label">Amount ({expense.currency})</label>
            <input
              required
              type="number"
              step="0.01"
              min="0.01"
              className="input"
              value={amount}
              onChange={(e) => {
                setAmount(e.target.value);
                setSplitTouched(true);
              }}
            />
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
                onClick={() => {
                  setSplitMethod(m.value);
                  setSplitTouched(true);
                }}
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
          <SplitEditor
            members={members}
            method={splitMethod}
            amount={amount}
            currency={expense.currency}
            rows={rows}
            onChange={(r) => {
              setRows(r);
              setSplitTouched(true);
            }}
          />
          {!splitTouched && <p className="mt-2 text-xs text-ink-faint">Existing splits shown. Change the amount, method, or any share to recompute.</p>}
        </div>

        <div>
          <label className="label">Notes (optional)</label>
          <textarea className="input" rows={2} value={notes} onChange={(e) => setNotes(e.target.value)} />
        </div>

        <button type="submit" disabled={mutation.isPending} className="btn-primary w-full">
          {mutation.isPending ? "Saving…" : "Save changes"}
        </button>
      </form>
    </Modal>
  );
}
