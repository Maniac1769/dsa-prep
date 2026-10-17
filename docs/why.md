# Why it works this way

Every rule in this app is a bet about what helps people get good at coding interviews
while holding a job. This page lists each bet, the habit it encodes, and where that habit
comes from, so a change can be argued against the evidence rather than against taste.

**How strong is the evidence?** Mostly community experience: LeetCode Discuss, Blind,
Reddit, Codeforces, and engineers' write-ups, plus one controlled study on retrieval
practice. Candidate stories are self-reported and survivor-biased, and some guides are
written by people selling a product. Where independent sources agree, we treat it as a
reasonable default, not a law. The exact intervals and caps are our choices.

## The dos and don'ts

| # | Do | Don't |
|---|---|---|
| 1 | Pick **one** curated list, in pattern order, and finish it. | Run several sheets as parallel completion goals, or hop between them. |
| 2 | Measure what you can solve **unaided**. | Count problems touched. |
| 3 | Attempt under a **timebox**, take **graduated hints**, then **re-solve from a blank editor** later. | Open the solution early, or stop at "I understood the editorial". |
| 4 | **Schedule revision**, with the next gap set by how the last attempt went. | Let old problems fade, or let reviews pile up unseen. |
| 5 | Keep a **sustainable budget**: about an hour, five days a week, with rest. | Grind 2 to 3 hours a day on top of a job, or double up after a miss. |
| 6 | When a day is lost, do the **smallest restart** and move on. | Shame streaks, gate work, or treat one miss as failure. |

## How each feature follows from them

| Feature | Rule | Evidence |
|---|---|---|
| You choose one list (Prep plan, Striver SDE, or Striver A2Z); Today, Plan and the completion bar use only that list | Do 1 | Comparisons of the major sheets converge on "pick one list, complete it, then layer in company prep" ([InterviewPilot](https://interviewpilot.dev/blog/neetcode-150-vs-striver-sde-vs-blind-75), [SpaceComplexity](https://spacecomplexity.ai/blog/best-dsa-sheet-for-beginners)). The overlap between sheets is large, so a second sheet mostly adds a longer todo list. |
| Other lists stay browsable as a library, and switching lists keeps all progress (progress is stored per problem, shared across lists) | Do 1 | Same sources. Lessons from a bigger sheet are still useful; completing it alongside another is what costs revision time ([LeetCode Top Interview 150](https://leetcode.com/studyplan/top-interview-150/) calls itself 3+ months on its own). |
| The plan runs in pattern blocks (arrays, two pointers, stacks, ...) | Do 1 | [NeetCode's preparation guide](https://blog.neetcode.io/p/prepare-coding-interviews) recommends learning patterns in order and revisiting them. |
| The headline number is "solved unaided"; help-assisted solves are drawn differently everywhere | Do 2 | Many candidates report hundreds of solves without being able to re-solve them; one Blind poster who finished NeetCode 150 could re-solve about 40 of 150 cold ([Blind](https://www.teamblind.com/post/leetcode-memorization-problem-wnz0lcrw), [Educative](https://www.educative.io/blog/how-many-leetcode-problems-should-i-do)). |
| Every attempt is scored 0 to 3 (stuck, with help, shaky, solid) | Do 2, Do 4 | A candidate reporting a Google offer used self-ratings plus spaced review ([r/leetcode](https://www.reddit.com/r/leetcode/comments/1khs9d0/my_lc_prep_google_offer_swe_ii_l3/)). The score drives the next review. |
| The focus card shows the 45-minute protocol: restate, find the improvement, code, one small hint after 10 stuck minutes | Do 3 | Community timeboxes cluster at about 20 minutes for an easy, 30 to 45 for a medium, 60 for a hard, followed by a hint before the full solution ([Design Gurus](https://www.designgurus.io/answers/detail/how-long-does-it-take-to-finish-a-leetcode), [Blind](https://www.teamblind.com/post/leetcode-problems-5kn28rw5)). |
| Re-solve sessions use a blank editor; mixed practice hides the topic | Do 3 | Re-solving cold is how people check a solution actually stuck; hiding the topic trains recognising the pattern, which is the real interview skill ([leetcode-coach](https://github.com/NeilP211/leetcode-coach)). |
| Logging a problem schedules recalls at +1, +7, +21 and +60 days, and full re-solves for anchor problems; a failed review comes back in 1 to 3 days | Do 4 | Spaced repetition is the common answer to forgetting solved problems ([LeetCode Discuss](https://leetcode.com/discuss/post/222829/spaced-learning-repetition-once-you-learned-it-you-will-never-forget-it/)). Retrieval practice improves delayed retention in a controlled study, though not one on programming ([Roediger and Karpicke, 2006](https://pubmed.ncbi.nlm.nih.gov/16507066/)). |
| When too many reviews are due, Today stops offering new work and says why | Do 4, Don't 5 | Caps keep revision from silently eating the hour, and stop the count-chasing that the dos warn against. |
| After missed days, one action spreads overdue reviews over the coming days, at most three a day | Do 4, Do 6 | Same reasoning: a backlog shown honestly, and cleared at a sustainable rate instead of all at once. |
| A weekly budget of 5 one-hour sessions (3 to 7, your choice) instead of fixed weekdays; a lost day just moves the next session along | Do 5 | People preparing while employed describe about an hour on weekdays as the sustainable band, and switching from daily quotas to weekly goals when work is unpredictable ([dev.to](https://dev.to/alex_hunter_44f4c9ed6671e/leetcode-burnout-while-working-full-time-the-sustainable-survival-guide-ch1), [Medium](https://medium.com/@codegrey/the-neetcode-study-schedule-that-works-for-people-with-full-time-jobs-88fd537dd2b7), [Blind](https://www.teamblind.com/post/lc-burnout-ff1vzgic)). An experienced developer's guide stresses consistent hours and separating planning from doing ([r/leetcode](https://www.reddit.com/r/leetcode/comments/1jffkq0/a_detailed_interview_prep_guide_for_experienced/)). |
| A week runs learn, learn, learn, re-solve, mixed: about three new problems a week | Do 3, Do 5 | Three new problems plus their reviews fits an hour a day; a guide for full-time workers puts the floor at 3 to 5 problems a week ([dev.to](https://dev.to/alex_hunter_44f4c9ed6671e/leetcode-burnout-while-working-full-time-the-sustainable-survival-guide-ch1)). |
| A 10-minute short day (one or two recalls) is always on offer and does not use up the week | Do 6 | Habit guidance: restart with the smallest version at the next chance, not next Monday ([habit research summary](https://dev.to/beusebiu/never-miss-twice-what-2066-habits-say-about-the-second-day-bo7)). |
| After two quiet days, one calm line offers that short day; nothing is blocked, nothing is red | Do 6, Don't 6 | "Never miss twice" is a useful heuristic, but one analysis of about 2,066 tracked habits found no cliff at exactly two days, just a steady decline, so the app informs and never punishes ([same source](https://dev.to/beusebiu/never-miss-twice-what-2066-habits-say-about-the-second-day-bo7)). |
| No badges, confetti, XP, or streak alarms | Don't 6 | Gamified progress rewards activity, not skill, which is the count-chasing the dos warn against. |

## What we chose not to build, and why

| Not built | Reason |
|---|---|
| A countdown timer per problem | The timebox matters; a stopwatch adds friction to the one habit that matters most, showing up. The protocol is shown at the moment it is needed instead. |
| Enforcing the struggle (blocking the solution link) | Unenforceable and patronising. Honest self-scoring is the check, and the review schedule catches what did not stick. |
| Mock interviews | Practising out loud under a clock is the most-cited missing skill among people who solved hundreds of problems and still froze ([dev.to](https://dev.to/hamzaibrahim49/solved-300-leetcode-problems-but-still-freeze-in-interviews-its-a-rehearsal-problem-4i8d), [Blind](https://www.teamblind.com/post/best-little-known-advice-for-leetcode-tajqsc7y)). It matters; it is better done with a person or a dedicated tool than in a tracker. |
| A difficulty gate (no mediums until N easies) | The lists already run easy first within each pattern. |
| Leaderboards or social features | Comparing counts is the vanity metric in its purest form. |

If you have evidence that one of these bets is wrong, open an issue with the source.
