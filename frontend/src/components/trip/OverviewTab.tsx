import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import * as tripsApi from "../../api/trips";
import type { Trip } from "../../types";
import { formatDate, formatMoney } from "../../utils/format";
import { Card } from "../ui/Card";
import { StatTile } from "../ui/StatTile";

export function OverviewTab({ trip, currentUserId }: { trip: Trip; currentUserId: number }) {
  const { data: balances } = useQuery({ queryKey: ["balances", trip.id], queryFn: () => tripsApi.getBalances(trip.id) });
  const { data: members } = useQuery({ queryKey: ["members", trip.id], queryFn: () => tripsApi.listMembers(trip.id) });

  const myBalance = balances?.balances.find((b) => b.user.id === currentUserId);
  const net = myBalance ? parseFloat(myBalance.net_balance) : 0;

  return (
    <div>
      {(trip.description || trip.destination) && (
        <Card className="mb-6">
          {trip.destination && <div className="text-sm text-ink-soft">{trip.destination}</div>}
          {trip.description && <p className="mt-1 text-sm text-ink-faint">{trip.description}</p>}
          {(trip.start_date || trip.end_date) && (
            <div className="mt-2 text-xs text-ink-faint">
              {formatDate(trip.start_date)} – {formatDate(trip.end_date)}
            </div>
          )}
        </Card>
      )}

      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        <Card>
          <StatTile label="Total spent" value={formatMoney(balances?.total_expenses ?? "0", trip.currency)} />
        </Card>
        <Card>
          <StatTile label="You paid" value={formatMoney(myBalance?.total_paid ?? "0", trip.currency)} />
        </Card>
        <Card>
          <StatTile label="Your share" value={formatMoney(myBalance?.total_owed ?? "0", trip.currency)} />
        </Card>
        <Card>
          <StatTile
            label={net >= 0 ? "You are owed" : "You owe"}
            value={
              <span className={net > 0 ? "text-accent-green" : net < 0 ? "text-accent-red" : ""}>
                {formatMoney(Math.abs(net), trip.currency)}
              </span>
            }
          />
        </Card>
      </div>

      <div className="mt-8">
        <h2 className="mb-3 font-serif text-lg text-ink">Members</h2>
        <div className="flex flex-wrap gap-3">
          {members?.map((m) => (
            <div key={m.id} className="flex items-center gap-2 rounded-full border border-line bg-cream-soft py-1.5 pl-1.5 pr-3">
              <div className="flex h-6 w-6 items-center justify-center rounded-full bg-ink text-[10px] font-medium text-cream-soft">
                {m.user.full_name.charAt(0).toUpperCase()}
              </div>
              <span className="text-xs text-ink-soft">{m.user.full_name}</span>
              <span className="text-[10px] uppercase text-ink-faint">{m.role}</span>
            </div>
          ))}
        </div>
      </div>

      <div className="mt-6">
        <Link to={`/trips/${trip.id}/reports`} className="text-sm font-medium text-ink hover:underline">
          View full reports & exports →
        </Link>
      </div>
    </div>
  );
}
