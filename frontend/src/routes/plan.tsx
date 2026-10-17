import { useState } from "react";
import { createFileRoute } from "@tanstack/react-router";
import { useSuspenseQuery } from "@tanstack/react-query";
import type { Plan, PlanSession, Resource, RoadGroup, RoadState, RoadStep, SessionKind } from "../api";
import { Icon } from "../components/Icon";
import { ResetPanel } from "../components/Reset";
import { Stepper } from "../components/Stepper";
import { planQuery, useSaveAccountSettings } from "../queries";

export const Route = createFileRoute("/plan")({
  loader: ({ context: { queryClient } }) => queryClient.ensureQueryData(planQuery()),
  component: PlanPage,
});

const plural = (n: number, word: string) => `${n} ${word}${n === 1 ? "" : "s"}`;

/** "At 3 new problems a week, this list takes about 42 more weeks." */
function paceSentence(pace: Plan["pace"]): string {
  if (pace.weeks_left <= 0) return "Every problem in this list has been started.";
  return `At ${plural(pace.new_per_week, "new problem")} a week, this list takes about ${plural(pace.weeks_left, "more week")}. A slower week just moves the date.`;
}

const isGroup = (r: RoadGroup | RoadStep): r is RoadGroup => "group" in r;

/** Sheet steps carry only done and total; the first unfinished step is where you are. */
function stepStates(steps: RoadStep[]): RoadState[] {
  const current = steps.findIndex((s) => s.done < s.total);
  return steps.map((s, i) => s.state ?? (s.done >= s.total ? "done" : i === current ? "current" : "upcoming"));
}

function PlanPage() {
  const { data: p } = useSuspenseQuery(planQuery());
  const groups = p.roadmap.filter(isGroup);
  const steps = p.roadmap.filter((r): r is RoadStep => !isGroup(r));
  const states = stepStates(steps);
  return (
    <>
      <header className="page-head">
        <h1>Plan</h1>
        <p className="sub">{paceSentence(p.pace)}</p>
      </header>

      <Schedule p={p} />

      <div className="two-col section">
        <section className="panel" aria-labelledby="road-h">
          <div className="section-head">
            <h2 id="road-h">{groups.length > 0 ? "DSA roadmap" : "Your list, step by step"}</h2>
            {groups.length > 0 && <p>42 blocks, three problems each</p>}
          </div>
          <ol className="road">
            {groups.map((r) => (
              <RoadItem key={r.group.key} state={r.state} title={r.group.title} count={`${r.done}/${r.rows}`}>
                <span>
                  Blocks {r.group.first}
                  {r.group.last !== r.group.first && ` to ${r.group.last}`}
                </span>
                {r.resources[0] && (
                  <span>
                    Learn from <ResourceLink r={r.resources[0]} />
                  </span>
                )}
              </RoadItem>
            ))}
            {steps.map((r, i) => (
              <RoadItem key={`${r.no ?? ""}${r.title}`} state={states[i] ?? "upcoming"} title={r.no ? `${r.no}. ${r.title}` : r.title} count={`${r.done}/${r.total}`} />
            ))}
            {groups.length > 0 && (
              <RoadItem state="upcoming" title="Interview preparation" count="4 wk">
                <span>Role targeting, timed mocks, unseen problems, failure repair</span>
              </RoadItem>
            )}
          </ol>
        </section>

        <section className="panel" aria-labelledby="droad-h">
          <div className="section-head">
            <h2 id="droad-h">System design roadmap</h2>
            <p>34 blocks</p>
          </div>
          <ol className="road">
            {p.design_road.map((d) => (
              <RoadItem key={d.no} state={d.state} title={d.title} count={`${d.done}/${d.count}`} />
            ))}
          </ol>
          <p className="muted small" style={{ marginTop: 12 }}>
            Phase 2 starts after the timed L9 build scores 2 or better.
          </p>
        </section>
      </div>

      <div className="two-col section">
        <section className="panel" aria-labelledby="session-h">
          <div className="section-head">
            <h2 id="session-h">A 45-minute DSA session</h2>
          </div>
          <ol className="steps">
            {p.session_steps.map((s) => (
              <li key={s.t}>
                <span className="t">{s.t} min</span>
                <p>{s.text}</p>
              </li>
            ))}
          </ol>
          <p className="muted small" style={{ marginTop: 10 }}>
            Brand-new topic: up to 20 minutes learning, then at least 25 implementing. Nobody discovers Dijkstra unaided.
          </p>
        </section>
        <section className="panel" aria-labelledby="dsession-h">
          <div className="section-head">
            <h2 id="dsession-h">A design session</h2>
          </div>
          <ol className="steps">
            {p.design_shapes.map((s) => (
              <li key={s.name}>
                <span className="t">{s.name}</span>
                <p>{s.text}</p>
              </li>
            ))}
          </ol>
          <p className="muted small" style={{ marginTop: 10 }}>
            Every block ends with one Defend session. A design you have never defended is not learned.
          </p>
        </section>
      </div>

      <section className="panel section" aria-labelledby="rules-h">
        <div className="section-head">
          <h2 id="rules-h">How scoring and reviews work</h2>
        </div>
        <div className="two-col" style={{ gap: 28 }}>
          <ol className="steps">
            {p.scores.map((s) => (
              <li key={s.n}>
                <span className="t">Score {s.n}</span>
                <p>{s.text}</p>
              </li>
            ))}
          </ol>
          <div className="rules">
            <div>
              <p className="label">DSA review ladder, days after first study</p>
              <p className="ladder">
                {p.ladder.recall_offsets.map((d) => (
                  <span key={`r${d}`} className="pill">
                    +{d} recall
                  </span>
                ))}
              </p>
              <p className="ladder">
                {p.ladder.anchor_offsets.map((d) => (
                  <span key={`a${d}`} className="pill pill-accent">
                    +{d} full re-solve
                  </span>
                ))}
              </p>
              <p className="muted">Anchors only: one per block. A re-solve replaces the recall due the same day.</p>
            </div>
            <div>
              <p className="label">Design review ladder</p>
              <p className="ladder">
                {p.design_ladder.recall_offsets.map((d) => (
                  <span key={`dr${d}`} className="pill">
                    +{d} recall
                  </span>
                ))}
              </p>
              <p className="ladder">
                {p.design_ladder.anchor_offsets.map((d) => (
                  <span key={`da${d}`} className="pill pill-accent">
                    +{d} rebuild
                  </span>
                ))}
              </p>
            </div>
            <p className="ink2">
              New work pauses when more than {p.ladder.max_queued_anchor} re-solves are due, more than {p.ladder.max_overdue_recall} recalls are overdue, or a failed
              review has waited over a week. Missed a day? Do not double tomorrow.
            </p>
          </div>
        </div>
      </section>

      <Resources p={p} />
      <ResetPanel />
    </>
  );
}

const KIND_NOTE: Record<SessionKind, string> = {
  learn: "New problems, one small hint if you are stuck",
  resolve: "Re-solve earlier work from a blank editor",
  mixed: "Mixed practice across topics",
  catchup: "Finish what is still open",
};

const WEEKLY = [3, 4, 5, 6, 7] as const;
const DESIGN_SESSIONS = [0, 1, 2, 3, 4, 5, 6, 7] as const;
const DESIGN_MINUTES = [15, 30, 45, 60] as const;

function SessionRow({ s }: { s: PlanSession }) {
  return (
    <li className={`session-row${s.next ? " is-next" : ""}${s.done ? " is-done" : ""}`}>
      <span className="session-mark" aria-hidden="true">
        {s.done && <Icon name="check" />}
      </span>
      <span className="session-name">
        {s.label}
        {s.next && <span className="here">Next</span>}
        {s.done && <span className="sr-only"> (done)</span>}
      </span>
      <span className="session-note">{KIND_NOTE[s.kind]}</span>
      <span className="mins num">{s.minutes} min</span>
    </li>
  );
}

function Schedule({ p }: { p: Plan }) {
  const save = useSaveAccountSettings();
  const [weekly, setWeekly] = useState(p.weekly_sessions);
  const [design, setDesign] = useState(p.design_sessions);
  const [minutes, setMinutes] = useState(p.design_minutes);
  const dirty = weekly !== p.weekly_sessions || design !== p.design_sessions || minutes !== p.design_minutes;

  return (
    <section className="panel" id="schedule" aria-labelledby="week-h">
      <div className="section-head">
        <h2 id="week-h">This week</h2>
        <p>{plural(p.sessions.filter((s) => s.done).length, "session")} done of {p.sessions.length}. A missed day costs nothing; the next session is simply the next one.</p>
      </div>
      <ol className="session-list">
        {p.sessions.map((s, i) => (
          <SessionRow key={`${i}-${s.kind}`} s={s} />
        ))}
      </ol>

      <form
        className="controls settings-form"
        aria-label="Weekly budget"
        onSubmit={(e) => {
          e.preventDefault();
          if (dirty) save.mutate({ weekly_sessions: weekly, design_sessions: design, design_minutes: minutes });
        }}
      >
        <span className="ctl">
          <span className="ctl-label">DSA sessions</span>
          <Stepper small label="DSA sessions per week" values={WEEKLY} value={weekly} onChange={setWeekly} />
        </span>
        <span className="ctl">
          <span className="ctl-label">Design sessions</span>
          <Stepper small label="Design sessions per week" values={DESIGN_SESSIONS} value={design} onChange={setDesign} />
        </span>
        <span className="ctl">
          <span className="ctl-label">Design length</span>
          <Stepper small label="Design session length" values={DESIGN_MINUTES} value={minutes} onChange={setMinutes} suffix=" min" />
        </span>
        <button className="btn btn-sm" type="submit" disabled={!dirty || save.isPending}>
          {save.isSuccess && !dirty ? (
            <>
              <Icon name="check" />
              Saved
            </>
          ) : (
            "Save"
          )}
        </button>
        {save.isError && <span className="error-text">{save.error.message}</span>}
      </form>
      <p className="muted small" style={{ marginTop: 8 }}>
        Set a number you can keep in your busiest week.
      </p>
    </section>
  );
}

function RoadItem({ state, title, count, children }: { state: RoadState; title: string; count: string; children?: React.ReactNode }) {
  return (
    <li data-state={state}>
      <span className="mark">{state === "done" && <Icon name="check" />}</span>
      <span className="r-title">
        {title} {state === "current" && <span className="here">You are here</span>}
      </span>
      <span className="r-count">{count}</span>
      {children && <span className="r-meta">{children}</span>}
    </li>
  );
}

function ResourceLink({ r }: { r: Resource }) {
  return r.url ? (
    <a href={r.url} target="_blank" rel="noreferrer">
      {r.name}
    </a>
  ) : (
    <>{r.name}</>
  );
}

function Resources({ p }: { p: Plan }) {
  const rows = p.roadmap.filter(isGroup).filter((r) => r.resources.length > 0);
  if (rows.length === 0 && p.extra_topics.length === 0) return null;
  const all = [
    ...rows.map((r) => ({ key: r.group.key, label: r.group.title, resources: r.resources })),
    ...p.extra_topics.map((t) => ({ key: t.key, label: t.key === "cpp_stl" ? "C++ STL" : "How to practise", resources: t.resources })),
  ];
  return (
    <section className="panel section" aria-labelledby="res-h" id="resources">
      <div className="section-head">
        <h2 id="res-h">Best free resource per topic</h2>
        <p>Researched October 2026. Sources and evidence: seed/TOPIC-RESOURCES.md</p>
      </div>
      <table className="res-table">
        <thead>
          <tr>
            <th>Topic</th>
            <th>Start with</th>
          </tr>
        </thead>
        <tbody>
          {all.map(({ key, label, resources }) => {
            const [top, ...alts] = resources;
            if (!top) return null;
            return (
              <tr key={key}>
                <td>{label}</td>
                <td>
                  <ResourceLink r={top} />
                  {top.creator && <span className="muted">, {top.creator}</span>}
                  {top.language && (
                    <span className="pill" style={{ marginLeft: 6 }}>
                      {top.language}
                    </span>
                  )}
                  {top.why && <p className="why">{top.why}</p>}
                  {alts.length > 0 && (
                    <p className="alt">
                      Also:{" "}
                      {alts.map((a, i) => (
                        <span key={a.name}>
                          <ResourceLink r={a} />
                          {a.creator && ` (${a.creator})`}
                          {i < alts.length - 1 && ", "}
                        </span>
                      ))}
                    </p>
                  )}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </section>
  );
}
