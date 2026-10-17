import type { DesignLink } from "../api";
import type { IconName } from "../icon-names";
import { Icon } from "./Icon";

const KIND: Record<DesignLink["kind"], { icon: IconName; label: string }> = {
  watch: { icon: "play-circle", label: "Watch" },
  read: { icon: "article", label: "Read" },
  practice: { icon: "code", label: "Practice" },
};

/** Compact chips for a design row: one per link, kind first so the eye can scan. */
export function DesignLinkChips({ links }: { links: DesignLink[] }) {
  if (links.length === 0) return null;
  return (
    <span className="dlinks">
      {links.map((l) => (
        <a key={l.url} className="dlink" href={l.url} target="_blank" rel="noreferrer" title={`${l.title}${l.source ? `, ${l.source}` : ""}${l.note ? `. ${l.note}` : ""}`}>
          <Icon name={KIND[l.kind].icon} />
          <span className="dlink-kind">{KIND[l.kind].label}</span>
          <span className="dlink-src">{l.source || new URL(l.url).hostname.replace(/^www\./, "")}</span>
        </a>
      ))}
    </span>
  );
}

/** Full list for the item page and Today: title, source and why, grouped by kind. */
export function DesignLinkList({ links }: { links: DesignLink[] }) {
  if (links.length === 0) return null;
  return (
    <ul className="dlist">
      {links.map((l) => (
        <li key={l.url}>
          <span className={`dlist-kind dlist-${l.kind}`}>
            <Icon name={KIND[l.kind].icon} />
            {KIND[l.kind].label}
          </span>
          <span className="dlist-body">
            <a href={l.url} target="_blank" rel="noreferrer">
              {l.title}
            </a>
            <span className="muted">
              {l.source}
              {l.note ? ` · ${l.note}` : ""}
            </span>
          </span>
        </li>
      ))}
    </ul>
  );
}
