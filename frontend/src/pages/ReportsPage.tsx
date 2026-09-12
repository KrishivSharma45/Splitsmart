import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import toast from "react-hot-toast";
import { Link, useParams } from "react-router-dom";
import { Bar, BarChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import * as reportsApi from "../api/reports";
import * as tripsApi from "../api/trips";
import { Badge } from "../components/ui/Badge";
import { Card } from "../components/ui/Card";
import { PageSpinner } from "../components/ui/Spinner";
import { categoryLabel, formatDate, formatMoney } from "../utils/format";

export function ReportsPage() {
  const { tripId } = useParams();
  const id = parseInt(tripId ?? "0", 10);
  const [exporting, setExporting] = useState<string | null>(null);

  const { data: trip } = useQuery({ queryKey: ["trip", id], queryFn: () => tripsApi.getTrip(id), enabled: !!id });
  const { data: report, isLoading } = useQuery({
    queryKey: ["report", id],
    queryFn: () => reportsApi.getReportSummary(id),
    enabled: !!id,
  });

  async function handleExport(kind: "expenses" | "balances" | "settlements" | "audit" | "pdf") {
    setExporting(kind);
    try {
      if (kind === "pdf") {
        await reportsApi.downloadExport(reportsApi.pdfExportUrl(id), `${trip?.name ?? "trip"}_summary.pdf`);
      } else {
        await reportsApi.downloadExport(reportsApi.csvExportUrl(id, kind), `${trip?.name ?? "trip"}_${kind}.csv`);
      }
    } catch {
      toast.error("Failed to generate export");
    } finally {
      setExporting(null);
    }
  }

  if (isLoading || !report || !trip) return <PageSpinner />;

  const chartData = report.category_breakdown.map((c) => ({ name: categoryLabel(c.category), total: parseFloat(c.total) }));

  return (
    <div>
      <div className="mb-2 flex items-center gap-2 text-sm text-ink-faint">
        <Link to={`/trips/${id}`} className="hover:text-ink">
          {trip.name}
        </Link>
        <span>/</span>
        <span className="text-ink">Reports</span>
      </div>

      <div className="mb-6 flex flex-wrap items-center justify-between gap-4">
        <h1 className="font-serif text-3xl text-ink">Reports</h1>
        <div className="flex flex-wrap gap-2">
          {(["expenses", "balances", "settlements", "audit"] as const).map((kind) => (
            <button key={kind} onClick={() => handleExport(kind)} disabled={exporting === kind} className="btn-secondary">
              {exporting === kind ? "Exporting…" : `Export ${kind} CSV`}
            </button>
          ))}
          <button onClick={() => handleExport("pdf")} disabled={exporting === "pdf"} className="btn-primary">
            {exporting === "pdf" ? "Exporting…" : "Export PDF summary"}
          </button>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        <Card>
          <div className="text-xs uppercase text-ink-faint">Total spent</div>
          <div className="mt-1 font-serif text-2xl text-ink">{formatMoney(report.total_expenses, trip.currency)}</div>
        </Card>
        <Card>
          <div className="text-xs uppercase text-ink-faint">Active expenses</div>
          <div className="mt-1 font-serif text-2xl text-ink">{report.active_expense_count}</div>
        </Card>
        <Card>
          <div className="text-xs uppercase text-ink-faint">Voided expenses</div>
          <div className="mt-1 font-serif text-2xl text-ink">{report.voided_expense_count}</div>
        </Card>
        <Card>
          <div className="text-xs uppercase text-ink-faint">Settlements</div>
          <div className="mt-1 font-serif text-2xl text-ink">{report.settlements.length}</div>
        </Card>
      </div>

      <div className="mt-8 grid grid-cols-1 gap-8 lg:grid-cols-2">
        <div>
          <h2 className="mb-3 font-serif text-lg text-ink">Spending by category</h2>
          <Card>
            {chartData.length === 0 ? (
              <p className="text-sm text-ink-faint">No expenses yet.</p>
            ) : (
              <ResponsiveContainer width="100%" height={220}>
                <BarChart data={chartData} layout="vertical" margin={{ left: 20 }}>
                  <XAxis type="number" hide />
                  <YAxis type="category" dataKey="name" width={100} tick={{ fontSize: 12, fill: "#454234" }} axisLine={false} tickLine={false} />
                  <Tooltip formatter={(value: number) => formatMoney(value, trip.currency)} cursor={{ fill: "#E3DDCC55" }} />
                  <Bar dataKey="total" fill="#17160F" radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            )}
          </Card>
        </div>

        <div>
          <h2 className="mb-3 font-serif text-lg text-ink">Member balances</h2>
          <Card className="p-0">
            <ul className="divide-y divide-line">
              {report.balances.map((b) => {
                const net = parseFloat(b.net_balance);
                return (
                  <li key={b.user.id} className="flex items-center justify-between px-5 py-3">
                    <span className="text-sm text-ink">{b.user.full_name}</span>
                    <span className={`mono text-sm ${net > 0 ? "text-accent-green" : net < 0 ? "text-accent-red" : "text-ink-faint"}`}>
                      {formatMoney(net, trip.currency)}
                    </span>
                  </li>
                );
              })}
            </ul>
          </Card>
        </div>
      </div>

      <div className="mt-8">
        <h2 className="mb-3 font-serif text-lg text-ink">Settlement history</h2>
        <Card className="p-0">
          {report.settlements.length === 0 ? (
            <div className="p-5 text-sm text-ink-faint">No settlements recorded.</div>
          ) : (
            <ul className="divide-y divide-line">
              {report.settlements.map((s) => (
                <li key={s.id} className="flex items-center justify-between px-5 py-3">
                  <div>
                    <div className="text-sm text-ink">
                      {s.payer.full_name} → {s.receiver.full_name}
                      {s.status === "CANCELLED" && (
                        <span className="ml-2">
                          <Badge tone="red">Cancelled</Badge>
                        </span>
                      )}
                    </div>
                    <div className="text-xs text-ink-faint">{formatDate(s.date)}</div>
                  </div>
                  <span className="mono text-sm text-ink-soft">{formatMoney(s.amount, s.currency)}</span>
                </li>
              ))}
            </ul>
          )}
        </Card>
      </div>
    </div>
  );
}
