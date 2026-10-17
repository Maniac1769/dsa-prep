import { Link, createFileRoute } from "@tanstack/react-router";
import { useSuspenseQuery } from "@tanstack/react-query";
import { useRef } from "react";
import { DesignLinkChips } from "../components/DesignLinks";
import { QuickLogTrigger } from "../components/QuickLog";
import { designQuery } from "../queries";

export const Route = createFileRoute("/design")({
  loader: ({ context: { queryClient } }) => queryClient.ensureQueryData(designQuery()),
  component: DesignPage,
});

const PHASE_NOTE: Record<string, string> = {
  "1": "Object-oriented fundamentals, the patterns that actually come up, and your first machine-coding builds.",
  "2": "The interview framework, estimation, the building blocks, and the classic designs.",
  "3": "Concurrency in C++, harder machine coding, and designs that survive a new requirement.",
  "4": "Consistency, failure, and the harder designs interviewers dig into.",
  "5": "Mocks out loud, and repairing whatever scored 0 or 1.",
};

function DesignPage() {
  const { data } = useSuspenseQuery(designQuery());
  const page = useRef<HTMLDivElement>(null);
  const total = data.phases.reduce((n, p) => n + p.rows.length, 0);
  const done = data.phases.reduce((n, p) => n + p.done, 0);
  const linked = data.phases.reduce((n, p) => n + p.rows.filter((r) => (r.links ?? []).length > 0).length, 0);

  return (
    <div ref={page}>
      <header className="page-head">
        <h1>System design</h1>
        <p className="sub">
          LLD first, then HLD, interleaved so neither goes cold. Blocks link out to a video to watch, something to read, and often a C++ reference or a place to
          practise. End every block with a decision note: what you chose, what you rejected, and the number that decided it.
        </p>
        <p className="muted small">
          {done} of {total} blocks solid{linked ? ` · ${linked} blocks with curated links` : ""}
        </p>
      </header>

      {data.phases.map((p) => (
        <section className="group phase" key={p.no ?? p.title}>
          <div className="group-head">
            <h2>
              <span className="phase-no">Phase {p.no}</span>
              {p.title}
            </h2>
            <div className="meta">
              <span className="num">
                {p.done} / {p.rows.length} solid
              </span>
            </div>
          </div>
          {p.no && PHASE_NOTE[p.no] && <p className="muted small phase-note">{PHASE_NOTE[p.no]}</p>}
          <ul className="drows">
            {p.rows.map((r) => (
              <li key={r.id} className={`drow${r.id === data.next_id ? " is-next" : ""}`}>
                <QuickLogTrigger itemId={r.id} status={r.status} title={r.title} />
                <div className="drow-main">
                  <div className="row-title">
                    <span className="mono">{r.block}</span>
                    <Link to="/items/$id" params={{ id: r.id }}>
                      {r.title}
                    </Link>
                    {r.id === data.next_id && <span className="pill pill-accent">Next</span>}
                    {r.section && <span className="pill">{r.section}</span>}
                    {r.is_anchor && (
                      <span className="pill" title="Anchor: rebuilt from a blank page at about +21 and +60 days">
                        Anchor
                      </span>
                    )}
                  </div>
                  {r.focus && <p className="drow-make">Make: {r.focus}</p>}
                  <DesignLinkChips links={r.links ?? []} />
                </div>
              </li>
            ))}
          </ul>
        </section>
      ))}
    </div>
  );
}
