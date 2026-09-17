import Link from "next/link";

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-ink-950">
      <header className="mx-auto flex max-w-5xl items-center justify-between px-6 py-6">
        <div className="flex items-center gap-2">
          <span className="h-2 w-2 rounded-full bg-signal-500" />
          <span className="font-display text-[16px] font-semibold text-mist-50">CodeGuard AI</span>
        </div>
        <div className="flex items-center gap-3 text-sm">
          <Link href="/login" className="px-3 py-2 text-mist-300 hover:text-mist-50">
            Log in
          </Link>
          <Link href="/register" className="rounded-md bg-signal-500 px-4 py-2 font-medium text-ink-950 hover:bg-signal-400">
            Get started
          </Link>
        </div>
      </header>

      <section className="mx-auto max-w-3xl px-6 pt-20 text-center">
        <h1 className="font-display text-5xl font-medium leading-[1.1] text-mist-50">
          Find risky code before it becomes a bug.
        </h1>
        <p className="mx-auto mt-6 max-w-xl text-balance text-lg text-mist-300">
          CodeGuard AI combines software metrics, code smells, security signals, and AI-based
          analysis to estimate code quality and defect risk.
        </p>
        <div className="mt-9 flex items-center justify-center gap-4">
          <Link
            href="/register"
            className="rounded-md bg-signal-500 px-6 py-3 font-medium text-ink-950 hover:bg-signal-400"
          >
            Analyze your code
          </Link>
          <Link
            href="/login"
            className="rounded-md border border-ink-600 px-6 py-3 font-medium text-mist-100 hover:border-ink-500"
          >
            View demo
          </Link>
        </div>
      </section>

      <section className="mx-auto mt-24 grid max-w-4xl grid-cols-1 gap-4 px-6 pb-24 sm:grid-cols-3">
        {[
          { title: "Metrics + smells", body: "Complexity, nesting, duplication, and naming issues detected from real AST data — no fabricated line numbers." },
          { title: "Explainable risk", body: "A scikit-learn risk model scores predicted defect risk and shows exactly which signals drove it." },
          { title: "One clear report", body: "Quality score, findings, and prioritized fixes in one downloadable PDF." },
        ].map((item) => (
          <div key={item.title} className="rounded-lg border border-ink-700 bg-ink-900 p-5">
            <h3 className="font-display text-sm font-semibold text-mist-50">{item.title}</h3>
            <p className="mt-2 text-sm leading-relaxed text-mist-300">{item.body}</p>
          </div>
        ))}
      </section>
    </div>
  );
}
