"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import AuthGuard from "@/components/AuthGuard";
import { api, ApiError } from "@/lib/api";

const SAMPLE_RISKY = `import hashlib

password = "SuperSecret123"


def process_payment(user, amount, currency, method, discount, tax_rate, notes, retries, meta, flag):
    result = None
    if user is not None:
        if amount > 0:
            if currency == "USD":
                if method == "card":
                    if discount is not None:
                        total = amount - discount
                        result = "ok"
                    else:
                        result = "missing_discount"
                else:
                    result = "unsupported_method"
            else:
                result = "unsupported_currency"
        else:
            result = "invalid_amount"
    else:
        result = "no_user"
    return result


def hash_password(pw):
    return hashlib.md5(pw.encode()).hexdigest()


def run_query(user_input):
    query = "SELECT * FROM users WHERE name = '" + user_input + "'"
    return query
`;

const SAMPLE_GOOD = `from dataclasses import dataclass


@dataclass
class Order:
    amount: float
    tax_rate: float
    discount: float = 0.0


def calculate_total(order: Order) -> float:
    """Return the final total for an order after discount and tax."""
    discounted = order.amount - order.discount
    return round(discounted * (1 + order.tax_rate), 2)
`;

export default function AnalyzePage() {
  const router = useRouter();
  const [filename, setFilename] = useState("pasted_code.py");
  const [code, setCode] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    if (!code.trim()) {
      setError("Please paste some Python code first.");
      return;
    }
    setLoading(true);
    try {
      const result = await api.createAnalysis(code, filename || "pasted_code.py");
      router.push(`/analysis/${result.id}`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Analysis could not be started. Please try again.");
      setLoading(false);
    }
  }

  return (
    <AuthGuard>
      <div className="mx-auto max-w-4xl">
        <h1 className="font-display text-2xl font-medium text-mist-50">Analyze Python code</h1>
        <p className="mt-1 text-sm text-mist-300">
          Paste a Python file below. Your code is analyzed statically and is never executed.
        </p>

        <div className="mt-4 flex gap-2">
          <button
            type="button"
            onClick={() => {
              setCode(SAMPLE_RISKY);
              setFilename("sample_risky.py");
            }}
            className="rounded-md border border-ink-600 px-3 py-1.5 text-xs text-mist-200 hover:border-ink-500"
          >
            Load risky sample
          </button>
          <button
            type="button"
            onClick={() => {
              setCode(SAMPLE_GOOD);
              setFilename("sample_good.py");
            }}
            className="rounded-md border border-ink-600 px-3 py-1.5 text-xs text-mist-200 hover:border-ink-500"
          >
            Load good-quality sample
          </button>
        </div>

        <form onSubmit={handleSubmit} className="mt-4">
          <input
            value={filename}
            onChange={(e) => setFilename(e.target.value)}
            className="mb-3 w-full max-w-xs rounded-md border border-ink-600 bg-ink-900 px-3 py-2 font-mono text-sm text-mist-50 outline-none focus:border-signal-500"
            placeholder="filename.py"
          />
          <textarea
            value={code}
            onChange={(e) => setCode(e.target.value)}
            spellCheck={false}
            placeholder="# Paste your Python code here"
            className="h-96 w-full resize-y rounded-lg border border-ink-600 bg-ink-900 p-4 font-mono text-sm leading-relaxed text-mist-100 outline-none focus:border-signal-500"
          />

          {error && <p className="mt-3 text-sm text-risk-high">{error}</p>}

          <div className="mt-4 flex items-center gap-3">
            <button
              type="submit"
              disabled={loading}
              className="rounded-md bg-signal-500 px-6 py-2.5 font-medium text-ink-950 hover:bg-signal-400 disabled:opacity-60"
            >
              {loading ? "Starting analysis…" : "Analyze"}
            </button>
            <span className="text-xs text-mist-400">Only Python is currently supported.</span>
          </div>
        </form>
      </div>
    </AuthGuard>
  );
}
