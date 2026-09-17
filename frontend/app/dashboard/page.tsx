"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  PieChart,
  Pie,
  Cell,
} from "recharts";
import AuthGuard from "@/components/AuthGuard";
import { api, AnalysisSummary } from "@/lib/api";

const RISK_COLORS: Record<string, string> = {
  LOW: "#4f8ff7",
  MEDIUM: "#e0a530",
  HIGH: "#e2694b",
  CRITICAL: "#c23f52",
};

function StatCard({ label, value, sub }: { label: string; value: string; sub?: string }) {
  return (
    <div className="rounded-lg border border-ink-700 bg-ink-900 p-5">
      <p className="text-xs uppercase tracking-wide text-mist-300">{label}</p>
      <p className="mt-2 font-display text-3xl font-medium text-mist-50">{value}</p>
      {sub && <p className="mt-1 text-xs text-mist-400">{sub}</p>}
    </div>
  );
}

export default function DashboardPage() {
  const [analyses, setAnalyses] = useState<AnalysisSummary[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.listAnalyses().then((data) => {
      setAnalyses(data);
      setLoading(false);
    }).catch(() => setLoading(false));
  }, []);

  const completed = useMemo(() => analyses.filter((a) => a.status === "COMPLETED"), [analyses]);

  const avgQuality = useMemo(() => {
    if (completed.length === 0) return 0;
    return Math.round(completed.reduce((sum, a) => sum + (a.quality_score ?? 0), 0) / completed.length);
  }, [completed]);

  const highRiskCount = useMemo(
    () => completed.filter((a) => a.risk_level === "HIGH" || a.risk_level === "CRITICAL").length,
    [completed]
  );

  const trendData = useMemo(
    () =>
      [...completed]
        .reverse()
        .slice(-12)
        .map((a, i) => ({ name: `#${i + 1}`, score: a.quality_score ?? 0 })),
    [completed]
  );

  const riskDistribution = useMemo(() => {
    const counts: Record<string, number> = { LOW: 0, MEDIUM: 0, HIGH: 0, CRITICAL: 0 };
    completed.forEach((a) => {
      if (a.risk_level) counts[a.risk_level] = (counts[a.risk_level] || 0) + 1;
    });
    return Object.entries(counts)
      .filter(([, v]) => v > 0)
      .map(([name, value]) => ({ name, value }));
  }, [completed]);

  return (
    <AuthGuard>
      <div className="mx-auto max-w-5xl">
        <div className="mb-8 flex items-center justify-between">
          <div>
            <h1 className="font-display text-2xl font-medium text-mist-50">Dashboard</h1>
            <p className="mt-1 text-sm text-mist-300">An overview of your recent code analyses.</p>
          </div>
          <Link href="/analyze" className="rounded-md bg-signal-500 px-4 py-2.5 text-sm font-medium text-ink-950 hover:bg-signal-400">
            New analysis
          </Link>
        </div>

        {!loading && analyses.length === 0 ? (
          <div className="rounded-lg border border-dashed border-ink-600 bg-ink-900 p-12 text-center">
            <p className="text-mist-200">No analyses yet.</p>
            <p className="mt-1 text-sm text-mist-400">Paste some Python code to see your first quality score and defect risk.</p>
            <Link href="/analyze" className="mt-5 inline-block rounded-md bg-signal-500 px-4 py-2.5 text-sm font-medium text-ink-950 hover:bg-signal-400">
              Analyze your first file
            </Link>
          </div>
        ) : (
          <>
            <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
              <StatCard label="Total analyses" value={String(analyses.length)} />
              <StatCard label="Avg quality score" value={completed.length ? `${avgQuality}/100` : "—"} />
              <StatCard label="High-risk files" value={String(highRiskCount)} />
              <StatCard
                label="Total findings"
                value={String(completed.reduce((sum) => sum, 0)) === "0" ? "—" : String(highRiskCount)}
                sub="across completed analyses"
              />
            </div>

            <div className="mt-6 grid grid-cols-1 gap-4 lg:grid-cols-3">
              <div className="rounded-lg border border-ink-700 bg-ink-900 p-5 lg:col-span-2">
                <h3 className="mb-4 text-sm font-medium text-mist-200">Quality score trend</h3>
                {trendData.length > 1 ? (
                  <ResponsiveContainer width="100%" height={220}>
                    <LineChart data={trendData}>
                      <CartesianGrid stroke="#1c212e" vertical={false} />
                      <XAxis dataKey="name" stroke="#5b6478" fontSize={12} />
                      <YAxis stroke="#5b6478" fontSize={12} domain={[0, 100]} />
                      <Tooltip contentStyle={{ background: "#151923", border: "1px solid #1c212e", fontSize: 12 }} />
                      <Line type="monotone" dataKey="score" stroke="#6c7ef0" strokeWidth={2} dot={{ r: 3 }} />
                    </LineChart>
                  </ResponsiveContainer>
                ) : (
                  <p className="py-16 text-center text-sm text-mist-400">Analyze a few more files to see a trend.</p>
                )}
              </div>

              <div className="rounded-lg border border-ink-700 bg-ink-900 p-5">
                <h3 className="mb-4 text-sm font-medium text-mist-200">Risk distribution</h3>
                {riskDistribution.length > 0 ? (
                  <ResponsiveContainer width="100%" height={220}>
                    <PieChart>
                      <Pie data={riskDistribution} dataKey="value" nameKey="name" innerRadius={45} outerRadius={75}>
                        {riskDistribution.map((entry) => (
                          <Cell key={entry.name} fill={RISK_COLORS[entry.name]} />
                        ))}
                      </Pie>
                      <Tooltip contentStyle={{ background: "#151923", border: "1px solid #1c212e", fontSize: 12 }} />
                    </PieChart>
                  </ResponsiveContainer>
                ) : (
                  <p className="py-16 text-center text-sm text-mist-400">No completed analyses yet.</p>
                )}
              </div>
            </div>

            <div className="mt-6 rounded-lg border border-ink-700 bg-ink-900">
              <div className="border-b border-ink-700 px-5 py-4">
                <h3 className="text-sm font-medium text-mist-200">Recent analyses</h3>
              </div>
              <div className="divide-y divide-ink-700">
                {analyses.slice(0, 6).map((a) => (
                  <Link
                    key={a.id}
                    href={`/analysis/${a.id}`}
                    className="flex items-center justify-between px-5 py-3.5 text-sm hover:bg-ink-800"
                  >
                    <span className="font-mono text-mist-100">{a.filename}</span>
                    <div className="flex items-center gap-4">
                      <span className="text-mist-400">{a.quality_score ? `${a.quality_score}/100` : a.status}</span>
                      {a.risk_level && (
                        <span className="font-mono text-xs" style={{ color: RISK_COLORS[a.risk_level] }}>
                          {a.risk_level}
                        </span>
                      )}
                    </div>
                  </Link>
                ))}
              </div>
            </div>
          </>
        )}
      </div>
    </AuthGuard>
  );
}
