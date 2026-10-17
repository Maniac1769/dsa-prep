# Your DSA preparation system — C++, one hour a day

Prepared 4 October 2026. Start on any day; “week” means a block of seven study sessions.

## The recommendation

Use **one curated curriculum, one revision queue, and one weekly mixed problem**. The curriculum below has **126 LeetCode problems in 42 learning blocks**, followed by four blocks of interview practice. It borrows heavily from NeetCode-style coverage and adds stepping stones for your gaps.

Budget approximately **10–12 months**, with permission to extend difficult blocks. At seven hours per week, 46 weeks provides 322 hours. This is a planning estimate, not a promise of interview readiness. Recursion, graphs, and DP are new to you; learning them and retaining them takes more time than ticking off a sheet.

Your success metric is: **Can I solve an unfamiliar problem, explain why the solution works, write correct C++, and test it within the available time?**

Start with Week 1 below. You do not need to buy anything or choose another sheet.

### Assumptions

- C++ is your preparation language; use the same language throughout.
- You can write basic loops, functions, arrays, and strings.
- You have not specified an interview deadline or seniority. The schedule stays relative, and the company phase must be adapted to the actual role.
- This is a complete DSA practice system. System design, project discussions, language internals, and behavioral preparation need separate planning when you know the role.

## Why this design

| Evidence | What I take from it | How it changes your system |
|---|---|---|
| [NeetCode's preparation guide](https://blog.neetcode.io/p/prepare-coding-interviews) recommends learning patterns in an appropriate order and revisiting problems. | Structured coverage and repeated retrieval are sensible foundations. | Follow one ordered curriculum; use NeetCode explanations when needed. |
| [LeetCode Top Interview 150](https://leetcode.com/studyplan/top-interview-150/) describes itself as a comprehensive list for 3+ months of preparation. | It is a useful catalogue, but its advertised duration does not account for your personal starting point or daily budget. | Use it for later unseen problems; do not complete it alongside another full sheet. |
| [An experienced developer's preparation account](https://www.reddit.com/r/leetcode/comments/1jffkq0/a_detailed_interview_prep_guide_for_experienced/) describes consistent hours, recall cards, and separating planning from execution. | A predictable routine reduces daily decisions. | Preselect work on Sunday; keep brief recall prompts and a fixed daily hour. |
| [A candidate reporting a Google offer](https://www.reddit.com/r/leetcode/comments/1khs9d0/my_lc_prep_google_offer_swe_ii_l3/) used self-ratings, spaced review, and shuffled practice. They already solved many mediums and reported a much larger workload. | Borrow the feedback loop; their volume and timeline do not transfer to a beginner with one hour. | Score every attempt and progressively introduce mixed problems. |
| [A Codeforces practice tutorial and its discussion](https://codeforces.com/blog/entry/66909) discuss matching practice to ability and learning from unsolved contest problems. | Challenging practice and revisiting failures matter. | Use occasional appropriate problems and upsolve failures before taking another contest problem. |
| [Roediger and Karpicke's retrieval study](https://pubmed.ncbi.nlm.nih.gov/16507066/) found delayed retention benefits from testing with prose material. | Active retrieval has experimental support, though this was not a programming study. | Explain or reconstruct before consulting notes. The exact intervals below are practical choices, not a scientifically established DSA formula. |

These sources have different evidential strength. Candidate stories are self-reported, subject to selection bias, and cannot establish which method caused an offer. No credible evidence here establishes one universally “best” sheet or an India-wide list of guaranteed interview questions. The schedule, workload caps, and readiness thresholds below are my synthesis for you.

## Your resource stack

| Purpose | Resource | Rule |
|---|---|---|
| Daily work | The 42-block curriculum below | Work left to right. Carry incomplete work forward. |
| Pattern explanations | [NeetCode roadmap](https://neetcode.io/roadmap) | Try first unless the underlying concept is entirely new. |
| First lessons in unfamiliar topics | [takeUforward learning dashboard / A2Z](https://takeuforward.org/dashboard) | Use the relevant lesson for recursion, trees, graphs, or DP. Cap the lesson segment; spend the rest of the session doing. |
| Additional unseen interview problems | [LeetCode Top Interview 150](https://leetcode.com/studyplan/top-interview-150/) | Use only problems you have not encountered, from topics already studied. |
| Occasional transfer practice | [Codeforces problemset](https://codeforces.com/problemset) | A small supplementary slot after Week 8. |
| Tracking | The accompanying CSV, imported into Sheets/Excel | Record results and due dates manually; it is a tracker, not an automatic scheduler. |

NeetCode 150 is the closest reference roadmap for this plan. **Do not add Blind 75, all of Top Interview 150, and the whole A2Z sheet as additional completion goals.** Their overlap would consume your revision time. A2Z explicitly spans basics through advanced material; it is useful as your lesson library. [Resource description](https://takeuforward.org/dashboard).

## The weekly hour budget

| Day | Exactly 60 minutes | Purpose |
|---|---|---|
| Monday–Thursday | 10 min due recall + 45 min learning/solving + 5 min log | Four work sessions for approximately three new problems, including theory and follow-through |
| Friday | 5 min recall + 50 min full re-solves + 5 min log | One difficult old problem or two shorter ones |
| Saturday | 45 min mixed attempt + 10 min feedback + 5 min log | Practice identifying a method without a topic label |
| Sunday | 20 min recall + 25 min unfinished work + 15 min planning | Clear small gaps and preselect next week's work |

This totals **420 minutes**. Videos, reading editorials, debugging, and planning all count inside the hour.

The learning budget is 180 minutes per week. Three new problems therefore average about an hour each, including learning. Some easy weeks will be faster. A hard graph or DP problem can consume two or three sessions. **Three is a planning target, never a daily or weekly pass condition.**

For Weeks 1–2, use Saturday to re-solve the week's work because your learned-topic pool is small. From Week 3, choose an unseen problem from an already studied topic. Hide the topic label until you have attempted it. Ask a friend to pick when possible; otherwise choose from a mixed list while avoiding tags.

### Inside a 45-minute work session

For a topic you already know:

1. **0–5:** Restate the problem, examine constraints, make examples, and describe brute force.
2. **5–20:** Explore improvements. Write the invariant, recurrence, or reason a data structure helps.
3. **20–35:** Code and test if you have an approach. If you have made no meaningful progress for about 10 minutes, take one small hint.
4. **35–45:** Debug, explain correctness and complexity, or study the missing idea.

If still stuck, read the relevant explanation, close it, and reconstruct the reasoning. Implement from a blank editor in the next work session. Mark this attempt assisted. Finishing after an explanation is useful learning, but does not establish independent mastery.

For a completely new topic, spend up to 20 minutes learning and tracing a tiny example, then at least 25 minutes implementing or solving. Longer lessons span multiple sessions. You do not have to discover recursion or Dijkstra unaided.

If you are actively making progress, the hint timer is not a command to abandon your thinking. Stop at the end of the hour, write the next step, and resume tomorrow.

## Revision that fits the hour

### Record two things separately

**Attempt score**

| Score | Meaning |
|---|---|
| 0 | Could not produce a valid approach, even after the attempt |
| 1 | Needed a substantive hint, explanation, or solution |
| 2 | Solved independently, but slowly, with significant debugging, or with weak explanation |
| 3 | Solved independently and can justify correctness, complexity, and tests |

**Review mode**

- **Recall:** Close everything. In 3–5 minutes, explain the approach, why it works, complexity, and one edge case. This is not a full coding attempt.
- **Full solve:** Start from the statement and an empty editor. Write and test the complete solution. Only this can establish coding mastery.
- **Transfer:** Solve a new variant, or reason about a changed constraint. Familiarity with an old statement does not establish transfer.

### The default schedule

After first studying a problem, schedule short recall around **day +1, +7, +21, and +60**. These are target dates; fit them into the allocated recall slots.

Choose **one anchor problem per learning week**: the problem that best represents a reusable idea or exposed your biggest gap. For the anchor:

- Around day +7, replace that recall with a full solve.
- Around day +30, do a second full solve.
- Use day +60 for a short recall or a related unseen problem.

Thus, you fully re-code selected representatives rather than every problem at every interval. A 126-problem curriculum with four five-minute recalls would cost about 42 hours across the programme; the regular recall budget can accommodate that if you retire confident repetitions. Anchor re-solves require additional time, supplied mainly by Fridays.

**A failed recall or solve takes priority over its future schedule:** study the gap, recall it the next day, and queue a full solve within the next three study sessions. Replace a new-problem session if needed.

### Prevent the revision queue from taking over

- Recall remains within the day's allocated minutes. Review weakest/overdue items first.
- Queue no more than **six full re-solves** at once. If you exceed six, or a failed problem waits more than seven days, replace the next new-work session with review.
- If more than **12 recall items** are overdue, use Sunday's catch-up slot and reduce next week's new target to two.
- An anchor can leave frequent review after two independent full solves separated by at least two weeks. Keep its pattern eligible for mixed practice.
- When two problems test essentially the same idea and both are comfortable, retain the more useful representative.
- After a week away, spend the first two sessions on recent failures and anchors. Resume at your current block; do not restart the whole curriculum.
- Never double tomorrow's workload to compensate for a missed day.

### Example: Two Sum

First attempt: you needed a hint, so score 1. Next day, explain what the map contains before processing the current element and why that prevents reusing an element. Within three study sessions, code it unaided.

A week later, explain how returning every valid pair would change duplicates and output size. A correct explanation helps test understanding; it does not replace a full solve if coding was the weakness.

## The curriculum: 42 learning blocks

Each row contains three ordered problems. The titles link directly to LeetCode. These are **representative preparation problems**, not a claim that each was asked at any particular company.

Spend four new-work sessions on each row. Thursday is often for finishing, debugging, and reconstructing an assisted solution. If the row is unfinished or its prerequisite is still weak, repeat the block with fewer new problems. Advanced rows can require two weeks.

| Week | Learn first | Ordered problems |
|---|---|---|
| 1 | Big O; vector/string operations; hash sets and maps | [217 Contains Duplicate](https://leetcode.com/problems/contains-duplicate/); [242 Valid Anagram](https://leetcode.com/problems/valid-anagram/); [1 Two Sum](https://leetcode.com/problems/two-sum/) |
| 2 | Frequency maps; grouping; set membership; bucket counting | [49 Group Anagrams](https://leetcode.com/problems/group-anagrams/); [347 Top K Frequent Elements](https://leetcode.com/problems/top-k-frequent-elements/); [128 Longest Consecutive Sequence](https://leetcode.com/problems/longest-consecutive-sequence/) |
| 3 | Prefix sums; prefix/suffix products; counting prefix states | [303 Range Sum Query - Immutable](https://leetcode.com/problems/range-sum-query-immutable/); [238 Product of Array Except Self](https://leetcode.com/problems/product-of-array-except-self/); [560 Subarray Sum Equals K](https://leetcode.com/problems/subarray-sum-equals-k/) |
| 4 | Two pointers; sorted search space; duplicate handling | [125 Valid Palindrome](https://leetcode.com/problems/valid-palindrome/); [167 Two Sum II - Input Array Is Sorted](https://leetcode.com/problems/two-sum-ii-input-array-is-sorted/); [15 3Sum](https://leetcode.com/problems/3sum/) |
| 5 | Fixed and variable sliding windows; maintaining validity | [643 Maximum Average Subarray I](https://leetcode.com/problems/maximum-average-subarray-i/); [3 Longest Substring Without Repeating Characters](https://leetcode.com/problems/longest-substring-without-repeating-characters/); [424 Longest Repeating Character Replacement](https://leetcode.com/problems/longest-repeating-character-replacement/) |
| 6 | Window expansion/contraction; frequency equality; positive-number assumptions | [209 Minimum Size Subarray Sum](https://leetcode.com/problems/minimum-size-subarray-sum/); [567 Permutation in String](https://leetcode.com/problems/permutation-in-string/); [438 Find All Anagrams in a String](https://leetcode.com/problems/find-all-anagrams-in-a-string/) |
| 7 | Stack invariants; auxiliary state; expression evaluation | [20 Valid Parentheses](https://leetcode.com/problems/valid-parentheses/); [155 Min Stack](https://leetcode.com/problems/min-stack/); [150 Evaluate Reverse Polish Notation](https://leetcode.com/problems/evaluate-reverse-polish-notation/) |
| 8 | Monotonic stacks; amortized reasoning; sorting before a scan | [496 Next Greater Element I](https://leetcode.com/problems/next-greater-element-i/); [739 Daily Temperatures](https://leetcode.com/problems/daily-temperatures/); [853 Car Fleet](https://leetcode.com/problems/car-fleet/) |
| 9 | Binary-search interval conventions; lower/upper bounds | [704 Binary Search](https://leetcode.com/problems/binary-search/); [35 Search Insert Position](https://leetcode.com/problems/search-insert-position/); [34 Find First and Last Position of Element in Sorted Array](https://leetcode.com/problems/find-first-and-last-position-of-element-in-sorted-array/) |
| 10 | Rotated arrays; binary search on an answer; monotone feasibility | [153 Find Minimum in Rotated Sorted Array](https://leetcode.com/problems/find-minimum-in-rotated-sorted-array/); [33 Search in Rotated Sorted Array](https://leetcode.com/problems/search-in-rotated-sorted-array/); [875 Koko Eating Bananas](https://leetcode.com/problems/koko-eating-bananas/) |
| 11 | Node pointers; dummy heads; pointer rewiring; slow/fast pointers | [206 Reverse Linked List](https://leetcode.com/problems/reverse-linked-list/); [21 Merge Two Sorted Lists](https://leetcode.com/problems/merge-two-sorted-lists/); [876 Middle of the Linked List](https://leetcode.com/problems/middle-of-the-linked-list/) |
| 12 | Cycle detection; pointer gaps; doubly linked list plus hash map | [141 Linked List Cycle](https://leetcode.com/problems/linked-list-cycle/); [19 Remove Nth Node From End of List](https://leetcode.com/problems/remove-nth-node-from-end-of-list/); [146 LRU Cache](https://leetcode.com/problems/lru-cache/) |
| 13 | Recursion: base case, shrinking input, call stack; merge sort | [509 Fibonacci Number](https://leetcode.com/problems/fibonacci-number/); [50 Pow(x, n)](https://leetcode.com/problems/powx-n/); [912 Sort an Array](https://leetcode.com/problems/sort-an-array/) |
| 14 | Backtracking: choices, partial state, undo, copying results | [78 Subsets](https://leetcode.com/problems/subsets/); [46 Permutations](https://leetcode.com/problems/permutations/); [77 Combinations](https://leetcode.com/problems/combinations/) |
| 15 | Reuse vs single use; pruning; constrained generation | [39 Combination Sum](https://leetcode.com/problems/combination-sum/); [40 Combination Sum II](https://leetcode.com/problems/combination-sum-ii/); [22 Generate Parentheses](https://leetcode.com/problems/generate-parentheses/) |
| 16 | Duplicate branches; partitioning; grid backtracking | [90 Subsets II](https://leetcode.com/problems/subsets-ii/); [131 Palindrome Partitioning](https://leetcode.com/problems/palindrome-partitioning/); [79 Word Search](https://leetcode.com/problems/word-search/) |
| 17 | Tree nodes; recursive DFS; meaning of a function's return value | [104 Maximum Depth of Binary Tree](https://leetcode.com/problems/maximum-depth-of-binary-tree/); [100 Same Tree](https://leetcode.com/problems/same-tree/); [226 Invert Binary Tree](https://leetcode.com/problems/invert-binary-tree/) |
| 18 | Postorder information; returned result vs global result; root-to-leaf state | [543 Diameter of Binary Tree](https://leetcode.com/problems/diameter-of-binary-tree/); [110 Balanced Binary Tree](https://leetcode.com/problems/balanced-binary-tree/); [112 Path Sum](https://leetcode.com/problems/path-sum/) |
| 19 | Queue-based BFS; level boundaries; iterative DFS | [102 Binary Tree Level Order Traversal](https://leetcode.com/problems/binary-tree-level-order-traversal/); [199 Binary Tree Right Side View](https://leetcode.com/problems/binary-tree-right-side-view/); [144 Binary Tree Preorder Traversal](https://leetcode.com/problems/binary-tree-preorder-traversal/) |
| 20 | BST global ordering; inorder traversal; search paths | [98 Validate Binary Search Tree](https://leetcode.com/problems/validate-binary-search-tree/); [230 Kth Smallest Element in a BST](https://leetcode.com/problems/kth-smallest-element-in-a-bst/); [235 Lowest Common Ancestor of a Binary Search Tree](https://leetcode.com/problems/lowest-common-ancestor-of-a-binary-search-tree/) |
| 21 | General-tree LCA; reconstructing trees; preserving pointers | [236 Lowest Common Ancestor of a Binary Tree](https://leetcode.com/problems/lowest-common-ancestor-of-a-binary-tree/); [105 Construct Binary Tree from Preorder and Inorder Traversal](https://leetcode.com/problems/construct-binary-tree-from-preorder-and-inorder-traversal/); [114 Flatten Binary Tree to Linked List](https://leetcode.com/problems/flatten-binary-tree-to-linked-list/) |
| 22 | Min/max heaps; priority_queue; keeping k candidates | [703 Kth Largest Element in a Stream](https://leetcode.com/problems/kth-largest-element-in-a-stream/); [215 Kth Largest Element in an Array](https://leetcode.com/problems/kth-largest-element-in-an-array/); [973 K Closest Points to Origin](https://leetcode.com/problems/k-closest-points-to-origin/) |
| 23 | Greedy choices; exchange arguments; reachability; counterexamples | [455 Assign Cookies](https://leetcode.com/problems/assign-cookies/); [55 Jump Game](https://leetcode.com/problems/jump-game/); [134 Gas Station](https://leetcode.com/problems/gas-station/) |
| 24 | Interval sorting; overlap; choosing an endpoint | [56 Merge Intervals](https://leetcode.com/problems/merge-intervals/); [57 Insert Interval](https://leetcode.com/problems/insert-interval/); [435 Non-overlapping Intervals](https://leetcode.com/problems/non-overlapping-intervals/) |
| 25 | Graph representations; grid neighbors; DFS and visited state | [733 Flood Fill](https://leetcode.com/problems/flood-fill/); [200 Number of Islands](https://leetcode.com/problems/number-of-islands/); [695 Max Area of Island](https://leetcode.com/problems/max-area-of-island/) |
| 26 | BFS shortest paths in unweighted graphs; multiple sources | [994 Rotting Oranges](https://leetcode.com/problems/rotting-oranges/); [542 01 Matrix](https://leetcode.com/problems/01-matrix/); [1091 Shortest Path in Binary Matrix](https://leetcode.com/problems/shortest-path-in-binary-matrix/) |
| 27 | Graph cloning; reversed reachability; boundary-connected regions | [133 Clone Graph](https://leetcode.com/problems/clone-graph/); [417 Pacific Atlantic Water Flow](https://leetcode.com/problems/pacific-atlantic-water-flow/); [130 Surrounded Regions](https://leetcode.com/problems/surrounded-regions/) |
| 28 | Directed cycles; topological sorting; indegrees | [207 Course Schedule](https://leetcode.com/problems/course-schedule/); [210 Course Schedule II](https://leetcode.com/problems/course-schedule-ii/); [802 Find Eventual Safe States](https://leetcode.com/problems/find-eventual-safe-states/) |
| 29 | Disjoint-set union: find, union, path compression, size | [684 Redundant Connection](https://leetcode.com/problems/redundant-connection/); [721 Accounts Merge](https://leetcode.com/problems/accounts-merge/); [1319 Number of Operations to Make Network Connected](https://leetcode.com/problems/number-of-operations-to-make-network-connected/) |
| 30 | Weighted paths; Dijkstra; expanded state; bounded-edge relaxation | [743 Network Delay Time](https://leetcode.com/problems/network-delay-time/); [1631 Path With Minimum Effort](https://leetcode.com/problems/path-with-minimum-effort/); [787 Cheapest Flights Within K Stops](https://leetcode.com/problems/cheapest-flights-within-k-stops/) |
| 31 | Trie nodes; prefixes; wildcard branching | [208 Implement Trie (Prefix Tree)](https://leetcode.com/problems/implement-trie-prefix-tree/); [211 Design Add and Search Words Data Structure](https://leetcode.com/problems/design-add-and-search-words-data-structure/); [648 Replace Words](https://leetcode.com/problems/replace-words/) |
| 32 | DP: recursive state, repeated subproblems, memoization, tabulation | [70 Climbing Stairs](https://leetcode.com/problems/climbing-stairs/); [746 Min Cost Climbing Stairs](https://leetcode.com/problems/min-cost-climbing-stairs/); [198 House Robber](https://leetcode.com/problems/house-robber/) |
| 33 | DP boundary cases; circular constraints; prefix decisions | [213 House Robber II](https://leetcode.com/problems/house-robber-ii/); [91 Decode Ways](https://leetcode.com/problems/decode-ways/); [139 Word Break](https://leetcode.com/problems/word-break/) |
| 34 | Unbounded vs 0/1 choices; sum states; counting vs feasibility | [322 Coin Change](https://leetcode.com/problems/coin-change/); [416 Partition Equal Subset Sum](https://leetcode.com/problems/partition-equal-subset-sum/); [494 Target Sum](https://leetcode.com/problems/target-sum/) |
| 35 | Grid DP; transitions; initialization; blocked cells | [62 Unique Paths](https://leetcode.com/problems/unique-paths/); [64 Minimum Path Sum](https://leetcode.com/problems/minimum-path-sum/); [63 Unique Paths II](https://leetcode.com/problems/unique-paths-ii/) |
| 36 | Subsequences; two-string states; counting combinations | [1143 Longest Common Subsequence](https://leetcode.com/problems/longest-common-subsequence/); [300 Longest Increasing Subsequence](https://leetcode.com/problems/longest-increasing-subsequence/); [518 Coin Change II](https://leetcode.com/problems/coin-change-ii/) |
| 37 | State machines; counting subsequences; edit transitions | [309 Best Time to Buy and Sell Stock with Cooldown](https://leetcode.com/problems/best-time-to-buy-and-sell-stock-with-cooldown/); [115 Distinct Subsequences](https://leetcode.com/problems/distinct-subsequences/); [72 Edit Distance](https://leetcode.com/problems/edit-distance/) |
| 38 | Binary representation; XOR; masks; bit-count recurrences | [136 Single Number](https://leetcode.com/problems/single-number/); [191 Number of 1 Bits](https://leetcode.com/problems/number-of-1-bits/); [338 Counting Bits](https://leetcode.com/problems/counting-bits/) |
| 39 | Advanced trees: path choices, serialization, tree DP | [124 Binary Tree Maximum Path Sum](https://leetcode.com/problems/binary-tree-maximum-path-sum/); [297 Serialize and Deserialize Binary Tree](https://leetcode.com/problems/serialize-and-deserialize-binary-tree/); [337 House Robber III](https://leetcode.com/problems/house-robber-iii/) |
| 40 | Advanced graphs: implicit BFS, Eulerian traversal, bottleneck paths | [127 Word Ladder](https://leetcode.com/problems/word-ladder/); [332 Reconstruct Itinerary](https://leetcode.com/problems/reconstruct-itinerary/); [778 Swim in Rising Water](https://leetcode.com/problems/swim-in-rising-water/) |
| 41 | Partition DP; interval DP; synchronized-path state | [1043 Partition Array for Maximum Sum](https://leetcode.com/problems/partition-array-for-maximum-sum/); [312 Burst Balloons](https://leetcode.com/problems/burst-balloons/); [741 Cherry Pickup](https://leetcode.com/problems/cherry-pickup/) |
| 42 | Combining foundations: covering windows, monotonic deque, trie plus backtracking | [76 Minimum Window Substring](https://leetcode.com/problems/minimum-window-substring/); [239 Sliding Window Maximum](https://leetcode.com/problems/sliding-window-maximum/); [212 Word Search II](https://leetcode.com/problems/word-search-ii/) |

**Difficulty handling:** Weeks 39–42 are stretch blocks. Expect to split them when needed. In Week 41, complete 1043 and understand 312 before attempting 741. Cherry Pickup is optional if prerequisite DP or mixed medium performance remains weak; replace it with a relevant medium or a failed anchor. Advanced breadth is useful, but difficulty labels are not progress metrics.

### Notes that make this order work

- Week 2: use the bucket-counting route for Top K Frequent Elements; revisit a heap solution in Week 22.
- Week 12: LRU Cache is a two-session exercise. First build and test a tiny doubly linked list, then add the map. Using std::list is also a useful second implementation.
- Week 13: trace small Fibonacci calls to understand the stack; use an efficient implementation for submission. Implement merge sort for Sort an Array. Calling std::sort would miss this lesson.
- Week 19: implement at least one traversal both iteratively and recursively.
- Week 23: write why the greedy choice is safe. Trying a few examples is not a proof.
- Week 30: plain BFS does not solve arbitrary weighted shortest paths. Stops in 787 are part of the state/constraint.
- Weeks 32–37: first define the state in a sentence. Start with recursion plus memoization, then tabulate a representative example. Derive transition order before trying space optimization.
- Week 36: first learn the O(n²) LIS DP; binary-search optimization can be a second pass.
- Week 40: Eulerian traversal is a new prerequisite for Reconstruct Itinerary; learn it before treating the problem as an independent test.
- Hard problems may require a worked example first. Your later cold re-solve is the test of learning.

## C++ skills to learn just in time

| Before | Be comfortable with |
|---|---|
| Week 1 | vector, string, references, const references, unordered_map, unordered_set, sort, pair, range loops, long long |
| Week 7 | stack and vector as stack; integer division; safe access to top/back |
| Week 9 | lower_bound, upper_bound, iterator differences; overflow-safe midpoint and arithmetic |
| Week 11 | Pointer vs pointee; nullptr; node ownership; dummy nodes; preserving next before rewiring |
| Week 13 | Function calls and stack frames; passing state by reference; copying only when needed; recursion depth |
| Week 19 | queue; iterative DFS with stack |
| Week 22 | priority_queue defaults to max-heap; min-heap with greater; comparator consistency |
| Week 25 | vector<vector<int>> adjacency lists; visited arrays; queueing a node only once when appropriate |
| Week 32 | DP array dimensions, sentinels, overflow, memo state completeness |
| Week 38 | Bitwise operators; shift widths; signed vs unsigned behavior |

Use your existing editor/compiler. For local checks, compile with warnings such as -std=c++17 -Wall -Wextra -Wshadow. When supported, AddressSanitizer and UndefinedBehaviorSanitizer are useful for local pointer/index debugging. Do not spend the first week building an elaborate template library.

For each data structure, learn operation costs. Include copying, recursion stack, output size, and sort cost in analysis. Know that hash-table complexity is typically stated as average-case.

## Recursion → trees → graphs → DP: the conceptual bridge

**Recursion:** What does this call promise to return? What is the base case? How does every recursive call move toward it? Draw the stack for three small inputs.

**Backtracking:** Which choices remain? What state changes? What must be undone before trying the next branch? When is an answer complete?

**Trees:** What information must children return? What can the current node compute? Distinguish the value returned to the parent from the best answer seen anywhere.

**Graphs:** What defines a vertex and an edge? Can states repeat? What does visited mean? Is the graph directed? Are edges weighted? Why is DFS, BFS, or a shortest-path algorithm appropriate?

**DP:** What is the smallest state that fully determines the remaining problem? What choices change that state? Which states repeat? What are the base cases? In what order are dependencies available?

For each DP problem, write:

1. State meaning.
2. Transition and justification.
3. Base cases.
4. Evaluation order.
5. Number of states × work per state.
6. Space use, including recursion where relevant.

Do not start by memorizing a table-filling loop.

## Codeforces: a controlled supplementary track

Start after Week 8. **Every second Saturday**, you may replace the mixed LeetCode slot with one Codeforces problem from an already learned topic. Keep the entire session to 60 minutes. If revision is overdue, or the previous Codeforces problem is unfinished, use the slot to resolve that first.

Start around 800–1000 rated problems and move toward 1100–1200 when several recent problems are independently manageable within 30–40 minutes. Ratings are only rough guides and are not comparable to LeetCode labels. Try 1300–1400 selectively after consistent success; no target Codeforces rating is required for this plan.

These are practice candidates, **not claimed company interview questions**:

| When ready | Problem | Skill |
|---|---|---|
| After Week 8 | [339A Helpful Maths](https://codeforces.com/problemset/problem/339/A) | Parsing and sorting |
| After Week 8 | [160A Twins](https://codeforces.com/problemset/problem/160/A) | Simple sorted choice; justify it |
| After Week 8 | [363B Fence](https://codeforces.com/problemset/problem/363/B) | Fixed window |
| After Week 10 | [706B Interesting drink](https://codeforces.com/problemset/problem/706/B) | Sorting and bounds |
| After Week 10, optional stretch | [279B Books](https://codeforces.com/problemset/problem/279/B) | Variable window; positive inputs |
| After Week 24 | [158B Taxi](https://codeforces.com/problemset/problem/158/B) | Greedy case analysis |
| After Week 27 | [580C Kefa and Park](https://codeforces.com/problemset/problem/580/C) | DFS carrying path state |
| After Week 30 | [20C Dijkstra?](https://codeforces.com/problemset/problem/20/C) | Weighted paths and reconstruction; optional stretch |
| After Week 34 | [455A Boredom](https://codeforces.com/problemset/problem/455/A) | Frequency aggregation plus DP |

Use the remaining optional Saturdays for similarly appropriate problems or upsolving. Approximately 10–16 Codeforces problems across the programme is enough supplementary work to start with.

“Upsolve” means finish an unsolved attempt, learn the missing idea if necessary, and later reconstruct it without the editorial. Codeforces exposes full input/output handling and unfamiliar presentations; LeetCode remains the majority of your interview practice.

Full contests often exceed your daily time budget. A 45-minute selection from a past contest is practice, not a claim of completing a full contest. If you eventually choose a full contest, budget it explicitly by replacing other sessions.

## Progress gates

Check these in existing Saturday/Friday slots. Do not add hours. These thresholds are planning heuristics, not company hiring cutoffs.

| Gate | Evidence to look for |
|---|---|
| After Week 6 | Solve an unfamiliar easy array/string problem in about 20 minutes; derive a basic window or prefix-sum solution and explain its assumptions |
| After Week 12 | Implement binary search and list reversal unaided; explain loop/pointer invariants; show independent progress on at least two of your last three appropriate mixed problems |
| After Week 16 | Generate subsets from scratch, trace the recursion, and justify undo operations without copying a template |
| After Week 24 | Implement tree DFS/BFS, use a heap correctly, and explain why a proposed greedy strategy works or fails |
| After Week 31 | Select BFS vs DFS vs Dijkstra correctly; handle cycles; explain topological order and DSU use cases |
| After Week 37 | Derive states and recurrences for fresh basic/medium DP; distinguish choices, counts, and optimization |
| Before active interviewing | Across the last ten unseen medium attempts spanning several topics, solve roughly seven independently within 35–45 minutes with explanation and tests; complete at least four timed mock sessions |

If a gate fails, spend the next block on the weakest prerequisite: one short lesson, two full re-solves, and one unseen transfer attempt. Resume when the evidence improves. Continue comfortable-topic mixed practice during repairs.

If multiple weeks feel trivial, combine two blocks while preserving Friday review and Saturday mixed practice. If almost every problem needs an explanation, reduce difficulty or add a prerequisite lesson. Increasing volume will not fix a missing concept.

## Final four blocks: prepare for the actual interviews

Use these after the core gates are broadly met. You can start this phase earlier if interviews are scheduled; pause optional hard blocks first.

| Block | Work inside the same seven hours |
|---|---|
| 43 | Select target role/company; use one Sunday planning slot to inspect recent relevant interview accounts; do two unseen mediums, one weak-pattern repair, one timed mock, and scheduled reviews |
| 44 | Do two or three role-relevant problems/variants; one timed mock; repair its biggest failure; continue reviews |
| 45 | Two 45-minute mocks on different days; use other work sessions for feedback repairs and one or two unseen problems |
| 46 | Two mocks; revisit high-value failures; rehearse explaining complexity and edge cases; avoid a rush to add advanced topics |

Each mock fits one hour: approximately 5 minutes clarification, 10 reasoning, 25 coding, 5 testing, 15 feedback. A peer mock is useful; a recorded spoken self-mock also works. Give the selector your studied-topic range and ask them not to reveal the pattern.

### How a target company changes the last phase (examples)

The rows below are examples. Replace them with the companies you are interviewing for, using the method under the table.

| Target | Evidence and practical adaptation |
|---|---|
| Amazon | Its [official preparation page](https://amazon.jobs/content/en/how-we-hire/interview-prep/software-development-topics) emphasizes applying fundamentals, coding, and broader technical topics, and advises asking the recruiter what to expect. Practise clear reasoning, working code, tests, and follow-ups. Ask about the actual assessment format; reserve separate preparation for Leadership Principles and role-dependent design. |
| Google | A [self-reported India L4 account](https://www.reddit.com/r/leetcode/comments/1jv6stf/my_interview_experience_for_google_india_l4/) includes a DFS/trie-style challenge. This supports retaining advanced combinations in your coverage; it does not establish their frequency. Emphasize unfamiliar variants, precise state definitions, and explaining tradeoffs. |
| LinkedIn | A [June 2025 India Staff account](https://leetcode.com/discuss/post/6858262/linkedin-staff-software-engineer-intervi-mg5c/) reports Max Stack in screening and discussion of implementation alternatives. It is a senior-role anecdote, not a universal bar. Retain data-structure composition exercises such as LRU Cache; adapt design depth to your seniority. |
| Broadcom / VMware | A [VMware MTS2 Pune C++/Windows-oriented account](https://leetcode.com/discuss/post/5216967/VMware-or-MTS-2-or-Pune-or-offer/) describes C++, memory-management, DSA, and reasoning emphasis. A [separate Broadcom account](https://leetcode.com/discuss/post/6888084/) describes substantial Java internals. Preparation should follow the actual job description and team stack; a generic DSA list cannot cover that variation. |

For company targeting, collect **5–10 dated accounts** matching role, level, location, and preferably the past 6–12 months. Record date, level, round, reported topic, and source. Reports are incomplete and unverifiable; tags are discovery aids. Choose the patterns that recur, then practise a reported problem plus an unseen variant.

Do not spend early months chasing volatile company-frequency lists. Recruiter instructions for your particular loop take priority over aggregate anecdotes.

## Your first 14 sessions

All entries include the standard review/log time. Stop at 60 minutes.

| Session | Main work |
|---|---|
| 1 | Set up tracker; review vector/map/set costs; attempt Contains Duplicate; explain time and space |
| 2 | Recall yesterday's idea; attempt Valid Anagram; test unequal lengths and repeated letters |
| 3 | Recall one earlier approach; attempt Two Sum; compare brute force and map approach |
| 4 | Finish/reconstruct the weakest assisted attempt; practise basic unordered_map operations |
| 5 | Full cold re-solve of Two Sum, or your weakest problem; explain the invariant |
| 6 | Re-solve another Week 1 problem without looking; reason about a changed constraint |
| 7 | Due recalls; clear unfinished work; choose next week's anchor and preselect problems |
| 8 | Learn canonical grouping keys; attempt Group Anagrams |
| 9 | Learn frequency buckets; attempt Top K Frequent Elements |
| 10 | Finish Top K Frequent Elements from a blank editor if yesterday was assisted |
| 11 | Attempt Longest Consecutive Sequence; if needed, use the next catch-up slot |
| 12 | Full re-solve of a due Week 1 anchor; do not read its solution first |
| 13 | Cold Week 2 re-solve; verify why the method avoids unnecessary repeated work |
| 14 | Review; clear the largest gap; plan Week 3; extend Week 2 if needed |

The first two weeks are calibration. If all six problems are independently easy and explainable, move faster. If medium problems take two sessions, the plan is working as intended.

## Using the tracker

Import **problem-tracker.csv** into your spreadsheet. It has one row for every curriculum problem and one row for each Codeforces starter.

Update only these after an attempt:

- First studied / last attempt dates.
- Attempt score 0–3; independent yes/no; minutes.
- One-sentence failure or lesson.
- Anchor yes/no.
- Next recall date and next full-solve date, when applicable.

The initial dates are blank because no start date was supplied. The sheet does not claim automated reminders or formulas. Filter next-due dates on or before today; use the queue rules above to select work. Dates should use YYYY-MM-DD.

A five-minute Sunday dashboard is enough:

| Measure | Desired direction |
|---|---|
| Sessions completed | Aim for 6–7; sustain the habit |
| Unseen independent solve rate | Improve over rolling sets of ten attempts |
| Full-review backlog | Six or fewer; no failed item ignored for weeks |
| Recurring failure | Identify one to repair next week |
| Explanation quality | Correct invariant/state, complexity, and tests |
| New problems | Usually 2–3 per learning block; fewer during repairs |

Copy this tiny note when needed:

> Trigger / useful clue:  
> Key invariant or DP state:  
> Why it is correct:  
> Time and auxiliary space:  
> My mistake:  
> A changed constraint to test next time:

Keep notes under five minutes. Do not transcribe editorials.

## If motivation or time drops

On an unusually busy day, do a 15-minute fallback: five minutes recall, eight minutes coding a small piece of a familiar solution, two minutes recording the next step. This preserves continuity but is fewer study hours; let the end date move accordingly.

After two weeks of poor consistency, reduce the new-problem target to two and keep review. After repeated frustration in one topic, move back one prerequisite, solve a smaller example, and then return.

If an interview arrives in six weeks, switch to mixed practice, recurring weak patterns, and role-specific preparation. At your starting level, compressing the full curriculum into six weeks would sacrifice understanding; treat that as a focused attempt with limited coverage.

**Tomorrow's decision is already made: start Contains Duplicate, write your own reasoning, and record when to revisit it.**
