import { Link } from "@tanstack/react-router";
import type { Row } from "../api";
import type { IconName } from "../icon-names";
import { useToggleStar } from "../queries";
import { Icon } from "./Icon";
import { QuickLogTrigger } from "./QuickLog";

export function Difficulty({ value }: { value: string | null }) {
  if (!value) return <span />;
  return <span className={`diff diff-${value.toLowerCase()}`}>{value}</span>;
}

interface LinkSpec {
  href: string;
  icon: IconName;
  label: string;
  title: string;
}

export function problemLinks(item: Pick<Row, "url" | "slug" | "article_url" | "video_url">): LinkSpec[] {
  const out: LinkSpec[] = [];
  if (item.url) {
    const site = item.url.includes("leetcode") ? "LeetCode" : item.url.includes("codeforces") ? "Codeforces" : "the source site";
    out.push({ href: item.url, icon: "code", label: "Practice", title: `Practice on ${site}` });
  }
  if (item.slug) {
    out.push({ href: `https://leetcode.com/problems/${item.slug}/editorial/`, icon: "book-open-text", label: "Editorial", title: "LeetCode editorial" });
  }
  if (item.article_url) out.push({ href: item.article_url, icon: "article", label: "Article", title: "takeuforward article" });
  if (item.video_url) out.push({ href: item.video_url, icon: "play-circle", label: "Video", title: "Video solution" });
  return out;
}

/** Practice, editorial, article and video. Icon-only in dense rows, labelled elsewhere. */
export function ProblemLinks({ item, wide = false }: { item: Row; wide?: boolean }) {
  const links = problemLinks(item);
  return (
    <>
      {links.map((l) =>
        wide ? (
          <a key={l.label} className="btn btn-sm" href={l.href} target="_blank" rel="noreferrer" title={l.title}>
            <Icon name={l.icon} />
            {l.label}
          </a>
        ) : (
          <a key={l.label} className="link-icon" href={l.href} target="_blank" rel="noreferrer" title={l.title} aria-label={l.label}>
            <Icon name={l.icon} />
          </a>
        ),
      )}
    </>
  );
}

export function StarButton({ item, wide = false }: { item: Row; wide?: boolean }) {
  const star = useToggleStar();
  const label = item.starred ? "Starred: in your review queue" : "Star to add it to your review queue";
  return (
    <button
      type="button"
      className={wide ? "btn btn-sm star-btn" : "link-icon star-btn"}
      aria-pressed={item.starred}
      title={star.isError ? star.error.message : label}
      aria-label={wide ? undefined : `Star ${item.title} for revision`}
      disabled={star.isPending}
      onClick={() => star.mutate(item.log_id ?? item.id)}
    >
      <Icon name={item.starred ? "star-fill" : "star"} />
      {wide && (item.starred ? "Starred for revision" : "Star for revision")}
    </button>
  );
}

export function ProblemRow({ item, showStar = false, hideDifficulty = false, badge }: { item: Row; showStar?: boolean; hideDifficulty?: boolean; badge?: string }) {
  const logId = item.log_id ?? item.id;
  return (
    <li className="row" data-filter={`${item.title} ${item.external_id ?? ""} ${item.difficulty ?? ""}`.toLowerCase()}>
      <QuickLogTrigger itemId={logId} status={item.status} title={item.title} />
      <div className="row-title">
        {(item.platform === "LeetCode" || item.platform === "Codeforces") && item.external_id && <span className="mono">{item.external_id}</span>}
        <Link to="/items/$id" params={{ id: logId }}>
          {item.title}
        </Link>
        {item.is_anchor && (
          <span className="pill" title="Anchor problem: full re-solves at about +7 and +30 days">
            Anchor
          </span>
        )}
        {item.plan_block && (
          <span className="pill pill-accent" title="Also in your plan. Progress is shared.">
            Block {item.plan_block}
          </span>
        )}
      </div>
      {badge ? <span className="pill">{badge}</span> : hideDifficulty ? <span /> : <Difficulty value={item.difficulty} />}
      <span className="linkset">
        <ProblemLinks item={item} />
        {showStar && <StarButton item={item} />}
      </span>
    </li>
  );
}
