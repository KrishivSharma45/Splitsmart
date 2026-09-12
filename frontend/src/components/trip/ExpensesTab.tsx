import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { Link } from "react-router-dom";
import * as expensesApi from "../../api/expenses";
import type { ExpenseCategory, ExpenseStatus, Trip, TripMember } from "../../types";
import { Badge } from "../ui/Badge";
import { Card } from "../ui/Card";
import { EmptyState } from "../ui/EmptyState";
import { Spinner } from "../ui/Spinner";
import { categoryLabel, formatDate, formatMoney } from "../../utils/format";
import { AddExpenseModal } from "../expense/AddExpenseModal";

const CATEGORIES: ExpenseCategory[] = ["FOOD", "TRANSPORT", "ACCOMMODATION", "SHOPPING", "ENTERTAINMENT", "BILLS", "OTHER"];

export function ExpensesTab({ trip, members, currentUserId }: { trip: Trip; members: TripMember[]; currentUserId: number }) {
  const [addOpen, setAddOpen] = useState(false);
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState<ExpenseCategory | "">("");
  const [status, setStatus] = useState<ExpenseStatus>("ACTIVE");
  const [sortBy, setSortBy] = useState<"date" | "amount" | "category">("date");
  const [sortDir, setSortDir] = useState<"asc" | "desc">("desc");

  const { data: expenses, isLoading } = useQuery({
    queryKey: ["expenses", trip.id, { search, category, status, sortBy, sortDir }],
    queryFn: () =>
      expensesApi.listExpenses(trip.id, {
        search: search || undefined,
        category: category || undefined,
        status,
        sort_by: sortBy,
        sort_dir: sortDir,
      }),
  });

  return (
    <div>
      <div className="mb-4 flex flex-wrap items-center gap-2">
        <input
          className="input max-w-xs"
          placeholder="Search expenses…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        <select className="input w-auto" value={category} onChange={(e) => setCategory(e.target.value as ExpenseCategory | "")}>
          <option value="">All categories</option>
          {CATEGORIES.map((c) => (
            <option key={c} value={c}>
              {categoryLabel(c)}
            </option>
          ))}
        </select>
        <select className="input w-auto" value={status} onChange={(e) => setStatus(e.target.value as ExpenseStatus)}>
          <option value="ACTIVE">Active</option>
          <option value="VOIDED">Voided</option>
        </select>
        <select
          className="input w-auto"
          value={`${sortBy}:${sortDir}`}
          onChange={(e) => {
            const [by, dir] = e.target.value.split(":");
            setSortBy(by as typeof sortBy);
            setSortDir(dir as typeof sortDir);
          }}
        >
          <option value="date:desc">Newest first</option>
          <option value="date:asc">Oldest first</option>
          <option value="amount:desc">Amount: high to low</option>
          <option value="amount:asc">Amount: low to high</option>
          <option value="category:asc">Category</option>
        </select>
        <button onClick={() => setAddOpen(true)} className="btn-primary ml-auto">
          Add expense
        </button>
      </div>

      {isLoading ? (
        <div className="flex justify-center py-10">
          <Spinner />
        </div>
      ) : !expenses || expenses.length === 0 ? (
        <EmptyState title="No expenses found" description="Try adjusting your filters, or add the first expense." />
      ) : (
        <Card className="p-0">
          <ul className="divide-y divide-line">
            {expenses.map((e) => (
              <li key={e.id}>
                <Link
                  to={`/trips/${trip.id}/expenses/${e.id}`}
                  className="flex items-center justify-between gap-4 px-5 py-3.5 transition hover:bg-ink/5"
                >
                  <div className="min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="truncate text-sm text-ink">{e.description}</span>
                      {e.status === "VOIDED" && <Badge tone="red">VOIDED</Badge>}
                      {e.has_receipt && <Badge tone="neutral">Receipt</Badge>}
                    </div>
                    <div className="mt-0.5 text-xs text-ink-faint">
                      {formatDate(e.date)} · Paid by {e.paid_by.full_name} · {categoryLabel(e.category)} · {e.split_method}
                    </div>
                  </div>
                  <div className="mono shrink-0 text-ink-soft">{formatMoney(e.amount, e.currency)}</div>
                </Link>
              </li>
            ))}
          </ul>
        </Card>
      )}

      <AddExpenseModal
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
