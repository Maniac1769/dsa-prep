# System design: LLD and HLD track

Companion to [DSA-SYSTEM.md](./DSA-SYSTEM.md). Same vocabulary: a **block** is a unit of work, not a
calendar week. Same 0-3 attempt score. Same anchor-and-recall retention model.

Resources are in [FREE-RESOURCES.md](./FREE-RESOURCES.md).

## Assumptions, stated so you can reject them

- Target level is **SDE-2 / SDE-3 equivalent in India**. That means LLD and machine coding carry more
  weight than staff-level HLD. If you are interviewing for a senior or staff loop, the HLD track needs
  to roughly double and this file is not sufficient.
- You will write LLD in **C++**. Most published LLD material is Java. The designs transfer; the idioms
  do not. Where it matters there is a C++ note in the block.
- This track runs **alongside** the DSA hour, not inside it. The DSA plan's 420 min/week stays intact.
- 34 blocks at roughly one block per week lands close to the DSA plan's 46-week nominal length, so the
  two tracks finish at about the same time. Blocks marked **[2]** usually take two.

## Why LLD first, then interleaved

Indian big-tech loops at this level fail candidates on machine coding more often than on distributed
systems depth. A machine coding round is a 60-90 minute live exercise: you get a loose problem
statement and must produce compiling, extensible, testable code with sane class boundaries. It is
closer to the DSA work you are already doing, so it compounds earlier.

HLD is slower-burning and benefits from having seen real systems. It is sequenced second but starts
before LLD finishes, so neither track goes cold.

Running order:

| Phase | Blocks | What it covers |
|---|---|---|
| 1 | L1-L9 | OO fundamentals, the patterns that actually appear, first four machine-coding problems |
| 2 | H1-H8 | HLD vocabulary and the five canonical designs |
| 3 | L10-L18 | Concurrency, harder machine coding, extensibility under changing requirements |
| 4 | H9-H16 | Storage/consistency depth, five harder designs, deep-dive defence |
| 5 | X1-X4 | Mock rounds, failure repair, company-specific targeting |

Do not start Phase 2 before L9 is scored 2 or better.

---

## The session shape

A system design session is **30 minutes** and has exactly one of three shapes. Pick by what the block
asks for; do not improvise a fourth.

**Shape A — Learn (30 min).** Read or watch one specific thing, then close it and write a half-page
of notes from memory. The notes are the artefact, not the highlighting. If you cannot write the page,
you did not learn it; reread once and try again next session.

**Shape B — Build (30 min, usually two or three consecutive sessions).** Write actual code or an
actual diagram. For LLD: compiling C++ with a `main` that exercises it. For HLD: a diagram plus a
written API surface plus a capacity estimate. Stop at 30 minutes mid-sentence; resume next session.

**Shape C — Defend (30 min).** Take a design you already built and attack it. Write down three
questions an interviewer would ask, then answer them in writing. Typical attacks: what breaks at 100x
traffic, what happens when this component dies, why not the obvious alternative.

Every block ends with Shape C at least once. A design you have never defended is not learned.

---

## Scoring, adapted for design

The DSA 0-3 scale does not transfer cleanly, because there is no "correct answer" to compile. Use this:

| Score | LLD meaning | HLD meaning |
|---|---|---|
| 0 | Could not produce a class model without the solution open | Could not name the components |
| 1 | Produced it, but needed the reference while working | Produced a diagram while looking at a reference |
| 2 | Produced it unaided, but it was rigid, or you could not justify a boundary, or it did not compile cleanly | Produced it unaided, but could not size it or defend one component choice |
| 3 | Unaided, compiles, and you can take a new requirement live and say exactly which classes change | Unaided, with capacity numbers, and you can defend two component choices against a named alternative |

The single most useful signal for LLD is the **extension test**: after you finish, invent a requirement
you did not design for and state which files change. If the answer is "most of them", you scored 1,
whatever the code looks like.

For HLD the equivalent is the **number test**: if you cannot state requests per second, storage growth
per year, and whether it fits in memory, you scored at most 1.

---

## Retention: what actually decays

Design knowledge decays differently from algorithms. You will not forget what a load balancer is. You
will forget the *decisions* — why a queue and not a direct call, why Cassandra and not Postgres, what
number made you shard. So the recall prompts target decisions, not definitions.

**Short recall (4 minutes), at +1, +10, +30, +75 days after the block.** One prompt, written answer:

- LLD block: "Name the classes and the one extension this design makes cheap."
- HLD block: "Name the bottleneck you designed around, and the number that proved it was a bottleneck."

**Anchor rebuild.** Each block has one anchor artefact. At roughly +21 days, rebuild it from a blank
page or blank file in 20 minutes, timed, without looking. Compare to the original afterwards, and
write down only what you lost. At roughly +60 days, rebuild it again or transfer it to a stated
variant ("same design, but reads are now 50x writes").

**Queue caps, same spirit as the DSA plan:**

- More than four anchor rebuilds queued: next block becomes a rebuild session instead of new work.
- More than eight overdue short recalls: the next Saturday slot is recall-only.
- Two clean unaided rebuilds at least three weeks apart retires an anchor from the frequent queue.
- A failed rebuild means: repair the gap the same session, recall at +1 day, rebuild within three
  sessions. It does not mean redoing the whole block.

**The thing that makes this stick is writing the decision down at the time you make it.** Every block
produces a `DECISIONS` note of three to six lines: what you chose, what you rejected, and the number
or constraint that decided it. The recall prompts read from that note. A block without a decisions
note cannot be recalled usefully and should be redone.

---

## Phase 1: LLD foundations (L1-L9)

| Block | Focus | Build artefact (anchor in bold) | Prerequisite / note |
|---|---|---|---|
| L1 | What machine coding actually grades: class boundaries, no god class, no premature interface. Read one worked example end to end. | Written half-page: the five grading criteria and what loses points | Shape A only. Do not write code this block. |
| L2 | SOLID, but only as a diagnostic. For each of the five, one concrete symptom in code you have written. | **Notes page naming a real violation you have personally shipped** | SOLID as vocabulary for explaining decisions out loud, not as a rulebook. |
| L3 | Composition over inheritance; interfaces vs abstract base. C++ note: no `interface` keyword, so this is pure virtual classes, and you must think about virtual destructors and slicing. | Small program: one design in inheritance, the same in composition, written comparison | |
| L4 | **Parking Lot** | **Working C++ parking lot** with vehicle types, spot allocation, pricing | [2] The canonical first machine-coding problem. Extension test: add a new vehicle type and a new pricing rule. |
| L5 | Creational patterns that appear: Factory, Abstract Factory, Builder, Singleton. Singleton including why interviewers increasingly treat it as a smell. | Refactor L4 to use a factory for vehicles and a builder for the pricing config | Only these four. Do not read all 23 patterns. |
| L6 | Behavioural patterns that appear: Strategy, Observer, State, Command. | **Small program using each of the four once, with a written note on which L4 problem each would have solved** | Strategy and Observer are the two you will actually reach for. |
| L7 | **Elevator system** | **Working C++ elevator** with a scheduling strategy swapped behind an interface | [2] Teaches State and Strategy under one roof. Extension test: change the scheduling policy. |
| L8 | Structural patterns: Adapter, Decorator, Facade, Composite. | Written note mapping each to one system you work on at your day job | Composite matters most; it shows up in file systems, menus, org charts. |
| L9 | **Design a deck-of-cards / card game** or **Snake and Ladders**, timed at 60 minutes in one sitting | **Timed solo build, scored** | Gate: score 2 or better before Phase 2. This is your first honest self-assessment. |

C++ specifics to pick up across Phase 1, just in time: `std::unique_ptr` and `std::shared_ptr` for
ownership in class graphs, `std::function` for strategies, virtual destructors, `enum class`, and why
you pass `const T&`. You do not need templates for machine coding.

---

## Phase 2: HLD vocabulary and the canonical five (H1-H8)

| Block | Focus | Build artefact (anchor in bold) | Prerequisite / note |
|---|---|---|---|
| H1 | The interview framework: requirements, scale estimate, API, data model, high-level diagram, deep dive. Learn the order and stick to it. | **Written one-page template you will reuse for every H block** | Shape A. The framework is the thing being graded as much as the design. |
| H2 | Numbers to know and back-of-envelope estimation: QPS, storage/year, bandwidth, what fits in RAM, latency ladder. | Estimate three systems you use daily; write the arithmetic | Without this, every later block scores at most 1. |
| H3 | Building blocks part one: load balancer, reverse proxy, caching (and the four invalidation strategies), CDN. | Notes page: when each is the wrong choice | |
| H4 | Building blocks part two: SQL vs NoSQL, indexing, replication, sharding and what a bad shard key costs. | **Notes page: three shard keys and why two of them are bad** | Shard-key reasoning is the single most common HLD follow-up. |
| H5 | Building blocks part three: message queues, pub/sub, idempotency, retries, dead letters. CAP as a vocabulary, not a law to recite. | Notes page: one at-least-once flow made idempotent | |
| H6 | **Design a URL shortener** | **Full design: API, key generation, data model, cache, estimates** | The cheapest full run of the H1 framework. Deep dive: key collisions and custom aliases. |
| H7 | **Design a rate limiter** | **Full design, with the four algorithms compared** | Distributed state is the real problem, not the algorithm. |
| H8 | **Design a news feed** (Twitter/LinkedIn timeline) | **Full design with fan-out-on-write vs on-read decided by a number** | [2] The celebrity problem is the point. Defend your hybrid. |

---

## Phase 3: LLD under pressure (L10-L18)

| Block | Focus | Build artefact (anchor in bold) | Prerequisite / note |
|---|---|---|---|
| L10 | Concurrency primitives in C++: `std::thread`, `std::mutex`, `lock_guard`, `condition_variable`, atomics. What a data race actually is. | Small program with a deliberate race, then fixed | Needed from here on; several machine-coding problems are graded on thread safety. |
| L11 | Thread-safe design: where to put the lock, lock granularity, why a thread-safe class is not a thread-safe program. | **Thread-safe bounded blocking queue in C++** | Classic warm-up asked on its own at Amazon and LinkedIn. |
| L12 | **Design a logging library** | **Working C++ logger**: levels, sinks, async, configurable | Strategy plus Observer plus concurrency in one. Extension test: add a new sink. |
| L13 | **Design Splitwise** | **Working expense-splitting model** with multiple split strategies and settlement | [2] Teaches domain modelling and the Strategy pattern on a problem with real ambiguity. |
| L14 | **Design an in-memory cache with LRU and pluggable eviction** | **Working C++ cache**, thread-safe, eviction behind an interface | Links back to DSA block 12 (LRU Cache). Extension test: swap LRU for LFU without touching the cache class. |
| L15 | **Design a vending machine or ATM** | **Working state-machine implementation** | The cleanest State-pattern problem. Fast if L6 landed. |
| L16 | **Design BookMyShow / movie ticket booking** | **Working seat-booking model with concurrent booking handled** | [2] Double-booking under concurrency is the whole grade. |
| L17 | **Design a rate limiter, as LLD this time** | **Working C++ token bucket and sliding window behind one interface** | Deliberate mirror of H7. Seeing the same problem at both levels is the point. |
| L18 | Testability: how to make a machine-coding solution testable in the 10 minutes you have left. Dependency injection by constructor, clock injection, no `new` in business logic. | **Add tests to any two Phase 3 artefacts** | Candidates lose points here more than they expect. |

---

## Phase 4: HLD depth (H9-H16)

| Block | Focus | Build artefact (anchor in bold) | Prerequisite / note |
|---|---|---|---|
| H9 | Consistency models, quorums, leader election, and what a distributed transaction costs. Saga as the usual answer. | Notes page: one saga with its compensating actions | |
| H10 | **Design a chat system** (WhatsApp / Slack) | **Full design: connection handling, delivery receipts, offline queue** | [2] WebSockets, presence, and ordering. |
| H11 | **Design a notification service** | **Full design: multi-channel, retries, dedup, user preferences** | The idempotency work from H5 pays off here. |
| H12 | **Design a distributed job scheduler** | **Full design: at-least-once execution, leasing, failure recovery** | [2] Leasing and fencing tokens are the deep dive. |
| H13 | **Design a video platform** (YouTube) or **file storage** (Dropbox) | **Full design: upload pipeline, chunking, CDN, transcoding** | Pick one. Both teach blob storage and the CDN story. |
| H14 | **Design a ride-hailing system** (Uber) | **Full design: geospatial index, matching, state across a trip** | [2] Geohash / quadtree is the component you have not seen elsewhere. |
| H15 | Observability, deployment, and failure: what you say when asked "how do you know it is broken". Metrics, SLOs, circuit breakers, bulkheads, graceful degradation. | **Notes page: the five questions you will be asked at the end of every HLD round, with your answers** | Underprepared by almost everyone; cheap to prepare. |
| H16 | Deep-dive defence drill: take three Phase 2 and 4 designs and run Shape C hard on each. | **Written attack-and-answer sheet per design** | This is the block that converts "I drew it" into "I can hold it under questioning". |

---

## Phase 5: Interview preparation (X1-X4)

| Block | Focus |
|---|---|
| X1 | Recruiter-led targeting. Ask your recruiter what the loop actually contains: machine coding, HLD, LLD, or a mix. Build the remaining plan from that answer, not from anecdotes. For Broadcom and VMware-lineage teams specifically, expect C++ and systems questions that this track does not cover. |
| X2 | Two timed LLD mocks, 60 minutes each, unseen problem, out loud. Record yourself or use a peer. |
| X3 | Two timed HLD mocks, 45 minutes each, unseen problem, out loud. The out-loud part is not optional; silent design is a different skill. |
| X4 | Failure repair. Go back to every block scored 0 or 1 and re-run it. Only then consider the track complete. |

Readiness heuristic, held loosely: you can take four unseen LLD problems and produce compiling,
extensible solutions in 60 minutes for three of them; and you can run the H1 framework on an unseen
HLD problem without referring to the template. No guarantee is attached to this.

---

## What this track deliberately does not cover

- Staff-plus HLD: multi-region active-active, cost modelling, organisational tradeoffs.
- Language-internals rounds (JVM internals, C++ memory model depth) that some Broadcom and VMware
  teams ask. If your loop includes one, that is separate preparation.
- Frontend or mobile system design.
- Infrastructure-as-code, Kubernetes, or cloud-provider-specific design.

Add any of these only when a recruiter tells you the loop contains it.

---

## Honest limitations

- The block ordering, session shapes, scoring rubric, and recall intervals are a considered synthesis,
  not experimentally validated. Treat them as a starting configuration and adjust using your own
  recorded scores.
- The problem selection reflects problems that recur in publicly posted Indian big-tech interview
  accounts. There is no verified claim that any specific company asked any specific problem on your
  loop.
- Thirty-four blocks at one per week is an estimate with no deadline attached to it. Heavy blocks are
  marked [2]; several will take three.
- Design interviews are graded partly on communication. Nothing in a written track measures that. The
  out-loud mocks in X2 and X3 are the only place it is tested, and two each is thin.
