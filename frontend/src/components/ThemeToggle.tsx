import type { IconName } from "../icon-names";
import { NEXT_THEME, useTheme, type Theme } from "../theme";
import { Icon } from "./Icon";

export const THEME_LABEL: Record<Theme, string> = { system: "System", light: "Light", dark: "Dark" };
const THEME_ICON: Record<Theme, IconName> = { system: "monitor", light: "sun", dark: "moon" };

/** Header button: one click moves system, light, dark, system. The icon shows the current mode. */
export function ThemeToggle() {
  const [theme, set] = useTheme();
  const next = NEXT_THEME[theme];
  const label = `Theme: ${THEME_LABEL[theme].toLowerCase()}. Switch to ${THEME_LABEL[next].toLowerCase()}.`;
  return (
    <button type="button" className="btn btn-icon btn-quiet" title={label} aria-label={label} onClick={() => set(next)}>
      <Icon name={THEME_ICON[theme]} />
    </button>
  );
}

const THEMES: Theme[] = ["system", "light", "dark"];

/** The same choice as the header button, laid out as three options. */
export function ThemeSegmented() {
  const [theme, set] = useTheme();
  return (
    <div className="segmented" role="group" aria-label="Theme">
      {THEMES.map((t) => (
        <button key={t} type="button" aria-pressed={theme === t} onClick={() => set(t)}>
          <Icon name={THEME_ICON[t]} />
          {THEME_LABEL[t]}
        </button>
      ))}
    </div>
  );
}
