import React from "react";
import {
  MapPin,
  DollarSign,
  Clock,
  ExternalLink,
  FileText,
  MessageSquare,
  Sparkles,
  TrendingUp,
  CheckCircle2,
  ShieldCheck,
  Briefcase,
  Layers,
  Info,
} from "lucide-react";

function formatRelativeTime(dateString) {
  if (!dateString) return null;
  const date = new Date(dateString);
  if (isNaN(date.getTime())) return null;
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  if (diffMs < 0) return "Just now";
  const diffSecs = Math.floor(diffMs / 1000);
  const diffMins = Math.floor(diffSecs / 60);
  const diffHours = Math.floor(diffMins / 60);
  const diffDays = Math.floor(diffHours / 24);

  if (diffSecs < 60) return "Just now";
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays === 1) return "1d ago";
  if (diffDays < 7) return `${diffDays}d ago`;
  if (diffDays < 30) return `${Math.floor(diffDays / 7)}w ago`;
  return `${Math.floor(diffDays / 30)}mo ago`;
}

export function JobDetailPanel({
  match,
  searchMode = "cv_grounded",
  onTailorCV,
  onStartInterview,
  onOpenDiagnostics,
}) {
  if (!match) {
    return (
      <div
        data-testid="job-detail-empty"
        className="h-full flex flex-col items-center justify-center p-8 text-center space-y-3 bg-slate-800/40 border border-slate-700/60 rounded-2xl"
      >
        <Briefcase className="w-10 h-10 text-slate-500" />
        <p className="text-sm font-medium text-slate-300">
          Select an opportunity from the list to inspect full role details.
        </p>
      </div>
    );
  }

  const isGrounded =
    searchMode !== "unbiased" &&
    match.match_score !== null &&
    match.match_score !== undefined;
  const matchPct = isGrounded ? Math.round(match.match_score * 100) : null;
  const isHigh = match.probability_band === "high";
  const isModerate = match.probability_band === "moderate";
  const breakdown = match.breakdown || null;

  const factorBars = breakdown
    ? [
        {
          label: "Skills Alignment",
          weight: "25%",
          value: breakdown.skill_score ?? 0,
        },
        {
          label: "Semantic Top-3",
          weight: "25%",
          value: breakdown.semantic_score ?? 0,
        },
        {
          label: "Seniority Fit",
          weight: "15%",
          value: breakdown.seniority_score ?? 0,
        },
        {
          label: "Domain & Context",
          weight: "15%",
          value: breakdown.context_score ?? breakdown.archetype_score ?? 0,
        },
        {
          label: "Compensation Fit",
          weight: "10%",
          value: breakdown.comp_score ?? 1.0,
        },
        {
          label: "Posting Freshness",
          weight: "10%",
          value: breakdown.freshness_booster ?? 0,
        },
      ]
    : [];

  return (
    <div
      data-testid="job-detail-panel"
      className="h-full flex flex-col bg-slate-800/90 border border-slate-700/80 rounded-2xl overflow-hidden shadow-xl"
    >
      {/* Pinned Sticky Action Header */}
      <div className="shrink-0 p-4 sm:p-5 border-b border-slate-700/80 bg-slate-900/80 space-y-3">
        <div className="flex flex-wrap items-center gap-2">
          {isGrounded && (
            <span
              className={`text-xs font-extrabold px-3 py-1 rounded-xl shadow-sm flex items-center gap-1 ${
                isHigh
                  ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/40"
                  : isModerate
                    ? "bg-amber-500/20 text-amber-400 border border-amber-500/40"
                    : "bg-sky-500/20 text-sky-300 border border-sky-500/40"
              }`}
            >
              <TrendingUp className="w-3.5 h-3.5" />
              {matchPct}% Match
            </span>
          )}

          {match.workplace_type && (
            <span className="text-[11px] font-semibold uppercase px-2.5 py-0.5 rounded-lg bg-slate-800 text-slate-300 border border-slate-700">
              {match.workplace_type}
            </span>
          )}

          {match.visa_sponsorship === "yes" && (
            <span className="text-[11px] uppercase font-bold px-2.5 py-0.5 rounded-lg bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 flex items-center gap-1">
              <ShieldCheck className="w-3 h-3" />
              Visa Sponsored
            </span>
          )}

          {match.posted_at && (
            <span className="text-[11px] font-medium px-2.5 py-0.5 rounded-lg bg-slate-800 text-slate-400 border border-slate-700 flex items-center gap-1">
              <Clock className="w-3 h-3 text-slate-500" />
              {formatRelativeTime(match.posted_at)}
            </span>
          )}

          {isGrounded && breakdown?.g_prob < 1.0 && (
            <span className="text-[11px] font-semibold px-2.5 py-0.5 rounded-lg bg-amber-500/10 text-amber-300 border border-amber-500/30">
              Bayesian {Number(breakdown.g_prob).toFixed(2)}x Gate
            </span>
          )}
        </div>

        <div>
          <h2 className="text-xl font-bold text-white leading-snug">
            {match.title}
          </h2>
          <div className="flex flex-wrap items-center gap-2 text-xs text-slate-300 mt-1">
            <span className="font-semibold text-sky-300">
              {match.company_name}
            </span>
            <span>•</span>
            <span className="flex items-center gap-1 text-slate-400">
              <MapPin className="w-3.5 h-3.5 text-slate-500" />
              {match.location}
            </span>
            {match.salary_range && (
              <>
                <span>•</span>
                <span className="flex items-center gap-1 text-emerald-400 font-semibold">
                  <DollarSign className="w-3.5 h-3.5" />
                  {match.salary_range}
                </span>
              </>
            )}
          </div>
        </div>

        {/* Action CTA Bar */}
        <div className="flex flex-wrap items-center gap-2 pt-1">
          {match.apply_url && (
            <a
              href={match.apply_url}
              target="_blank"
              rel="noopener noreferrer"
              data-testid={`apply-link-${match.job_id}`}
              title="Open original job application in new tab"
              className="px-4 py-2 text-xs font-semibold rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white transition-all shadow-md shadow-emerald-600/20 flex items-center gap-1.5 cursor-pointer"
            >
              <ExternalLink className="w-3.5 h-3.5" />
              <span>Apply</span>
            </a>
          )}

          <button
            type="button"
            onClick={() => onTailorCV(match)}
            className="px-4 py-2 text-xs font-semibold rounded-xl bg-sky-600 hover:bg-sky-500 text-white transition-all shadow-md shadow-sky-600/20 flex items-center gap-1.5"
          >
            <FileText className="w-3.5 h-3.5" /> Tailor CV
          </button>

          <button
            type="button"
            onClick={() => onStartInterview(match)}
            className="px-4 py-2 text-xs font-semibold rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white transition-all shadow-md shadow-indigo-600/20 flex items-center gap-1.5"
          >
            <MessageSquare className="w-3.5 h-3.5" /> Mock Interview
          </button>

          {isGrounded && onOpenDiagnostics && (
            <button
              type="button"
              onClick={() => onOpenDiagnostics(match)}
              title="Decompose acceptance probability factors"
              className="px-3.5 py-2 text-xs font-semibold rounded-xl border border-sky-500/40 bg-sky-500/10 hover:bg-sky-500/20 text-sky-300 transition-all flex items-center gap-1.5"
            >
              <Sparkles className="w-3.5 h-3.5 text-sky-400" />
              Why this match?
            </button>
          )}
        </div>
      </div>

      {/* Single Continuous Scrollable Body (NO nested scrollbar!) */}
      <div
        data-testid="job-detail-scroll-body"
        className="flex-1 overflow-y-auto p-5 space-y-5"
      >
        {/* Grounded Mode Inline Match Intelligence */}
        {isGrounded && (
          <div className="space-y-4 bg-slate-900/70 border border-slate-700/60 rounded-xl p-4">
            <div className="flex items-center justify-between">
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-300 flex items-center gap-1.5">
                <Layers className="w-3.5 h-3.5 text-sky-400" />
                Match Breakdown & Skill Alignment
              </h3>
              {breakdown?.d_core !== undefined && breakdown.d_core < 1.0 && (
                <span className="text-[11px] text-amber-300 font-medium">
                  Core Multiplier: {Number(breakdown.d_core).toFixed(2)}x
                </span>
              )}
            </div>

            {/* 6-Factor Mini Progress Bars */}
            {factorBars.length > 0 && (
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                {factorBars.map((f) => {
                  const pct = Math.round(
                    Math.min(1, Math.max(0, f.value)) * 100,
                  );
                  return (
                    <div
                      key={f.label}
                      className="bg-slate-800/80 border border-slate-700/60 rounded-lg p-2.5 space-y-1.5"
                    >
                      <div className="flex items-center justify-between text-[11px]">
                        <span className="text-slate-400 truncate">
                          {f.label}
                        </span>
                        <span className="font-bold text-slate-200">{pct}%</span>
                      </div>
                      <div className="w-full h-1.5 bg-slate-950 rounded-full overflow-hidden">
                        <div
                          className={`h-full rounded-full ${
                            pct >= 75
                              ? "bg-emerald-500"
                              : pct >= 50
                                ? "bg-sky-500"
                                : "bg-amber-500"
                          }`}
                          style={{ width: `${pct}%` }}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            )}

            {/* Skills & Equivalents Pills */}
            {(match.matched_skills?.length > 0 ||
              match.missing_dealbreakers?.length > 0 ||
              match.phrasing_equivalents?.length > 0) && (
              <div className="flex flex-wrap items-center gap-1.5 pt-1">
                {match.matched_skills?.map((skill, sIdx) => (
                  <span
                    key={sIdx}
                    className="text-[11px] px-2.5 py-0.5 rounded-full bg-emerald-500/10 text-emerald-300 border border-emerald-500/20 flex items-center gap-1"
                  >
                    <CheckCircle2 className="w-2.5 h-2.5" />
                    {skill}
                  </span>
                ))}

                {match.missing_dealbreakers?.map((miss, mIdx) => (
                  <span
                    key={mIdx}
                    className="text-[11px] px-2.5 py-0.5 rounded-full bg-rose-500/10 text-rose-300 border border-rose-500/20"
                  >
                    Missing: {miss}
                  </span>
                ))}

                {match.phrasing_equivalents?.map((eq, eqIdx) => (
                  <span
                    key={eqIdx}
                    className="text-[11px] px-2 py-0.5 rounded-full bg-indigo-500/10 text-indigo-300 border border-indigo-500/20"
                  >
                    Equiv: {eq.candidate_has} →{" "}
                    {eq.job_requested || eq.job_term}
                  </span>
                ))}
              </div>
            )}

            {/* Gate Notes */}
            {match.gate_notes?.length > 0 && (
              <div className="flex flex-wrap items-center gap-2 text-[11px] text-slate-400 pt-1 border-t border-slate-800">
                <Info className="w-3.5 h-3.5 text-slate-500 shrink-0" />
                <span>{match.gate_notes.join(" • ")}</span>
              </div>
            )}
          </div>
        )}

        {/* Full Job Description: Natural document flow without separate nested scrollbox */}
        <div className="space-y-3">
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400">
            Role Description & Requirements
          </h3>
          {match.raw_description ? (
            <div
              data-testid="job-detail-raw-description"
              className="text-xs text-slate-200 leading-relaxed whitespace-pre-line bg-slate-900/60 border border-slate-800/80 rounded-xl p-5 shadow-inner"
            >
              {match.raw_description}
            </div>
          ) : (
            <div className="text-xs text-slate-400 italic bg-slate-900/40 border border-slate-800 rounded-xl p-4">
              Full job description text is available on the company application
              page.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
