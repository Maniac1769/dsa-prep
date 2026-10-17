import type { InputHTMLAttributes } from "react";

type Props = InputHTMLAttributes<HTMLInputElement> & {
  id: string;
  label: string;
  /** The rule, always visible, so nobody has to fail first to learn it. */
  hint?: string;
  /** Set once the value has been touched and breaks the rule. */
  invalid?: boolean;
};

/** A labelled input. The rule sits under it and is tied to it for screen readers. */
export function TextField({ id, label, hint, invalid = false, ...input }: Props) {
  const hintId = `${id}-hint`;
  return (
    <div className="field">
      <label htmlFor={id}>{label}</label>
      <input id={id} aria-invalid={invalid || undefined} aria-describedby={hint ? hintId : undefined} {...input} />
      {hint && (
        <p id={hintId} className={`field-hint${invalid ? " is-invalid" : ""}`}>
          {hint}
        </p>
      )}
    </div>
  );
}
