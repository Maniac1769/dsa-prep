import { useState, type FormEvent } from "react";
import { Link, createFileRoute, redirect } from "@tanstack/react-router";
import { useMutation, useSuspenseQuery } from "@tanstack/react-query";
import { api, type AuthStatus, type ListKey } from "../api";
import { authErrorText, safeNext, useAfterSignIn } from "../auth";
import { TextField } from "../components/Field";
import { authStatusQuery } from "../queries";
import { AuthIntro } from "../components/AuthIntro";

export const Route = createFileRoute("/register")({
  validateSearch: (search: Record<string, unknown>): { next?: string } => ({ next: safeNext(search.next) }),
  beforeLoad: ({ context, search }) => {
    if (context.user) throw redirect({ href: search.next ?? "/" });
  },
  loader: ({ context: { queryClient } }) => queryClient.ensureQueryData(authStatusQuery()),
  component: RegisterPage,
});

const USERNAME_RULE = /^[a-z0-9_-]{3,24}$/;
const USERNAME_HINT = "3 to 24 characters: a to z, 0 to 9, underscore or hyphen.";
const PASSWORD_HINT = "At least 10 characters.";

/** One plain sentence per list, built from the real count so it cannot drift. */
function listSentence(key: ListKey, total: number): string {
  if (key === "plan") return `${total} problems in 42 pattern blocks, the recommended default`;
  if (key === "sde") return `${total} classic interview problems`;
  return `${total} problems from basics to advanced`;
}

// The API titles carry the count ("Prep plan (126)"); the sentence already says it.
const bareTitle = (title: string) => title.replace(/\s*\(\d+\)\s*$/, "");

function RegisterPage() {
  const { data: status } = useSuspenseQuery(authStatusQuery());
  const { next } = Route.useSearch();

  return (
    <div className="auth">
      <AuthIntro />
      <h1>Create an account</h1>
      <p className="auth-lede">{status.registration_open ? <Places status={status} /> : <Full status={status} next={next} />}</p>
      {status.registration_open && <RegisterForm status={status} next={next} />}
      <p className="auth-foot muted">
        Already have an account? <Link to="/login" search={{ next }}>Sign in</Link>
      </p>
    </div>
  );
}

function Places({ status }: { status: AuthStatus }) {
  const left = Math.max(status.cap - status.users, 0);
  return <span className="muted">{left} of {status.cap} places left. No email needed.</span>;
}

function Full({ status, next }: { status: AuthStatus; next?: string }) {
  return (
    <span>
      Sign-ups are full: {status.users} of {status.cap} places taken. If you already have an account,{" "}
      <Link to="/login" search={{ next }}>sign in</Link>.
    </span>
  );
}

function RegisterForm({ status, next }: { status: AuthStatus; next?: string }) {
  const afterSignIn = useAfterSignIn();
  const [list, setList] = useState<ListKey>(status.lists.find((l) => l.key === "plan")?.key ?? status.lists[0]?.key ?? "plan");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [touched, setTouched] = useState({ username: false, password: false });
  const register = useMutation({
    mutationFn: api.register,
    onSuccess: ({ user }) => afterSignIn(user, next),
  });

  const usernameOk = USERNAME_RULE.test(username);
  const passwordOk = password.length >= 10 && password.length <= 128;

  const submit = (e: FormEvent) => {
    e.preventDefault();
    setTouched({ username: true, password: true });
    if (!usernameOk || !passwordOk) return;
    register.mutate({
      username,
      password,
      preferred_list: list,
      // The browser's zone, sent silently: it sets which midnight starts a day.
      timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
    });
  };

  return (
    <form className="panel auth-form" onSubmit={submit} noValidate>
      <fieldset className="choice">
        <legend>Your list</legend>
        <p className="field-hint">Pick one to finish. You can switch later and keep your progress.</p>
        {status.lists.map((l) => (
          <label key={l.key} className="choice-item">
            <input type="radio" name="list" value={l.key} checked={list === l.key} onChange={() => setList(l.key)} />
            <span>
              <b>{bareTitle(l.title)}</b>
              <span className="muted">{listSentence(l.key, l.total)}</span>
            </span>
          </label>
        ))}
      </fieldset>
      <TextField
        id="reg-username"
        label="Username"
        value={username}
        onChange={(e) => setUsername(e.target.value.toLowerCase())}
        onBlur={() => setTouched((t) => ({ ...t, username: true }))}
        hint={USERNAME_HINT}
        invalid={touched.username && !usernameOk}
        autoComplete="username"
        autoCapitalize="none"
        spellCheck={false}
        maxLength={24}
        required
      />
      <TextField
        id="reg-password"
        label="Password"
        type="password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        onBlur={() => setTouched((t) => ({ ...t, password: true }))}
        hint={PASSWORD_HINT}
        invalid={touched.password && !passwordOk}
        autoComplete="new-password"
        maxLength={128}
        required
      />
      {register.isError && (
        <p className="form-error" role="alert">
          {authErrorText(register.error)}
        </p>
      )}
      <button type="submit" className="btn btn-primary" disabled={register.isPending}>
        {register.isPending ? "Creating account" : "Create account"}
      </button>
    </form>
  );
}
