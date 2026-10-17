import { useEffect, useId, useRef, useState } from "react";
import { Link, createFileRoute } from "@tanstack/react-router";
import { useQuery, useSuspenseQuery } from "@tanstack/react-query";
import type { Row, Today, TodaySession } from "../api";
import { DesignLinkList } from "../components/DesignLinks";
import { Icon } from "../components/Icon";
import { SCORE_OPTIONS } from "../components/QuickLog";
import { ReviewList } from "../components/Reviews";
import { Difficulty, ProblemLinks, ProblemRow } from "../components/Rows";
import { gsap, prefersReducedMotion, useGSAP } from "../motion";
import { itemQuery, todayQuery, useCompleteReview, useLogAttempt } from "../queries";

export const Route = createFileRoute("/")({
  loader: ({ context: { queryClient } }) => queryClient.ensureQueryData(todayQuery()),
  component: TodayPage,
});

function formatDate(iso: string) {
  const [y, m, d] = iso.split("-").map(Number);
  return new Date(Date.UTC(y!, m! - 1, d!)).toLocaleDateString("en-GB", { timeZone: "UTC", weekday: "long", day: "numeric", month: "long" });
}

const bareTitle = (title: string) => title.replace(/\s*\(\d+\)\s*$/, "");

function sessionLine(s: TodaySession): string {
  if (s.week_done) return "This week's sessions are done; anything more is extra.";
  return `Session ${s.number} of ${s.of} this week${s.done_today ? ". Today's is logged." : ""}`;
}

function TodayPage() {
  const { data: t } = useSuspenseQuery(todayQuery());
  // Cards that hand over after a log rise in; the first paint does not animate.
  const settled = useRef(false);
  useEffect(() => {
    settled.current = true;
  }, []);

  return (
    <div className="today-page">
      <header className="today-head">
        <p className="kicker">{formatDate(t.on)}</p>
        <h1>{t.day.headline}</h1>
        <p className="session-line">{sessionLine(t.session)}</p>
        {t.quiet_days !== null && (
          <p className="quiet-line">{t.quiet_days} days since your last session. A 10-minute day is enough to restart.</p>
        )}
        <p className="context">
          {t.context}
          <span className="muted"> · {bareTitle(t.list.title)}</span>
        </p>
      </header>

      <div className="today-main">
        <ShortDay t={t} />
        <section className="panel session" aria-labelledby="dsa-h">
          <div className="session-head">
            <h2 id="dsa-h">DSA</h2>
            <span className="mins">{t.day.segments.reduce((n, s) => n + s.minutes, 0)} min</span>
          </div>
          <Hour segments={t.day.segments} />

          {!t.verdict.allow_new_work && (
            <p className="notice">
              <Icon name="arrow-counter-clockwise" />
              <span>{t.verdict.reason}</span>
            </p>
          )}

          <ReviewList reviews={t.reviews} />
          <SessionWork t={t} animate={settled.current} />

          {t.revisit_count > 0 && (
            <p className="muted small revisit">
              {t.revisit_count} solved with help. Their re-solves come back on schedule; no need to grind them now.
            </p>
          )}
        </section>

        {t.design && (
          <section className="panel session session-design" aria-labelledby="design-h">
            <div className="session-head">
              <h2 id="design-h">System design</h2>
              <span className="mins">{t.design.minutes} min, after DSA</span>
            </div>
            <p className="session-count">
              Design session {Math.min(t.design.sessions_done + 1, t.design.sessions_target)} of {t.design.sessions_target} this week
            </p>
            {!t.design.verdict.allow_new_work && (
              <p className="notice">
                <Icon name="arrow-counter-clockwise" />
                <span>{t.design.verdict.reason}</span>
              </p>
            )}
            <ReviewList reviews={t.design.reviews} />
            {t.design.focus && (
              <>
                <p className="subhead">{t.design.focus_is_blocking ? "Finish this first" : "Next"}</p>
                <FocusCard key={`${t.design.focus.id}-${t.design.focus.attempts}`} item={t.design.focus} label="Done for today? Log how it went" design animate={settled.current} />
              </>
            )}
          </section>
        )}
      </div>

      <Rail t={t} />
    </div>
  );
}

/** The hour as one bar, with a legend that never has to squeeze into a 5-minute slice. */
function Hour({ segments }: { segments: Today["day"]["segments"] }) {
  const longest = Math.max(...segments.map((s) => s.minutes));
  return (
    <div className="hour" aria-label="How to spend the hour">
      <div className="hour-bar" aria-hidden="true">
        {segments.map((s, i) => (
          <span key={s.label} className={s.minutes === longest ? "is-main" : undefined} style={{ ["--m" as string]: s.minutes, ["--i" as string]: i }} />
        ))}
      </div>
      <ol className="hour-legend">
        {segments.map((s) => (
          <li key={s.label} className={s.minutes === longest ? "is-main" : undefined}>
            <b className="num">{s.minutes} min</b>
            <span>{s.label}</span>
          </li>
        ))}
      </ol>
    </div>
  );
}

/** One quiet column: where the plan stands, this week, and what is coming back. */
function Rail({ t }: { t: Today }) {
  const pct = t.total ? t.unaided / t.total : 0;
  return (
    <aside className="rail" aria-label="Progress">
      <section className="rail-sec">
        <h2 className="rail-h">Solved unaided</h2>
        <div className="ring-row">
          <Ring value={pct} />
          <p>
            <b className="num">{t.unaided}</b> <span className="muted">of {t.total} in {bareTitle(t.list.title)}</span>
          </p>
        </div>
        <ul className="split">
          {t.split.map((s) => (
            <li key={s.label}>
              <span className={`diff diff-${s.label.toLowerCase()}`}>{s.label}</span>
              <span className="thin" aria-hidden="true">
                <i style={{ width: `${s.total ? (100 * s.solid) / s.total : 0}%` }} data-d={s.label.toLowerCase()} />
              </span>
              <span className="num muted">
                {s.solid}/{s.total}
              </span>
            </li>
          ))}
        </ul>
      </section>

      <section className="rail-sec">
        <div className="rail-row">
          <h2 className="rail-h">Activity</h2>
          <span className="muted small num">
            {t.activity.active_days} day{t.activity.active_days === 1 ? "" : "s"} in 16 weeks
          </span>
        </div>
        <MiniHeat activity={t.activity} today={t.on} />
      </section>

      <section className="rail-sec">
        <h2 className="rail-h">Coming up</h2>
        <p className="rail-line rail-line-plain">
          <span>Reviews due in 7 days</span>
          <b className="num">{t.due_week}</b>
        </p>
        <Link to="/stats" className="rail-link">
          See all progress
          <Icon name="arrow-up-right" />
        </Link>
      </section>
    </aside>
  );
}

/** Sixteen weeks of practice, one column per week, Monday on top. Shade = entries logged. */
function MiniHeat({ activity, today }: { activity: Today["activity"]; today: string }) {
  const level = (n: number) => (n === 0 ? 0 : n === 1 ? 1 : n === 2 ? 2 : n <= 4 ? 3 : 4);
  return (
    <div className="miniheat" role="img" aria-label={`${activity.active_days} days with practice in the last 16 weeks`}>
      {activity.days.map((d) => (
        <span
          key={d.on}
          className={`hc heat-${level(d.n)}${d.future ? " is-future" : ""}${d.on === today ? " is-today" : ""}`}
          title={d.future ? undefined : `${d.on}: ${d.n ? `${d.n} logged` : "nothing logged"}`}
        />
      ))}
    </div>
  );
}

function Ring({ value }: { value: number }) {
  const r = 22;
  const c = 2 * Math.PI * r;
  return (
    <svg className="ring" viewBox="0 0 52 52" aria-hidden="true">
      <circle className="ring-track" cx="26" cy="26" r={r} />
      <circle className="ring-value" cx="26" cy="26" r={r} strokeDasharray={c} strokeDashoffset={c * (1 - Math.min(1, value))} />
      <text x="26" y="26" dominantBaseline="central" textAnchor="middle">
        {Math.round(value * 100)}%
      </text>
    </svg>
  );
}

/** Short on time: ten minutes of recall, offered up front and never required. */
function ShortDay({ t }: { t: Today }) {
  const [open, setOpen] = useState(false);
  const panel = useId();
  const { reviews, recall_item } = t.short_day;
  // A brand-new list has nothing to recall yet; there is no short day to offer.
  if (reviews.length === 0 && !recall_item) return null;
  return (
    <div className="shortday">
      <button type="button" className="btn btn-text btn-sm shortday-toggle" aria-expanded={open} aria-controls={panel} onClick={() => setOpen((o) => !o)}>
        Short on time? Do a 10-minute day
        <Icon name="caret-down" />
      </button>
      {open && (
        <div id={panel} className="shortday-panel">
          {reviews.length > 0 ? (
            <>
              <p className="ink2 small">Ten minutes is a real day. Do these and stop.</p>
              <ReviewList reviews={reviews} />
            </>
          ) : (
            recall_item && <RecallCard item={recall_item} />
          )}
        </div>
      )}
    </div>
  );
}

const RECALL_FALLBACK = "Without opening the solution, say the approach and its complexity out loud.";

function RecallCard({ item }: { item: Row }) {
  const logId = item.log_id ?? item.id;
  // The item page carries the recall prompt; the card reads fine without it while it loads.
  const detail = useQuery(itemQuery(logId));
  const log = useLogAttempt();
  return (
    <article className="recall-card">
      <div className="focus-title">
        <h3>
          <Link to="/items/$id" params={{ id: logId }}>
            {item.title}
          </Link>
        </h3>
        <Difficulty value={item.difficulty} />
      </div>
      <p className="prompt-line">
        <Icon name="target" />
        <span>{detail.data?.prompt || RECALL_FALLBACK}</span>
      </p>
      <div className="form-actions">
        <button type="button" className="btn btn-primary btn-sm" disabled={log.isPending || log.isSuccess} onClick={() => log.mutate({ item_id: logId, mode: "recall", score: null })}>
          <Icon name="check" />
          {log.isPending ? "Logging" : "Done"}
        </button>
        {log.isSuccess && (
          <span className="ok-text" role="status">
            Logged. Ten minutes is enough for today.
          </span>
        )}
        {log.isError && (
          <span className="error-text" role="alert">
            {log.error.message}
          </span>
        )}
      </div>
    </article>
  );
}

/** The session-specific part of the hour, chosen by the kind the server picked for this week. */
function SessionWork({ t, animate }: { t: Today; animate: boolean }) {
  const { kind } = t.session;
  const listName = bareTitle(t.list.title);

  // A blocked queue turns any session into a review session; the blocking problem comes first.
  if (t.focus && t.focus_is_blocking) {
    return (
      <>
        <p className="subhead">Finish this first</p>
        <FocusCard key={`${t.focus.id}-${t.focus.attempts}`} item={t.focus} topic={t.block_topic} resource={t.resource} animate={animate} />
      </>
    );
  }
  if (kind === "learn") {
    if (t.focus) {
      return (
        <>
          <p className="subhead">Next</p>
          <FocusCard key={`${t.focus.id}-${t.focus.attempts}`} item={t.focus} topic={t.block_topic} resource={t.resource} animate={animate} />
        </>
      );
    }
    if (t.verdict.allow_new_work) return <p className="ink2">Every problem in {listName} has been started. Use the hour for re-solves.</p>;
    return null;
  }
  if (kind === "resolve") {
    if (t.pulled_forward && !t.reviews.some((r) => r.kind === "full_solve")) return <PulledForward review={t.pulled_forward} />;
    if (!t.reviews.length)
      return <p className="ink2">Nothing has reached a full re-solve yet. Pick the hardest problem from earlier this week and solve it from a blank editor.</p>;
    return null;
  }
  if (kind === "mixed") {
    return (
      <>
        <p className="subhead">Mixed practice</p>
        <p className="ink2">{t.day.guidance}</p>
        {t.this_week.length > 0 ? (
          <MiniList rows={t.this_week} />
        ) : (
          <p style={{ marginTop: 12 }}>
            <Link to="/problems" search={{ view: t.list.key, q: "" }} className="btn btn-sm">
              <Icon name="list-checks" />
              Pick from {listName}
            </Link>
          </p>
        )}
      </>
    );
  }
  return (
    <>
      <p className="subhead">Catch up</p>
      <p className="ink2">{t.day.guidance}</p>
      {t.blocking.length > 0 && <MiniList rows={t.blocking} pill="No approach yet" />}
      <p style={{ marginTop: 12 }}>
        <Link to="/plan" className="btn btn-sm">
          <Icon name="calendar-blank" />
          See your week
        </Link>
      </p>
    </>
  );
}

function MiniList({ rows, pill }: { rows: Row[]; pill?: string }) {
  return (
    <ul className="rows mini-rows">
      {rows.map((r) => (
        <ProblemRow key={r.id} item={r} badge={pill} />
      ))}
    </ul>
  );
}

function FocusCard({ item, topic, resource, label = "Done? Log how it went", design = false, animate = false }: { item: Row; topic?: string | null; resource?: Today["resource"]; label?: string; design?: boolean; animate?: boolean }) {
  const log = useLogAttempt();
  const [picked, setPicked] = useState<number | null>(null);
  const card = useRef<HTMLElement>(null);
  // Keyed by item: when a logged problem hands over to the next one, the new card
  // rises in. First paint and hidden tabs skip it, so the card is never left invisible.
  useGSAP(() => {
    if (animate && !document.hidden && !prefersReducedMotion()) gsap.from(card.current, { y: 8, opacity: 0, duration: 0.4 });
  }, { scope: card });
  return (
    <article ref={card} className="focus-card">
      <div className="focus-title">
        <span className="mono muted">{design ? item.block : item.external_id}</span>
        <h3>
          <Link to="/items/$id" params={{ id: item.id }}>
            {item.title}
          </Link>
        </h3>
        {item.is_anchor && !design && <span className="pill">Anchor</span>}
        {design && item.section && <span className="pill">{item.section}</span>}
      </div>
      {design ? (
        <>
          {item.focus && <p className="ink2 small">Make: {item.focus}</p>}
          {item.note && <p className="muted small">{item.note}</p>}
          <DesignLinkList links={item.links ?? []} />
        </>
      ) : (
        <>
          <div className="focus-meta">
            <Difficulty value={item.difficulty} />
            {topic && <span>Learn first: {topic}</span>}
          </div>
          {resource && (
            <p className="ink2 small">
              New to this? Start with{" "}
              {resource.url ? (
                <a href={resource.url} target="_blank" rel="noreferrer">
                  {resource.name}
                </a>
              ) : (
                resource.name
              )}
              {resource.creator ? ` by ${resource.creator}` : ""}.
            </p>
          )}
          <div className="linkset-wide">
            <ProblemLinks item={item} wide />
          </div>
        </>
      )}
      {!design && <Timebox />}
      <div className="scorebar">
        <p className="scorebar-label">{log.isError ? log.error.message : label}</p>
        <div className="scorebar-buttons">
          {SCORE_OPTIONS.map((o) => (
            <button
              key={o.n}
              type="button"
              className={`score-btn${picked === o.n ? " is-done" : ""}`}
              title={o.long}
              disabled={log.isPending || log.isSuccess}
              onClick={() => {
                setPicked(o.n);
                log.mutate({ item_id: item.id, mode: item.attempts === 0 ? "solve" : "resolve", score: o.n });
              }}
            >
              <span className="n">{o.n}</span>
              {o.short}
            </button>
          ))}
        </div>
      </div>
    </article>
  );
}

/** The protocol, shown where it is used: on the card for the problem in front of you. */
function Timebox() {
  return (
    <div className="timebox">
      <ol className="timebox-steps" aria-label="Timebox in minutes">
        <li>
          <b className="num">0-5</b> restate and brute force
        </li>
        <li>
          <b className="num">5-20</b> find the improvement
        </li>
        <li>
          <b className="num">20-35</b> code
        </li>
      </ol>
      <p>Stuck for 10 minutes? Take one small hint.</p>
    </div>
  );
}

function PulledForward({ review }: { review: NonNullable<Today["pulled_forward"]> }) {
  const complete = useCompleteReview();
  return (
    <>
      <p className="subhead">Nothing due for a full re-solve. Pull this one forward</p>
      <article className="focus-card">
        <div className="focus-title">
          <h3>
            <Link to="/items/$id" params={{ id: review.item_id }}>
              {review.title}
            </Link>
          </h3>
          <span className="pill">Due {review.due_date}</span>
        </div>
        <p className="ink2 small">Blank editor, no peeking. Then mark it below.</p>
        <div className="review-actions">
          {review.url && (
            <a className="btn btn-sm" href={review.url} target="_blank" rel="noreferrer">
              <Icon name="code" />
              Open problem
            </a>
          )}
          <button type="button" className="btn btn-sm btn-good" disabled={complete.isPending} onClick={() => complete.mutate({ id: review.id, outcome: "pass" })}>
            <Icon name="check" />
            Got it
          </button>
          <button type="button" className="btn btn-sm btn-bad" disabled={complete.isPending} onClick={() => complete.mutate({ id: review.id, outcome: "fail" })}>
            <Icon name="x" />
            Missed
          </button>
        </div>
      </article>
    </>
  );
}
