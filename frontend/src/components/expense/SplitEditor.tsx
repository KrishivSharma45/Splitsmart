import { useMemo } from "react";
import type { Expense, ExpenseParticipantInput, SplitMethod, TripMember } from "../../types";
import { formatMoney } from "../../utils/format";

export interface SplitRow {
  user_id: number;
  selected: boolean;
  amount: string;
  percentage: string;
  shares: string;
}

export function initialSplitRows(members: TripMember[]): SplitRow[] {
  return members
    .filter((m) => m.status === "ACTIVE")
    .map((m) => ({ user_id: m.user.id, selected: true, amount: "", percentage: "", shares: "1" }));
}

export function rowsFromExpense(expense: Expense, members: TripMember[]): SplitRow[] {
  const splitByUser = new Map(expense.splits.map((s) => [s.user.id, s]));
  return members
    .filter((m) => m.status === "ACTIVE")
    .map((m) => {
      const split = splitByUser.get(m.user.id);
      return {
        user_id: m.user.id,
        selected: !!split,
        amount: split ? split.share_amount : "",
        percentage: split?.percentage ?? "",
        shares: split?.shares ? String(split.shares) : "1",
      };
    });
}

export function buildParticipants(rows: SplitRow[], method: SplitMethod): ExpenseParticipantInput[] {
  return rows
    .filter((r) => r.selected)
    .map((r) => {
      const p: ExpenseParticipantInput = { user_id: r.user_id };
      if (method === "EXACT") p.amount = r.amount || "0";
      if (method === "PERCENTAGE") p.percentage = r.percentage || "0";
      if (method === "SHARES") p.shares = parseInt(r.shares || "0", 10);
      return p;
    });
}

export function SplitEditor({
  members,
  method,
  amount,
  currency,
  rows,
  onChange,
}: {
  members: TripMember[];
  method: SplitMethod;
  amount: string;
  currency: string;
  rows: SplitRow[];
  onChange: (rows: SplitRow[]) => void;
}) {
  const activeMembers = members.filter((m) => m.status === "ACTIVE");
  const total = parseFloat(amount || "0");

  function updateRow(userId: number, patch: Partial<SplitRow>) {
    onChange(rows.map((r) => (r.user_id === userId ? { ...r, ...patch } : r)));
  }

  const selectedRows = rows.filter((r) => r.selected);

  const equalShare = useMemo(() => {
    if (method !== "EQUAL" || selectedRows.length === 0) return 0;
    return total / selectedRows.length;
  }, [method, selectedRows.length, total]);

  const exactSum = useMemo(
    () => (method === "EXACT" ? selectedRows.reduce((s, r) => s + (parseFloat(r.amount) || 0), 0) : 0),
    [method, selectedRows],
  );
  const percentageSum = useMemo(
    () => (method === "PERCENTAGE" ? selectedRows.reduce((s, r) => s + (parseFloat(r.percentage) || 0), 0) : 0),
    [method, selectedRows],
  );
  const sharesSum = useMemo(
    () => (method === "SHARES" ? selectedRows.reduce((s, r) => s + (parseInt(r.shares, 10) || 0), 0) : 0),
    [method, selectedRows],
  );

  return (
    <div>
      <div className="max-h-56 space-y-2 overflow-y-auto rounded-lg border border-line p-2">
        {activeMembers.map((m) => {
          const row = rows.find((r) => r.user_id === m.user.id);
          if (!row) return null;
          return (
            <div key={m.user.id} className="flex items-center gap-3 rounded-lg px-1.5 py-1.5">
              <input
                type="checkbox"
                checked={row.selected}
                onChange={(e) => updateRow(m.user.id, { selected: e.target.checked })}
                className="h-4 w-4 rounded border-line"
              />
              <span className="flex-1 truncate text-sm text-ink">{m.user.full_name}</span>

              {row.selected && method === "EQUAL" && (
                <span className="mono text-xs text-ink-faint">{formatMoney(equalShare, currency)}</span>
              )}
              {row.selected && method === "EXACT" && (
                <input
                  type="number"
                  step="0.01"
                  min="0"
                  className="input w-28 py-1 text-right"
                  value={row.amount}
                  onChange={(e) => updateRow(m.user.id, { amount: e.target.value })}
                  placeholder="0.00"
                />
              )}
              {row.selected && method === "PERCENTAGE" && (
                <input
                  type="number"
                  step="0.01"
                  min="0"
                  max="100"
                  className="input w-24 py-1 text-right"
                  value={row.percentage}
                  onChange={(e) => updateRow(m.user.id, { percentage: e.target.value })}
                  placeholder="0"
                />
              )}
              {row.selected && method === "SHARES" && (
                <input
                  type="number"
                  step="1"
                  min="0"
                  className="input w-20 py-1 text-right"
                  value={row.shares}
                  onChange={(e) => updateRow(m.user.id, { shares: e.target.value })}
                />
              )}
            </div>
          );
        })}
      </div>

      <div className="mt-2 flex items-center justify-between text-xs">
        <span className="text-ink-faint">{selectedRows.length} participant{selectedRows.length === 1 ? "" : "s"} selected</span>
        {method === "EXACT" && (
          <span className={Math.abs(exactSum - total) < 0.01 ? "text-accent-green" : "text-accent-red"}>
            {formatMoney(exactSum, currency)} / {formatMoney(total, currency)}
          </span>
        )}
        {method === "PERCENTAGE" && (
          <span className={Math.abs(percentageSum - 100) < 0.01 ? "text-accent-green" : "text-accent-red"}>
            {percentageSum.toFixed(2)}% / 100%
          </span>
        )}
        {method === "SHARES" && <span className="text-ink-faint">{sharesSum} total shares</span>}
      </div>
    </div>
  );
}
