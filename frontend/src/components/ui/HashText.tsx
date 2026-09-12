import { truncateHash } from "../../utils/format";

export function HashText({ hash, full = false }: { hash: string; full?: boolean }) {
  return <span className="mono text-ink-soft">{full ? hash : truncateHash(hash)}</span>;
}
