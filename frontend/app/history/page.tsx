"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import AuthGuard from "@/components/AuthGuard";
import SeverityBadge from "@/components/SeverityBadge";
import { api, AnalysisSummary } from "@/lib/api";

export default function HistoryPage() {
  const [analyses, setAnalyses] = useState<AnalysisSummary[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.listAnalyses().then((data) => {
      setAnalyses(data);
      setLoading(false);
    }).catch(() => setLoading(false));
  }, []);

  return (
    <AuthGuard>
      <div className="mx-auto max-w-4xl">
        <h1 className="font-display text-2xl font-medium text-mist-50">Analysis history</h1>
        <p className="mt-1 text-sm text-mist-300">All analyses you&apos;ve run, most recent first.</p>

        {!loading && analyses.length === 0 && (
          <div className="mt-8 rounded-lg border border-dashed border-ink-600 bg-ink-900 p-12 text-center">
            <p className="text-mist-200">No analyses yet.</p>
            <Link href="/analyze" className="mt-4 inline-block rounded-md bg-signal-500 px-4 py-2.5 text-sm font-medium text-ink-950 hover:bg-signal-400">
              Run your first analysis
            </Link>
          </div>
        )}

        {analyses.length > 0 && (
          <div className="mt-6 overflow-hidden rounded-lg border border-ink-700 bg-ink-900">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-xs uppercase tracking-wide text-mist-400">
                  <th className="px-6 py-3 font-normal">File</th>
                  <th className="px-6 py-3 font-normal">Date</th>
                  <th className="px-6 py-3 font-normal">Quality</th>
                  <th className="px-6 py-3 font-normal">Risk</th>
                  <th className="px-6 py-3 font-normal">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-ink-700">
                {analyses.map((a) => (
                  <tr key={a.id} className="cursor-pointer hover:bg-ink-800">
                    <td className="px-6 py-3.5">
                      <Link href={`/analysis/${a.id}`} className="font-mono text-mist-100">
                        {a.filename}
                      </Link>
                    </td>
                    <td className="px-6 py-3.5 text-mist-400">{new Date(a.created_at).toLocaleDateString()}</td>
                    <td className="px-6 py-3.5 text-mist-200">{a.quality_score ?? "—"}</td>
                    <td className="px-6 py-3.5">{a.risk_level ? <SeverityBadge severity={a.risk_level} /> : "—"}</td>
                    <td className="px-6 py-3.5 text-mist-400">{a.status}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </AuthGuard>
  );
}
