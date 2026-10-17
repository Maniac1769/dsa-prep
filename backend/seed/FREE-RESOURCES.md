# Free system design resources

Verified 4 October 2026. Treat every "free" claim as of that date.

Audience: working engineers preparing for product-company interviews; most interview reports cited are from India-based loops. Language: C++ (most LLD resources are Java or Python; C++ coverage is noted per resource).

## How I checked

I ran HTTP status checks and the GitHub API for last-push dates, and used WebFetch on the Hello Interview and ByteByteGo pages. I did not read most of the content in depth. "Free" means the core content was reachable without a login prompt, except where noted. Paid products (Grokking, DesignGurus, Alex Xu's books, Exponent) are excluded.

## HLD resources (ranked)

| # | Name and URL | Format | Best for | Limitation |
|---|---|---|---|---|
| 1 | [Hello Interview, System Design in a Hurry](https://www.hellointerview.com/learn/system-design/in-a-hurry/introduction) | Written course | A structured delivery framework, core concepts (caching, CAP, API design) and tech primers (Redis, Kafka, Cassandra, DynamoDB). Free: Bitly, Dropbox, Uber, YouTube, WhatsApp and Rate Limiter breakdowns. | Premium locks Yelp, Instagram, Notification System, Payment System, Job Scheduler, Flash Sale and others. It also locks "Numbers to Know", Database Indexing, and patterns such as Dealing with Contention and Scaling Reads/Writes. Those patterns are the most interview-relevant part. |
| 2 | [donnemartin/system-design-primer](https://github.com/donnemartin/system-design-primer) | Repo | A broad free reference for fundamentals. 373k stars; last pushed 2026-09-15. | Python-flavoured and long. It is a reference rather than a method for running an interview, and its worked solutions are dated. |
| 3 | [ByteByteGo](https://blog.bytebytego.com) (blog, newsletter, [YouTube](https://bytebytego.com)) | Blog, newsletter, video | Short visual explainers of how real systems work. | The full "System Design Interview" course chapters are probably a paid product. The chapter page loaded with full text for me, but the page gave no free-or-paid signal, so I could not confirm free access. Treat only the blog, newsletter and YouTube as free. |
| 4 | [karanpratapsingh/system-design](https://github.com/karanpratapsingh/system-design) | Repo and book | A free end-to-end walk through concepts, with case studies such as URL shortener, WhatsApp and Uber. 46k stars; last pushed 2026-07-08. | Case studies are shallow compared with Hello Interview. It has no company-specific depth. |
| 5 | [ashishps1/awesome-system-design-resources](https://github.com/ashishps1/awesome-system-design-resources) | Repo of links and notes | A quick concept checklist and curated links. 42k stars; last pushed 2026-02-16. | Mostly aggregation, so quality depends on the linked material. Last push was about 8 months ago. |
| 6 | [ByteByteGo system-design-101](https://github.com/ByteByteGoHq/system-design-101) | Repo of diagrams | Quick visual revision the night before. 90k stars. | Last push was 2025-04-04, so it is stale. It is diagrams only, with no problem-solving process. |
| 7 | [Tech Dummies (Narendra L)](https://www.youtube.com/@TechDummiesNarendraL), [codeKarle](https://www.youtube.com/@codeKarle) and [Gaurav Sen](https://www.youtube.com/@gkcs) | YouTube | Walkthrough videos of the classic problems. Narendra L and codeKarle are India-based. | Handles loaded, but I did not check upload dates. Older videos may predate current practice, so check each video's date. |
| 8 | [binhnguyennus/awesome-scalability](https://github.com/binhnguyennus/awesome-scalability) | Repo of links | Real engineering-blog case studies, useful as depth for follow-up questions. | Last push was 2026-01-04. It is a link dump with no structure, so do not use it as a first resource. |

Also checked and left out: [High Scalability](https://highscalability.com) is reachable but is an older-style blog, so I did not rank it. The GeeksforGeeks system design tutorial is reachable but looks like SEO-style content, so I would not use it as a primary resource.

## LLD resources (ranked, C++ noted)

| # | Name and URL | Format | Best for | Limitation |
|---|---|---|---|---|
| 1 | [ashishps1/awesome-low-level-design](https://github.com/ashishps1/awesome-low-level-design) | Repo | The best free fit for C++. It has a `solutions/cpp` directory with about 34 full problems, plus separate directories for class diagrams, design patterns and OOP. 27k stars; last pushed 2026-08-19. | The primary language is Java, so C++ coverage may lag Java. I did not check each C++ solution. |
| 2 | [Hello Interview, LLD](https://www.hellointerview.com/learn/low-level-design/in-a-hurry/introduction) | Written course | The delivery framework, design principles, OOP concepts and patterns are free. Connect Four, Amazon Locker and Elevator are free. | Parking Lot, File System, Movie Ticket Booking, Logging Service, Rate Limiter and Inventory Management are locked. It uses pseudocode and Python, not C++. |
| 3 | [Concept && Coding (YouTube)](https://www.youtube.com/@ConceptAndCoding) | YouTube | India-oriented machine-coding walkthroughs in Java. | Java only. I did not verify the video catalogue or dates. |
| 4 | [Refactoring.Guru, design patterns in C++](https://refactoring.guru/design-patterns/cpp) | Website | Pattern explanations, and the only C++-native resource in this list. The companion [design-patterns-cpp repo](https://github.com/RefactoringGuru/design-patterns-cpp) was last pushed 2025-08-30. | The site's book and course are paid. Patterns are taught in isolation, not as full machine-coding problems. |
| 5 | [Christopher Okhravi (YouTube)](https://www.youtube.com/@ChristopherOkhravi) | YouTube | Clear explanations of design patterns and OOP theory. | Java, and not interview-oriented. |
| 6 | [tssovi/grokking-the-object-oriented-design-interview](https://github.com/tssovi/grokking-the-object-oriented-design-interview) | Repo (free recreation of a paid course) | Classic OOD problem write-ups. 6.4k stars; last pushed 2026-08-08. | Because it mirrors a paid course, licensing is unclear, so use it as a problem list. It is Python and UML-heavy. |
| 7 | [TharunKumarReddyPolu/LLD-Handbook-for-Coding-Interviews](https://github.com/TharunKumarReddyPolu/LLD-Handbook-for-Coding-Interviews) | Repo | Runnable solutions to Parking Lot, Splitwise, BookMyShow, Elevator, Snake and Ladder and Vending Machine. Last pushed 2026-09-20. | 76 stars and one maintainer. The language appears to be JavaScript. I did not read it, so treat it as unvetted. |
| 8 | [llucifer97/low-level-design](https://github.com/llucifer97/low-level-design) | Repo | C++ OOD examples. | 8 stars, last pushed 2026-02-11, and I did not review the code quality. Use it only as a second C++ reference. |

Flagged and excluded:

- `prasadgujar/low-level-design-primer` has 7.9k stars, but its last push was 2024-01-01, so it is effectively abandoned.
- `parthdevani98/awesome-low-level-designn` has 0 stars and was last pushed 2024-05-08.
- `lld-crafts.lovable.app` appeared in search results as a "C++ LLD practice platform". I did not check it, and it looks like a throwaway app.
- Several repo names I guessed, such as `ByteByteGoHq/system-design-interview` and `Ishan-Shukla/LLD-Cpp`, returned 404. They are not real.

## Canonical HLD problems

Frequency in Indian big-tech loops is my judgement from the interview reports below, not a measured count. The reports I could actually read were Amazon-only.

| Problem | Core concept it teaches |
|---|---|
| URL shortener | Key generation, read-heavy caching, and the sharding trade-off |
| Rate limiter | Token bucket versus sliding window, and distributed counters in Redis |
| Notification system | Fan-out, queues, retries, idempotency and prioritisation |
| News feed or Twitter timeline | Fan-out on write versus fan-out on read |
| Chat system (WhatsApp) | WebSockets, ordering, delivery guarantees and presence |
| YouTube or Netflix | Blob storage, CDN and the video processing pipeline (a YouTube design was a reported Amazon HLD question) |
| Ride-hailing (Uber) | Geospatial indexing and real-time matching |
| Distributed cache or key-value store | Consistent hashing, replication and eviction |
| File storage (Dropbox or Drive) | Chunking, sync and dedup |
| E-commerce or flash sale (Amazon) | Inventory contention, order pipeline and sagas |
| Web crawler | The URL frontier, politeness and dedup |
| Typeahead or search autocomplete | Tries, ranking and offline aggregation |
| Distributed job scheduler or message queue | At-least-once delivery, delayed jobs and partitioning |
| Payment system | Idempotency, ledger design and exactly-once effects |

## Canonical LLD problems

Most of these have C++ solutions in `ashishps1/awesome-low-level-design`. I checked the directory listing (`parkinglot`, `elevatorsystem`, `lrucache`, `vendingmachine`, `splitwise`, `snakeandladdergame`, `loggingframework`, `movieticketbookingsystem`, `pubsubsystem`, `ridesharingservice`, `stackoverflow`, `trafficsignalsystem`, `atm`). Rate limiter and the notification service did not appear in the listing, so find those elsewhere.

| Problem | Core concept it teaches |
|---|---|
| Parking lot | Entity modelling, strategy pattern for pricing and slot allocation |
| Elevator system | State machine and scheduling algorithms |
| LRU cache | Hash map plus doubly linked list, with thread-safety follow-ups |
| Splitwise | Graph balances, debt simplification and split strategies |
| BookMyShow or movie ticket booking | Seat locking and concurrency |
| Vending machine or ATM | The State pattern |
| Snake and ladder, tic-tac-toe or chess | Game loop, rules engine and extensibility |
| Logging framework | Singleton, chain of responsibility and observers |
| Rate limiter (LLD version) | A pluggable strategy for the algorithm |
| Pub/sub or notification service | Observer pattern and decoupling |
| Stack Overflow clone | Relationships among users, questions, votes and tags (a reported Amazon LLD question) |
| Ride-sharing or food delivery | Matching strategies and state transitions |
| In-memory key-value store or file system | Composite pattern and a clean API |
| Traffic signal system | State machine with timers |

## India-specific interview experience sources

- [LeetCode Discuss, interview experiences](https://leetcode.com/discuss/post/8420230/amazon-sde-2-interview-experience-2026-e-t1g8/). The search surfaced a dated post, "Amazon SDE-2 interview experience, 2026". It returned 403 to my script, so I did not read it, but it should open in a browser. It is the best source for Google and LinkedIn, but filter by India yourself.
- [Desi QnA](https://www.desiqna.in/19193/amazon-sde-2-recent-interview-experiences-2026-set-58) (reachable). It posts numbered sets of recent Indian experiences, such as "Amazon SDE 2 Recent Interview Experiences 2026, Set-58". Useful for round structure; quality varies and I did not read them in depth.
- Medium write-ups, for example [Amazon SDE-II (AFFS, Pune) in 2026](https://medium.com/@nitiaanrj/amazons-sde-ii-interview-affs-pune-in-2026-a-full-breakdown-19b9593b32ec) and [Amazon SDE-2 2026](https://medium.com/@himanshudimp05/amazon-interview-experience-sde-2-2026-c2cd6e71c035). Dated 2026 and written by individuals. They do not cover Google, LinkedIn or Broadcom.
- GeeksforGeeks company tags. The [LinkedIn tag](https://www.geeksforgeeks.org/tag/linkedin/) is reachable, but the Broadcom tag returned 404, so I found no GfG Broadcom page. GfG content is of mixed quality and often undated.
- Glassdoor India (an Amazon SDE 2 page appeared in search) and Blind (reachable) also carry experiences. I did not read either in depth.

Gap: only Amazon reports were read in depth. For other companies, recent dated reports have not been verified. LeetCode Discuss and Glassdoor are the likeliest sources; confirm directly for the companies you target.

Avoid `tryrehearsal.ai/blog/amazon-india-sde-interview-2026`: it is a commercial blog and reads as SEO content.

## Planning notes

- The best free combination is Hello Interview's free tier plus the system-design-primer for HLD, and `ashishps1/awesome-low-level-design` for LLD in C++.
- Hello Interview's paywall hits the highest-value patterns, so supplement them from the primer and the ByteByteGo blog.

## What I did not verify

- YouTube upload dates, view counts and catalogue depth for every channel listed.
- The ByteByteGo free versus paid split: the chapter page gave no paywall signal either way.
- Depth and quality of content in most resources; I checked reachability, last-push dates and (for Hello Interview) lock status, not the substance.
- Whether each C++ solution in `ashishps1/awesome-low-level-design` is complete and correct; I only read the directory listing.
- The code quality and language of the smaller LLD repos (TharunKumarReddyPolu, llucifer97).
- The content of the LeetCode Discuss post (403 to my script), and Glassdoor and Blind in depth.
- Dated interview reports for companies other than Amazon.
- The frequency ranking of the canonical problems, which is judgement rather than measured data.
