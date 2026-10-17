import { useMemo, useState, type FormEvent, type ReactNode } from "react";
import { createFileRoute, useRouter } from "@tanstack/react-router";
import { useMutation, useQueryClient, useSuspenseQuery } from "@tanstack/react-query";
import { api, type ListInfo, type ListKey, type SettingsPatch, type User } from "../api";
import { authErrorText } from "../auth";
import { TextField } from "../components/Field";
import { Icon } from "../components/Icon";
import { HoldButton } from "../components/Reset";
import { Stepper } from "../components/Stepper";
import { ThemeSegmented } from "../components/ThemeToggle";
import { accountListsQuery, meQuery, useSaveAccountSettings } from "../queries";

export const Route = createFileRoute("/account")({
  loader: ({ context: { queryClient } }) => Promise.all([queryClient.ensureQueryData(meQuery()), queryClient.ensureQueryData(accountListsQuery())]),
  component: AccountPage,
});

const WEEKLY = [3, 4, 5, 6, 7] as const;
const DESIGN_SESSIONS = [0, 1, 2, 3, 4, 5, 6, 7] as const;
const DESIGN_MINUTES = [15, 30, 45, 60] as const;

const bareTitle = (title: string) => title.replace(/\s*\(\d+\)\s*$/, "");

function AccountPage() {
  const { data: user } = useSuspenseQuery(meQuery());
  const { data: lists } = useSuspenseQuery(accountListsQuery());
  const qc = useQueryClient();
  const router = useRouter();

  const signOut = useMutation({
    mutationFn: api.logout,
    onSuccess: async () => {
      // Navigate first so no mounted page refetches into a 401, then drop every cache.
      await router.navigate({ to: "/login", search: {} });
      qc.clear();
    },
  });

  return (
    <div className="narrow account">
      <header className="page-head">
        <div className="head-row">
          <h1>Account</h1>
          <button type="button" className="btn" disabled={signOut.isPending} onClick={() => signOut.mutate()}>
            <Icon name="sign-out" />
            {signOut.isPending ? "Signing out" : "Sign out"}
          </button>
        </div>
        <p className="sub">Signed in as {user.username}.</p>
        {signOut.isError && (
          <p className="form-error" role="alert">
            {authErrorText(signOut.error)}
          </p>
        )}
      </header>

      <StudyForm user={user} lists={lists} />
      <Appearance />
      <PasswordForm />
      <DeleteAccount />
    </div>
  );
}

function Setting({ title, hint, children, stacked = false }: { title: string; hint?: string; children: ReactNode; stacked?: boolean }) {
  return (
    <div className={`setting${stacked ? " is-stacked" : ""}`}>
      <div className="setting-text">
        <p className="setting-title">{title}</p>
        {hint && <p className="setting-hint">{hint}</p>}
      </div>
      <div className="setting-control">{children}</div>
    </div>
  );
}

function StudyForm({ user, lists }: { user: User; lists: ListInfo[] }) {
  const save = useSaveAccountSettings();
  const [draft, setDraft] = useState({
    preferred_list: user.preferred_list,
    weekly_sessions: user.weekly_sessions,
    design_sessions: user.design_sessions,
    design_minutes: user.design_minutes,
    timezone: user.timezone,
  });
  const patch: SettingsPatch = {};
  (Object.keys(draft) as (keyof typeof draft)[]).forEach((k) => {
    if (draft[k] !== user[k]) Object.assign(patch, { [k]: draft[k] });
  });
  const dirty = Object.keys(patch).length > 0;
  const set = <K extends keyof typeof draft>(k: K, v: (typeof draft)[K]) => setDraft((d) => ({ ...d, [k]: v }));

  const zones = useMemo(() => {
    const all = Intl.supportedValuesOf("timeZone");
    return all.includes(user.timezone) ? all : [user.timezone, ...all];
  }, [user.timezone]);

  const submit = (e: FormEvent) => {
    e.preventDefault();
    if (dirty) save.mutate(patch);
  };

  return (
    <form className="panel" onSubmit={submit} aria-labelledby="study-h">
      <div className="section-head">
        <h2 id="study-h">Study</h2>
      </div>

      <fieldset className="choice">
        <legend>Your list</legend>
        <p className="field-hint">Progress is kept per problem; switching lists loses nothing.</p>
        {lists.map((l) => (
          <label key={l.key} className="choice-item">
            <input type="radio" name="preferred_list" value={l.key} checked={draft.preferred_list === l.key} onChange={() => set("preferred_list", l.key as ListKey)} />
            <span>
              <b>{bareTitle(l.title)}</b>
              <span className="muted num">
                {l.solid} of {l.total} solved unaided
              </span>
            </span>
          </label>
        ))}
      </fieldset>

      <Setting title="DSA sessions per week" hint="A number you can keep up in a busy week. Change it any time.">
        <Stepper label="DSA sessions per week" values={WEEKLY} value={draft.weekly_sessions} onChange={(v) => set("weekly_sessions", v)} />
      </Setting>
      <Setting title="Design sessions per week" hint="0 hides the design section from Today.">
        <Stepper label="Design sessions per week" values={DESIGN_SESSIONS} value={draft.design_sessions} onChange={(v) => set("design_sessions", v)} />
      </Setting>
      <Setting title="Design session length">
        <Stepper label="Design session length" values={DESIGN_MINUTES} value={draft.design_minutes} onChange={(v) => set("design_minutes", v)} suffix=" min" />
      </Setting>
      <Setting title="Time zone" hint="Decides when your day ends and your week starts on Monday." stacked>
        <select aria-label="Time zone" value={draft.timezone} onChange={(e) => set("timezone", e.target.value)}>
          {zones.map((z) => (
            <option key={z} value={z}>
              {z.replaceAll("_", " ")}
            </option>
          ))}
        </select>
      </Setting>

      <div className="form-actions">
        <button type="submit" className="btn btn-primary" disabled={!dirty || save.isPending}>
          {save.isPending ? "Saving" : "Save settings"}
        </button>
        {save.isSuccess && !dirty && (
          <span className="ok-text" role="status">
            <Icon name="check" />
            Saved
          </span>
        )}
        {save.isError && (
          <span className="form-error" role="alert">
            {authErrorText(save.error)}
          </span>
        )}
      </div>
    </form>
  );
}

function Appearance() {
  return (
    <section className="panel" aria-labelledby="look-h">
      <div className="section-head">
        <h2 id="look-h">Appearance</h2>
        <p>Saved on this device only.</p>
      </div>
      <ThemeSegmented />
    </section>
  );
}

function PasswordForm() {
  const [current, setCurrent] = useState("");
  const [next, setNext] = useState("");
  const [touched, setTouched] = useState(false);
  const change = useMutation({
    mutationFn: api.changePassword,
    onSuccess: () => {
      setCurrent("");
      setNext("");
      setTouched(false);
    },
  });
  const nextOk = next.length >= 10 && next.length <= 128;

  const submit = (e: FormEvent) => {
    e.preventDefault();
    setTouched(true);
    if (!current || !nextOk) return;
    change.mutate({ current_password: current, new_password: next });
  };

  return (
    <form className="panel" onSubmit={submit} noValidate aria-labelledby="pw-h">
      <div className="section-head">
        <h2 id="pw-h">Change password</h2>
        <p>Other devices are signed out.</p>
      </div>
      <div className="form-grid">
        <TextField id="pw-current" label="Current password" type="password" autoComplete="current-password" value={current} onChange={(e) => setCurrent(e.target.value)} required />
        <TextField
          id="pw-new"
          label="New password"
          type="password"
          autoComplete="new-password"
          value={next}
          onChange={(e) => setNext(e.target.value)}
          hint="At least 10 characters."
          invalid={touched && !nextOk}
          maxLength={128}
          required
        />
        <div className="form-actions">
          <button type="submit" className="btn" disabled={change.isPending || !current || !next}>
            {change.isPending ? "Changing" : "Change password"}
          </button>
          {change.isSuccess && (
            <span className="ok-text" role="status">
              <Icon name="check" />
              Password changed
            </span>
          )}
          {change.isError && (
            <span className="form-error" role="alert">
              {authErrorText(change.error)}
            </span>
          )}
        </div>
      </div>
    </form>
  );
}

function DeleteAccount() {
  const qc = useQueryClient();
  const router = useRouter();
  const [password, setPassword] = useState("");
  const remove = useMutation({
    mutationFn: api.deleteAccount,
    onSuccess: async () => {
      await router.navigate({ to: "/login", search: {} });
      qc.clear();
    },
  });

  return (
    <section className="panel danger-zone" aria-labelledby="del-h">
      <div className="section-head">
        <h2 id="del-h">Delete account</h2>
      </div>
      <p className="ink2 small">Removes your account and all of your progress, reviews and notes. This cannot be undone.</p>
      <div className="form-grid">
        <TextField id="del-password" label="Your password" type="password" autoComplete="current-password" value={password} onChange={(e) => setPassword(e.target.value)} />
        <div className="form-actions">
          <HoldButton
            label="Hold to delete account"
            pendingLabel="Deleting"
            icon="x"
            disabled={!password}
            pending={remove.isPending}
            onConfirm={() => remove.mutate({ password })}
          />
          {remove.isError && (
            <span className="form-error" role="alert">
              {authErrorText(remove.error)}
            </span>
          )}
        </div>
      </div>
    </section>
  );
}
