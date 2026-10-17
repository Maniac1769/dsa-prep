// Charts as plain HTML and CSS: text stays at its real size at every width, colors
// are theme tokens, and every mark carries a title for hover plus a table twin.
// Marks follow the dataviz spec: columns at most 24px with a 4px rounded data end,
// solid hairline gridlines, a 2px surface gap between touching fills, text in ink
// tokens. No entrance motion: a product page loads straight into its data.

import type { ReactNode } from "react";

const DAY_MS = 86_400_000;

function parseDay(iso: string): Date {
  const [y, m, d] = iso.split("-").map(Number);
  return new Date(Date.UTC(y!, m! - 1, d!));
}

function fmt(d: Date, opts: Intl.DateTimeFormatOptions) {
  return d.toLocaleDateString("en-GB", { timeZone: "UTC", ...opts });
}

/** Shade by problems logged that day. Quick logs carry no minutes, so minutes cannot drive it. */
export function heatLevel(entries: number): number {
  if (entries === 0) return 0;
  if (entries === 1) return 1;
  if (entries === 2) return 2;
  if (entries <= 4) return 3;
  return 4;
}

export function Heatmap({ today, days, weeks = 52 }: { today: string; days: { on: string; entries: number; minutes: number }[]; weeks?: number }) {
  const end = parseDay(today);
  const monday = new Date(end.getTime() - ((end.getUTCDay() + 6) % 7) * DAY_MS);
  const start = new Date(monday.getTime() - (weeks - 1) * 7 * DAY_MS);
  const byDay = new Map(days.map((d) => [d.on, d]));

  const months: ReactNode[] = [];
  let lastMonth = -1;
  const cells: ReactNode[] = [];
  for (let col = 0; col < weeks; col++) {
    const weekStart = new Date(start.getTime() + col * 7 * DAY_MS);
    if (weekStart.getUTCMonth() !== lastMonth && weekStart.getUTCDate() <= 7 && col <= weeks - 3) {
      months.push(
        <span key={col} style={{ gridColumn: `${col + 1} / span 3` }}>
          {fmt(weekStart, { month: "short" })}
        </span>,
      );
      lastMonth = weekStart.getUTCMonth();
    }
    for (let row = 0; row < 7; row++) {
      const d = new Date(weekStart.getTime() + row * DAY_MS);
      const iso = d.toISOString().slice(0, 10);
      if (d > end) {
        cells.push(<span key={iso} className="hc is-future" aria-hidden="true" />);
        continue;
      }
      const day = byDay.get(iso);
      const label = fmt(d, { weekday: "short", day: "numeric", month: "short" });
      const tip = day ? `${label}: ${day.entries} logged${day.minutes ? `, ${day.minutes} min` : ""}` : `${label}: nothing logged`;
      cells.push(
        <span
          key={iso}
          className={`hc heat-${heatLevel(day?.entries ?? 0)}${iso === today ? " is-today" : ""}`}
          data-col={col}
          title={tip}
        />,
      );
    }
  }

  return (
    <div className="hm" role="img" aria-label={`Daily activity for the last ${weeks} weeks`} style={{ ["--weeks" as string]: weeks }}>
      <div
        className="hm-scroll"
        ref={(el) => {
          if (el) el.scrollLeft = el.scrollWidth;
        }}
      >
        <div className="hm-inner">
          <div className="hm-months" aria-hidden="true">
            {months}
          </div>
          <div className="hm-body">
            <div className="hm-days" aria-hidden="true">
              <span>Mon</span>
              <span />
              <span>Wed</span>
              <span />
              <span>Fri</span>
              <span />
              <span />
            </div>
            <div className="hm-grid">{cells}</div>
          </div>
        </div>
      </div>
    </div>
  );
}

function niceMax(value: number): number {
  if (value <= 0) return 1;
  for (const step of [1, 2, 4, 5, 10, 20, 30, 60, 90, 120, 150, 180, 240, 300, 360, 420, 480, 600, 720, 900, 1200]) {
    if (value <= step) return step;
  }
  return Math.ceil(value * 1.1);
}

export interface Column {
  label: string;
  value: number;
  tip: string;
  current?: boolean;
}

export function Columns({ data, target, targetLabel, aria }: { data: Column[]; target?: number; targetLabel?: string; aria: string }) {
  const yMax = niceMax(Math.max(...data.map((c) => c.value), target ?? 0));
  const ticks = [...new Set([0, Math.floor(yMax / 2), yMax])];
  const dense = data.length > 8;
  return (
    <div className="cols" role="img" aria-label={aria} style={{ ["--n" as string]: data.length }}>
      <div className="cols-plot">
        {ticks.map((t) => (
          <span key={t} className="cg" style={{ bottom: `${(100 * t) / yMax}%` }}>
            <i>{t}</i>
          </span>
        ))}
        {target ? (
          <span className="ct" style={{ bottom: `${(100 * target) / yMax}%` }}>
            <i>{targetLabel}</i>
          </span>
        ) : null}
        <div className="cols-bars">
          {data.map((c) => (
            <span key={c.label} className={c.current ? "cb is-current" : "cb"} title={c.tip} tabIndex={0} aria-label={c.tip}>
              <span className="cb-bar" style={{ height: `${(100 * c.value) / yMax}%` }} />
            </span>
          ))}
        </div>
      </div>
      <div className="cols-x" aria-hidden="true">
        {data.map((c, i) => (
          <span key={c.label}>{!dense || i % 2 === (data.length - 1) % 2 ? c.label : ""}</span>
        ))}
      </div>
    </div>
  );
}

export function ProgressBars({ bars }: { bars: { label: string; solid: number; started: number; total: number }[] }) {
  return (
    <div className="pbars" role="img" aria-label="Progress by track: unaided, started, not started">
      {bars.map((b) => {
        const total = Math.max(b.total, 1);
        return (
          <div className="pb-row" key={b.label}>
            <span className="pb-label">{b.label}</span>
            <span className="pb-track">
              {b.solid > 0 && <span className="pb-solid" style={{ width: `${(100 * b.solid) / total}%` }} title={`${b.label}: ${b.solid} unaided of ${b.total}`} />}
              {b.started > 0 && <span className="pb-started" style={{ width: `${(100 * b.started) / total}%` }} title={`${b.label}: ${b.started} started, not yet unaided`} />}
            </span>
            <span className="pb-val">
              {b.solid} / {b.total} <span className="muted">{Math.round((100 * b.solid) / total)}%</span>
            </span>
          </div>
        );
      })}
    </div>
  );
}

export function dayLabel(iso: string, opts: Intl.DateTimeFormatOptions) {
  return fmt(parseDay(iso), opts);
}
