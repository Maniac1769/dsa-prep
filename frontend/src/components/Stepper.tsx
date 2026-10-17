import { Icon } from "./Icon";

interface Props {
  /** Names the group for assistive tech, e.g. "DSA sessions per week". */
  label: string;
  /** The allowed values in order. The stepper moves one position at a time. */
  values: readonly number[];
  value: number;
  onChange: (v: number) => void;
  /** Appended to the shown value, e.g. " min". */
  suffix?: string;
  small?: boolean;
  disabled?: boolean;
}

/** Minus, value, plus: a choice from a short ordered list, with no typing and no invalid state. */
export function Stepper({ label, values, value, onChange, suffix = "", small = false, disabled = false }: Props) {
  const i = Math.max(values.indexOf(value), 0);
  const prev = values[i - 1];
  const next = values[i + 1];
  return (
    <span className={`stepper${small ? " is-sm" : ""}`} role="group" aria-label={label}>
      <button type="button" aria-label={`Fewer: ${label}`} disabled={disabled || prev === undefined} onClick={() => prev !== undefined && onChange(prev)}>
        <Icon name="minus" />
      </button>
      <output aria-live="polite">
        {value}
        {suffix}
      </output>
      <button type="button" aria-label={`More: ${label}`} disabled={disabled || next === undefined} onClick={() => next !== undefined && onChange(next)}>
        <Icon name="plus" />
      </button>
    </span>
  );
}
