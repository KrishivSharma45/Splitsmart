import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import toast from "react-hot-toast";
import { Link, useNavigate } from "react-router-dom";
import { extractErrorMessage } from "../api/client";
import * as tripsApi from "../api/trips";
import { Badge } from "../components/ui/Badge";
import { EmptyState } from "../components/ui/EmptyState";
import { Modal } from "../components/ui/Modal";
import { PageSpinner } from "../components/ui/Spinner";
import { formatMoney } from "../utils/format";

export function Trips() {
  const [modalOpen, setModalOpen] = useState(false);
  const { data: trips, isLoading } = useQuery({ queryKey: ["trips"], queryFn: tripsApi.listTrips });

  return (
    <div>
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="font-serif text-3xl text-ink">Trips</h1>
          <p className="mt-1 text-sm text-ink-faint">Every group you're a part of.</p>
        </div>
        <button onClick={() => setModalOpen(true)} className="btn-primary">
          New trip
        </button>
      </div>

      {isLoading ? (
        <PageSpinner />
      ) : !trips || trips.length === 0 ? (
        <EmptyState
          title="No trips yet"
          description="Create a trip to start adding members and recording expenses."
          action={
            <button onClick={() => setModalOpen(true)} className="btn-primary">
              Create your first trip
            </button>
          }
        />
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {trips.map((trip) => {
            const net = parseFloat(trip.my_net_balance);
            return (
              <Link key={trip.id} to={`/trips/${trip.id}`} className="card block p-5 transition hover:border-ink/30">
                <div className="flex items-start justify-between gap-2">
                  <h3 className="font-serif text-lg text-ink">{trip.name}</h3>
                  <Badge tone={trip.status === "ACTIVE" ? "green" : "neutral"}>{trip.status}</Badge>
                </div>
                {trip.destination && <div className="mt-0.5 text-xs text-ink-faint">{trip.destination}</div>}
                <div className="mt-3 text-xs text-ink-faint">
                  {trip.member_count} member{trip.member_count === 1 ? "" : "s"} · your role: {trip.my_role}
                </div>
                <div className="mt-3 text-sm text-ink-soft">
                  {formatMoney(trip.total_expenses, trip.currency)} tracked
                </div>
                <div className="mt-2 text-sm">
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

      <CreateTripModal open={modalOpen} onClose={() => setModalOpen(false)} />
    </div>
  );
}

function CreateTripModal({ open, onClose }: { open: boolean; onClose: () => void }) {
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const [name, setName] = useState("");
  const [destination, setDestination] = useState("");
  const [description, setDescription] = useState("");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [currency, setCurrency] = useState("INR");

  const mutation = useMutation({
    mutationFn: () =>
      tripsApi.createTrip({
        name,
        destination: destination || undefined,
        description: description || undefined,
        start_date: startDate || undefined,
        end_date: endDate || undefined,
        currency,
      }),
    onSuccess: (trip) => {
      queryClient.invalidateQueries({ queryKey: ["trips"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      toast.success("Trip created");
      onClose();
      navigate(`/trips/${trip.id}`);
    },
    onError: (err) => toast.error(extractErrorMessage(err)),
  });

  return (
    <Modal open={open} onClose={onClose} title="New trip">
      <form
        onSubmit={(e) => {
          e.preventDefault();
          mutation.mutate();
        }}
        className="space-y-4"
      >
        <div>
          <label className="label">Trip name</label>
          <input required className="input" value={name} onChange={(e) => setName(e.target.value)} placeholder="Goa Trip" />
        </div>
        <div>
          <label className="label">Destination</label>
          <input className="input" value={destination} onChange={(e) => setDestination(e.target.value)} />
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="label">Start date</label>
            <input type="date" className="input" value={startDate} onChange={(e) => setStartDate(e.target.value)} />
          </div>
          <div>
            <label className="label">End date</label>
            <input type="date" className="input" value={endDate} onChange={(e) => setEndDate(e.target.value)} />
          </div>
        </div>
        <div>
          <label className="label">Currency</label>
          <select className="input" value={currency} onChange={(e) => setCurrency(e.target.value)}>
            <option value="INR">INR (₹)</option>
            <option value="USD">USD ($)</option>
            <option value="EUR">EUR (€)</option>
            <option value="GBP">GBP (£)</option>
          </select>
        </div>
        <div>
          <label className="label">Description</label>
          <textarea className="input" rows={2} value={description} onChange={(e) => setDescription(e.target.value)} />
        </div>
        <button type="submit" disabled={mutation.isPending} className="btn-primary w-full">
          {mutation.isPending ? "Creating…" : "Create trip"}
        </button>
      </form>
    </Modal>
  );
}
