// frontend/app/page.tsx
"use client";
import { useEffect, useState } from "react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// --- Types ---
type Finding = {
  id: number;
  file_path: string;
  line_number: string;
  severity: string;
  issue: string;
  suggestion: string;
};

type Review = {
  id: number;
  repo_name: string;
  pr_number: number;
  pr_title: string;
  reviewed_at: string;
  total_findings: number;
  critical: number;
  major: number;
  minor: number;
};

type Stats = {
  total_prs_reviewed: number;
  total_findings: number;
  critical: number;
  major: number;
  minor: number;
};

type PRDetail = {
  pr: Review;
  findings: Finding[];
};

// --- Helpers ---
const severityStyle = (s: string) => {
  const val = s?.toLowerCase() ?? "";
  if (val.includes("critical")) return "bg-red-100 text-red-700 border border-red-200";
  if (val.includes("major"))    return "bg-orange-100 text-orange-700 border border-orange-200";
  if (val.includes("minor"))    return "bg-yellow-100 text-yellow-700 border border-yellow-200";
  return "bg-gray-100 text-gray-500";
};

const severityIcon = (s: string) => {
  const val = s?.toLowerCase() ?? "";
  if (val.includes("critical")) return "🔴";
  if (val.includes("major"))    return "🟠";
  if (val.includes("minor"))    return "🟡";
  return "⚪";
};

const formatDate = (iso: string) =>
  new Date(iso).toLocaleString("en-US", {
    month: "short", day: "numeric",
    hour: "2-digit", minute: "2-digit"
  });

// --- Stat Card ---
function StatCard({ label, value, icon, color }: {
  label: string; value: number; icon: string; color: string;
}) {
  return (
    <div className={`rounded-2xl p-5 flex items-center gap-4 ${color} shadow-sm`}>
      <span className="text-3xl">{icon}</span>
      <div>
        <div className="text-2xl font-bold">{value}</div>
        <div className="text-xs opacity-70 mt-0.5">{label}</div>
      </div>
    </div>
  );
}

// --- Findings Modal ---
function FindingsModal({ prId, onClose }: { prId: number; onClose: () => void }) {
  const [data, setData] = useState<PRDetail | null>(null);

  useEffect(() => {
    fetch(`${API}/api/reviews/${prId}/findings`)
      .then((r) => r.json())
      .then(setData);
  }, [prId]);

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4 backdrop-blur-sm">
      <div className="bg-white rounded-2xl w-full max-w-2xl max-h-[85vh] overflow-y-auto shadow-2xl">

        {/* Modal Header */}
        <div className="sticky top-0 bg-white border-b px-6 py-4 flex justify-between items-start rounded-t-2xl z-10">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="text-xs bg-gray-100 text-gray-500 px-2 py-0.5 rounded-full font-mono">
                {data?.pr.repo_name} · PR #{data?.pr.pr_number}
              </span>
            </div>
            <h2 className="text-base font-semibold text-gray-800 leading-snug">
              {data?.pr.pr_title ?? "Loading..."}
            </h2>
          </div>
          <button
            onClick={onClose}
            className="ml-4 mt-1 text-gray-300 hover:text-gray-600 transition-colors text-2xl leading-none"
          >
            ×
          </button>
        </div>

        {/* Findings */}
        <div className="px-6 py-5 flex flex-col gap-3">
          {!data ? (
            <div className="text-center text-gray-400 py-12">Loading findings...</div>
          ) : data.findings.length === 0 ? (
            <div className="text-center text-gray-400 py-12">
              <div className="text-4xl mb-3">✅</div>
              <p className="font-medium text-gray-500">No issues found</p>
              <p className="text-xs text-gray-400 mt-1">This PR passed the AI review clean</p>
            </div>
          ) : (
            <>
              <p className="text-xs text-gray-400 mb-1">
                {data.findings.length} issue{data.findings.length > 1 ? "s" : ""} found
              </p>
              {data.findings.map((f, i) => (
                <div key={f.id} className="border rounded-xl overflow-hidden">
                  {/* Finding Header */}
                  <div className="flex items-center gap-3 px-4 py-3 bg-gray-50 border-b">
                    <span className="text-base">{severityIcon(f.severity)}</span>
                    <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${severityStyle(f.severity)}`}>
                      {f.severity}
                    </span>
                    <span className="text-xs text-gray-400 font-mono ml-auto">
                      {f.file_path}{f.line_number ? ` · line ${f.line_number}` : ""}
                    </span>
                  </div>
                  {/* Finding Body */}
                  <div className="px-4 py-3 flex flex-col gap-2">
                    <p className="text-sm text-gray-800 font-medium">{f.issue}</p>
                    {f.suggestion && (
                      <div className="bg-blue-50 border border-blue-100 rounded-lg px-3 py-2">
                        <p className="text-xs text-blue-500 font-semibold mb-1">💡 Suggestion</p>
                        <p className="text-xs text-blue-700">{f.suggestion}</p>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </>
          )}
        </div>
      </div>
    </div>
  );
}

// --- Main Dashboard ---
export default function Dashboard() {
  const [stats, setStats]       = useState<Stats | null>(null);
  const [reviews, setReviews]   = useState<Review[]>([]);
  const [selected, setSelected] = useState<number | null>(null);
  const [loading, setLoading]   = useState(true);

  useEffect(() => {
    Promise.all([
      fetch(`${API}/api/stats`).then((r) => r.json()),
      fetch(`${API}/api/reviews`).then((r) => r.json()),
    ]).then(([s, r]) => {
      setStats(s);
      setReviews(r);
      setLoading(false);
    });
  }, []);

  return (
    <main className="min-h-screen bg-gray-50">

      {/* Top Nav */}
      <div className="bg-white border-b px-6 py-4 flex items-center gap-3 shadow-sm">
        <span className="text-2xl">🤖</span>
        <div>
          <h1 className="text-base font-bold text-gray-900 leading-none">PR Review Agent</h1>
          <p className="text-xs text-gray-400 mt-0.5">AI-powered code review · Joprax</p>
        </div>
      </div>

      <div className="max-w-4xl mx-auto px-6 py-8 flex flex-col gap-8">

        {/* Stats */}
        {stats && (
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <StatCard icon="📋" label="PRs Reviewed"   value={stats.total_prs_reviewed} color="bg-white border text-gray-800" />
            <StatCard icon="🔍" label="Total Findings" value={stats.total_findings}     color="bg-white border text-gray-800" />
            <StatCard icon="🔴" label="Critical"       value={stats.critical}           color="bg-red-50 text-red-800" />
            <StatCard icon="🟠" label="Major"          value={stats.major}              color="bg-orange-50 text-orange-800" />
          </div>
        )}

        {/* Reviews */}
        <div className="bg-white rounded-2xl border shadow-sm overflow-hidden">
          <div className="px-6 py-4 border-b flex items-center justify-between">
            <h2 className="font-semibold text-gray-700">Recent Reviews</h2>
            <span className="text-xs text-gray-400">{reviews.length} total</span>
          </div>

          {loading ? (
            <div className="text-center text-gray-400 py-16">Loading reviews...</div>
          ) : reviews.length === 0 ? (
            <div className="text-center text-gray-400 py-16">
              <div className="text-4xl mb-3">📭</div>
              <p>No reviews yet — open a PR to get started</p>
            </div>
          ) : (
            <div className="divide-y divide-gray-50">
              {reviews.map((r) => (
                <div key={r.id} className="px-6 py-4 flex items-center gap-4 hover:bg-gray-50 transition-colors">

                  {/* PR Info */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-xs font-mono text-gray-400">{r.repo_name}</span>
                      <span className="text-xs text-gray-300">·</span>
                      <span className="text-xs text-gray-400">#{r.pr_number}</span>
                    </div>
                    <p className="text-sm font-medium text-gray-800 truncate">{r.pr_title}</p>
                    <p className="text-xs text-gray-400 mt-0.5">{formatDate(r.reviewed_at)}</p>
                  </div>

                  {/* Severity Pills */}
                  <div className="flex gap-1.5 flex-shrink-0">
                    {r.critical > 0 && (
                      <span className="text-xs px-2 py-0.5 rounded-full bg-red-100 text-red-700 font-medium">
                        {r.critical} critical
                      </span>
                    )}
                    {r.major > 0 && (
                      <span className="text-xs px-2 py-0.5 rounded-full bg-orange-100 text-orange-700 font-medium">
                        {r.major} major
                      </span>
                    )}
                    {r.minor > 0 && (
                      <span className="text-xs px-2 py-0.5 rounded-full bg-yellow-100 text-yellow-700 font-medium">
                        {r.minor} minor
                      </span>
                    )}
                    {r.total_findings === 0 && (
                      <span className="text-xs px-2 py-0.5 rounded-full bg-green-100 text-green-700 font-medium">
                        ✓ Clean
                      </span>
                    )}
                  </div>

                  {/* View Button */}
                  <button
                    onClick={() => r.total_findings > 0 && setSelected(r.id)}
                    className={`text-xs font-medium px-3 py-1.5 rounded-lg transition-colors flex-shrink-0 ${
                      r.total_findings > 0
                        ? "bg-gray-900 text-white hover:bg-gray-700 cursor-pointer"
                        : "bg-gray-100 text-gray-300 cursor-default"
                    }`}
                  >
                    View
                  </button>

                </div>
              ))}
            </div>
          )}
        </div>

      </div>

      {selected !== null && (
        <FindingsModal prId={selected} onClose={() => setSelected(null)} />
      )}
    </main>
  );
}