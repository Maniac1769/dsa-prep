import { useState, type CSSProperties } from "react";
import { flushSync } from "react-dom";
import { Link } from "@tanstack/react-router";
import type { Review } from "../api";
import { prefersReducedMotion } from "../motion";
import { useCompleteReview, useSpreadOverdue } from "../queries";
import { Icon } from "./Icon";

const KIND: Record<Review["kind"], string> = { recall: "Recall", full_solve: "Full re-solve", rebuild: "Rebuild" };
const VISIBLE = 5;

/**
 * Reviews due now. A resolved row slides out and the rows below glide up into the gap.
 * The browser's view transition snapshots before and after, so the reflow is a
 * compositor animation with no library; where unsupported, the row simply goes.
 */
export function ReviewList({ reviews }: { reviews: Review[] }) {
  const complete = useCompleteReview();
  const [hidden, setHidden] = useState<Set<number>>(() => new Set());
  const [expanded, setExpanded] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const spread = useSpreadOverdue();
  const remaining = reviews.filter((r) => !hidden.has(r.id));
  const overdue = remaining.filter((r) => r.days_late > 0).length;
  const shown = expanded ? remaining : remaining.slice(0, VISIBLE);

  if (remaining.length === 0) return null;

  const kinds = new Set(remaining.map((r) => r.kind));
  const resolve = (r: Review, outcome: "pass" | "fail") => {
    setError(null);
    const hide = () => setHidden((s) => new Set(s).add(r.id));
    complete.mutate(
      { id: r.id, outcome },
      {
        onError: (err) => {
          setHidden((s) => {
            const next = new Set(s);
            next.delete(r.id);
            return next;
          });
          setError(err.message);
        },
      },
    );
    if (prefersReducedMotion() || !document.startViewTransition) hide();
    else document.startViewTransition(() => flushSync(hide));
  };

  return (
    <>
      <p className="subhead">Due now · {remaining.length}</p>
      <p className="prompt-line">
        <Icon name="target" />
        <span>
          {kinds.has("recall") && <>Recall: {remaining.find((r) => r.kind === "recall")?.prompt.toLowerCase()} </>}
          {kinds.has("full_solve") && <>Full re-solve: from a blank editor, no notes, then test it. </>}
          {kinds.has("rebuild") && <>Rebuild: blank page, 20 minutes, then compare with your original.</>}
        </span>
      </p>
      {overdue > 3 && (
        <div className="backlog">
          <p>
            {overdue} of these piled up from earlier days. Spreading them puts at most three on each day, oldest first.
          </p>
          <button type="button" className="btn btn-sm" disabled={spread.isPending} onClick={() => spread.mutate()}>
            <Icon name="calendar-blank" />
            {spread.isPending ? "Spreading" : "Spread over the next days"}
          </button>
          {spread.isError && <span className="error-text">{spread.error.message}</span>}
        </div>
      )}
      {error && <p className="notice notice-bad">{error}</p>}
      <div>
        {shown.map((r) => (
          <div className="review" data-review-row key={r.id} style={{ viewTransitionName: `rv-${r.id}`, viewTransitionClass: "review" } as CSSProperties}>
            <div className="review-title">
              <Link to="/items/$id" params={{ id: r.item_id }}>
                {r.title}
              </Link>
              <span className="pill">{KIND[r.kind]}</span>
              {r.days_late > 0 && (
                <span className="pill" title={`Was due ${r.due_date}`}>
                  Overdue
                </span>
              )}
              {r.url && r.kind !== "recall" && (
                <a className="link-icon" href={r.url} target="_blank" rel="noreferrer" title="Open the problem" aria-label={`Open ${r.title}`}>
                  <Icon name="code" />
                </a>
              )}
            </div>
            <div className="review-actions">
              <button type="button" className="btn btn-sm btn-good" onClick={() => resolve(r, "pass")}>
                <Icon name="check" />
                Got it
              </button>
              <button type="button" className="btn btn-sm btn-bad" onClick={() => resolve(r, "fail")}>
                <Icon name="x" />
                Missed
              </button>
            </div>
          </div>
        ))}
      </div>
      {remaining.length > VISIBLE && (
        <button type="button" className="text-btn" onClick={() => setExpanded((v) => !v)}>
          {expanded ? "Show fewer" : `Show ${remaining.length - VISIBLE} more`}
        </button>
      )}
    </>
  );
}
