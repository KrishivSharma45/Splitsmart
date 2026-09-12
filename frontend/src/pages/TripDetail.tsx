import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import toast from "react-hot-toast";
import { Link, useNavigate, useParams } from "react-router-dom";
import { extractErrorMessage } from "../api/client";
import * as tripsApi from "../api/trips";
import { BalancesTab } from "../components/trip/BalancesTab";
import { ExpensesTab } from "../components/trip/ExpensesTab";
import { MembersTab } from "../components/trip/MembersTab";
import { OverviewTab } from "../components/trip/OverviewTab";
import { SettlementsTab } from "../components/trip/SettlementsTab";
import { TripAuditTab } from "../components/trip/TripAuditTab";
import { Badge } from "../components/ui/Badge";
import { PageSpinner } from "../components/ui/Spinner";
import { useAuth } from "../context/AuthContext";
import type { Trip } from "../types";

const TABS = ["Overview", "Expenses", "Balances", "Settlements", "Members", "Audit"] as const;
type Tab = (typeof TABS)[number];

export function TripDetail() {
  const { tripId } = useParams();
  const id = parseInt(tripId ?? "0", 10);
  const { user } = useAuth();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [tab, setTab] = useState<Tab>("Overview");

  const { data: trip, isLoading } = useQuery({ queryKey: ["trip", id], queryFn: () => tripsApi.getTrip(id), enabled: !!id });

  const archiveMutation = useMutation({
    mutationFn: () => tripsApi.archiveTrip(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["trips"] });
      queryClient.invalidateQueries({ queryKey: ["trip", id] });
      toast.success("Trip archived");
    },
    onError: (err) => toast.error(extractErrorMessage(err)),
  });

  if (isLoading || !trip || !user) return <PageSpinner />;

  const isOwner = trip.my_role === "OWNER";

  return (
    <div>
      <div className="mb-2 flex items-center gap-2 text-sm text-ink-faint">
        <Link to="/trips" className="hover:text-ink">
          Trips
        </Link>
        <span>/</span>
        <span className="text-ink">{trip.name}</span>
      </div>

      <div className="mb-6 flex flex-wrap items-start justify-between gap-4">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="font-serif text-3xl text-ink">{trip.name}</h1>
            <Badge tone={trip.status === "ACTIVE" ? "green" : "neutral"}>{trip.status}</Badge>
          </div>
          {trip.destination && <p className="mt-1 text-sm text-ink-faint">{trip.destination}</p>}
        </div>
        {isOwner && trip.status === "ACTIVE" && (
          <button
            onClick={() => {
              if (confirm("Archive this trip? It will move out of your active trips but stay fully accessible for history and audit.")) {
                archiveMutation.mutate();
              }
            }}
            className="btn-secondary"
            disabled={archiveMutation.isPending}
          >
            Archive trip
          </button>
        )}
      </div>

      <div className="mb-6 flex gap-1 border-b border-line">
        {TABS.map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`border-b-2 px-3 py-2.5 text-sm transition ${
              tab === t ? "border-ink font-medium text-ink" : "border-transparent text-ink-faint hover:text-ink"
            }`}
          >
            {t}
          </button>
        ))}
      </div>

      {tab === "Overview" && <OverviewTab trip={trip} currentUserId={user.id} />}
      {tab === "Expenses" && <ExpensesTabWrapper tripId={id} trip={trip} currentUserId={user.id} />}
      {tab === "Balances" && <BalancesTab trip={trip} />}
      {tab === "Settlements" && <SettlementsTabWrapper tripId={id} trip={trip} currentUserId={user.id} />}
      {tab === "Members" && <MembersTab trip={trip} currentUserId={user.id} />}
      {tab === "Audit" && <TripAuditTab trip={trip} />}
    </div>
  );
}

// Small wrappers fetch members once so tabs that need the roster (splits,
// settlement payer/receiver pickers) don't each issue their own request.
function ExpensesTabWrapper({ tripId, trip, currentUserId }: { tripId: number; trip: Trip; currentUserId: number }) {
  const { data: members } = useQuery({ queryKey: ["members", tripId], queryFn: () => tripsApi.listMembers(tripId) });
  if (!members) return <PageSpinner />;
  return <ExpensesTab trip={trip} members={members} currentUserId={currentUserId} />;
}

function SettlementsTabWrapper({ tripId, trip, currentUserId }: { tripId: number; trip: Trip; currentUserId: number }) {
  const { data: members } = useQuery({ queryKey: ["members", tripId], queryFn: () => tripsApi.listMembers(tripId) });
  if (!members) return <PageSpinner />;
  return <SettlementsTab trip={trip} members={members} currentUserId={currentUserId} />;
}
