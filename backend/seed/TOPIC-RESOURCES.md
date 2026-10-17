# Best free resource per topic

Researched 4 October 2026.

For a C++ learner with near-zero background, one hour a day. Each topic has one primary pick (follow this) and up to two alternates. The machine-readable version is `topic-resources.csv` in this folder.

How links were checked: every YouTube link resolved through YouTube's oEmbed endpoint with the expected channel and title, and playlist video counts were read from the playlist page. Other web links returned HTTP 200. LeetCode Discuss and Reddit block automated HTTP requests, so LeetCode thread links were confirmed through LeetCode's own GraphQL API (the topic id resolves to the stated title) and Reddit threads through the Arctic Shift Reddit archive (post and comments retrieved). Upvote counts quoted below come from those APIs.

## Your beliefs, tested

- **Aditya Verma for DP: half right.** He is the most loved DP intuition builder (124-upvote comment, "pure gold"), but his 50-video playlist has no 1D, grid, LIS or stock (state machine) DP at all. It covers knapsack, unbounded knapsack, LCS, MCM and a little DP on trees. Striver's 57-video series covers every bucket in the plan. Commenters on r/developersIndia say the same thing: watch Aditya for the gist, rely on Striver. So the primary pick for DP is Striver, with Aditya Verma as the first alternate.
- **Striver for Binary Search: holds.** Of the series reviewed, it is the only one that goes deep on binary search on answer. Aditya Verma's binary search playlist has just one such problem.
- **Striver for Linked Lists: nothing contradicts it.** No thread specifically endorses Striver for linked lists, though; the praise is for his channel in general. Add mycodeschool if C++ pointers feel shaky.

## arrays_hashing

- **Primary: Arrays Playlist, Basics to Advanced (Striver, takeUforward).** [Playlist](https://www.youtube.com/playlist?list=PLgUwDviBIf0rENwdL0nEH0uGom9no0nyB), 28 videos, English.
- Alternate: NeetCode 150, Arrays & Hashing section. [neetcode.io/practice](https://neetcode.io/practice)

On r/leetcode the most repeated advice is "Striver if you are learning, NeetCode for revision" (10 and 12 upvotes in two separate threads). Evidence is general rather than topic-specific. Evidence: [Neetcode 250 vs Striver A2Z](https://www.reddit.com/r/leetcode/comments/1lujlhm/), [Neetcode or Striver](https://www.reddit.com/r/leetcode/comments/1lsd3gg/).

## two_pointers_window

- **Primary: Two Pointer and Sliding Window Playlist (Striver).** [Playlist](https://www.youtube.com/playlist?list=PLgUwDviBIf0q7vrFA_HEWcqRqMpCXzYAL), 12 videos, English.
- Alternate: Sliding Window Algorithm (Aditya Verma). [Playlist](https://www.youtube.com/playlist?list=PL_z_8CaSLPWeM8BDJmIYDaoQ5zuwyxnfj), 13 videos, Hinglish.
- Alternate: [Solved all two pointers problems in 100 days](https://leetcode.com/discuss/post/1688903/) (LeetCode Discuss, 2.4k upvotes).

An r/leetcode commenter credits this exact Striver playlist: "he starts out simple and before you know it, you can solve one of his Hard sliding window problems on your own." In an "Aditya Verma or Striver" thread for this topic, the top answer (8 upvotes) says to skip both and solve 10 to 15 tagged problems. Evidence: [Striver vs Neetcode](https://www.reddit.com/r/leetcode/comments/1kd28u9/), [Aditya Verma or Striver](https://www.reddit.com/r/leetcode/comments/1e83fea/).

## stacks

- **Primary: Stack Playlist (Aditya Verma).** [Playlist](https://www.youtube.com/playlist?list=PL_z_8CaSLPWdeOezg68SKkeLN4-T_jNHd), 11 videos, Hinglish.
- Alternate: Stack and Queue Playlist (Striver). [Playlist](https://www.youtube.com/playlist?list=PLgUwDviBIf0pOd5zvVVSzgpo6BaCpHT9c), 19 videos, broader coverage.
- Alternate: [Monotonic stack guide and template](https://leetcode.com/discuss/post/2347639/) (LeetCode Discuss, 1.2k upvotes).

The 208-upvote r/developersIndia post "Aditya verma is a legend" is about this playlist: the OP understood maximum area histogram and max rectangle "in one go." Another commenter says that for stack, heaps and sliding window, Aditya Verma "is pure gold." Evidence: [Aditya verma is a legend](https://www.reddit.com/r/developersIndia/comments/19d1uwu/).

## binary_search

- **Primary: Binary Search Beginner to Advanced (Striver).** [Playlist](https://www.youtube.com/playlist?list=PLgUwDviBIf0pMFMWuuvDNMAkoQFi-h0ZF), 29 videos, English.
- Alternate: Binary Search (Aditya Verma). [Playlist](https://www.youtube.com/playlist?list=PL_z_8CaSLPWeYfhtuKHj-9MpYb6XQJ_f2), 21 videos, Hinglish.
- Alternate: [Powerful Ultimate Binary Search Template](https://leetcode.com/discuss/post/786126/) (LeetCode Discuss, 5.4k upvotes, Python).

Striver's list goes from lower and upper bound through binary search on answer (Koko, bouquets, aggressive cows, book allocation) to median of two sorted arrays. Aditya Verma is good at spotting binary search in disguised problems but covers only one binary-search-on-answer problem. Evidence: [Neetcode 250 vs Striver A2Z](https://www.reddit.com/r/leetcode/comments/1lujlhm/), [Striver sheet and NeetCode for Amazon](https://www.reddit.com/r/leetcode/comments/1m6zqc3/).

## linked_lists

- **Primary: Linked List, Beginner to Advanced (Striver).** [Playlist](https://www.youtube.com/playlist?list=PLgUwDviBIf0rAuz8tVcM0AymmhTRsfaLU), 29 videos, English.
- Alternate: Data structures (mycodeschool). [Playlist](https://www.youtube.com/playlist?list=PL2_aWCzGMAwI3W_JlcBbtYTwiQSsOTa6P), linked-list section first, C/C++.
- Alternate: Linked List (NeetCode). [Playlist](https://www.youtube.com/playlist?list=PLot-Xpze53leU0Ec0VkBhnf4npMRFiNcB), Python.

Striver covers everything up to reverse in k-groups, flattening, merge k lists and clone with random pointer. A 212-upvote LeetCode guide recommends mycodeschool specifically for C++ programmers who want to understand pointers and memory. Evidence: [Beginner's guide on interview preparation](https://leetcode.com/discuss/post/1691931/), [Neetcode or Striver](https://www.reddit.com/r/leetcode/comments/1lsd3gg/).

## recursion

- **Primary: Recursion Playlist (Aditya Verma).** [Playlist](https://www.youtube.com/playlist?list=PL_z_8CaSLPWeT1ffjiImo0sYTcnLzo-wY), 19 videos, Hinglish.
- Alternate: Recursion (Basics to Advanced) and Backtracking Series (Striver). [Playlist](https://www.youtube.com/playlist?list=PLgUwDviBIf0rGlzIn_7rsaR2FQ5e6ZOL9), 22 videos, English.

The 212-upvote LeetCode beginner's guide names Aditya Verma's recursion playlist as "a nice place to start," and a popular LeetCode "Master Recursion" post was written from it. His hypothesis, induction and base-condition method is the part people credit. Striver's subsequence-pattern videos are what his DP series builds on, so watch them before DP. Evidence: [Beginner's guide on interview preparation](https://leetcode.com/discuss/post/1691931/), [Full Interview Preparation Guides + Lists](https://leetcode.com/discuss/post/1854225/).

## backtracking

- **Primary: Striver's Recursion and Backtracking Series, lectures L8 to L19.** [Playlist](https://www.youtube.com/playlist?list=PLgUwDviBIf0rGlzIn_7rsaR2FQ5e6ZOL9).
- Alternate: Backtracking (Aditya Verma). [Playlist](https://www.youtube.com/playlist?list=PL_z_8CaSLPWdbOTog8Jxk9XOjzUs3egMP), 21 videos, Hinglish.
- Alternate: Backtracking (NeetCode). [Playlist](https://www.youtube.com/playlist?list=PLot-Xpze53lf5C3HSjCnyFghlW0G1HHXo), Python.

This pick rests on coverage, not on threads about backtracking. The Striver lectures cover combination sum I and II, subsets I and II, permutations, N-Queens, Sudoku, M-coloring, palindrome partitioning and rat in a maze. Evidence (channel-level only): [Neetcode 250 vs Striver A2Z](https://www.reddit.com/r/leetcode/comments/1lujlhm/), [Neetcode or Striver](https://www.reddit.com/r/leetcode/comments/1lsd3gg/).

## trees

- **Primary: Binary Trees and Binary Search Trees, the official Striver tree series.** [Playlist](https://www.youtube.com/playlist?list=PLgUwDviBIf0q8Hkd7bK2Bpryj2xVJk8Vk), 54 videos, English.
- Alternate: mycodeschool Data structures, tree and BST videos. [Playlist](https://www.youtube.com/playlist?list=PL2_aWCzGMAwI3W_JlcBbtYTwiQSsOTa6P).
- Alternate: Dynamic Programming on Trees (Aditya Verma). [Playlist](https://www.youtube.com/playlist?list=PL_z_8CaSLPWfxJPz2-YKqL9gXWdgrhvdn), 5 videos.

Striver's series covers traversals, views, LCA, construction from traversals, serialize, Morris traversal and the BST set. It is used widely enough that LeetCode users publish handwritten notes built on it. The YouTube search "Striver Tree Series" also returns a third-party re-upload, so use the takeUforward-owned link above. Evidence: [Handwritten Notes on Trees from Striver's SDE Sheet](https://leetcode.com/discuss/post/5913935/), [My 2 month journey learning graphs and trees (Codeforces)](https://codeforces.com/blog/entry/112228).

## heaps

- **Primary: Heap Playlist (Aditya Verma).** [Playlist](https://www.youtube.com/playlist?list=PL_z_8CaSLPWdtY9W22VjnPxG30CXNZpI9), 10 videos, Hinglish.
- Alternate: [Master HEAP: 4 patterns](https://leetcode.com/discuss/post/1127238/) (LeetCode Discuss).

There is no free Striver heap playlist. One r/Btechtards learner used Aditya Verma's for that reason and reports understanding the whole thing. Aditya Verma teaches the top-K and k-closest patterns but not heap internals or the two-heap median. Evidence: [Aditya verma is a legend](https://www.reddit.com/r/developersIndia/comments/19d1uwu/), [Can I watch HEAP by Aditya Verma as a beginner](https://www.reddit.com/r/Btechtards/comments/1ko09fp/).

## greedy_intervals

- **Primary: Greedy Algorithm Playlist (Striver).** [Playlist](https://www.youtube.com/playlist?list=PLgUwDviBIf0rF1w2Koyh78zafB0cz7tea), 13 videos, English.
- Alternate: [Line Sweep Algorithms](https://leetcode.com/discuss/post/2166045/) (LeetCode Discuss, 1.1k upvotes).
- Alternate: Algorithms, greedy method chapter (Abdul Bari). [Playlist](https://www.youtube.com/playlist?list=PLDN4rrl48XKpZkf03iYFl-O29szjTrs_O), theory only.

This pick also rests on coverage: N meetings, non-overlapping intervals, insert interval, minimum platforms, jump game, job sequencing, candy. Merge intervals sits in the A2Z arrays step instead. Evidence (weak): [Neetcode 250 vs Striver A2Z](https://www.reddit.com/r/leetcode/comments/1lujlhm/), [Line Sweep Algorithms](https://leetcode.com/discuss/post/2166045/).

## graphs

- **Primary: Graph Series by Striver.** [Playlist](https://www.youtube.com/playlist?list=PLgUwDviBIf0oE3gA41TKO2H5bHpPd7fzn), 56 videos, English, C++ and Java code.
- Alternate: Graph Theory Playlist (William Fiset). [Playlist](https://www.youtube.com/playlist?list=PLDV1Zeh2NRsDGO4--qE8yH72HFL1Km93P), 43 videos, Java.
- Alternate: Algorithms, graph chapters (Abdul Bari). [Playlist](https://www.youtube.com/playlist?list=PLDN4rrl48XKpZkf03iYFl-O29szjTrs_O), theory only.

A 922-upvote LeetCode graph guide is explicitly built on Striver's series, and one r/leetcode commenter says his "progression through graphs and DP is more thorough." William Fiset is the most-named alternative on LeetCode ("the best source of learning graph algorithms"). For extra practice, r/codeforces suggests the CSES graph problems ([cses.fi/problemset](https://cses.fi/problemset/)). Evidence: [Become Master In Graph](https://leetcode.com/discuss/post/2360573/), [Graph For Beginners](https://leetcode.com/discuss/post/655708/), [Dynamic Programming: Aditya Verma vs Striver](https://www.reddit.com/r/developersIndia/comments/1951epg/), [Neetcode 250 vs Striver A2Z](https://www.reddit.com/r/leetcode/comments/1lujlhm/).

## tries

- **Primary: Trie Series (Striver).** [Playlist](https://www.youtube.com/playlist?list=PLgUwDviBIf0pcIDCZnxhv0LkHf5KzG9zp), 7 videos, English.
- Alternate: [Beginner-friendly guide to Trie](https://leetcode.com/discuss/post/931977/) (LeetCode Discuss).

Weak evidence: no 2023 to 2026 thread argues about trie resources. The pick fits the A2Z order and runs from basic insert and search through the bitwise trie (maximum XOR). Evidence: [Beginner-friendly guide to Trie](https://leetcode.com/discuss/post/931977/).

## dp

- **Primary: Striver's DP Series.** [Playlist](https://www.youtube.com/playlist?list=PLgUwDviBIf0qUlt5H_kiKYaNSqJ81PMMY), 57 videos, English.
- Alternate: Dynamic Programming Playlist (Aditya Verma). [Playlist](https://www.youtube.com/playlist?list=PL_z_8CaSLPWekqhdCPmFohncHwz8TY2Go), 50 videos, Hinglish.
- Alternate: [Dynamic Programming Patterns](https://leetcode.com/discuss/post/458695/) (LeetCode Discuss, 13k upvotes).

The top comment in the r/developersIndia thread (124 upvotes) praises Aditya Verma's DP. Another commenter there writes that his playlist "is wonderful if you want to understand the gist behind dp. But dont rely on it alone... Striver's dp playlist is the BOMB for dp." Replies in an r/developersIndia "best DP playlist" thread are "Striver, no questions asked" and "Striver hands down." Suggested order: Striver DP 1 to 13 (1D and grids), then Aditya Verma's knapsack, LCS and MCM videos for intuition, then Striver's matching lectures and the stock and LIS sections. Evidence: [Aditya verma is a legend](https://www.reddit.com/r/developersIndia/comments/19d1uwu/), [Best Dynamic Programming Playlist](https://www.reddit.com/r/developersIndia/comments/1dy8jdc/), [Aditya DP vs Striver DP](https://www.reddit.com/r/leetcode/comments/1kq9ree/).

## bits

- **Primary: Bit Manipulation Playlist (Striver).** [Playlist](https://www.youtube.com/playlist?list=PLgUwDviBIf0rnqh8QsJaHyIX7KUiaPUv7), 9 videos, English.
- Alternate: [Bitwise Operations tutorial #1](https://www.youtube.com/watch?v=xXKL9YBWgCY) (Errichto), single video.
- Alternate: [Bit manipulation](https://cp-algorithms.com/algebra/bit-manipulation.html) (CP-Algorithms), C++ reference.

Weak evidence: there are no topic-specific threads. The pick is short and covers what interviews ask (tricks, power set by bitmask, single number I to III). A LeetCode Guardian lists Errichto among their sources for less common topics. Evidence: [Resources I followed to become Guardian](https://leetcode.com/discuss/post/5650816/).

## cpp_stl

- **Primary: C++ STL, Competitive Programming (Luv).** [Playlist](https://www.youtube.com/playlist?list=PLauivoElc3gh3RCiQA82MDI-gJfXQQVnn), 19 videos, Hinglish.
- Alternate: [Complete C++ STL in 1 Video](https://www.youtube.com/watch?v=RRVYpIET_RU) (Striver), English.
- Alternate: [C++ STL powerful guide](https://leetcode.com/discuss/post/1154632/) (LeetCode Discuss cheat sheet).

A LeetCode Guardian credits Luv for "custom sorting, upper bound, lower bound," and a Codeforces learner says Luv explains things "in an optimized and easy-to-understand manner." On r/Btechtards, Striver's one-shot is suggested as the English starter. Evidence: [Resources I followed to become Guardian](https://leetcode.com/discuss/post/5650816/), [Codeforces learning journey](https://codeforces.com/blog/entry/112228), [Best resource for C++ STL](https://www.reddit.com/r/Btechtards/comments/1k36lht/).

## problem_solving

- **Primary: NeetCode Roadmap (NeetCode 150/250).** [neetcode.io/roadmap](https://neetcode.io/roadmap), as the revision and pattern-recognition pass.
- Alternate: [How to Practice](https://usaco.guide/general/practicing) (USACO Guide).
- Alternate: [Competitive Programming: How to Learn from Contests](https://www.youtube.com/watch?v=E-aylp6MZnM) (Colin Galen).

The consistent community split is to learn with Striver and revise and drill patterns with NeetCode. The USACO Guide page gives a concrete difficulty rule: a problem is at the right level if you either struggle for a while and solve it, or miss one small piece and need the solution for it. Evidence: [Neetcode 250 vs Striver A2Z](https://www.reddit.com/r/leetcode/comments/1lujlhm/), [Neetcode or Striver](https://www.reddit.com/r/leetcode/comments/1lsd3gg/).

## How people say they study

- **Learn the pattern first, then solve.** The 1.6k-upvote LeetCode post "Doing Leetcode the wrong way" argues for reading and reproducing good solutions to learn patterns, and explaining your solution in your own words (the Feynman method). Its top reply (261 upvotes) agrees. [Source](https://leetcode.com/discuss/post/5031884/)
- **Timebox, then read the solution.** One commenter suggests attempting for 30 to 40 minutes before reading other solutions. The USACO Guide adds that a little time stuck is instructive, but switch to a hint before it turns into frustration. [LeetCode](https://leetcode.com/discuss/post/5031884/), [USACO Guide](https://usaco.guide/general/practicing)
- **Re-solve after a gap.** A Google offer write-up: "For the problems that I couldn't get I went to Neetcode's channel and watched the explanations. I'd sit for a few days and then attempt the problems again." [Source](https://leetcode.com/discuss/post/2435493/)
- **Keep personal lists to revise from.** The "Solved 1000 problems" post keeps topic-wise lists plus "unsolved" and "not solved in contest" lists, and solves the last before the next contest. [Source](https://leetcode.com/discuss/post/4583640/)
- **Mix in contests once topics are covered.** The same post and the "Newbie to Guardian" post both call regular weekly and biweekly contests essential for working under time pressure. [Source](https://leetcode.com/discuss/post/4583640/), [Source](https://leetcode.com/discuss/post/3171049/)
- **Learn from one source, revise from another.** "Striver if you are learning then neetcode for revision" and "If you are in the learning phase, go with striver. If revising, then neetcode 150" both recur on r/leetcode. [Source](https://www.reddit.com/r/leetcode/comments/1lujlhm/), [Source](https://www.reddit.com/r/leetcode/comments/1lsd3gg/)
- **Try before you watch.** "Never spoon-feed your brain before trying a question at least 2-3 times" (31 upvotes). Another reply: "Agar time ho to khudse solve karo, playlist mat follow karo" (if you have time, solve it yourself rather than following a playlist; 35 upvotes). [Source](https://www.reddit.com/r/developersIndia/comments/19d1uwu/)
- **Do not chase streaks.** Skip a daily problem you cannot solve rather than forcing it, and focus on mediums. [Source](https://leetcode.com/discuss/post/4583640/)

## What I could not verify

- **Reddit and LeetCode pages over plain HTTP.** Both block automated clients (HTTP 403), and Reddit's own search needs a login. Reddit threads were found and read through the Arctic Shift archive, and LeetCode threads through LeetCode's GraphQL API. The links are canonical forms of real thread ids. Comment scores are as archived and may differ from live scores. Some later Reddit threads were removed by moderators and are not cited.
- **Coverage of the Reddit search.** The archive search kept timing out (HTTP 422 and 429), so only title searches for creator names and a few "best resource" phrases were completed, and only in r/leetcode, r/developersIndia, r/Btechtards, r/csMajors and r/codeforces. r/cscareerquestions and r/learnprogramming returned few or no matching titles. Treat the consensus as directional.
- **Weak topic-specific evidence** for backtracking, tries, bits, greedy_intervals and arrays_hashing. Those picks rest on coverage and fit with the A2Z order, not on threads about those topics.
- **Kunal Kushwaha, Pepcoding, Love Babbar, Back To Back SWE, Tushar Roy, MIT 6.006, Codeforces EDU and LeetCode Explore cards.** I found no recent thread with substantive comments comparing them for these topics, so none are ranked. Kunal's Recursion + Backtracking playlist exists and resolves (Java, long videos) but is left out for lack of evidence.
- **Third alternates with creator-level evidence only:** Abdul Bari for greedy, CP-Algorithms for bits, Errichto for bits and Colin Galen for contests. The threads cited praise the creator or the method, not that specific video or page.
- **Aditya Verma's newer Graph playlist** (57 videos, 2025) exists on his channel. One r/Btechtards thread suggests it is not taught by him, and there is too little feedback to rank it.
- **takeUforward changes in 2026.** Post titles on r/developersIndia from August and September 2026 say Striver's revamped sheet removed LeetCode links, and a July 2025 comment says site content after binary search is mostly paid (TUF+, about Rs 2,999 a year). The posts themselves were removed, so I could not read the details. The YouTube playlists above are free and resolve today.
- **NeetCode site language support.** NeetCode videos code in Python. I did not confirm whether the site shows C++ solutions for every problem.
