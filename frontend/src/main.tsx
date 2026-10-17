import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { RouterProvider, createRouter } from "@tanstack/react-router";
import { routeTree } from "./routeTree.gen";
import { ApiError, setUnauthorizedHandler } from "./api";
import { PageError, PagePending } from "./components/Page";
import { keys } from "./queries";
import "./styles.css";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      // Default 0 would refetch on every navigation. Data changes only when this one
      // user logs something, and every write invalidates what it touched.
      staleTime: 30_000,
      // A 401 or 429 will not change on a second try; anything else gets one.
      retry: (count, error) => count < 1 && !(error instanceof ApiError && (error.status === 401 || error.status === 429)),
      refetchOnWindowFocus: true,
    },
  },
});

const router = createRouter({
  routeTree,
  context: { queryClient },
  // Hover or focus on a link starts the route loader before the click.
  defaultPreload: "intent",
  // Let TanStack Query decide freshness; the router always calls the loader.
  defaultPreloadStaleTime: 0,
  // Navigations run inside document.startViewTransition: the header holds, the tab
  // pill glides, the page crossfades. CSS defines the animation.
  defaultViewTransition: true,
  defaultPendingComponent: PagePending,
  defaultErrorComponent: PageError,
  // No spinner flash for fast loads; once shown, keep it long enough to read.
  defaultPendingMs: 300,
  defaultPendingMinMs: 300,
  scrollRestoration: true,
});

declare module "@tanstack/react-router" {
  interface Register {
    router: typeof router;
  }
}

// Any 401 from a data call sends the person to sign in, and back to this page afterwards.
// One bounce at a time: a page fires several requests and they all fail together.
let bouncing = false;
setUnauthorizedHandler(() => {
  const here = router.state.location;
  if (bouncing || here.pathname === "/login" || here.pathname === "/register") return;
  bouncing = true;
  queryClient.removeQueries({ queryKey: keys.me });
  void router.navigate({ to: "/login", search: { next: here.href } }).finally(() => {
    bouncing = false;
  });
});

const root = document.getElementById("root");
if (!root) throw new Error("index.html is missing #root");

createRoot(root).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router} />
    </QueryClientProvider>
  </StrictMode>,
);
