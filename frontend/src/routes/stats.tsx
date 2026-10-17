import { useRef } from "react";
import { Link, createFileRoute } from "@tanstack/react-router";
import { useSuspenseQuery } from "@tanstack/react-query";
import { Columns, Heatmap, ProgressBars, dayLabel } from "../components/Charts";
import { statsQuery } from "../queries";

export const Route = createFileRoute("/stats")({
  loader: ({ context: { queryClient } }) => queryClient.ensureQueryData(statsQuery()),
  component: StatsPage,
});

function StatsPage() {
  const { data: s } = useSuspenseQuery(statsQuery());
  const page = useRef<HTMLDivElement>(null);

  const weekly = s.weekly.map((w) => {
    const label = dayLabel(w.start, { day: "numeric", month: "short" });
    return { label, value: w.entries, tip: `Week of ${label}: ${w.entries} logged on ${w.days} day${w.days === 1 ? "" : "s"}`, current: w.current };
  });
  const upcoming = s.upcoming.map((u, i) => {
    const label = i === 0 ? "Today" : dayLabel(u.on, { weekday: "short", day: "numeric" });
    return {
      label,
      value: u.count,
      tip: `${i === 0 ? "Today, incl. overdue" : dayLabel(u.on, { weekday: "short", day: "numeric", month: "short" })}: ${u.count} review${u.count === 1 ? "" : "s"}`,
      current: i === 0,
    };
  });

  return (
    <div ref={page}>
      <header className="page-head">
        <h1>Progress</h1>
        <p className="sub">Counts what you can do unaided, not what you have touched.</p>
      </header>

      {!s.any_activity && (
        <div className="empty" style={{ marginBottom: 20 }}>
          <h2>Nothing logged yet</h2>
          <p>Every chart below starts with your first entry.{s.next_item && ` Tonight's problem is ${s.next_item.title}.`}</p>
          {s.next_item && (
            <Link to="/items/$id" params={{ id: s.next_item.id }} className="btn btn-primary btn-sm">
              Open {s.next_item.title}
            </Link>
          )}
        </div>
      )}

      <section className="kpis" aria-label="Summary">
        <Kpi label="Solved unaided" value={s.kpi.unaided} suffix={`of ${s.kpi.plan_total}`} hint="Problems in your list scored 2 or 3" />
        <Kpi label="Days in a row" value={s.kpi.streak} hint="A missed day resets it. That is all it does." />
        <Kpi
          label="Sessions this week"
          value={s.kpi.sessions_week}
          suffix={`of ${s.kpi.sessions_target}`}
          hint={`${s.kpi.week_entries} problem${s.kpi.week_entries === 1 ? "" : "s"} logged on ${s.kpi.week_days} day${s.kpi.week_days === 1 ? "" : "s"}`}
        />
        <Kpi
          label="Reviews due, next 7 days"
          value={s.kpi.due_7}
          hint={s.kpi.indep_rate !== null ? `${s.kpi.indep_rate}% of attempts were unaided` : "No attempts yet"}
        />
      </section>

      <section className="panel chart-card section reveal" aria-labelledby="heat-h">
        <div className="section-head">
          <h2 id="heat-h">Activity, last 12 months</h2>
          <div className="legend">
            <span>Less</span>
            {[0, 1, 2, 3, 4].map((i) => (
              <i key={i} className="sw" style={{ background: `var(--heat-${i})`, margin: 0 }} />
            ))}
            <span>More</span>
          </div>
        </div>
        <Heatmap today={s.on} days={s.days} />
        <p className="muted small" style={{ marginTop: 8 }}>
          Shade follows problems logged that day: 1, 2, 3 or 4, 5 or more. Today is outlined.
        </p>
        <TableTwin head={["Date", "Entries", "Minutes"]} rows={s.days.map((d) => [dayLabel(d.on, { weekday: "short", day: "numeric", month: "short" }), d.entries, d.minutes || ""])} empty="No days logged yet." />
      </section>

      <div className="two-col two-even section">
        <section className="panel chart-card reveal" aria-labelledby="week-h" style={{ marginTop: 0 }}>
          <div className="section-head">
            <h2 id="week-h">Problems logged per week</h2>
          </div>
          <Columns data={weekly} aria="Problems logged per week, last 12 weeks" />
          <TableTwin head={["Week of", "Logged"]} rows={[...weekly].reverse().map((c) => [c.label, c.value])} />
        </section>
        <section className="panel chart-card reveal" aria-labelledby="due-h" style={{ marginTop: 0 }}>
          <div className="section-head">
            <h2 id="due-h">Reviews coming up</h2>
          </div>
          <Columns data={upcoming} aria="Reviews due per day, next 14 days" />
          <TableTwin head={["Day", "Due"]} rows={upcoming.map((c) => [c.label, c.value])} />
        </section>
      </div>

      <section className="panel chart-card section reveal" aria-labelledby="prog-h">
        <div className="section-head">
          <h2 id="prog-h">Where you stand</h2>
          <div className="legend">
            <span>
              <i className="sw" style={{ background: "var(--heat-4)" }} />
              Unaided
            </span>
            <span>
              <i className="sw" style={{ background: "var(--heat-2)" }} />
              Started
            </span>
            <span>
              <i className="sw" style={{ background: "var(--raised)", border: "1px solid var(--line)" }} />
              Not started
            </span>
          </div>
        </div>
        <ProgressBars bars={s.bars} />
        <TableTwin
          head={["List", "Unaided", "Started", "Not started", "Total"]}
          rows={s.bars.map((b) => [b.label, b.solid, b.started, Math.max(b.total - b.solid - b.started, 0), b.total])}
        />
      </section>
    </div>
  );
}

function Kpi({ label, value, suffix, hint }: { label: string; value: number; suffix?: string; hint: string }) {
  return (
    <div className="kpi">
      <span className="label">{label}</span>
      <span className="value">
        <span data-count={value}>{value}</span>
        {suffix && <small> {suffix}</small>}
      </span>
      <span className="hint">{hint}</span>
    </div>
  );
}

function TableTwin({ head, rows, empty }: { head: string[]; rows: (string | number)[][]; empty?: string }) {
  return (
    <details className="table-twin">
      <summary>Show as a table</summary>
      {rows.length === 0 && empty ? (
        <p className="muted" style={{ marginTop: 8 }}>
          {empty}
        </p>
      ) : (
        <div className="table-scroll">
          <table>
            <thead>
              <tr>
                {head.map((h) => (
                  <th key={h}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map((r, i) => (
                <tr key={i}>
                  {r.map((c, j) => (
                    <td key={j}>{c}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </details>
  );
}
