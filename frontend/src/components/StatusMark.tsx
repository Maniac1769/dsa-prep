import { useRef } from "react";
import type { Status } from "../api";
import { gsap, prefersReducedMotion, useGSAP } from "../motion";
import { Icon } from "./Icon";

export const STATUS_LABEL: Record<Status, string> = {
  todo: "Not started",
  started: "Started, no approach yet",
  helped: "Solved with help",
  unaided: "Unaided, still shaky",
  solid: "Unaided and solid",
};

/** The status circle. Springs once when its status changes, never on first paint. */
export function StatusMark({ status }: { status: Status }) {
  const ref = useRef<HTMLSpanElement>(null);
  const first = useRef(true);

  useGSAP(
    () => {
      if (first.current) {
        first.current = false;
        return;
      }
      if (prefersReducedMotion() || document.hidden || !ref.current) return;
      gsap.fromTo(ref.current, { scale: 0.7 }, { scale: 1, duration: 0.55, ease: "back.out(2.4)" });
      const icon = ref.current.querySelector(".icon");
      if (icon) gsap.fromTo(icon, { scale: 0.4, rotate: -14, opacity: 0 }, { scale: 1, rotate: 0, opacity: 1, duration: 0.4, delay: 0.05 });
    },
    { dependencies: [status], scope: ref },
  );

  return (
    <span ref={ref} className="status" data-status={status}>
      {(status === "unaided" || status === "solid") && <Icon name="check" />}
    </span>
  );
}
