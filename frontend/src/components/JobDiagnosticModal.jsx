import React, { useState, useEffect } from "react";
import {
  X,
  ShieldCheck,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  Repeat,
  Sparkles,
  ArrowRight,
  TrendingUp,
} from "lucide-react";
import { getJobDiagnostics } from "../services/api";

export function JobDiagnosticModal({
  jobId,
  jobTitle,
  companyName,
  personaId,
  onClose,
  onTailorCV,
  onStartInterview,
}) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function loadDiagnostics() {
      try {
        setLoading(true);
        setError(null);
        const res = await getJobDiagnostics(jobId, personaId);
        setData(res);
      } catch (err) {
        console.error("Failed to load job diagnostics:", err);
        setError("Unable to compute diagnostic drilldown. Please retry.");
      } finally {
        setLoading(false);
      }
    }
    if (jobId) {
      loadDiagnostics();
    }
  }, [jobId, personaId]);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-2xl max-h-[90vh] overflow-hidden flex flex-col shadow-2xl">
        {/* Header */}
        <div className="p-5 border-b border-slate-800 flex items-center justify-between bg-slate-850">
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold uppercase tracking-wider text-sky-400">
                Tier 1 Match Diagnostics
              </span>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-slate-800 text-slate-400 border border-slate-700">
                ADR-002 Engine
              </span>
            </div>
            <h2 className="text-base font-bold text-white mt-1">
              {jobTitle} • <span className="text-slate-400">{companyName}</span>
            </h2>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content Body */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {loading && (
            <div className="py-12 text-center text-slate-400 space-y-2">
              <Sparkles className="w-8 h-8 text-sky-400 animate-spin mx-auto" />
              <p className="text-sm">Decomposing multi-factor acceptance probability...</p>
            </div>
          )}

          {error && (
            <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-400 text-sm">
              {error}
            </div>
          )}

          {data && !loading && (
            <>
              {/* Score Gauge & Acceptance Probability */}
              <div className="flex flex-col sm:flex-row items-center justify-between p-4 rounded-2xl bg-gradient-to-r from-slate-850 to-slate-800 border border-slate-750 gap-4">
                <div className="flex items-center gap-4">
                  <div
                    className={`w-16 h-16 rounded-2xl flex flex-col items-center justify-center font-extrabold text-xl shadow-lg ${
                      data.probability_band === "high"
                        ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30"
                        : data.probability_band === "moderate"
                        ? "bg-amber-500/20 text-amber-400 border border-amber-500/30"
                        : "bg-rose-500/20 text-rose-400 border border-rose-500/30"
                    }`}
                  >
                    <span>{Math.round(data.match_score * 100)}%</span>
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-xs uppercase font-bold text-slate-400">
                        Acceptance Probability
                      </span>
                      <span
                        className={`text-[10px] font-bold px-2 py-0.5 rounded-full uppercase ${
                          data.probability_band === "high"
                            ? "bg-emerald-500/20 text-emerald-300"
                            : data.probability_band === "moderate"
                            ? "bg-amber-500/20 text-amber-300"
                            : "bg-rose-500/20 text-rose-300"
                        }`}
                      >
                        {data.probability_band} probability
                      </span>
                    </div>
                    <p className="text-xs text-slate-300 mt-1 max-w-sm">
                      {data.next_step_action}
                    </p>
                  </div>
                </div>

                <div className="text-right text-xs text-slate-400 border-t sm:border-t-0 sm:border-l border-slate-700/80 pt-2 sm:pt-0 sm:pl-4">
                  <div className="flex items-center gap-1.5 justify-end">
                    <TrendingUp className="w-3.5 h-3.5 text-sky-400" />
                    <span>Hiring Calibrated</span>
                  </div>
                  <p className="text-[11px] text-slate-500 mt-0.5">
                    Includes prestige & recency
                  </p>
                </div>
              </div>

              {/* Hard Gate & Visa Status Pill */}
              <div className="p-3.5 rounded-xl bg-slate-800/60 border border-slate-700/60 flex items-start gap-3">
                {data.hard_gate_pass ? (
                  <ShieldCheck className="w-5 h-5 text-emerald-400 shrink-0 mt-0.5" />
                ) : (
                  <AlertTriangle className="w-5 h-5 text-rose-400 shrink-0 mt-0.5" />
                )}
                <div>
                  <h4 className="text-xs font-bold text-slate-200">
                    {data.hard_gate_pass
                      ? "Work Authorization & Modality Passed"
                      : "Hard Gate Disqualification"}
                  </h4>
                  <p className="text-xs text-slate-400 mt-0.5">
                    {data.visa_status_message}
                  </p>
                </div>
              </div>

              {/* Matched Competencies Chips */}
              <div>
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-2 flex items-center gap-1.5">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                  Verified Skills in Your Profile ({data.matched_skills.length})
                </h4>
                <div className="flex flex-wrap gap-1.5">
                  {data.matched_skills.map((skill, idx) => (
                    <span
                      key={idx}
                      className="text-xs font-medium px-2.5 py-1 rounded-lg bg-emerald-500/10 text-emerald-300 border border-emerald-500/20"
                    >
                      {skill}
                    </span>
                  ))}
                  {data.matched_skills.length === 0 && (
                    <span className="text-xs text-slate-500 italic">
                      No exact keyword matches found in current persona.
                    </span>
                  )}
                </div>
              </div>

              {/* Missing Dealbreaker Skills */}
              {data.missing_dealbreakers.length > 0 && (
                <div>
                  <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-2 flex items-center gap-1.5">
                    <XCircle className="w-3.5 h-3.5 text-rose-400" />
                    Missing Required Tech Stack ({data.missing_dealbreakers.length})
                  </h4>
                  <div className="flex flex-wrap gap-1.5">
                    {data.missing_dealbreakers.map((skill, idx) => (
                      <span
                        key={idx}
                        className="text-xs font-medium px-2.5 py-1 rounded-lg bg-rose-500/10 text-rose-300 border border-rose-500/20"
                      >
                        Missing: {skill}
                      </span>
                    ))}
                  </div>
                  <p className="text-[11px] text-slate-500 mt-1.5">
                    These technologies are non-negotiable hard criteria in the ATS job description.
                  </p>
                </div>
              )}

              {/* Phrasing & Hidden Semantic Equivalents */}
              {data.phrasing_equivalents.length > 0 && (
                <div className="p-3.5 rounded-xl bg-indigo-500/10 border border-indigo-500/20">
                  <h4 className="text-xs font-bold uppercase tracking-wider text-indigo-300 mb-2 flex items-center gap-1.5">
                    <Repeat className="w-3.5 h-3.5 text-indigo-400" />
                    Phrasing Equivalents Recognized
                  </h4>
                  <div className="space-y-1.5">
                    {data.phrasing_equivalents.map((eq, idx) => (
                      <div
                        key={idx}
                        className="text-xs text-slate-300 flex items-center gap-2"
                      >
                        <span className="font-semibold text-white">
                          You have {eq.candidate_has}
                        </span>
                        <ArrowRight className="w-3 h-3 text-slate-500" />
                        <span className="text-indigo-200">
                          Job asks for {eq.job_term} (Treated as equivalent match)
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </>
          )}
        </div>

        {/* Footer Actions */}
        <div className="p-4 border-t border-slate-800 bg-slate-850 flex items-center justify-between">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-xl text-xs font-medium text-slate-400 hover:text-white transition-colors"
          >
            Close
          </button>
          <div className="flex items-center gap-2">
            {onStartInterview && (
              <button
                onClick={() => {
                  onClose();
                  onStartInterview();
                }}
                className="px-3.5 py-2 rounded-xl text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition-colors"
              >
                Mock Interview
              </button>
            )}
            {onTailorCV && (
              <button
                onClick={() => {
                  onClose();
                  onTailorCV();
                }}
                className="px-4 py-2 rounded-xl text-xs font-semibold bg-sky-500 hover:bg-sky-400 text-white shadow-md shadow-sky-500/20 transition-all flex items-center gap-1.5"
              >
                <Sparkles className="w-3.5 h-3.5" /> Tailor CV Now
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default JobDiagnosticModal;

