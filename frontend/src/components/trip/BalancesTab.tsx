import { useQuery } from "@tanstack/react-query";
import * as tripsApi from "../../api/trips";
import type { Trip } from "../../types";
import { Card } from "../ui/Card";
import { PageSpinner } from "../ui/Spinner";
import { formatMoney } from "../../utils/format";

export function BalancesTab({ trip }: { trip: Trip }) {
  const { data: balances, isLoading: balancesLoading } = useQuery({
    queryKey: ["balances", trip.id],
    queryFn: () => tripsApi.getBalances(trip.id),
  });
  const { data: debts, isLoading: debtsLoading } = useQuery({
    queryKey: ["debts", trip.id],
    queryFn: () => tripsApi.getDebts(trip.id),
  });

  if (balancesLoading || debtsLoading) return <PageSpinner />;

  return (
    <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
      <div>
        <h2 className="mb-3 font-serif text-lg text-ink">Member balances</h2>
        <Card className="p-0">
          <ul className="divide-y divide-line">
            {balances?.balances.map((b) => {
              const net = parseFloat(b.net_balance);
              return (
                <li key={b.user.id} className="flex items-center justify-between px-5 py-3.5">
                  <div>
                    <div className="text-sm text-ink">{b.user.full_name}</div>
                    <div className="text-xs text-ink-faint">
                      Paid {formatMoney(b.total_paid, trip.currency)} · Owes {formatMoney(b.total_owed, trip.currency)}
                    </div>
                  </div>
                  <div
                    className={`mono text-sm ${net > 0 ? "text-accent-green" : net < 0 ? "text-accent-red" : "text-ink-faint"}`}
                  >
                    {net === 0 ? "Settled" : net > 0 ? `+${formatMoney(net, trip.currency)}` : formatMoney(net, trip.currency)}
                  </div>
                </li>
              );
            })}
          </ul>
        </Card>
      </div>

      <div>
        <h2 className="mb-3 font-serif text-lg text-ink">Who owes whom</h2>
        <p className="mb-3 text-xs text-ink-faint">
          Simplified into the fewest transactions needed to settle the trip.
        </p>
        <Card className="p-0">
          {!debts || debts.simplified_debts.length === 0 ? (
            <div className="p-5 text-sm text-ink-faint">Everyone is settled up.</div>
          ) : (
            <ul className="divide-y divide-line">
              {debts.simplified_debts.map((edge, i) => (
                <li key={i} className="flex items-center justify-between px-5 py-3.5">
                  <div className="flex items-center gap-2 text-sm text-ink">
                    <span>{edge.from_user.full_name}</span>
                    <span className="text-ink-faint">→</span>
                    <span>{edge.to_user.full_name}</span>
                  </div>
                  <div className="mono text-sm text-ink-soft">{formatMoney(edge.amount, trip.currency)}</div>
                </li>
              ))}
            </ul>
          )}
        </Card>
      </div>
    </div>
  );
}
