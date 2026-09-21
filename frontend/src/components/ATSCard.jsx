import React from "react";
import { CheckCircle2, AlertTriangle, RefreshCw, Award, Target, Hash } from "lucide-react";

export function ATSCard({ score, feedback, revisionCount, onRetry }) {
  const isPassing = score >= 75.0;

  return (
    <div className="bg-slate-800/90 border border-slate-700/80 rounded-2xl p-6 shadow-xl space-y-5">
      {/* Header with Pass/Fail Status */}
      <div className="flex items-center justify-between border-b border-slate-700/60 pb-4">
        <div className="flex items-center gap-3">
          <div
            className={`p-2.5 rounded-xl ${
              isPassing
                ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                : "bg-amber-500/10 text-amber-400 border border-amber-500/20"
            }`}
          >
            {isPassing ? (
              <CheckCircle2 className="w-6 h-6" />
            ) : (
              <AlertTriangle className="w-6 h-6" />
            )}
          </div>
          <div>
            <h3 className="text-base font-bold text-white flex items-center gap-2">
              ATS Match Score: {score}%
              <span
                className={`text-xs px-2 py-0.5 rounded-full font-bold uppercase ${
                  isPassing
                    ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/40"
                    : "bg-amber-500/20 text-amber-300 border border-amber-500/40"
                }`}
              >
                {isPassing ? "PASSED (≥75%)" : "NEEDS REVISION (<75%)"}
              </span>
            </h3>
            <p className="text-xs text-slate-400">
              Evaluated against employer ATS screening algorithms
            </p>
          </div>
        </div>

        <div className="flex items-center gap-1.5 text-xs font-mono text-slate-400 bg-slate-900/80 px-3 py-1.5 rounded-lg border border-slate-700/60">
          <Hash className="w-3.5 h-3.5 text-sky-400" />
          <span>Revision #{revisionCount || 1}</span>
        </div>
      </div>

      {/* Score Progress Bar */}
      <div className="space-y-1.5">
        <div className="flex justify-between text-xs text-slate-400 font-medium">
          <span>0%</span>
          <span className="text-sky-400 font-semibold">Threshold: 75%</span>
          <span>100%</span>
        </div>
        <div className="w-full h-3 rounded-full bg-slate-900 border border-slate-700/60 overflow-hidden relative">
          {/* 75% target indicator line */}
          <div className="absolute left-[75%] top-0 bottom-0 w-0.5 bg-sky-400/80 z-10" />
          <div
            className={`h-full transition-all duration-700 rounded-full ${
              isPassing
                ? "bg-gradient-to-r from-emerald-500 to-teal-400"
                : "bg-gradient-to-r from-amber-500 to-yellow-400"
            }`}
            style={{ width: `${Math.min(score, 100)}%` }}
          />
        </div>
      </div>

      {/* Keywords Breakdown */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Matched Keywords */}
        <div className="bg-slate-900/60 rounded-xl p-3.5 border border-slate-700/50 space-y-2">
          <div className="text-xs font-semibold text-emerald-400 flex items-center gap-1.5 uppercase tracking-wider">
            <Target className="w-3.5 h-3.5" /> Matched Keywords (
            {feedback?.matched_keywords?.length || 0})
          </div>
          <div className="flex flex-wrap gap-1">
            {feedback?.matched_keywords?.map((kw, idx) => (
              <span
                key={idx}
                className="text-[11px] px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-300 border border-emerald-500/20 font-mono"
              >
                {kw}
              </span>
            ))}
          </div>
        </div>

        {/* Missing Keywords */}
        <div className="bg-slate-900/60 rounded-xl p-3.5 border border-slate-700/50 space-y-2">
          <div className="text-xs font-semibold text-amber-400 flex items-center gap-1.5 uppercase tracking-wider">
            <AlertTriangle className="w-3.5 h-3.5" /> Missing Keywords (
            {feedback?.missing_keywords?.length || 0})
          </div>
          <div className="flex flex-wrap gap-1">
            {feedback?.missing_keywords?.length > 0 ? (
              feedback.missing_keywords.map((kw, idx) => (
                <span
                  key={idx}
                  className="text-[11px] px-2 py-0.5 rounded bg-amber-500/10 text-amber-300 border border-amber-500/20 font-mono"
                >
                  {kw}
                </span>
              ))
            ) : (
              <span className="text-xs text-slate-500 italic">
                None! All critical keywords present.
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Recommendation Footer & Action */}
      <div className="pt-2 flex flex-col sm:flex-row items-center justify-between gap-3 text-xs text-slate-400">
        <p className="flex items-center gap-1.5">
          <Award className="w-4 h-4 text-sky-400" />
          <span>{feedback?.recommendation || "Optimization complete."}</span>
        </p>
        {!isPassing && onRetry && (
          <button
            onClick={onRetry}
            className="px-4 py-2 bg-amber-600 hover:bg-amber-500 text-white font-semibold rounded-xl text-xs transition-all flex items-center gap-1.5"
          >
            <RefreshCw className="w-3.5 h-3.5" /> Auto-Revise (Cycle Loop)
          </button>
        )}
      </div>
    </div>
  );
}
