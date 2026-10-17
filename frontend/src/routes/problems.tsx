import { useDeferredValue, type ReactNode } from "react";
import { Link, createFileRoute, useNavigate } from "@tanstack/react-router";
import { useSuspenseQuery } from "@tanstack/react-query";
import type { Block, ListInfo, ListKey, Row } from "../api";
import { Icon } from "../components/Icon";
import { ProblemRow } from "../components/Rows";
import { prefersReducedMotion } from "../motion";
import { meQuery, planProblemsQuery, sheetQuery, useSaveAccountSettings } from "../queries";

type View = ListKey;
type Diff = "" | "easy" | "medium" | "hard" | "basic" | "core" | "pro";
interface Filter {
  q: string;
  d: Diff;
  open: boolean;
}

const DIFF_ORDER: { value: Exclude<Diff, "">; label: string }[] = [
  { value: "easy", label: "Easy" },
  { value: "medium", label: "Medium" },
  { value: "hard", label: "Hard" },
  { value: "basic", label: "Basic" },
  { value: "core", label: "Core" },
  { value: "pro", label: "Pro" },
];
const DIFF_VALUES = new Set<string>(DIFF_ORDER.map((d) => d.value));
const VIEWS = new Set<string>(["plan", "sde", "a2z"]);

// The chips follow the difficulty words the list actually uses (the sheets differ).
const diffsIn = (rows: Row[]) => {
  const seen = new Set(rows.map((r) => (r.difficulty ?? "").toLowerCase()));
  return DIFF_ORDER.filter((d) => seen.has(d.value));
};

const TAB_LABEL: Record<ListKey, string> = { plan: "Prep plan", sde: "SDE sheet", a2z: "A2Z sheet" };
const bareTitle = (title: string) => title.replace(/\s*\(\d+\)\s*$/, "");

export const Route = createFileRoute("/problems")({
  // The view and the filter live in the URL: reload-safe, shareable, back-button-correct.
  // No view in the URL means the person's own list.
  validateSearch: (search: Record<string, unknown>): { view?: View; q: string; d?: Diff; open?: boolean } => ({
    view: typeof search.view === "string" && VIEWS.has(search.view) ? (search.view as View) : undefined,
    q: typeof search.q === "string" ? search.q.slice(0, 80) : "",
    d: typeof search.d === "string" && DIFF_VALUES.has(search.d) ? (search.d as Diff) : undefined,
    open: search.open === true || search.open === "true" ? true : undefined,
  }),
  loaderDeps: ({ search }) => ({ view: search.view }),
  // Every view's payload carries the three list names and counts, so one request is enough.
  loader: ({ context: { queryClient, user }, deps }) => {
    const view = deps.view ?? user?.preferred_list ?? "plan";
    return view === "plan" ? queryClient.ensureQueryData(planProblemsQuery()) : queryClient.ensureQueryData(sheetQuery(view));
  },
  component: ProblemsPage,
});

const isOpen = (r: Row) => r.status !== "unaided" && r.status !== "solid";

function matches(row: Row, f: Filter) {
  if (f.d && (row.difficulty ?? "").toLowerCase() !== f.d) return false;
  if (f.open && !isOpen(row)) return false;
  if (!f.q) return true;
  return `${row.title} ${row.external_id ?? ""} ${row.difficulty ?? ""}`.toLowerCase().includes(f.q);
}

const active = (f: Filter) => !!(f.q || f.d || f.open);

function ProblemsPage() {
  const search = Route.useSearch();
  const { data: user } = useSuspenseQuery(meQuery());
  const view = search.view ?? user.preferred_list;
  // The input shows the typed text at once; the list filters on a deferred copy.
  const query = useDeferredValue(search.q.trim().toLowerCase());
  const filter: Filter = { q: query, d: search.d ?? "", open: search.open ?? false };
  return view === "plan" ? <PlanView f={filter} /> : <SheetView view={view} f={filter} />;
}

/** Title, list tabs, list bar, filters. Each view passes its own lists and rows. */
function ProblemsHead({ view, lists, rows, children }: { view: View; lists: ListInfo[]; rows: Row[]; children: ReactNode }) {
  const search = Route.useSearch();
  const navigate = useNavigate({ from: Route.fullPath });
  const d = search.d ?? "";
  const open = search.open ?? false;
  const set = (patch: Partial<{ q: string; d: Diff | undefined; open: boolean | undefined }>) =>
    void navigate({ search: (s) => ({ ...s, ...patch }), replace: true, viewTransition: false });
  const info = lists.find((l) => l.key === view);
  const filter: Filter = { q: search.q.trim().toLowerCase(), d, open };

  return (
    <>
      <header className="page-head">
        <div className="head-row">
          <h1>Problems</h1>
          <nav className="segmented" aria-label="Problem list">
            {lists.map((l) => (
              <Link key={l.key} to="/problems" search={{ view: l.key, q: "" }} aria-current={view === l.key ? "page" : undefined} title={bareTitle(l.title)}>
                {TAB_LABEL[l.key]} <span className="count">{l.total}</span>
                {l.preferred && (
                  <>
                    <span className="own-dot" aria-hidden="true" />
                    <span className="sr-only">, your list</span>
                  </>
                )}
              </Link>
            ))}
          </nav>
        </div>
      </header>

      {info && <ListBar info={info} />}

      <div className="toolbar">
        <label className="search">
          <Icon name="magnifying-glass" />
          <span className="sr-only">Filter problems</span>
          <input
            type="search"
            placeholder={view === "plan" ? "Filter by name or number" : "Filter by name"}
            autoComplete="off"
            value={search.q}
            onChange={(e) => set({ q: e.target.value })}
          />
        </label>
        <div className="chips" role="group" aria-label="Difficulty">
          {diffsIn(rows).map((o) => (
            <button key={o.value} type="button" className={`chip chip-${o.value}`} aria-pressed={d === o.value} onClick={() => set({ d: d === o.value ? undefined : o.value })}>
              {o.label}
            </button>
          ))}
          <button type="button" className="chip" aria-pressed={open} onClick={() => set({ open: open ? undefined : true })}>
            Unsolved
          </button>
        </div>
        <RandomPick rows={rows} filter={filter} />
      </div>

      {children}
    </>
  );
}

/** Your list shows its completion; any other list is a library with one way to adopt it. */
function ListBar({ info }: { info: ListInfo }) {
  const adopt = useSaveAccountSettings();
  if (info.preferred) {
    return (
      <div className="list-bar">
        <p className="list-summary">
          <span className="pill pill-accent">Your list</span>
          <span>
            <b className="num">{info.solid}</b> of {info.total} solved unaided.
          </span>
        </p>
        <span className="thin thin-wide" aria-hidden="true">
          <i style={{ width: `${info.total ? (100 * info.solid) / info.total : 0}%` }} />
        </span>
      </div>
    );
  }
  return (
    <div className="list-bar">
      <div className="controls">
        <p className="list-summary grow">Not your list. Browse it, and star what you want to revisit. Anything you solve here is remembered.</p>
        <button type="button" className="btn btn-sm" disabled={adopt.isPending} onClick={() => adopt.mutate({ preferred_list: info.key })}>
          {adopt.isPending ? "Switching" : "Make this my list"}
        </button>
      </div>
      {adopt.isError && <p className="error-text">{adopt.error.message}</p>}
    </div>
  );
}

/** Takes the guesswork out of starting: one unsolved problem from whatever is filtered. */
function RandomPick({ rows, filter }: { rows: Row[]; filter: Filter }) {
  const navigate = useNavigate();
  const pool = rows.filter((r) => isOpen(r) && matches(r, { ...filter, open: true }));
  const pick = () => {
    const r = pool[Math.floor(Math.random() * pool.length)];
    if (r) void navigate({ to: "/items/$id", params: { id: r.log_id ?? r.id } });
  };
  return (
    <button type="button" className="btn btn-sm toolbar-end" disabled={pool.length === 0} onClick={pick}>
      <Icon name="shuffle" />
      Random unsolved
    </button>
  );
}

function jumpTo(block: string) {
  const el = document.getElementById(`block-${block}`);
  if (!(el instanceof HTMLDetailsElement)) return;
  el.open = true;
  el.scrollIntoView({ behavior: prefersReducedMotion() ? "auto" : "smooth", block: "start" });
  el.classList.remove("flash");
  void el.offsetWidth;
  el.classList.add("flash");
}

function PlanView({ f }: { f: Filter }) {
  const { data } = useSuspenseQuery(planProblemsQuery());
  const blocks = data.groups.flatMap((g) => g.blocks);
  // Only your own list is a goal. Another list keeps its rows and statuses but shows no
  // completion: no map, no bars, no fractions.
  const library = !data.lists.find((l) => l.key === "plan")?.preferred;
  const filtering = active(f);
  const nothing = filtering && !data.groups.some((g) => g.blocks.some((b) => b.rows.some((r) => matches(r, f)))) && !data.codeforces.some((r) => matches(r, f));

  return (
    <ProblemsHead view="plan" lists={data.lists} rows={blocks.flatMap((b) => b.rows)}>
      <p className="muted small list-hint">Tap a status circle to log a result.</p>
      {!library && (
        <>
          <div className="blockmap" aria-label="Blocks 1 to 42">
            {blocks.map((b) => (
              <a
                key={b.block}
                href={`#block-${b.block}`}
                data-state={b.state}
                className={b.block === data.current_block ? "is-current" : undefined}
                title={`Block ${b.block}: ${b.topic}. ${b.done} of ${b.rows.length} unaided`}
                aria-label={`Block ${b.block}, ${b.done} of ${b.rows.length} unaided`}
                onClick={(e) => {
                  e.preventDefault();
                  jumpTo(b.block);
                }}
              >
                {b.block}
              </a>
            ))}
          </div>
          <div className="legend">
            <span>
              <i className="sw" style={{ background: "var(--heat-0)" }} />
              Not started
            </span>
            <span>
              <i className="sw" style={{ background: "var(--heat-2)" }} />
              In progress
            </span>
            <span>
              <i className="sw" style={{ background: "var(--heat-4)" }} />
              All unaided
            </span>
          </div>
        </>
      )}

      {data.groups.map((g) => {
        const visible = g.blocks.filter((b) => b.rows.some((r) => matches(r, f)));
        if (filtering && visible.length === 0) return null;
        return (
          <section className="group" key={g.group.key}>
            <div className="group-head">
              <h2>{g.group.title}</h2>
              <div className="meta">
                {!library && (
                  <span className="group-progress">
                    <span className="thin" aria-hidden="true">
                      <i style={{ width: `${g.total ? (100 * g.done) / g.total : 0}%` }} />
                    </span>
                    <span className="num">
                      {g.done} / {g.total} unaided
                    </span>
                  </span>
                )}
                {g.resource && (
                  <span>
                    Learn from{" "}
                    {g.resource.url ? (
                      <a href={g.resource.url} target="_blank" rel="noreferrer">
                        {g.resource.name}
                        <Icon name="arrow-up-right" />
                      </a>
                    ) : (
                      g.resource.name
                    )}
                  </span>
                )}
              </div>
            </div>
            {(filtering ? visible : g.blocks).map((b) => (
              <BlockDetails key={b.block} b={b} current={!library && b.block === data.current_block} f={f} library={library} />
            ))}
          </section>
        );
      })}

      {data.codeforces.length > 0 && (!filtering || data.codeforces.some((r) => matches(r, f))) && (
        <section className="group">
          <div className="group-head">
            <h2>Codeforces, optional</h2>
            <div className="meta">
              <span>Full input and output handling, for when a problem needs it.</span>
            </div>
          </div>
          <Collapsible
            id="block-cf"
            no="CF"
            title="Nine starter problems"
            frac={library ? undefined : `${data.codeforces.filter((r) => r.status === "unaided" || r.status === "solid").length}/${data.codeforces.length}`}
            open={filtering}
          >
            <ul className="rows">
              {data.codeforces.filter((r) => matches(r, f)).map((r) => (
                <ProblemRow key={r.id} item={r} showStar={library} />
              ))}
            </ul>
          </Collapsible>
        </section>
      )}
      <EmptyFilter show={nothing} />
    </ProblemsHead>
  );
}

function BlockDetails({ b, current, f, library }: { b: Block; current: boolean; f: Filter; library: boolean }) {
  return (
    <Collapsible id={`block-${b.block}`} no={b.block} title={b.topic} frac={library ? undefined : `${b.done}/${b.rows.length}`} open={current || active(f)} current={current}>
      <ul className="rows">
        {b.rows.filter((r) => matches(r, f)).map((r) => (
          <ProblemRow key={r.id} item={r} showStar={library} />
        ))}
      </ul>
    </Collapsible>
  );
}

function Collapsible({ id, no, title, frac, open, current, children }: { id?: string; no: ReactNode; title: ReactNode; frac?: string; open: boolean; current?: boolean; children: ReactNode }) {
  return (
    // Uncontrolled <details>: open state belongs to the user once they toggle it. The
    // key resets it when the filter changes so matches are shown expanded.
    <details id={id} className={`block${current ? " is-current" : ""}`} open={open} key={String(open)}>
      <summary>
        <span className="bno">{no}</span>
        <span className="topic">{title}</span>
        <span className="frac">{frac}</span>
        <span className="caret">
          <Icon name="caret-down" />
        </span>
      </summary>
      <div className="block-body">{children}</div>
    </details>
  );
}

/** sde and a2z: steps, lectures, rows. */
function SheetView({ view, f }: { view: "sde" | "a2z"; f: Filter }) {
  const { data } = useSuspenseQuery(sheetQuery(view));
  const library = !data.lists.find((l) => l.key === view)?.preferred;
  const rows = data.steps.flatMap((s) => s.lectures.flatMap((l) => l.rows));
  const name = TAB_LABEL[view];

  if (data.steps.length === 0) {
    return (
      <ProblemsHead view={view} lists={data.lists} rows={rows}>
        <div className="empty">
          <h2>This sheet is not loaded yet</h2>
          <p>The problem list is seeded on the next deploy. Your other lists are unaffected.</p>
        </div>
      </ProblemsHead>
    );
  }
  let any = false;
  return (
    <ProblemsHead view={view} lists={data.lists} rows={rows}>
      <p className="muted small list-hint">
        {data.total} problems{data.source ? `, list fetched ${data.source.fetched}` : ""}.
        {data.overlap !== undefined && ` ${data.overlap} are also in the Prep plan.`} Problems on more than one list share one record, so progress carries over. Links open the
        original article, video and practice page.
        {library && ` Star a problem in the ${name} to put it in your review queue.`}
      </p>
      {data.steps.map((s, i) => {
        const lectures = s.lectures.map((l) => ({ ...l, rows: l.rows.filter((r) => matches(r, f)) })).filter((l) => l.rows.length > 0);
        if (active(f) && lectures.length === 0) return null;
        any = true;
        return (
          <Collapsible key={s.title} no={s.no} title={s.title} frac={library ? undefined : `${s.done}/${s.total}`} open={i === 0 || active(f)}>
            {lectures.map((l, li) => (
              <div key={`${s.title}-${li}-${l.title}`}>
                {l.title && <p className="lecture">{l.title}</p>}
                <ul className="rows">
                  {l.rows.map((r) => (
                    <ProblemRow key={r.id} item={r} showStar={library} />
                  ))}
                </ul>
              </div>
            ))}
          </Collapsible>
        );
      })}
      <EmptyFilter show={active(f) && !any} />
    </ProblemsHead>
  );
}

function EmptyFilter({ show }: { show: boolean }) {
  if (!show) return null;
  return <p className="empty-filter">No problem matches these filters. Clear a chip or the search to see more.</p>;
}
