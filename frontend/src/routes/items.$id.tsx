import { useState } from "react";
import { Link, createFileRoute, notFound } from "@tanstack/react-router";
import { useQuery, useSuspenseQuery } from "@tanstack/react-query";
import type { Mode } from "../api";
import { DesignLinkList } from "../components/DesignLinks";
import { Icon } from "../components/Icon";
import { HoldButton, UndoBar } from "../components/Reset";
import { SCORE_OPTIONS } from "../components/QuickLog";
import { Difficulty, ProblemLinks, StarButton } from "../components/Rows";
import { STATUS_LABEL, StatusMark } from "../components/StatusMark";
import { itemQuery, meQuery, resetQuery, useLogAttempt, useReset, useSaveDecision } from "../queries";

export const Route = createFileRoute("/items/$id")({
  params: {
    parse: ({ id }) => {
      const n = Number(id);
      if (!Number.isInteger(n) || n <= 0) throw notFound();
      return { id: n };
    },
    stringify: ({ id }) => ({ id: String(id) }),
  },
  loader: ({ context: { queryClient }, params }) => queryClient.ensureQueryData(itemQuery(params.id)),
  component: ItemPage,
});

const DESIGN = new Set(["lld", "hld", "prep"]);
const KIND = { recall: "Recall", full_solve: "Full re-solve", rebuild: "Rebuild" } as const;
const MODES: { value: Mode; label: string }[] = [
  { value: "solve", label: "First real attempt" },
  { value: "learn", label: "Studied it, did not solve" },
  { value: "resolve", label: "Came back to it" },
  { value: "rebuild", label: "Blank page, timed" },
  { value: "mock", label: "Timed, out loud" },
];

function ItemPage() {
  const { id } = Route.useParams();
  const { data } = useSuspenseQuery(itemQuery(id));
  const { item } = data;
  const { data: user } = useSuspenseQuery(meQuery());
  const design = DESIGN.has(item.track);
  // Rows of the two Striver sheets use the sheet layout; the plan's track is "dsa".
  const sheet = item.track === "a2z" || item.track === "sde";
  const inYourList = item.track === (user.preferred_list === "plan" ? "dsa" : user.preferred_list);

  return (
    <>
      {design ? (
        <Link to="/design" className="back">
          <Icon name="caret-down" />
          System design
        </Link>
      ) : sheet ? (
        <Link to="/problems" search={{ view: item.track === "sde" ? "sde" : "a2z", q: "" }} className="back">
          <Icon name="caret-down" />
          {item.track === "sde" ? "Striver SDE sheet" : "Striver A2Z sheet"}
        </Link>
      ) : (
        <Link to="/problems" search={{ view: "plan", q: "" }} className="back">
          <Icon name="caret-down" />
          Block {item.block}
        </Link>
      )}

      <header className="page-head">
        <p className="kicker">
          {item.track === "dsa" && data.topic && `Block ${item.block}: ${data.topic}`}
          {sheet && `${item.section ?? ""}${item.subsection ? `, ${item.subsection}` : ""}`}
          {design && `${item.track.toUpperCase()} · ${item.block}`}
        </p>
        <div className="title-row">
          <StatusMark status={item.status} />
          <h1>{item.title}</h1>
        </div>
        <div className="focus-meta">
          <span>{STATUS_LABEL[item.status]}</span>
          <Difficulty value={item.difficulty} />
          {item.platform && item.external_id && (
            <span className="mono">
              {item.platform} {item.external_id}
            </span>
          )}
          {item.is_anchor && <span className="pill">Anchor</span>}
          {design && item.section && <span className="pill">{item.section}</span>}
        </div>
        {data.plan_twin && (
          <p className="sub">
            This problem is also block {data.plan_twin.block} of your plan.{" "}
            <Link to="/items/$id" params={{ id: data.plan_twin.id }}>
              Log it there
            </Link>{" "}
            so the progress stays in one place.
          </p>
        )}
        {!design && (
          <div className="item-links">
            <ProblemLinks item={item} wide />
            {sheet && !data.plan_twin && !inYourList && <StarButton item={item} wide />}
          </div>
        )}
      </header>

      <div className="two-col">
        <div className="stack">
          {(item.focus || design) && (
            <section className="panel">
              {item.focus && (
                <>
                  <p className="label">{design ? "Make" : "Focus"}</p>
                  <p>{item.focus}</p>
                </>
              )}
              {item.note && <p className="muted small" style={{ marginTop: 6 }}>{item.note}</p>}
              {design && (item.links ?? []).length > 0 && (
                <>
                  <p className="label" style={{ marginTop: 14 }}>
                    Watch, read, practise
                  </p>
                  <DesignLinkList links={item.links ?? []} />
                </>
              )}
            </section>
          )}
          <LogForm itemId={item.id} attempts={item.attempts} key={`log-${item.id}`} />
          {design && <DecisionForm itemId={item.id} decisions={data.decisions} />}
        </div>

        <div className="stack">
          <div className="prompt-card">
            <span className="label">Recall prompt</span>
            <p>{data.prompt}</p>
          </div>

          <section className="panel" aria-labelledby="rev-h">
            <div className="section-head">
              <h2 id="rev-h">Reviews</h2>
            </div>
            {data.reviews.length > 0 ? (
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Kind</th>
                    <th>Due</th>
                    <th>Result</th>
                  </tr>
                </thead>
                <tbody>
                  {data.reviews.map((r) => (
                    <tr key={r.id}>
                      <td>{KIND[r.kind]}</td>
                      <td>{r.due_date}</td>
                      <td>
                        {r.outcome ? (
                          <>
                            <span className={`outcome-${r.outcome}`}>{r.outcome === "pass" ? "Passed" : "Missed"}</span> <span className="muted">{r.done_date}</span>
                          </>
                        ) : (
                          <span className="muted">Waiting</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <p className="muted small">
                {!design && !inYourList && !item.starred
                  ? "Problems outside your list stay out of the review queue unless you star them."
                  : "The review ladder is laid down when you log the first attempt."}
              </p>
            )}
          </section>

          <section className="panel" aria-labelledby="hist-h">
            <div className="section-head">
              <h2 id="hist-h">History</h2>
              <p>
                {data.attempts.length} entr{data.attempts.length === 1 ? "y" : "ies"}
              </p>
            </div>
            {data.attempts.length > 0 ? (
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Date</th>
                    <th>What</th>
                    <th>Score</th>
                  </tr>
                </thead>
                <tbody>
                  {data.attempts.map((a) => (
                    <tr key={a.id}>
                      <td>{a.on_date}</td>
                      <td>
                        {a.mode}
                        {a.minutes ? `, ${a.minutes} min` : ""}
                        {a.note && (
                          <>
                            <br />
                            <span className="muted">{a.note}</span>
                          </>
                        )}
                      </td>
                      <td>{a.score ?? ""}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <p className="muted small">Not started.</p>
            )}
            <ItemReset itemId={item.id} empty={data.attempts.length === 0 && data.reviews.length === 0} />
          </section>
        </div>
      </div>
    </>
  );
}

/** Clear one problem's attempts, reviews and notes, so it reads as never started. */
function ItemReset({ itemId, empty }: { itemId: number; empty: boolean }) {
  const { data } = useQuery(resetQuery());
  const reset = useReset();
  const undo = data?.undo?.scope === "item" ? data.undo : null;
  if (empty && !undo) return null;
  return (
    <div className="item-reset">
      {undo && <UndoBar undo={undo} />}
      {!empty && (
        <div className="item-reset-row">
          <p className="muted small">Start this problem over: history, reviews and notes are cleared.</p>
          <HoldButton label="Hold to reset" pending={reset.isPending} onConfirm={() => reset.mutate({ scope: "item", item_id: itemId })} />
        </div>
      )}
      {reset.isError && <p className="error-text">{reset.error.message}</p>}
    </div>
  );
}

function LogForm({ itemId, attempts }: { itemId: number; attempts: number }) {
  const log = useLogAttempt();
  const [mode, setMode] = useState<Mode>(attempts === 0 ? "solve" : "resolve");
  const [minutes, setMinutes] = useState("");
  const [score, setScore] = useState("");
  const [note, setNote] = useState("");

  return (
    <section className="panel" aria-labelledby="log-h">
      <div className="section-head">
        <h2 id="log-h">Log an attempt</h2>
      </div>
      <form
        className="form-grid"
        onSubmit={(e) => {
          e.preventDefault();
          log.mutate(
            { item_id: itemId, mode, score: score === "" ? null : Number(score), minutes: minutes === "" ? null : Number(minutes), note },
            {
              onSuccess: () => {
                setMinutes("");
                setScore("");
                setNote("");
                setMode("resolve");
              },
            },
          );
        }}
      >
        <div className="field-row">
          <label className="field">
            <span>What you did</span>
            <select value={mode} onChange={(e) => setMode(e.target.value as Mode)}>
              {MODES.map((m) => (
                <option key={m.value} value={m.value}>
                  {m.label}
                </option>
              ))}
            </select>
          </label>
          <label className="field">
            <span>Minutes</span>
            <input type="number" min={1} max={600} inputMode="numeric" placeholder="45" value={minutes} onChange={(e) => setMinutes(e.target.value)} />
          </label>
        </div>
        <label className="field">
          <span>How it went</span>
          <select value={score} onChange={(e) => setScore(e.target.value)}>
            <option value="">Not scored</option>
            {SCORE_OPTIONS.map((o) => (
              <option key={o.n} value={o.n}>
                {o.n}: {o.long}
              </option>
            ))}
          </select>
        </label>
        <label className="field">
          <span>What to remember next time</span>
          <input type="text" maxLength={2000} placeholder="The idea you missed, or the bug that cost you" value={note} onChange={(e) => setNote(e.target.value)} />
        </label>
        <div className="form-actions">
          <button className="btn btn-primary" type="submit" disabled={log.isPending}>
            {log.isPending ? "Saving" : "Log attempt"}
          </button>
          {log.isSuccess && !log.isPending && (
            <span className="ok-text">
              <Icon name="check" />
              Logged
            </span>
          )}
          {log.isError && <span className="error-text">{log.error.message}</span>}
        </div>
      </form>
      <p className="muted small" style={{ marginTop: 12 }}>
        Reproducing a solution after watching it is a 1, however clean it looks. A 3 means you could take a new requirement and say exactly what changes.
      </p>
    </section>
  );
}

function DecisionForm({ itemId, decisions }: { itemId: number; decisions: { id: number; chose: string; rejected: string | null; because: string | null; on_date: string }[] }) {
  const save = useSaveDecision(itemId);
  const [chose, setChose] = useState("");
  const [rejected, setRejected] = useState("");
  const [because, setBecause] = useState("");
  return (
    <section className="panel" id="decisions" aria-labelledby="dec-h">
      <div className="section-head">
        <h2 id="dec-h">Decision note</h2>
        <p>Write it now, while you remember why</p>
      </div>
      <form
        className="form-grid"
        onSubmit={(e) => {
          e.preventDefault();
          save.mutate({ chose, rejected, because }, { onSuccess: () => (setChose(""), setRejected(""), setBecause("")) });
        }}
      >
        <label className="field">
          <span>I chose</span>
          <input type="text" required maxLength={500} placeholder="Fan-out on write for normal users" value={chose} onChange={(e) => setChose(e.target.value)} />
        </label>
        <label className="field">
          <span>Over</span>
          <input type="text" maxLength={500} placeholder="Fan-out on read" value={rejected} onChange={(e) => setRejected(e.target.value)} />
        </label>
        <label className="field">
          <span>Because</span>
          <input type="text" maxLength={500} placeholder="The number or constraint that decided it" value={because} onChange={(e) => setBecause(e.target.value)} />
        </label>
        <div className="form-actions">
          <button className="btn" type="submit" disabled={save.isPending}>
            Save note
          </button>
          {save.isError && <span className="error-text">{save.error.message}</span>}
        </div>
      </form>
      {decisions.length > 0 && (
        <ul className="mini-list" style={{ marginTop: 14 }}>
          {decisions.map((d) => (
            <li key={d.id}>
              <span>
                <b>{d.chose}</b>
                {d.rejected && ` over ${d.rejected}`}
                {d.because && `, because ${d.because}`}
              </span>
              <span className="muted num small">{d.on_date}</span>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
