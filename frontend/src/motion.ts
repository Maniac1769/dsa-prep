// GSAP is used only where CSS cannot do the job: the stats entrance timeline, the
// KPI count-up, the strip cascade, card handovers, and the spring pop on a changed
// status. List reflow uses the browser's view transitions (zero bytes); press, hover,
// accordions and page transitions are CSS.
//
// Every tween moves transform or opacity only, and every entry point checks
// reduced motion first.

import { gsap } from "gsap";
import { useGSAP } from "@gsap/react";

gsap.registerPlugin(useGSAP);

// Matches the CSS --ease-out-expo token, so GSAP and CSS motion feel like one system.
gsap.defaults({ ease: "expo.out", duration: 0.6 });

export function prefersReducedMotion(): boolean {
  return typeof window !== "undefined" && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
}

export { gsap, useGSAP };
