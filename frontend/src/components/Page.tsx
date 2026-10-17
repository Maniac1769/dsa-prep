import type { ErrorComponentProps } from "@tanstack/react-router";
import { useQueryErrorResetBoundary } from "@tanstack/react-query";
import { useEffect } from "react";

/** Skeleton shaped like a page head and two panels, so a slow load does not jump. */
export function PagePending() {
  return (
    <div className="skeleton" aria-busy="true" aria-label="Loading">
      <span className="sk sk-line" style={{ width: 120 }} />
      <span className="sk sk-title" />
      <span className="sk sk-line" style={{ width: "52%" }} />
      <span className="sk sk-panel" />
      <span className="sk sk-panel" style={{ height: 120 }} />
    </div>
  );
}

export function PageError({ error, reset }: ErrorComponentProps) {
  const queryReset = useQueryErrorResetBoundary();
  useEffect(() => {
    queryReset.reset();
  }, [queryReset]);
  return (
    <div className="empty">
      <h2>That did not load</h2>
      <p>{error instanceof Error ? error.message : String(error)}</p>
      <button type="button" className="btn btn-sm" onClick={reset}>
        Try again
      </button>
    </div>
  );
}
