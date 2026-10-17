import { useSyncExternalStore } from "react";

export type Theme = "system" | "light" | "dark";

const KEY = "prep-theme";
const LIGHT_COLOR = "#ffffff";
const DARK_COLOR = "#0d0d0d";

export const NEXT_THEME: Record<Theme, Theme> = { system: "light", light: "dark", dark: "system" };

// localStorage can throw (private windows, blocked site data); the theme then lasts
// until the tab closes, which is the right degradation.
function read(): Theme {
  try {
    const v = localStorage.getItem(KEY);
    return v === "light" || v === "dark" ? v : "system";
  } catch {
    return "system";
  }
}

let current: Theme = read();
const listeners = new Set<() => void>();

/** Mirror the choice onto <html data-theme> and the theme-color metas. */
function apply(t: Theme) {
  const root = document.documentElement;
  if (t === "system") root.removeAttribute("data-theme");
  else root.setAttribute("data-theme", t);
  const metas = document.querySelectorAll<HTMLMetaElement>('meta[name="theme-color"]');
  metas.forEach((m, i) => {
    if (t === "system") {
      m.media = i === 0 ? "(prefers-color-scheme: light)" : "(prefers-color-scheme: dark)";
      m.content = i === 0 ? LIGHT_COLOR : DARK_COLOR;
    } else {
      m.media = "all";
      m.content = t === "dark" ? DARK_COLOR : LIGHT_COLOR;
    }
  });
}

function emit() {
  listeners.forEach((l) => l());
}

export function setTheme(t: Theme) {
  current = t;
  try {
    localStorage.setItem(KEY, t);
  } catch {
    // Not persisted; the choice still applies to this page.
  }
  apply(t);
  emit();
}

// Another tab changed the preference.
window.addEventListener("storage", (e) => {
  if (e.key !== KEY) return;
  current = read();
  apply(current);
  emit();
});

function subscribe(l: () => void) {
  listeners.add(l);
  return () => listeners.delete(l);
}

export function useTheme(): [Theme, (t: Theme) => void] {
  const theme = useSyncExternalStore(subscribe, () => current, () => "system" as Theme);
  return [theme, setTheme];
}
