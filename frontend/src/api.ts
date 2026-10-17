// Typed client for the FastAPI backend. One request per screen; every write is JSON.

export type Status = "todo" | "started" | "helped" | "unaided" | "solid";
export type Track = "dsa" | "lld" | "hld" | "prep" | "a2z" | "sde";
export type ReviewKind = "recall" | "full_solve" | "rebuild";
// "recall" is the 10-minute short day: a recall with no score.
export type Mode = "learn" | "solve" | "resolve" | "rebuild" | "mock" | "recall";

export type ListKey = "plan" | "sde" | "a2z";
export type SessionKind = "learn" | "resolve" | "mixed" | "catchup";

export interface User {
  id: number;
  username: string;
  preferred_list: ListKey;
  timezone: string;
  weekly_sessions: number;
  design_sessions: number;
  design_minutes: number;
  created_at: string;
}

export interface ListInfo {
  key: ListKey;
  title: string;
  total: number;
  solid: number;
  preferred: boolean;
}

export interface AuthStatus {
  registration_open: boolean;
  users: number;
  cap: number;
  lists: { key: ListKey; title: string; total: number }[];
}

export interface SettingsPatch {
  preferred_list?: ListKey;
  timezone?: string;
  weekly_sessions?: number;
  design_sessions?: number;
  design_minutes?: number;
}

export interface Row {
  id: number;
  track: Track;
  block: string;
  phase: string | null;
  title: string;
  platform: string | null;
  external_id: string | null;
  difficulty: string | null;
  url: string | null;
  slug: string | null;
  article_url: string | null;
  video_url: string | null;
  is_anchor: boolean;
  starred: boolean;
  status: Status;
  attempts: number;
  focus: string | null;
  note: string | null;
  section: string | null;
  // Striver rows that are also plan problems log against the plan item.
  plan_block?: string | null;
  log_id?: number;
  // System design blocks: verified watch / read / practice links.
  links?: DesignLink[];
}

export interface DesignLink {
  kind: "watch" | "read" | "practice";
  title: string;
  url: string;
  source: string;
  note: string;
}

export interface Review {
  id: number;
  kind: ReviewKind;
  due_date: string;
  item_id: number;
  title: string;
  track: Track;
  block: string;
  url: string | null;
  difficulty: string | null;
  prompt: string;
  days_late: number;
}

export interface Verdict {
  allow_new_work: boolean;
  reason: string;
}

export interface Segment {
  minutes: number;
  label: string;
}

export interface DayPlan {
  name: string;
  headline: string;
  segments: Segment[];
  guidance: string;
}

export interface Group {
  key: string;
  title: string;
  first: number;
  last: number;
  resource_topic: string;
}

export interface Resource {
  topic: string;
  rank: number;
  name: string;
  creator: string;
  url: string;
  format: string;
  language: string;
  why: string;
  caveat: string;
}

export interface WeekDay {
  letter: string;
  name: string;
  worked: boolean;
  minutes: number;
  today: boolean;
  future: boolean;
}

export interface SplitRow {
  label: "Easy" | "Medium" | "Hard";
  solid: number;
  total: number;
}

export interface TodaySession {
  kind: SessionKind;
  number: number;
  of: number;
  done_today: boolean;
  week_done: boolean;
  short_days: number;
}

export interface Today {
  on: string;
  day: DayPlan;
  list: ListInfo;
  context: string;
  session: TodaySession;
  short_day: { reviews: Review[]; recall_item: Row | null };
  quiet_days: number | null;
  block_topic: string | null;
  resource: Resource | null;
  week_days: WeekDay[];
  streak: number;
  best_streak: number;
  activity: { start: string; days: { on: string; n: number; future: boolean }[]; active_days: number };
  split: SplitRow[];
  due_week: number;
  reviews: Review[];
  verdict: Verdict;
  focus: Row | null;
  focus_is_blocking: boolean;
  blocking: Row[];
  revisit_count: number;
  pulled_forward: (Omit<Review, "prompt" | "days_late" | "difficulty">) | null;
  this_week: Row[];
  design: null | {
    minutes: number;
    reviews: Review[];
    verdict: Verdict;
    focus: Row | null;
    focus_is_blocking: boolean;
    sessions_done: number;
    sessions_target: number;
  };
  unaided: number;
  total: number;
}

export interface Block {
  block: string;
  topic: string;
  rows: Row[];
  state: "todo" | "partial" | "done";
  done: number;
}

export interface PlanProblems {
  current_block: string | null;
  groups: { group: Group; blocks: Block[]; resource: Resource | null; done: number; total: number }[];
  codeforces: Row[];
  solid: number;
  total: number;
  lists: ListInfo[];
}

export interface A2Z {
  steps: {
    title: string;
    no: string | null;
    total: number;
    done: number;
    lectures: { title: string | null; rows: Row[] }[];
  }[];
  total: number;
  // The sde view shares this shape; these two describe the A2Z crawl and may be absent.
  overlap?: number;
  source?: { fetched: string } | null;
  lists: ListInfo[];
}

export interface Design {
  phases: { no: string | null; title: string; rows: Row[]; done: number }[];
  next_id: number | null;
}

export interface Ladder {
  recall_offsets: number[];
  anchor_offsets: number[];
  anchor_kind: ReviewKind;
  max_queued_anchor: number;
  max_overdue_recall: number;
  retire_after_clean: number;
  retire_min_gap_days: number;
}

export interface PlanSession {
  kind: SessionKind;
  label: string;
  minutes: number;
  done: boolean;
  next: boolean;
}

/** Plan list: one entry per pattern group. */
export interface RoadGroup {
  group: Group;
  state: RoadState;
  rows: number;
  done: number;
  resources: Resource[];
}

/** Sheet lists (sde, a2z): one entry per step. The contract names only done and total. */
export interface RoadStep {
  title: string;
  no?: string | null;
  state?: RoadState;
  total: number;
  done: number;
}

export interface Plan {
  on: string;
  sessions: PlanSession[];
  weekly_sessions: number;
  design_sessions: number;
  design_minutes: number;
  pace: { new_per_week: number; weeks_left: number };
  roadmap: (RoadGroup | RoadStep)[];
  design_road: { no: string; title: string; state: RoadState; count: number; done: number }[];
  session_steps: { t: string; text: string }[];
  design_shapes: { name: string; text: string }[];
  scores: { n: number; text: string }[];
  ladder: Ladder;
  design_ladder: Ladder;
  extra_topics: { key: string; resources: Resource[] }[];
}

export type RoadState = "done" | "current" | "upcoming";

export interface Stats {
  on: string;
  target: number;
  kpi: {
    unaided: number;
    plan_total: number;
    streak: number;
    week_minutes: number;
    target: number;
    week_days: number;
    week_entries: number;
    sessions_week: number;
    sessions_target: number;
    due_7: number;
    indep_rate: number | null;
  };
  days: { on: string; entries: number; minutes: number }[];
  weekly: { start: string; minutes: number; entries: number; days: number; current: boolean }[];
  upcoming: { on: string; count: number }[];
  bars: { label: string; solid: number; started: number; total: number }[];
  any_activity: boolean;
  next_item: Row | null;
}

export interface ItemDetail {
  item: Row & { subsection: string | null; best: number | null };
  topic: string | null;
  attempts: { id: number; on_date: string; mode: Mode; score: number | null; independent: number; minutes: number | null; note: string | null }[];
  reviews: { id: number; kind: ReviewKind; due_date: string; done_date: string | null; outcome: "pass" | "fail" | null }[];
  decisions: { id: number; chose: string; rejected: string | null; because: string | null; on_date: string }[];
  plan_twin: { id: number; block: string } | null;
  prompt: string;
}

export interface LogResult {
  id: number;
  status: Status;
  label: string;
  best: number | null;
  attempts: number;
}

export type ResetScope = "week" | "plan" | "sde" | "a2z" | "design" | "item" | "all";

export interface ResetPreview {
  scopes: Record<Exclude<ResetScope, "item">, { attempts: number; reviews: number }>;
  week_of: string;
  undo: { scope: ResetScope; at: string; title: string | null } | null;
}

export class ApiError extends Error {
  constructor(
    readonly status: number,
    message: string,
    /** The server's human sentence, without the request prefix. Safe to show in a form. */
    readonly detail: string,
    /** Seconds from `Retry-After` on a 429. */
    readonly retryAfter: number | null = null,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

// Any 401 from a data call means the session is gone. The router registers one handler
// that sends the person to /login and back. Calls where a 401 is an expected answer
// (sign-in, the session probe, a wrong current password) opt out with `quiet401`.
let onUnauthorized: (() => void) | null = null;
export function setUnauthorizedHandler(fn: (() => void) | null) {
  onUnauthorized = fn;
}

async function request<T>(path: string, init?: { method?: "POST"; body?: unknown; quiet401?: boolean }): Promise<T> {
  const method = init?.method ?? "GET";
  const res = await fetch(path, {
    method,
    credentials: "same-origin",
    headers: {
      Accept: "application/json",
      ...(init?.body !== undefined ? { "Content-Type": "application/json" } : {}),
      // Required by the server on every write; a cross-site form cannot send it.
      ...(method === "POST" ? { "X-Prep": "1" } : {}),
    },
    body: init?.body !== undefined ? JSON.stringify(init.body) : undefined,
  });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = (await res.json()) as { detail?: unknown };
      detail = typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail);
    } catch {
      // The body was not JSON; the status text is the best detail available.
    }
    const wait = Number.parseInt(res.headers.get("Retry-After") ?? "", 10);
    const err = new ApiError(res.status, `${method} ${path} failed with ${res.status}: ${detail}`, detail, Number.isFinite(wait) ? wait : null);
    if (res.status === 401 && !init?.quiet401) onUnauthorized?.();
    throw err;
  }
  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

export const api = {
  authStatus: () => request<AuthStatus>("/api/auth/status", { quiet401: true }),
  me: () => request<{ user: User }>("/api/auth/me", { quiet401: true }),
  register: (body: { username: string; password: string; timezone: string; preferred_list?: ListKey }) =>
    request<{ user: User }>("/api/auth/register", { method: "POST", body, quiet401: true }),
  login: (body: { username: string; password: string }) =>
    request<{ user: User }>("/api/auth/login", { method: "POST", body, quiet401: true }),
  logout: () => request<void>("/api/auth/logout", { method: "POST", quiet401: true }),
  accountSettings: (body: SettingsPatch) => request<{ user: User }>("/api/account/settings", { method: "POST", body }),
  changePassword: (body: { current_password: string; new_password: string }) =>
    request<void>("/api/account/password", { method: "POST", body, quiet401: true }),
  deleteAccount: (body: { password: string }) => request<void>("/api/account/delete", { method: "POST", body, quiet401: true }),
  accountLists: () => request<{ lists: ListInfo[] }>("/api/account/lists"),
  today: () => request<Today>("/api/today"),
  planProblems: () => request<PlanProblems>("/api/problems?view=plan"),
  // The sde view is served in the a2z shape.
  sheet: (view: "sde" | "a2z") => request<A2Z>(`/api/problems?view=${view}`),
  design: () => request<Design>("/api/design"),
  plan: () => request<Plan>("/api/plan"),
  stats: () => request<Stats>("/api/stats"),
  item: (id: number) => request<ItemDetail>(`/api/items/${id}`),
  log: (body: { item_id: number; mode: Mode; score: number | null; minutes?: number | null; note?: string }) =>
    request<LogResult>("/api/log", { method: "POST", body }),
  review: (id: number, outcome: "pass" | "fail") =>
    request<{ id: number; outcome: string; item_id: number }>(`/api/reviews/${id}`, { method: "POST", body: { outcome } }),
  star: (id: number) => request<{ id: number; starred: boolean }>(`/api/items/${id}/star`, { method: "POST" }),
  decision: (body: { item_id: number; chose: string; rejected: string; because: string }) =>
    request<{ id: number }>("/api/decisions", { method: "POST", body }),
  spreadOverdue: () => request<{ moved: number; through: string }>("/api/reviews/spread", { method: "POST" }),
  resetPreview: () => request<ResetPreview>("/api/reset"),
  reset: (body: { scope: ResetScope; item_id?: number }) =>
    request<{ scope: ResetScope; attempts: number; reviews: number; snapshot: string }>("/api/reset", { method: "POST", body }),
  undoReset: () => request<{ restored: ResetScope }>("/api/reset/undo", { method: "POST" }),
};
