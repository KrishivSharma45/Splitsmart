import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import * as notificationsApi from "../api/notifications";
import { relativeTime } from "../utils/format";

export function NotificationBell() {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  const queryClient = useQueryClient();

  const { data: notifications = [] } = useQuery({
    queryKey: ["notifications"],
    queryFn: () => notificationsApi.listNotifications(),
    refetchInterval: 30000,
  });

  const unreadCount = notifications.filter((n) => !n.is_read).length;

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  async function handleMarkAllRead() {
    await notificationsApi.markAllRead();
    queryClient.invalidateQueries({ queryKey: ["notifications"] });
  }

  return (
    <div className="relative" ref={ref}>
      <button
        onClick={() => setOpen((o) => !o)}
        className="relative flex h-9 w-9 items-center justify-center rounded-full border border-line bg-cream-soft text-ink transition hover:bg-ink/5"
        aria-label="Notifications"
      >
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
          <path
            d="M18 8a6 6 0 10-12 0c0 7-3 9-3 9h18s-3-2-3-9"
            stroke="currentColor"
            strokeWidth="1.6"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
          <path d="M13.7 21a2 2 0 01-3.4 0" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
        </svg>
        {unreadCount > 0 && (
          <span className="absolute -right-0.5 -top-0.5 flex h-4 min-w-4 items-center justify-center rounded-full bg-accent-red px-1 text-[10px] font-medium text-white">
            {unreadCount > 9 ? "9+" : unreadCount}
          </span>
        )}
      </button>
      {open && (
        <div className="absolute right-0 z-20 mt-2 w-80 rounded-2xl border border-line bg-cream-card p-2 shadow-lg">
          <div className="flex items-center justify-between px-2 py-1.5">
            <span className="text-sm font-medium text-ink">Notifications</span>
            {unreadCount > 0 && (
              <button onClick={handleMarkAllRead} className="text-xs text-ink-faint hover:text-ink">
                Mark all read
              </button>
            )}
          </div>
          <div className="max-h-80 overflow-y-auto">
            {notifications.length === 0 && (
              <div className="px-2 py-6 text-center text-sm text-ink-faint">No notifications yet.</div>
            )}
            {notifications.slice(0, 15).map((n) => (
              <Link
                key={n.id}
                to={n.trip_id ? `/trips/${n.trip_id}` : "#"}
                onClick={() => setOpen(false)}
                className={`block rounded-lg px-2 py-2 text-sm transition hover:bg-ink/5 ${
                  n.is_read ? "text-ink-soft" : "text-ink"
                }`}
              >
                <div className="flex items-start gap-2">
                  {!n.is_read && <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-accent-green" />}
                  <div className={n.is_read ? "pl-3.5" : ""}>
                    <div>{n.message}</div>
                    <div className="mt-0.5 text-xs text-ink-faint">{relativeTime(n.created_at)}</div>
                  </div>
                </div>
              </Link>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
