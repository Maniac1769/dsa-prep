import { useQueryClient } from "@tanstack/react-query";
import { useRouter } from "@tanstack/react-router";
import { ApiError, type User } from "./api";
import { keys } from "./queries";

/** A same-site path to return to after signing in; anything else is dropped. */
export function safeNext(raw: unknown): string | undefined {
  if (typeof raw !== "string" || raw.length > 500) return undefined;
  if (!raw.startsWith("/") || raw.startsWith("//") || raw.startsWith("/\\")) return undefined;
  if (/^\/(login|register)(\/|\?|#|$)/.test(raw)) return undefined;
  return raw;
}

/** Store the new session's user, drop anything cached for a previous user, and go on. */
export function useAfterSignIn() {
  const qc = useQueryClient();
  const router = useRouter();
  return (user: User, next?: string) => {
    qc.removeQueries({ queryKey: keys.all });
    qc.setQueryData(keys.me, user);
    router.history.push(next ?? "/");
  };
}

export function waitText(seconds: number): string {
  if (seconds < 90) return `${Math.max(1, Math.round(seconds))} seconds`;
  const m = Math.ceil(seconds / 60);
  return m < 90 ? `${m} minutes` : `${Math.ceil(m / 60)} hours`;
}

/** One sentence a person can act on, for any failure of a sign-in, sign-up or account call. */
export function authErrorText(e: unknown): string {
  if (e instanceof ApiError) {
    if (e.status === 429) return e.retryAfter ? `Too many attempts. Try again in ${waitText(e.retryAfter)}.` : "Too many attempts. Try again in a little while.";
    return e.detail || "That did not work. Try again.";
  }
  return "Could not reach the server. Check your connection and try again.";
}
