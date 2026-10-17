import { useState, type FormEvent } from "react";
import { Link, createFileRoute, redirect } from "@tanstack/react-router";
import { useMutation } from "@tanstack/react-query";
import { api } from "../api";
import { authErrorText, safeNext, useAfterSignIn } from "../auth";
import { TextField } from "../components/Field";
import { AuthIntro } from "../components/AuthIntro";

export const Route = createFileRoute("/login")({
  validateSearch: (search: Record<string, unknown>): { next?: string } => ({ next: safeNext(search.next) }),
  // Someone who is already signed in has no use for this page.
  beforeLoad: ({ context, search }) => {
    if (context.user) throw redirect({ href: search.next ?? "/" });
  },
  component: LoginPage,
});

function LoginPage() {
  const { next } = Route.useSearch();
  const afterSignIn = useAfterSignIn();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const login = useMutation({
    mutationFn: api.login,
    onSuccess: ({ user }) => afterSignIn(user, next),
  });

  const submit = (e: FormEvent) => {
    e.preventDefault();
    login.mutate({ username: username.trim().toLowerCase(), password });
  };

  return (
    <div className="auth">
      <AuthIntro />
      <h1>Sign in</h1>
      <form className="panel auth-form" onSubmit={submit} noValidate>
        <TextField
          id="login-username"
          label="Username"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          autoComplete="username"
          autoCapitalize="none"
          spellCheck={false}
          autoFocus
          required
        />
        <TextField
          id="login-password"
          label="Password"
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          autoComplete="current-password"
          required
        />
        {login.isError && (
          <p className="form-error" role="alert">
            {authErrorText(login.error)}
          </p>
        )}
        <button type="submit" className="btn btn-primary" disabled={login.isPending || !username || !password}>
          {login.isPending ? "Signing in" : "Sign in"}
        </button>
      </form>
      <p className="auth-foot muted">
        New here? <Link to="/register" search={{ next }}>Create an account</Link>
      </p>
      <p className="auth-foot muted">Forgot your password? Ask whoever runs this server to reset it.</p>
    </div>
  );
}
