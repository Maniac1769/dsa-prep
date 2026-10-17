# API contract (v2: accounts)

The backend (`backend/app`) and the front end (`frontend/src`) both build against this
file. JSON everywhere. Dates are ISO `YYYY-MM-DD` in the user's timezone; timestamps are
ISO 8601 UTC.

## Conventions

- **Auth.** A session cookie `prep_session`: `HttpOnly`, `SameSite=Lax`, `Path=/`,
  `Secure` unless `COOKIE_SECURE=0` (local dev), 30-day expiry, refreshed when under 15
  days remain. The cookie holds a random token; the database stores only its SHA-256.
- **Every POST** needs header `X-Prep: 1` (existing CSRF guard), including auth routes.
- **Every `/api/*` route except `/api/auth/*`** needs a session, else `401`.
- **Errors**: `{"detail": "<human sentence>"}` with 400 invalid input, 401 not signed in,
  403 forbidden (sign-ups full, wrong password on delete), 404, 409 conflict,
  429 too many attempts (with `Retry-After` seconds).

## Types

```ts
type ListKey = "plan" | "sde" | "a2z";       // the three problem lists
type SessionKind = "learn" | "resolve" | "mixed" | "catchup";
type Theme = "system" | "light" | "dark";      // stored per device in localStorage only

interface User {
  id: number;
  username: string;          // 3-24 chars, [a-z0-9_-], case-insensitive unique
  preferred_list: ListKey;   // the list Today, Plan and Stats are built from
  timezone: string;          // IANA, e.g. "Asia/Kolkata"
  weekly_sessions: number;   // DSA sessions per week, 3-7, default 5
  design_sessions: number;   // system design sessions per week, 0-7, default 3
  design_minutes: number;    // 15 | 30 | 45 | 60, default 30
  created_at: string;
}

interface ListInfo { key: ListKey; title: string; total: number; solid: number; preferred: boolean }
```

`lists` titles: `plan` = "Prep plan (126)", `sde` = "Striver SDE sheet (153)",
`a2z` = "Striver A2Z sheet (495)" (totals computed, not hard-coded).

## Auth

| Method | Path | Body | Response |
|---|---|---|---|
| GET | `/api/auth/status` | | `{registration_open: bool, users: number, cap: number, lists: {key: ListKey, title: string, total: number}[]}` (public: the register page needs the list names) |
| GET | `/api/auth/me` | | `{user: User}` or 401 |
| POST | `/api/auth/register` | `{username, password, timezone, preferred_list?}` | 201 `{user: User}` + cookie |
| POST | `/api/auth/login` | `{username, password}` | `{user: User}` + cookie |
| POST | `/api/auth/logout` | | 204, cookie cleared |

- Password: 10-128 chars. Hash: stdlib `hashlib.scrypt` (n=2^14, r=8, p=1, 16-byte salt),
  stored as `scrypt$<n>$<r>$<p>$<salt b64>$<hash b64>`, compared with
  `hmac.compare_digest`. Unknown usernames still run one scrypt (equal timing).
- Registration cap: `MAX_USERS` env (default 20), enforced inside the insert
  transaction. Over the cap: 403 "Sign-ups are full: 20 of 20 places taken."
- Login throttle: per username, 5 failures in 15 minutes locks it for 15 minutes (429);
  globally, more than 30 login or register attempts a minute returns 429.
- Register signs the user in.

## Account

| Method | Path | Body | Response |
|---|---|---|---|
| POST | `/api/account/settings` | any of `{preferred_list, timezone, weekly_sessions, design_sessions, design_minutes}` | `{user: User}` |
| POST | `/api/account/password` | `{current_password, new_password}` | 204; other sessions of this user are ended |
| POST | `/api/account/delete` | `{password}` | 204; user and all their data deleted, cookie cleared |
| GET | `/api/account/lists` | | `{lists: ListInfo[]}` |

Changing `preferred_list` never deletes progress: progress is stored per problem, and a
problem that appears in several lists shares one record, matched by LeetCode slug.

**Canonical record.** For a slug present in more than one list, the canonical item is the
one in `plan`, else `sde`, else `a2z` (lowest `seq` within that list). Rows in the other
lists carry `log_id` = the canonical item's id and show its status; logging, starring
and resetting always act on the canonical item. Problems without a slug are their own
record.

**Review ladder eligibility.** Problems in the user's preferred list get the review ladder
when first studied. Problems from other lists get it only when starred.

**Anchors** (get full re-solves, not just recalls): `plan` = the first problem of each
numbered block (as today); `sde` and `a2z` = the first problem of each lecture
(`subsection`).

## Practice (all scoped to the signed-in user)

Unchanged paths, unchanged bodies unless noted: `GET /api/items/{id}`, `POST /api/log`,
`POST /api/reviews/{id}`, `POST /api/items/{id}/star`, `POST /api/decisions`,
`POST /api/reviews/spread`, `GET /api/design`. `POST /api/settings` is removed (use
`/api/account/settings`). `POST /api/log` also accepts `mode: "recall"` (short days).

### GET /api/today

Existing fields keep their meaning. Changed or new:

```ts
{
  // ...existing fields (on, reviews, verdict, focus, blocking, design, split, activity,
  //    streak, best_streak, due_week, unaided, total, week_days, ...)
  list: ListInfo;                       // the preferred list
  context: string;                      // e.g. "Block 2 of 42, arrays, strings and hashing"
                                        //   or "Step 3 of 20: Arrays, lecture Easy problems"
  session: {
    kind: SessionKind;                  // what this session is for
    number: number;                     // 1-based index of this session in the week
    of: number;                         // user.weekly_sessions
    done_today: boolean;                // a full session is already logged today
    week_done: boolean;                 // weekly budget met; extra sessions are optional
    short_days: number;                 // short days logged this week
  };
  day: DayPlan;                         // headline/segments/guidance for session.kind
  short_day: {                          // always present: the 10-minute fallback
    reviews: Review[];                  // up to 2 due recalls
    recall_item: Row | null;            // if none due: the most recently studied problem
  };
  quiet_days: number | null;            // days since the last session if >= 2, else null
  design: null | { /* existing */ sessions_done: number; sessions_target: number };
  unaided: number; total: number;       // now over the preferred list
}
```

Removed: `weekday`-driven branching. The kind comes from the weekly sequence below.

### Weekly session model

A **full session** is a day with at least one attempt in mode learn, solve, resolve,
rebuild or mock. A **short day** is a day whose only attempts are recalls. Weeks start
Monday in the user's timezone.

The week runs a fixed sequence, indexed by the number of full sessions already done this
week (a day that already has a full session keeps that day's kind):

| weekly_sessions | sequence |
|---|---|
| 3 | learn, learn, resolve |
| 4 | learn, learn, learn, resolve |
| 5 | learn, learn, learn, resolve, mixed |
| 6 | learn, learn, learn, learn, resolve, mixed |
| 7 | learn, learn, learn, learn, resolve, mixed, catchup |

Past the budget, the kind repeats `learn` and `week_done` is true. The queue caps still
win: when new work is blocked the session is a review session whatever its kind.
Missed days cost nothing: the sequence simply continues the next time you open Today.

Design: offered after DSA while `design sessions done this week < design_sessions`
(a design session is a day with an attempt on an LLD/HLD/prep item).

### GET /api/problems?view=plan|sde|a2z

`plan` keeps its current shape. `sde` uses the `a2z` shape (steps, lectures, rows). Every
response adds `lists: ListInfo[]`. Rows show the status of the shared problem record.

### GET /api/plan

`week` (seven weekday rows) is replaced by:

```ts
sessions: { kind: SessionKind; label: string; minutes: number; done: boolean; next: boolean }[];
weekly_sessions: number; design_sessions: number; design_minutes: number;
pace: { new_per_week: number; weeks_left: number };  // from learn sessions per week
roadmap: ...;   // plan: groups as today; sde/a2z: steps with done/total
```

### GET /api/stats

`bars` keeps the preferred list's bar plus LLD and HLD; other lists are not shown as
completion goals. KPI adds `sessions_week` and `sessions_target`.

### Reset

`GET /api/reset`, `POST /api/reset`, `POST /api/reset/undo` keep their shapes. Scopes:
`week | plan | sde | a2z | design | item | all`, all limited to the signed-in user.
Snapshots are per user (rows serialised to JSON in the database), never a whole-database
copy, so one user's undo cannot touch another user.

## Operational

- `GET /healthz` unchanged. `GET /digest?token=..&user=<username>` builds that user's
  digest.
- Migration to schema v3 copies any pre-accounts progress into `legacy_*` tables and
  starts every account fresh. Nothing is deleted.
- `python -m app.admin reset-password <username>` (run in the container) prints a one-time
  random password; `python -m app.admin delete-user <username>` removes an account.
