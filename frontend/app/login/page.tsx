"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { api, setToken, ApiError } from "@/lib/api";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const res = await api.login(email, password);
      setToken(res.access_token);
      router.push("/dashboard");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Something went wrong. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-ink-950 px-6">
      <div className="w-full max-w-sm">
        <div className="mb-8 flex items-center gap-2">
          <span className="h-2 w-2 rounded-full bg-signal-500" />
          <span className="font-display text-[16px] font-semibold text-mist-50">CodeGuard AI</span>
        </div>
        <h1 className="font-display text-2xl font-medium text-mist-50">Log in</h1>
        <p className="mt-1 text-sm text-mist-300">Access your analysis history and dashboard.</p>

        <form onSubmit={handleSubmit} className="mt-8 flex flex-col gap-4">
          <div>
            <label className="mb-1.5 block text-xs font-medium uppercase tracking-wide text-mist-300">Email</label>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full rounded-md border border-ink-600 bg-ink-900 px-3 py-2.5 text-sm text-mist-50 outline-none focus:border-signal-500"
              placeholder="you@example.com"
            />
          </div>
          <div>
            <label className="mb-1.5 block text-xs font-medium uppercase tracking-wide text-mist-300">Password</label>
            <input
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full rounded-md border border-ink-600 bg-ink-900 px-3 py-2.5 text-sm text-mist-50 outline-none focus:border-signal-500"
              placeholder="••••••••"
            />
          </div>

          {error && <p className="text-sm text-risk-high">{error}</p>}

          <button
            type="submit"
            disabled={loading}
            className="mt-2 rounded-md bg-signal-500 py-2.5 font-medium text-ink-950 hover:bg-signal-400 disabled:opacity-60"
          >
            {loading ? "Logging in…" : "Log in"}
          </button>
        </form>

        <p className="mt-6 text-sm text-mist-300">
          Don&apos;t have an account?{" "}
          <Link href="/register" className="text-signal-400 hover:text-signal-300">
            Create one
          </Link>
        </p>
      </div>
    </div>
  );
}
