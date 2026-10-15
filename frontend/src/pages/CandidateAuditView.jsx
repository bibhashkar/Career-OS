import React, { useState, useEffect } from "react";
import {
  Award,
  Trophy,
  Star,
  BarChart3,
  GitBranch,
  ArrowRight,
  TrendingUp,
  Sparkles,
  Layers,
  CheckCircle2,
  AlertCircle,
  RefreshCw,
} from "lucide-react";
import { getCandidateAudit } from "../services/api";

export function CandidateAuditView({ onNavigateBack }) {
  const [audit, setAudit] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadAudit();
  }, []);

  async function loadAudit() {
    try {
      setLoading(true);
      setError(null);
      const res = await getCandidateAudit();
      setAudit(res);
    } catch (err) {
      console.error("Failed to load candidate audit:", err);
      setError("Unable to compute holistic candidate audit. Please retry.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pb-6 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-xs font-bold uppercase tracking-wider text-sky-400">
              Tier 0 Candidate Intelligence
            </span>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-slate-800 text-slate-400 border border-slate-700">
              360° Holistic Audit
            </span>
          </div>
          <h1 className="text-2xl font-extrabold text-white mt-1">
            Candidate Career Health & Market Standing
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Holistic analysis of your master career blocks, pedigree signals, and hiring market competitiveness.
          </p>
        </div>

        <button
          onClick={loadAudit}
          disabled={loading}
          className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition-all"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
          Recalculate Audit
        </button>
      </div>

      {loading && (
        <div className="py-20 text-center text-slate-400 space-y-3">
          <Sparkles className="w-10 h-10 text-sky-400 animate-spin mx-auto" />
          <p className="text-base font-medium text-slate-200">
            Synthesizing 360° Candidate Assessment...
          </p>
          <p className="text-xs text-slate-500">
            Evaluating T-shaped radar, STAR quantification ratios, and market percentile...
          </p>
        </div>
      )}

      {error && (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-400 text-sm">
          {error}
        </div>
      )}

      {audit && !loading && (
        <>
          {/* Top Metric Cards Grid */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
            {/* 1. Market Percentile */}
            <div className="p-5 rounded-2xl bg-gradient-to-tr from-slate-850 to-slate-800 border border-slate-750 shadow-lg relative overflow-hidden">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold uppercase tracking-wider text-slate-400">
                  Market Standing
                </span>
                <TrendingUp className="w-4 h-4 text-emerald-400" />
              </div>
              <div className="mt-4 flex items-baseline gap-2">
                <span className="text-4xl font-extrabold text-white">
                  Top {100 - audit.market_percentile}%
                </span>
                <span className="text-xs text-slate-400 font-mono">
                  ({audit.market_percentile}th percentile)
                </span>
              </div>
              <p className="text-xs text-slate-400 mt-2">
                Benchmarked against active engineering profiles in your primary target role.
              </p>
            </div>

            {/* 2. Overall Career Health */}
            <div className="p-5 rounded-2xl bg-gradient-to-tr from-slate-850 to-slate-800 border border-slate-750 shadow-lg relative overflow-hidden">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold uppercase tracking-wider text-slate-400">
                  Career Health Score
                </span>
                <Sparkles className="w-4 h-4 text-sky-400" />
              </div>
              <div className="mt-4 flex items-baseline gap-2">
                <span className="text-4xl font-extrabold text-sky-400">
                  {audit.overall_health_score}
                </span>
                <span className="text-xs text-slate-400">/ 100</span>
              </div>
              <p className="text-xs text-slate-400 mt-2">
                Composite of quantified proof points, pedigree, and skill stack breadth.
              </p>
            </div>

            {/* 3. STAR Quantified Impact Ratio */}
            <div className="p-5 rounded-2xl bg-gradient-to-tr from-slate-850 to-slate-800 border border-slate-750 shadow-lg relative overflow-hidden">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold uppercase tracking-wider text-slate-400">
                  STAR Metric Ratio
                </span>
                <BarChart3 className="w-4 h-4 text-amber-400" />
              </div>
              <div className="mt-4 flex items-baseline gap-2">
                <span className="text-4xl font-extrabold text-amber-300">
                  {Math.round(audit.quantified_impact_ratio * 100)}%
                </span>
                <span className="text-xs text-slate-400 font-mono">
                  ({audit.quantified_blocks_count} of {audit.total_blocks_count} bullets)
                </span>
              </div>
              {/* Progress bar */}
              <div className="w-full bg-slate-700/60 rounded-full h-2 mt-3 overflow-hidden">
                <div
                  className="bg-amber-400 h-2 rounded-full transition-all duration-500"
                  style={{ width: `${Math.round(audit.quantified_impact_ratio * 100)}%` }}
                />
              </div>
              <p className="text-xs text-slate-400 mt-2">
                {audit.quantified_impact_ratio >= 0.6
                  ? "High-signal quantified outcomes."
                  : "Needs more numerical impact metrics."}
              </p>
            </div>
          </div>

          {/* Distinction Badges Showcase */}
          <div className="p-6 rounded-2xl bg-slate-850 border border-slate-800 shadow-md">
            <div className="flex items-center gap-2 mb-4">
              <Award className="w-4 h-4 text-sky-400" />
              <h3 className="text-sm font-bold uppercase tracking-wider text-slate-200">
                Verified Distinction Badges
              </h3>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              {audit.distinction_badges.map((b) => (
                <div
                  key={b.code}
                  className={`p-4 rounded-xl border transition-all ${
                    b.verified
                      ? "bg-slate-800/80 border-slate-700/80 text-white shadow-sm"
                      : "bg-slate-900/40 border-slate-800/50 text-slate-500 opacity-60"
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div
                      className={`p-2 rounded-lg ${
                        b.verified
                          ? "bg-sky-500/10 text-sky-400"
                          : "bg-slate-800 text-slate-600"
                      }`}
                    >
                      {b.code === "hackathon_winner" && <Trophy className="w-4 h-4" />}
                      {b.code === "tier1_pedigree" && <Star className="w-4 h-4" />}
                      {b.code === "quantified_metrics" && <BarChart3 className="w-4 h-4" />}
                      {b.code === "open_source_author" && <GitBranch className="w-4 h-4" />}
                    </div>
                    {b.verified ? (
                      <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 flex items-center gap-1">
                        <CheckCircle2 className="w-2.5 h-2.5" /> Verified
                      </span>
                    ) : (
                      <span className="text-[10px] text-slate-600 font-mono">
                        Not detected
                      </span>
                    )}
                  </div>
                  <h4 className="text-xs font-bold mt-2.5">{b.title}</h4>
                  <p className="text-[11px] text-slate-400 mt-1 leading-relaxed">
                    {b.description}
                  </p>
                </div>
              ))}
            </div>
          </div>

          {/* T-Shaped Competency Radar Breakdown & Career Ceiling */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Left: T-Shaped Competency Radar */}
            <div className="p-6 rounded-2xl bg-slate-850 border border-slate-800 shadow-md flex flex-col justify-between">
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <Layers className="w-4 h-4 text-indigo-400" />
                  <h3 className="text-sm font-bold uppercase tracking-wider text-slate-200">
                    T-Shaped Competency Depth vs Breadth
                  </h3>
                </div>
                <p className="text-xs text-slate-400 mb-5">
                  Visualizes specialization depth in primary systems vs adjacent cloud & AI tools.
                </p>

                <div className="space-y-4">
                  {audit.t_shaped_radar.map((domain) => (
                    <div key={domain.category} className="space-y-1.5">
                      <div className="flex items-center justify-between text-xs">
                        <span className="font-semibold text-slate-200">
                          {domain.category}
                        </span>
                        <span className="text-slate-400 font-mono">
                          {domain.score}% ({domain.skill_count} skills)
                        </span>
                      </div>
                      <div className="w-full bg-slate-800 rounded-full h-2 overflow-hidden">
                        <div
                          className="bg-gradient-to-r from-sky-500 to-indigo-500 h-2 rounded-full transition-all duration-500"
                          style={{ width: `${domain.score}%` }}
                        />
                      </div>
                      {domain.top_skills?.length > 0 && (
                        <div className="flex flex-wrap gap-1 pt-0.5">
                          {domain.top_skills.map((s) => (
                            <span
                              key={s}
                              className="text-[10px] px-2 py-0.5 rounded bg-slate-800/80 text-slate-300 border border-slate-700/60"
                            >
                              {s}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Right: Career Ceiling Diagnosis */}
            <div className="p-6 rounded-2xl bg-slate-850 border border-slate-800 shadow-md flex flex-col justify-between">
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <AlertCircle className="w-4 h-4 text-amber-400" />
                  <h3 className="text-sm font-bold uppercase tracking-wider text-slate-200">
                    Career Ceiling & Promotion Diagnostics
                  </h3>
                </div>
                <p className="text-xs text-slate-400 mb-5">
                  AI analysis identifying what is required to advance to the next seniority tier.
                </p>

                <div className="p-4 rounded-xl bg-slate-800/70 border border-slate-700/70 mb-4">
                  <div className="flex items-center justify-between text-xs pb-3 border-b border-slate-700/60">
                    <span className="text-slate-400">Current Calibrated Level:</span>
                    <span className="font-bold text-white">
                      {audit.career_ceiling_diagnosis.current_tier}
                    </span>
                  </div>
                  <div className="flex items-center justify-between text-xs pt-3">
                    <span className="text-slate-400">Target Next Tier:</span>
                    <span className="font-bold text-sky-400 flex items-center gap-1">
                      {audit.career_ceiling_diagnosis.next_target_tier}
                      <ArrowRight className="w-3 h-3 text-sky-400" />
                    </span>
                  </div>
                </div>

                <div className="space-y-3">
                  <div className="p-3.5 rounded-xl bg-amber-500/10 border border-amber-500/20">
                    <span className="text-[11px] font-bold uppercase tracking-wider text-amber-400 block mb-1">
                      Primary Advancement Barrier
                    </span>
                    <p className="text-xs font-semibold text-slate-200">
                      {audit.career_ceiling_diagnosis.primary_barrier}
                    </p>
                  </div>

                  <div className="p-3.5 rounded-xl bg-slate-800/60 border border-slate-700/60">
                    <span className="text-[11px] font-bold uppercase tracking-wider text-sky-400 block mb-1">
                      Actionable Recommendation
                    </span>
                    <p className="text-xs text-slate-300 leading-relaxed">
                      {audit.career_ceiling_diagnosis.recommended_action}
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}

export default CandidateAuditView;
