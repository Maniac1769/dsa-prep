import type { IconName } from "../icon-names";

/** A glyph from the Phosphor sprite in public/icons.svg. Decorative: label the control, not the icon. */
export function Icon({ name }: { name: IconName }) {
  return (
    <svg className="icon" aria-hidden="true" focusable="false" fill="currentColor">
      <use href={`/icons.svg#i-${name}`} />
    </svg>
  );
}
