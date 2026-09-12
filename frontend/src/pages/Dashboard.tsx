import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";
import * as dashboardApi from "../api/dashboard";
import { Badge } from "../components/ui/Badge";
import { Card } from "../components/ui/Card";
import { EmptyState } from "../components/ui/EmptyState";
import { PageSpinner } from "../components/ui/Spinner";
import { StatTile } from "../components/ui/StatTile";
import { categoryLabel, formatDate, formatMoney } from "../utils/format";

const CHART_COLORS = ["#17160F", "#3D6B4C", "#B4762A", "#A5402F", "#8A8672", "#6b7280", "#94867a"];

export function Dashboard() {
  const { data, isLoading } = useQuery({ queryKey: ["dashboard"], queryFn: dashboardApi.getDashboard });

  if (isLoading || !data) return <PageSpinner />;

  const categoryTotals = new Map<string, number>();
  for (const e of data.recent_expenses) {
    categoryTotals.set(e.category, (categoryTotals.get(e.category) ?? 0) + parseFloat(e.amount));
  }
  const chartData = Array.from(categoryTotals.entries()).map(([category, total]) => ({
    name: categoryLabel(category),
    value: total,
  }));

  return (
    <div>
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="font-serif text-3xl text-ink">Dashboard</h1>
          <p className="mt-1 text-sm text-ink-faint">Your finances across every trip, calculated by the backend.</p>
        </div>
        <Link to="/trips" className="btn-primary">
          New trip
        </Link>
      </div>

      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        <Card>
          <StatTile label="Total spending" value={formatMoney(data.total_spending)} hint="Paid by you" />
        </Card>
        <Card>
          <StatTile label="Trips" value={data.trip_count} hint={`${data.active_trip_count} active`} />
        </Card>
        <Card>
          <StatTile
            label="You owe"
            value={<span className="text-accent-red">{formatMoney(data.amount_you_owe)}</span>}
          />
        </Card>
        <Card>
          <StatTile
            label="Owed to you"
            value={<span className="text-accent-green">{formatMoney(data.amount_owed_to_you)}</span>}
          />
        </Card>
      </div>

      <div className="mt-8 grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2">
          <h2 className="mb-3 font-serif text-lg text-ink">Your trips</h2>
          {data.trips.length === 0 ? (
            <EmptyState
              title="No trips yet"
              description="Create your first trip to start recording expenses."
              action={
                <Link to="/trips" className="btn-primary">
                  Create a trip
                </Link>
              }
            />
          ) : (
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              {data.trips.map((trip) => {
                const net = parseFloat(trip.my_net_balance);
                return (
                  <Link key={trip.id} to={`/trips/${trip.id}`} className="card block p-5 transition hover:border-ink/30">
                    <div className="flex items-start justify-between">
                      <h3 className="font-serif text-lg text-ink">{trip.name}</h3>
                      <Badge tone={trip.status === "ACTIVE" ? "green" : "neutral"}>{trip.status}</Badge>
                    </div>
                    <div className="mt-1 text-xs text-ink-faint">
                      {trip.member_count} member{trip.member_count === 1 ? "" : "s"} · {formatMoney(trip.total_expenses, trip.currency)} tracked
                    </div>
                    <div className="mt-4 text-sm">
                      {net === 0 ? (
                        <span className="text-ink-faint">Settled up</span>
                      ) : net > 0 ? (
                        <span className="text-accent-green">You are owed {formatMoney(net, trip.currency)}</span>
                      ) : (
                        <span className="text-accent-red">You owe {formatMoney(-net, trip.currency)}</span>
                      )}
                    </div>
                  </Link>
                );
              })}
            </div>
          )}

          <h2 className="mb-3 mt-8 font-serif text-lg text-ink">Recent expenses</h2>
          <Card className="p-0">
            {data.recent_expenses.length === 0 ? (
              <div className="p-5 text-sm text-ink-faint">No expenses recorded yet.</div>
            ) : (
              <ul className="divide-y divide-line">
                {data.recent_expenses.map((e) => (
                  <li key={e.id}>
                    <Link to={`/trips/${e.trip_id}/expenses/${e.id}`} className="flex items-center justify-between px-5 py-3 transition hover:bg-ink/5">
                      <div>
                        <div className="text-sm text-ink">{e.description}</div>
                        <div className="text-xs text-ink-faint">
                          {formatDate(e.date)} · {e.paid_by.full_name} · {categoryLabel(e.category)}
                        </div>
                      </div>
                      <div className="mono text-ink-soft">{formatMoney(e.amount, e.currency)}</div>
                    </Link>
                  </li>
                ))}
              </ul>
            )}
          </Card>
        </div>

        <div>
          <h2 className="mb-3 font-serif text-lg text-ink">Recent activity by category</h2>
          <Card>
            {chartData.length === 0 ? (
              <p className="text-sm text-ink-faint">No expenses yet.</p>
            ) : (
              <ResponsiveContainer width="100%" height={200}>
                <PieChart>
                  <Pie data={chartData} dataKey="value" nameKey="name" innerRadius={50} outerRadius={80} paddingAngle={2}>
                    {chartData.map((entry, i) => (
                      <Cell key={entry.name} fill={CHART_COLORS[i % CHART_COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip formatter={(value: number) => formatMoney(value)} />
                </PieChart>
              </ResponsiveContainer>
            )}
            <ul className="mt-2 space-y-1.5">
              {chartData.map((c, i) => (
                <li key={c.name} className="flex items-center justify-between text-xs">
                  <span className="flex items-center gap-2 text-ink-soft">
                    <span className="h-2 w-2 rounded-full" style={{ background: CHART_COLORS[i % CHART_COLORS.length] }} />
                    {c.name}
                  </span>
                  <span className="mono text-ink-faint">{formatMoney(c.value)}</span>
                </li>
              ))}
            </ul>
          </Card>

          <h2 className="mb-3 mt-8 font-serif text-lg text-ink">Recent settlements</h2>
          <Card className="p-0">
            {data.recent_settlements.length === 0 ? (
              <div className="p-5 text-sm text-ink-faint">No settlements recorded yet.</div>
            ) : (
              <ul className="divide-y divide-line">
                {data.recent_settlements.map((s) => (
                  <li key={s.id} className="px-5 py-3">
                    <div className="text-sm text-ink">
                      {s.payer.full_name} → {s.receiver.full_name}
                    </div>
                    <div className="text-xs text-ink-faint">{formatDate(s.date)}</div>
                    <div className="mono mt-1 text-ink-soft">{formatMoney(s.amount, s.currency)}</div>
                  </li>
                ))}
              </ul>
            )}
          </Card>
        </div>
      </div>
    </div>
  );
}
