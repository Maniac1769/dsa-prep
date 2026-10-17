import { queryOptions, useMutation, useQueryClient, type QueryClient } from "@tanstack/react-query";
import { api, type ResetScope, type A2Z, type Design, type ListKey, type LogResult, type Mode, type PlanProblems, type Row, type Status } from "./api";

// Every key descends from one root: a single attempt changes Today, the lists, the
// plan roadmap and the stats at once, so writes invalidate the whole branch.
export const keys = {
  // Session state lives outside the "prep" branch: a log or a reset must not refetch it.
  me: ["auth", "me"] as const,
  authStatus: ["auth", "status"] as const,
  all: ["prep"] as const,
  today: () => [...keys.all, "today"] as const,
  problems: (view: ListKey) => [...keys.all, "problems", view] as const,
  design: () => [...keys.all, "design"] as const,
  plan: () => [...keys.all, "plan"] as const,
  stats: () => [...keys.all, "stats"] as const,
  item: (id: number) => [...keys.all, "item", id] as const,
  reset: () => [...keys.all, "reset"] as const,
  accountLists: () => [...keys.all, "account", "lists"] as const,
};

export const meQuery = () => queryOptions({ queryKey: keys.me, queryFn: () => api.me().then((r) => r.user), staleTime: 5 * 60_000 });
export const authStatusQuery = () => queryOptions({ queryKey: keys.authStatus, queryFn: api.authStatus, staleTime: 0 });
export const accountListsQuery = () => queryOptions({ queryKey: keys.accountLists(), queryFn: () => api.accountLists().then((r) => r.lists) });
export const todayQuery = () => queryOptions({ queryKey: keys.today(), queryFn: api.today, staleTime: 10_000 });
export const planProblemsQuery = () => queryOptions({ queryKey: keys.problems("plan"), queryFn: api.planProblems });
// A sheet's curriculum never changes at runtime; only statuses do, and those are
// patched in place after each log. sde and a2z share one shape.
export const sheetQuery = (view: "sde" | "a2z") => queryOptions({ queryKey: keys.problems(view), queryFn: () => api.sheet(view), staleTime: 5 * 60_000 });
export const designQuery = () => queryOptions({ queryKey: keys.design(), queryFn: api.design });
export const planQuery = () => queryOptions({ queryKey: keys.plan(), queryFn: api.plan });
export const statsQuery = () => queryOptions({ queryKey: keys.stats(), queryFn: api.stats });
export const resetQuery = () => queryOptions({ queryKey: keys.reset(), queryFn: api.resetPreview, staleTime: 0 });
export const itemQuery = (id: number) => queryOptions({ queryKey: keys.item(id), queryFn: () => api.item(id) });

function patchRows(rows: Row[], id: number, status: Status): Row[] {
  let changed = false;
  const next = rows.map((r) => {
    if ((r.log_id ?? r.id) !== id) return r;
    changed = true;
    return { ...r, status, attempts: r.attempts + 1 };
  });
  return changed ? next : rows;
}

const isSolid = (r: Row) => r.status === "unaided" || r.status === "solid";

function blockState(rows: Row[]): "todo" | "partial" | "done" {
  if (rows.length > 0 && rows.every(isSolid)) return "done";
  if (rows.some((r) => r.status !== "todo")) return "partial";
  return "todo";
}

/**
 * Put a freshly logged status into every cached list, counts included, so rows and
 * fractions update at once without refetching the lists (the sheet alone is 245 KB).
 */
function patchStatus(qc: QueryClient, result: LogResult) {
  qc.setQueryData<PlanProblems>(keys.problems("plan"), (old) => {
    if (!old) return old;
    const groups = old.groups.map((g) => {
      const blocks = g.blocks.map((b) => {
        const rows = patchRows(b.rows, result.id, result.status);
        return { ...b, rows, done: rows.filter(isSolid).length, state: blockState(rows) };
      });
      return { ...g, blocks, done: blocks.reduce((n, b) => n + b.done, 0) };
    });
    return { ...old, groups, codeforces: patchRows(old.codeforces, result.id, result.status), solid: groups.reduce((n, g) => n + g.done, 0) };
  });
  for (const view of ["sde", "a2z"] as const) {
    qc.setQueryData<A2Z>(keys.problems(view), (old) => {
      if (!old) return old;
      return {
        ...old,
        steps: old.steps.map((s) => {
          const lectures = s.lectures.map((l) => ({ ...l, rows: patchRows(l.rows, result.id, result.status) }));
          return { ...s, lectures, done: lectures.reduce((n, l) => n + l.rows.filter(isSolid).length, 0) };
        }),
      };
    });
  }
  qc.setQueryData<Design>(keys.design(), (old) =>
    old && { ...old, phases: old.phases.map((p) => ({ ...p, rows: patchRows(p.rows, result.id, result.status) })) },
  );
}

export function useLogAttempt() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (v: { item_id: number; mode: Mode; score: number | null; minutes?: number | null; note?: string }) =>
      api.log(v),
    onSuccess: (result) => {
      patchStatus(qc, result);
      // Today, stats, the plan roadmap and the item page derive from the new attempt;
      // refetch those. The problem lists were patched above, counts included.
      void qc.invalidateQueries({ queryKey: keys.all, predicate: (q) => q.queryKey[1] !== "problems" });
    },
  });
}

export function useCompleteReview() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (v: { id: number; outcome: "pass" | "fail" }) => api.review(v.id, v.outcome),
    onSettled: () => qc.invalidateQueries({ queryKey: keys.all }),
  });
}

export function useToggleStar() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => api.star(id),
    onSuccess: ({ id, starred }) => {
      // A star lands on the canonical record, so every row that shows it changes.
      for (const view of ["sde", "a2z"] as const) {
        qc.setQueryData<A2Z>(keys.problems(view), (old) =>
          old && {
            ...old,
            steps: old.steps.map((s) => ({
              ...s,
              lectures: s.lectures.map((l) => ({ ...l, rows: l.rows.map((r) => ((r.log_id ?? r.id) === id ? { ...r, starred } : r)) })),
            })),
          },
        );
      }
      void qc.invalidateQueries({ queryKey: keys.item(id) });
      void qc.invalidateQueries({ queryKey: keys.today() });
      void qc.invalidateQueries({ queryKey: keys.stats() });
    },
  });
}

export function useSaveDecision(itemId: number) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (v: { chose: string; rejected: string; because: string }) => api.decision({ item_id: itemId, ...v }),
    onSuccess: () => qc.invalidateQueries({ queryKey: keys.item(itemId) }),
  });
}

/** Study settings change what every screen is built from, so the whole branch refetches. */
export function useSaveAccountSettings() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: api.accountSettings,
    onSuccess: ({ user }) => {
      qc.setQueryData(keys.me, user);
      void qc.invalidateQueries({ queryKey: keys.all });
    },
  });
}

/** A reset or its undo changes every screen, so the whole branch refetches. */
export function useReset() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (v: { scope: ResetScope; item_id?: number }) => api.reset(v),
    onSettled: () => qc.invalidateQueries({ queryKey: keys.all }),
  });
}

export function useUndoReset() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: api.undoReset,
    onSettled: () => qc.invalidateQueries({ queryKey: keys.all }),
  });
}

export function useSpreadOverdue() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: api.spreadOverdue,
    onSettled: () => qc.invalidateQueries({ queryKey: keys.all }),
  });
}
