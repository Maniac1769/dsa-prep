import { createContext, useCallback, useContext, useEffect, useLayoutEffect, useRef, useState, type ReactNode } from "react";
import { Link } from "@tanstack/react-router";
import type { Status } from "../api";
import { useLogAttempt } from "../queries";
import { Icon } from "./Icon";
import { STATUS_LABEL, StatusMark } from "./StatusMark";

export const SCORE_OPTIONS = [
  { n: 0, short: "Stuck", long: "No valid approach" },
  { n: 1, short: "With help", long: "Needed a hint, explanation or the solution" },
  { n: 2, short: "Shaky", long: "Unaided, but slow or shaky" },
  { n: 3, short: "Solid", long: "Unaided, and can justify it" },
] as const;

interface Target {
  itemId: number;
  status: Status;
  anchor: HTMLElement;
}

const Ctx = createContext<(t: Target) => void>(() => {
  throw new Error("QuickLogTrigger rendered outside QuickLogProvider");
});

/**
 * One score picker for the whole page. 500 rows share it instead of each carrying
 * its own form; a trigger only passes its item id and position.
 */
export function QuickLogProvider({ children }: { children: ReactNode }) {
  const [target, setTarget] = useState<Target | null>(null);
  const panel = useRef<HTMLDivElement>(null);
  const log = useLogAttempt();
  const [pos, setPos] = useState({ left: 0, top: 0, origin: "14px 0" });

  const open = useCallback((t: Target) => setTarget((cur) => (cur?.anchor === t.anchor ? null : t)), []);
  const close = useCallback((refocus = false) => {
    setTarget((cur) => {
      if (refocus) cur?.anchor.focus();
      return null;
    });
  }, []);

  useLayoutEffect(() => {
    if (!target || !panel.current) return;
    const r = target.anchor.getBoundingClientRect();
    const width = panel.current.offsetWidth;
    const left = Math.min(Math.max(8, r.left - 6), document.documentElement.clientWidth - width - 8);
    setPos({ left: left + window.scrollX, top: r.bottom + 6 + window.scrollY, origin: `${r.left - left + r.width / 2}px 0` });
    panel.current.querySelector<HTMLButtonElement>("button")?.focus({ preventScroll: true });
  }, [target]);

  useEffect(() => {
    if (!target) return;
    const onDown = (e: PointerEvent) => {
      const node = e.target as Node;
      if (!panel.current?.contains(node) && !target.anchor.contains(node)) close();
    };
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") close(true);
    };
    const onResize = () => close();
    document.addEventListener("pointerdown", onDown);
    document.addEventListener("keydown", onKey);
    window.addEventListener("resize", onResize);
    return () => {
      document.removeEventListener("pointerdown", onDown);
      document.removeEventListener("keydown", onKey);
      window.removeEventListener("resize", onResize);
    };
  }, [target, close]);

  const submit = (score: number) => {
    if (!target) return;
    log.mutate(
      { item_id: target.itemId, mode: target.status === "todo" ? "solve" : "resolve", score },
      { onSuccess: () => close(true) },
    );
  };

  return (
    <Ctx.Provider value={open}>
      {children}
      {target && (
        <div
          ref={panel}
          className="qlog-panel"
          role="dialog"
          aria-label="How did it go?"
          aria-invalid={log.isError || undefined}
          title={log.isError ? log.error.message : undefined}
          style={{ left: pos.left, top: pos.top, transformOrigin: pos.origin }}
        >
          {SCORE_OPTIONS.map((o) => (
            <button key={o.n} type="button" className="score-chip" title={o.long} disabled={log.isPending} onClick={() => submit(o.n)}>
              <b>{o.n}</b>
              {o.short}
            </button>
          ))}
          <span className="sep" aria-hidden="true" />
          <Link to="/items/$id" params={{ id: target.itemId }} className="more" title="Log with notes and minutes" aria-label="Log with notes and minutes" onClick={() => close()}>
            <Icon name="arrow-up-right" />
          </Link>
        </div>
      )}
    </Ctx.Provider>
  );
}

/** The status circle as a button that opens the shared picker under itself. */
export function QuickLogTrigger({ itemId, status, title }: { itemId: number; status: Status; title: string }) {
  const open = useContext(Ctx);
  return (
    <button
      type="button"
      className="qtrig"
      title={STATUS_LABEL[status]}
      aria-label={`Log a result for ${title}. Now: ${STATUS_LABEL[status]}`}
      aria-haspopup="dialog"
      onClick={(e) => open({ itemId, status, anchor: e.currentTarget })}
    >
      <StatusMark status={status} />
    </button>
  );
}
