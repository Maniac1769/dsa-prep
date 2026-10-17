# Product

Every design decision in this repo reads from this file. The evidence behind each rule is
in [docs/why.md](docs/why.md).

## Register

product

## Users

Engineers preparing for coding interviews while working full time. A typical day leaves
about an hour, usually in the evening with LeetCode open in the next tab; some days work
takes everything. They glance at the site on a phone in the morning and do the real work
at a desk at night. Starting is the hardest step, attention is limited after a workday,
and visible progress keeps them coming back.

Sign-ups are capped (20 accounts) while the free-tier server's limits are measured.

## Product purpose

Say what to do in this session, record what happened honestly, and bring old problems
back before they fade. Success is a run of honest sessions and a growing count of problems
solved unaided, not a count of problems touched.

## Brand personality

Calm, exact, unhurried. A good study desk: everything needed is within reach, nothing
else is on it. The voice is a peer who states the next action and stops talking.

## Anti-references

- Gamified study apps: confetti, XP bars, badges, mascots, streak shaming.
- SaaS dashboard templates: hero metric with gradient accent, rows of identical cards.
- Sheets presented as todo lists to complete in parallel.
- Copying takeuforward's look. Borrow its affordances (collapsible steps, per-problem
  article, video and practice links, a revision star), not its skin.

## Design principles

1. **One next action above the fold.** Every screen answers "what do I do now" before it
   shows anything else.
2. **Honest progress.** Solved with help and solved unaided look different everywhere. The
   numbers never flatter.
3. **Flexible, not fixed.** The plan is a weekly budget, not a calendar. A lost day costs
   nothing; a 10-minute day is always on offer.
4. **Quiet until it matters.** Colour, motion and weight are reserved for state: due,
   failed, done. Decoration is absent. No red warnings for missed days.
5. **Earned familiarity.** Standard controls, standard links, standard layout. The tool
   disappears into the hour.
6. **Phone and desk are both first class.** The morning glance and the evening session are
   the same product.

## Accessibility and inclusion

WCAG 2.2 AA. Text contrast at least 4.5:1 in both themes, chosen by the system or by the
header toggle. Never colour alone: every state carries a label or icon. Respect
`prefers-reduced-motion`. Every chart has a table view. Usable at 360px wide with no
horizontal page scroll.
