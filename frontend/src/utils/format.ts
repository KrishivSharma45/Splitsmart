const CURRENCY_SYMBOLS: Record<string, string> = {
  INR: "₹",
  USD: "$",
  EUR: "€",
  GBP: "£",
};

export function currencySymbol(currency: string) {
  return CURRENCY_SYMBOLS[currency] ?? currency + " ";
}

export function formatMoney(amount: string | number, currency = "INR") {
  const value = typeof amount === "string" ? parseFloat(amount) : amount;
  const formatted = new Intl.NumberFormat("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(
    Math.abs(value),
  );
  const sign = value < 0 ? "-" : "";
  return `${sign}${currencySymbol(currency)}${formatted}`;
}

export function formatDate(iso: string | null | undefined) {
  if (!iso) return "—";
  const d = new Date(iso);
  return d.toLocaleDateString("en-IN", { day: "2-digit", month: "short", year: "numeric" });
}

export function formatDateTime(iso: string | null | undefined) {
  if (!iso) return "—";
  const d = new Date(iso);
  return d.toLocaleString("en-IN", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function truncateHash(hash: string, chars = 6) {
  if (!hash) return "";
  return `${hash.slice(0, chars)}…${hash.slice(-4)}`;
}

export function relativeTime(iso: string) {
  const diffMs = Date.now() - new Date(iso).getTime();
  const diffSec = Math.round(diffMs / 1000);
  if (diffSec < 60) return "just now";
  const diffMin = Math.round(diffSec / 60);
  if (diffMin < 60) return `${diffMin}m ago`;
  const diffHour = Math.round(diffMin / 60);
  if (diffHour < 24) return `${diffHour}h ago`;
  const diffDay = Math.round(diffHour / 24);
  return `${diffDay}d ago`;
}

export function categoryLabel(category: string) {
  return category.charAt(0) + category.slice(1).toLowerCase();
}
