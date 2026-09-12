import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useRef, useState } from "react";
import toast from "react-hot-toast";
import { Link, useParams } from "react-router-dom";
import * as auditApi from "../api/audit";
import { extractErrorMessage } from "../api/client";
import * as expensesApi from "../api/expenses";
import * as tripsApi from "../api/trips";
import { AuditLogTable } from "../components/audit/AuditLogTable";
import { EditExpenseModal } from "../components/expense/EditExpenseModal";
import { Badge } from "../components/ui/Badge";
import { Card } from "../components/ui/Card";
import { PageSpinner } from "../components/ui/Spinner";
import { useAuth } from "../context/AuthContext";
import { categoryLabel, formatDate, formatDateTime, formatMoney } from "../utils/format";
import { isAtLeast } from "../utils/role";

export function ExpenseDetail() {
  const { tripId, expenseId } = useParams();
  const id = parseInt(expenseId ?? "0", 10);
  const tid = parseInt(tripId ?? "0", 10);
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [editOpen, setEditOpen] = useState(false);

  const { data: expense, isLoading } = useQuery({ queryKey: ["expense", id], queryFn: () => expensesApi.getExpense(id), enabled: !!id });
  const { data: trip } = useQuery({ queryKey: ["trip", tid], queryFn: () => tripsApi.getTrip(tid), enabled: !!tid });
  const { data: members } = useQuery({ queryKey: ["members", tid], queryFn: () => tripsApi.listMembers(tid), enabled: !!tid });
  const { data: auditRecords } = useQuery({
    queryKey: ["trip-audit", tid],
    queryFn: () => auditApi.listTripAuditLog(tid),
    enabled: !!tid,
  });

  const voidMutation = useMutation({
    mutationFn: (reason: string) => expensesApi.voidExpense(id, reason),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["expense", id] });
      queryClient.invalidateQueries({ queryKey: ["expenses", tid] });
      queryClient.invalidateQueries({ queryKey: ["balances", tid] });
      queryClient.invalidateQueries({ queryKey: ["debts", tid] });
      toast.success("Expense voided");
    },
    onError: (err) => toast.error(extractErrorMessage(err)),
  });

  const uploadMutation = useMutation({
    mutationFn: (file: File) => expensesApi.uploadReceipt(id, file),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["expense", id] });
      toast.success("Receipt attached");
    },
    onError: (err) => toast.error(extractErrorMessage(err)),
  });

  if (isLoading || !expense || !trip || !members || !user) return <PageSpinner />;

  const canManage = isAtLeast(trip.my_role, "ADMIN") || expense.created_by === user.id;
  const expenseEvents = (auditRecords ?? []).filter((r) => r.entity_type === "expense" && r.entity_id === String(id));

  return (
    <div className="mx-auto max-w-3xl">
      <div className="mb-4 flex items-center gap-2 text-sm text-ink-faint">
        <Link to={`/trips/${tid}`} className="hover:text-ink">
          {trip.name}
        </Link>
        <span>/</span>
        <span className="text-ink">Expense</span>
      </div>

      <Card>
        <div className="flex items-start justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <h1 className="font-serif text-2xl text-ink">{expense.description}</h1>
              {expense.status === "VOIDED" && <Badge tone="red">VOIDED</Badge>}
            </div>
            <div className="mt-1 text-sm text-ink-faint">
              {formatDate(expense.date)} · {categoryLabel(expense.category)} · {expense.split_method} split
            </div>
          </div>
          <div className="mono text-2xl text-ink">{formatMoney(expense.amount, expense.currency)}</div>
        </div>

        {expense.status === "VOIDED" && expense.void_reason && (
          <div className="mt-3 rounded-lg bg-accent-red/5 px-3 py-2 text-xs text-accent-red">
            Voided: {expense.void_reason}
          </div>
        )}

        <div className="mt-4 grid grid-cols-2 gap-4 border-t border-line pt-4 text-sm">
          <div>
            <div className="text-xs uppercase text-ink-faint">Paid by</div>
            <div className="mt-0.5 text-ink">{expense.paid_by.full_name}</div>
          </div>
          <div>
            <div className="text-xs uppercase text-ink-faint">Created</div>
            <div className="mt-0.5 text-ink">{formatDateTime(expense.created_at)}</div>
          </div>
        </div>

        {expense.notes && (
          <div className="mt-4 border-t border-line pt-4">
            <div className="text-xs uppercase text-ink-faint">Notes</div>
            <p className="mt-1 text-sm text-ink-soft">{expense.notes}</p>
          </div>
        )}

        <div className="mt-4 border-t border-line pt-4">
          <div className="mb-2 text-xs uppercase text-ink-faint">Split breakdown</div>
          <ul className="space-y-1.5">
            {expense.splits.map((s) => (
              <li key={s.id} className="flex items-center justify-between text-sm">
                <span className="text-ink-soft">
                  {s.user.full_name}
                  {s.percentage && <span className="text-ink-faint"> · {s.percentage}%</span>}
                  {s.shares && <span className="text-ink-faint"> · {s.shares} share{s.shares === 1 ? "" : "s"}</span>}
                </span>
                <span className="mono text-ink-soft">{formatMoney(s.share_amount, expense.currency)}</span>
              </li>
            ))}
          </ul>
        </div>

        <div className="mt-4 flex flex-wrap items-center gap-3 border-t border-line pt-4">
          {expense.has_receipt ? (
            <button onClick={() => expensesApi.downloadReceipt(id)} className="btn-secondary">
              Download receipt
            </button>
          ) : (
            <>
              <input
                ref={fileInputRef}
                type="file"
                accept="image/png,image/jpeg,image/webp,application/pdf"
                className="hidden"
                onChange={(e) => {
                  const file = e.target.files?.[0];
                  if (file) uploadMutation.mutate(file);
                }}
              />
              <button onClick={() => fileInputRef.current?.click()} disabled={uploadMutation.isPending} className="btn-secondary">
                {uploadMutation.isPending ? "Uploading…" : "Attach receipt"}
              </button>
            </>
          )}

          {expense.status === "ACTIVE" && canManage && (
            <>
              <button onClick={() => setEditOpen(true)} className="btn-secondary">
                Edit
              </button>
              <button
                onClick={() => {
                  const reason = prompt("Reason for voiding this expense (optional):") ?? "";
                  voidMutation.mutate(reason);
                }}
                disabled={voidMutation.isPending}
                className="btn-danger"
              >
                Void expense
              </button>
            </>
          )}
        </div>
      </Card>

      <div className="mt-8">
        <h2 className="mb-3 font-serif text-lg text-ink">History for this expense</h2>
        <AuditLogTable records={expenseEvents} />
      </div>

      <EditExpenseModal open={editOpen} onClose={() => setEditOpen(false)} expense={expense} members={members} />
    </div>
  );
}
