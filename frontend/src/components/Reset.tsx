import { useEffect, useId, useRef, useState, type KeyboardEvent } from "react";
import { useQuery } from "@tanstack/react-query";
import type { ResetPreview, ResetScope } from "../api";
import { resetQuery, useReset, useUndoReset } from "../queries";
import type { IconName } from "../icon-names";
import { Icon } from "./Icon";

const HOLD_MS = 1500;

/**
 * A destructive button that fires only after being held. The fill sweeps across while
 * held (slow, linear: the user is deciding) and snaps back on release (fast: the
 * system is responding). Space or Enter held down works the same as a pointer.
 */
export function HoldButton({
  label,
  onConfirm,
  disabled = false,
  pending = false,
  pendingLabel = "Resetting",
  icon = "arrow-counter-clockwise",
}: {
  label: string;
  onConfirm: () => void;
  disabled?: boolean;
  pending?: boolean;
  pendingLabel?: string;
  icon?: IconName;
}) {
  const [holding, setHolding] = useState(false);
  const timer = useRef<number | null>(null);
  const hint = useId();

  const stop = () => {
    if (timer.current !== null) window.clearTimeout(timer.current);
    timer.current = null;
    setHolding(false);
  };
  const start = () => {
    if (disabled || pending || timer.current !== null) return;
    setHolding(true);
    timer.current = window.setTimeout(() => {
      timer.current = null;
      setHolding(false);
      onConfirm();
    }, HOLD_MS);
  };
  useEffect(() => stop, []);

  const onKeyDown = (e: KeyboardEvent) => {
    if (e.key !== " " && e.key !== "Enter") return;
    e.preventDefault();
    if (!e.repeat) start();
  };
  const onKeyUp = (e: KeyboardEvent) => {
    if (e.key === " " || e.key === "Enter") stop();
  };

  return (
    <>
      <button
        type="button"
        className="hold-btn"
        data-holding={holding || undefined}
        style={{ ["--hold" as string]: `${HOLD_MS}ms` }}
        disabled={disabled || pending}
        aria-describedby={hint}
        onPointerDown={(e) => {
          if (e.button !== 0) return;
          e.currentTarget.setPointerCapture(e.pointerId);
          start();
        }}
        onPointerUp={stop}
        onPointerCancel={stop}
        onLostPointerCapture={stop}
        onKeyDown={onKeyDown}
        onKeyUp={onKeyUp}
        onBlur={stop}
        onContextMenu={(e) => e.preventDefault()}
      >
        <span className="hold-fill" aria-hidden="true" />
        <span className="hold-label">
          <Icon name={icon} />
          {pending ? pendingLabel : holding ? "Keep holding" : label}
        </span>
      </button>
      <span id={hint} className="sr-only">
        Press and hold for {HOLD_MS / 1000} seconds to confirm.
      </span>
    </>
  );
}

const SCOPES: { scope: Exclude<ResetScope, "item">; title: string; what: (p: ResetPreview) => string }[] = [
  { scope: "week", title: "This week", what: (p) => `Everything logged since Monday ${shortDate(p.week_of)}. Earlier weeks stay.` },
  { scope: "plan", title: "Prep plan", what: () => "Attempts, reviews and notes for every plan problem, Codeforces included." },
  { scope: "sde", title: "Striver SDE sheet", what: () => "Attempts, reviews, notes and stars on the sheet's own problems. Problems it shares with the plan keep their progress." },
  { scope: "a2z", title: "Striver A2Z sheet", what: () => "Attempts, reviews, notes and stars on the sheet's own problems. Problems it shares with the plan keep their progress." },
  { scope: "design", title: "System design", what: () => "LLD, HLD and interview prep blocks, decisions included." },
  { scope: "all", title: "Everything", what: () => "All progress, reviews, notes and stars. Settings and the curriculum stay." },
];

const SCOPE_NAME: Record<ResetScope, string> = {
  week: "this week",
  plan: "the Prep plan",
  sde: "the SDE sheet",
  a2z: "the A2Z sheet",
  design: "system design",
  item: "one problem",
  all: "everything",
};

function shortDate(iso: string) {
  const [y, m, d] = iso.split("-").map(Number);
  return new Date(Date.UTC(y!, m! - 1, d!)).toLocaleDateString("en-GB", { timeZone: "UTC", day: "numeric", month: "short" });
}

function clock(iso: string) {
  return new Date(iso).toLocaleTimeString("en-GB", { hour: "2-digit", minute: "2-digit" });
}

function plural(n: number, word: string) {
  return `${n} ${word}${n === 1 ? "" : "s"}`;
}

/** Undo for the latest reset, offered until something new is logged. */
export function UndoBar({ undo }: { undo: ResetPreview["undo"] }) {
  const undoReset = useUndoReset();
  if (!undo) return null;
  return (
    <div className="undo-bar" role="status">
      <span>
        Reset {undo.title ? <b>{undo.title}</b> : SCOPE_NAME[undo.scope]} at {clock(undo.at)}. A copy was saved first.
      </span>
      <button type="button" className="btn btn-sm" disabled={undoReset.isPending} onClick={() => undoReset.mutate()}>
        <Icon name="arrow-counter-clockwise" />
        {undoReset.isPending ? "Restoring" : "Undo reset"}
      </button>
      {undoReset.isError && <span className="error-text">{undoReset.error.message}</span>}
    </div>
  );
}

/** Plan page: one row per scope, with what it would clear and a hold-to-reset button. */
export function ResetPanel() {
  const { data, isPending, isError, error } = useQuery(resetQuery());
  const reset = useReset();

  return (
    <section className="panel section" id="reset" aria-labelledby="reset-h">
      <div className="section-head">
        <h2 id="reset-h">Start over</h2>
        <p>Each reset saves a copy first. Undo works until you log something new.</p>
      </div>
      {isPending && <p className="muted small">Counting what each reset would clear.</p>}
      {isError && <p className="notice notice-bad">{error.message}</p>}
      {data && (
        <>
          <UndoBar undo={data.undo} />
          <ul className="reset-list">
            {SCOPES.map(({ scope, title, what }) => {
              const c = data.scopes[scope];
              const empty = c.attempts === 0 && c.reviews === 0;
              return (
                <li key={scope} data-scope={scope}>
                  <div className="reset-text">
                    <p className="reset-title">{title}</p>
                    <p className="reset-what">{what(data)}</p>
                    <p className="reset-count num">{empty ? "Nothing logged yet" : `${plural(c.attempts, "attempt")}, ${plural(c.reviews, "review")}`}</p>
                  </div>
                  <HoldButton
                    label={scope === "all" ? "Hold to reset all" : "Hold to reset"}
                    disabled={empty}
                    pending={reset.isPending && reset.variables?.scope === scope}
                    onConfirm={() => reset.mutate({ scope })}
                  />
                </li>
              );
            })}
          </ul>
          {reset.isError && <p className="notice notice-bad">{reset.error.message}</p>}
        </>
      )}
    </section>
  );
}
