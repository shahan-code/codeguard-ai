"use client";

import { useEffect, useRef, useState } from "react";
import { useParams } from "next/navigation";
import AuthGuard from "@/components/AuthGuard";
import ScoreDial from "@/components/ScoreDial";
import SeverityBadge from "@/components/SeverityBadge";
import { api, AnalysisDetail } from "@/lib/api";

const RISK_COLORS: Record<string, string> = {
  LOW: "#4f8ff7",
  MEDIUM: "#e0a530",
  HIGH: "#e2694b",
  CRITICAL: "#c23f52",
};

function SubScoreBar({ label, value }: { label: string; value: number }) {
  return (
    <div>
      <div className="mb-1 flex items-center justify-between text-xs">
        <span className="text-mist-300">{label}</span>
        <span className="font-mono text-mist-200">{value}</span>
      </div>
      <div className="h-1.5 w-full overflow-hidden rounded-full bg-ink-700">
        <div className="h-full rounded-full bg-signal-500" style={{ width: `${value}%` }} />
      </div>
    </div>
  );
}

export default function AnalysisResultsPage() {
  const params = useParams<{ id: string }>();
  const [analysis, setAnalysis] = useState<AnalysisDetail | null>(null);
  const [downloading, setDownloading] = useState(false);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function poll() {
      try {
        const detail = await api.getAnalysis(params.id);
        if (cancelled) return;
        setAnalysis(detail);
        if (detail.status === "COMPLETED" || detail.status === "FAILED") {
          if (pollRef.current) clearInterval(pollRef.current);
        }
      } catch {
        if (pollRef.current) clearInterval(pollRef.current);
      }
    }

    poll();
    pollRef.current = setInterval(poll, 900);
    return () => {
      cancelled = true;
      if (pollRef.current) clearInterval(pollRef.current);
    };
  }, [params.id]);

  async function handleDownload() {
    setDownloading(true);
    try {
      const blob = await api.downloadReport(params.id);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `codeguard-report-${params.id}.pdf`;
      a.click();
      URL.revokeObjectURL(url);
    } finally {
      setDownloading(false);
    }
  }

  if (!analysis) {
    return (
      <AuthGuard>
        <div className="flex h-64 items-center justify-center text-mist-400">Loading…</div>
      </AuthGuard>
    );
  }

  if (analysis.status === "QUEUED" || analysis.status === "RUNNING") {
    return (
      <AuthGuard>
        <div className="mx-auto flex max-w-2xl flex-col items-center justify-center py-24 text-center">
          <div className="h-10 w-10 animate-spin rounded-full border-2 border-ink-600 border-t-signal-500" />
          <p className="mt-6 font-display text-lg text-mist-50">
            {analysis.status === "QUEUED" ? "Queued for analysis…" : "Analyzing your code…"}
          </p>
          <p className="mt-1 text-sm text-mist-400">
            Running metrics, code smell, and security checks. This usually takes a few seconds.
          </p>
        </div>
      </AuthGuard>
    );
  }

  if (analysis.status === "FAILED") {
    return (
      <AuthGuard>
        <div className="mx-auto max-w-2xl rounded-lg border border-risk-critical/30 bg-risk-critical/10 p-8 text-center">
          <p className="font-display text-lg text-mist-50">Analysis failed</p>
          <p className="mt-2 text-sm text-mist-300">{analysis.error_message}</p>
        </div>
      </AuthGuard>
    );
  }

  const metrics = analysis.metrics!;
  const findings = analysis.findings || [];
  const security = analysis.security_findings || [];
  const functionRisk = analysis.function_risk || [];
  const subScores = analysis.sub_scores || {};
  const recs = analysis.recommendations || [];

  return (
    <AuthGuard>
      <div className="mx-auto max-w-5xl">
        <div className="mb-6 flex items-start justify-between">
          <div>
            <h1 className="font-display text-2xl font-medium text-mist-50">{analysis.filename}</h1>
            <p className="mt-1 text-sm text-mist-400">
              {analysis.from_cache ? "Result loaded from cache · " : ""}
              {new Date(analysis.created_at).toLocaleString()}
            </p>
          </div>
          <button
            onClick={handleDownload}
            disabled={downloading}
            className="rounded-md border border-ink-600 px-4 py-2.5 text-sm font-medium text-mist-100 hover:border-ink-500 disabled:opacity-60"
          >
            {downloading ? "Preparing PDF…" : "Download PDF report"}
          </button>
        </div>

        <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
          <div className="rounded-lg border border-ink-700 bg-ink-900 p-6">
            <div className="flex items-center justify-around">
              <ScoreDial score={analysis.quality_score ?? 0} label="Quality score" />
              <div className="flex flex-col items-center gap-2">
                <span
                  className="rounded-md border px-4 py-2 font-display text-xl font-medium"
                  style={{
                    color: RISK_COLORS[analysis.risk_level ?? "LOW"],
                    borderColor: `${RISK_COLORS[analysis.risk_level ?? "LOW"]}55`,
                    backgroundColor: `${RISK_COLORS[analysis.risk_level ?? "LOW"]}15`,
                  }}
                >
                  {analysis.risk_level}
                </span>
                <span className="font-mono text-xs uppercase tracking-wider text-mist-300">
                  Predicted defect risk ({analysis.risk_score}/100)
                </span>
              </div>
            </div>
          </div>

          <div className="rounded-lg border border-ink-700 bg-ink-900 p-6 lg:col-span-2">
            <h3 className="mb-4 text-sm font-medium text-mist-200">Quality sub-scores</h3>
            <div className="grid grid-cols-2 gap-x-6 gap-y-3">
              {Object.entries(subScores).map(([k, v]) => (
                <SubScoreBar key={k} label={k.charAt(0).toUpperCase() + k.slice(1)} value={v as number} />
              ))}
            </div>
          </div>
        </div>

        {analysis.ai_explanation && (
          <div className="mt-4 rounded-lg border border-signal-500/30 bg-signal-500/10 p-5">
            <h3 className="mb-1.5 text-xs font-medium uppercase tracking-wide text-signal-400">AI explanation</h3>
            <p className="text-sm leading-relaxed text-mist-100">{analysis.ai_explanation}</p>
          </div>
        )}

        <div className="mt-4 rounded-lg border border-ink-700 bg-ink-900 p-6">
          <h3 className="mb-4 text-sm font-medium text-mist-200">Code metrics</h3>
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
            {[
              ["Lines of code", metrics.loc],
              ["Functions", metrics.function_count],
              ["Classes", metrics.class_count],
              ["Avg complexity", metrics.avg_complexity],
              ["Max complexity", metrics.max_complexity],
              ["Avg fn length", metrics.avg_function_length],
              ["Max fn length", metrics.max_function_length],
              ["Max nesting depth", metrics.max_nesting_depth],
            ].map(([label, value]) => (
              <div key={label as string}>
                <p className="text-xs text-mist-400">{label}</p>
                <p className="mt-0.5 font-mono text-lg text-mist-50">{String(value)}</p>
              </div>
            ))}
          </div>
        </div>

        {functionRisk.length > 0 && (
          <div className="mt-4 rounded-lg border border-ink-700 bg-ink-900">
            <div className="border-b border-ink-700 px-6 py-4">
              <h3 className="text-sm font-medium text-mist-200">Function-level risk</h3>
            </div>
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-xs uppercase tracking-wide text-mist-400">
                  <th className="px-6 py-2 font-normal">Function</th>
                  <th className="px-6 py-2 font-normal">Complexity</th>
                  <th className="px-6 py-2 font-normal">Length</th>
                  <th className="px-6 py-2 font-normal">Risk</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-ink-700">
                {functionRisk.map((f) => (
                  <tr key={f.name + f.line}>
                    <td className="px-6 py-3 font-mono text-mist-100">{f.name}()</td>
                    <td className="px-6 py-3 text-mist-300">{f.complexity}</td>
                    <td className="px-6 py-3 text-mist-300">{f.length}</td>
                    <td className="px-6 py-3">
                      <SeverityBadge severity={f.risk} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {findings.length > 0 && (
          <div className="mt-4 rounded-lg border border-ink-700 bg-ink-900 p-6">
            <h3 className="mb-4 text-sm font-medium text-mist-200">Code smells</h3>
            <div className="flex flex-col divide-y divide-ink-700">
              {findings.map((f, i) => (
                <div key={i} className="py-3.5 first:pt-0 last:pb-0">
                  <div className="flex items-center gap-2">
                    <SeverityBadge severity={f.severity} />
                    <span className="text-sm font-medium text-mist-50">{f.title}</span>
                    {f.line && <span className="font-mono text-xs text-mist-400">Line {f.line}</span>}
                  </div>
                  <p className="mt-1.5 text-sm text-mist-300">{f.description}</p>
                  <p className="mt-1 text-xs text-mist-400">{f.recommendation}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {security.length > 0 && (
          <div className="mt-4 rounded-lg border border-ink-700 bg-ink-900 p-6">
            <h3 className="mb-1 text-sm font-medium text-mist-200">Security findings</h3>
            <p className="mb-4 text-xs text-mist-400">Basic Security Pattern Analysis — not a complete security audit.</p>
            <div className="flex flex-col divide-y divide-ink-700">
              {security.map((f, i) => (
                <div key={i} className="py-3.5 first:pt-0 last:pb-0">
                  <div className="flex items-center gap-2">
                    <SeverityBadge severity={f.severity} />
                    <span className="text-sm font-medium text-mist-50">{f.issue}</span>
                    {f.line && <span className="font-mono text-xs text-mist-400">Line {f.line}</span>}
                  </div>
                  <p className="mt-1.5 text-sm text-mist-300">{f.explanation}</p>
                  <p className="mt-1 text-xs text-mist-400">{f.recommendation}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {recs.length > 0 && (
          <div className="mt-4 rounded-lg border border-ink-700 bg-ink-900 p-6">
            <h3 className="mb-4 text-sm font-medium text-mist-200">Recommendations</h3>
            <ol className="flex flex-col gap-3">
              {recs.map((r) => (
                <li key={r.rank} className="text-sm">
                  <span className="font-mono text-xs uppercase tracking-wide text-signal-400">{r.priority_label}</span>
                  <p className="mt-0.5 text-mist-100">{r.recommendation}</p>
                </li>
              ))}
            </ol>
          </div>
        )}

        {analysis.source_code && (
          <div className="mt-4 rounded-lg border border-ink-700 bg-ink-900">
            <div className="border-b border-ink-700 px-6 py-4">
              <h3 className="text-sm font-medium text-mist-200">Source</h3>
            </div>
            <pre className="scrollbar-thin max-h-[480px] overflow-auto p-6 font-mono text-xs leading-relaxed text-mist-200">
              {analysis.source_code.split("\n").map((line, i) => (
                <div key={i} className="flex gap-4">
                  <span className="w-8 shrink-0 select-none text-right text-mist-500">{i + 1}</span>
                  <span>{line}</span>
                </div>
              ))}
            </pre>
          </div>
        )}
      </div>
    </AuthGuard>
  );
}
