import { Link, Outlet, createRootRouteWithContext, redirect, type ErrorComponentProps } from "@tanstack/react-router";
import type { QueryClient } from "@tanstack/react-query";
import { ApiError, type User } from "../api";
import { Icon } from "../components/Icon";
import { QuickLogProvider } from "../components/QuickLog";
import { ThemeToggle } from "../components/ThemeToggle";
import type { IconName } from "../icon-names";
import { meQuery } from "../queries";

export interface RouterContext {
  queryClient: QueryClient;
}

const TABS: { to: "/" | "/plan" | "/problems" | "/design" | "/stats"; label: string; icon: IconName }[] = [
  { to: "/", label: "Today", icon: "sun-horizon" },
  { to: "/plan", label: "Plan", icon: "calendar-blank" },
  { to: "/problems", label: "Problems", icon: "list-checks" },
  { to: "/design", label: "Design", icon: "book-open-text" },
  { to: "/stats", label: "Stats", icon: "chart-bar" },
];

const isAuthPath = (path: string) => path === "/login" || path === "/register";

export const Route = createRootRouteWithContext<RouterContext>()({
  // The guard: every page except sign-in and sign-up needs a session. The probe is cached,
  // so it costs one request per visit, not one per navigation.
  beforeLoad: async ({ context: { queryClient }, location }): Promise<{ user: User | null }> => {
    try {
      return { user: await queryClient.ensureQueryData(meQuery()) };
    } catch (e) {
      if (!(e instanceof ApiError) || e.status !== 401) throw e;
      if (isAuthPath(location.pathname)) return { user: null };
      throw redirect({ to: "/login", search: { next: location.href } });
    }
  },
  component: Shell,
  errorComponent: RootError,
  notFoundComponent: NotFound,
});

function Shell() {
  const { user } = Route.useRouteContext();
  return (
    <QuickLogProvider>
      <header className="top">
        <div className="top-inner">
          <Link to="/" className="brand">
            <span className="brand-mark">
              <Icon name="target" />
            </span>
            Prep
          </Link>
          {user && (
            <nav className="tabs" aria-label="Main">
              {TABS.map((t) => (
                <Link
                  key={t.to}
                  to={t.to}
                  className="tab"
                  activeOptions={{ exact: t.to === "/", includeSearch: false }}
                  activeProps={{ "aria-current": "page" }}
                >
                  <Icon name={t.icon} />
                  <span>{t.label}</span>
                </Link>
              ))}
            </nav>
          )}
          <div className="top-actions">
            {user && (
              <Link to="/account" className="btn btn-quiet account-link" aria-label={`Account: ${user.username}`} title="Account">
                <Icon name="user" />
                <span className="account-name">{user.username}</span>
              </Link>
            )}
            <ThemeToggle />
          </div>
        </div>
      </header>
      <main>
        <Outlet />
      </main>
    </QuickLogProvider>
  );
}

function RootError({ error, reset }: ErrorComponentProps) {
  return (
    <main>
      <div className="empty">
        <h2>That page did not load</h2>
        <p>{error instanceof Error ? error.message : String(error)}</p>
        <button type="button" className="btn btn-sm" onClick={reset}>
          Try again
        </button>
      </div>
    </main>
  );
}

function NotFound() {
  return (
    <div className="empty">
      <h2>Nothing here</h2>
      <p>That address is not part of the tracker.</p>
      <Link to="/" className="btn btn-sm">
        Go to Today
      </Link>
    </div>
  );
}
