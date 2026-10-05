import React, { useState, useEffect } from "react";
import { ArrowLeft, Loader2, RefreshCw, AlertCircle, FileCheck } from "lucide-react";
import { generateCV } from "../services/api";
import { ATSCard } from "../components/ATSCard";
import { CVPreview } from "../components/CVPreview";

export function CVTailorView({ job, onBack, onStartInterview }) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [data, setData] = useState(null);

  const runTailoring = async () => {
    if (!job?.id) return;
    setLoading(true);
    setError(null);
    try {
      const skills = job?.ats_requirements?.required_skills || [];
      const res = await generateCV(
        job.id,
        skills,
        job.title,
        job.company_name
      );
      setData(res);
    } catch (err) {
      setError(
        err.response?.data?.detail || "Failed to generate tailored CV."
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (job?.id) {
      runTailoring();
    }
  }, [job]);

  if (!job) {
    return (
      <div className="max-w-2xl mx-auto px-4 py-20 text-center space-y-6">
        <div className="w-16 h-16 rounded-2xl bg-slate-800 border border-slate-700 mx-auto flex items-center justify-center text-slate-400 shadow-xl">
          <FileCheck className="w-8 h-8 text-sky-400" />
        </div>
        <div className="space-y-2">
          <h2 className="text-xl font-bold text-white">No Target Job Selected</h2>
          <p className="text-sm text-slate-400 max-w-md mx-auto">
            Select a target position from the Discovery dashboard to run the multi-agent
            tailoring loop, retrieve matching career blocks, and optimize ATS score.
          </p>
        </div>
        <button
          onClick={onBack}
          className="px-5 py-2.5 bg-sky-600 hover:bg-sky-500 text-white text-xs font-semibold rounded-xl shadow-lg shadow-sky-600/20 transition-all inline-flex items-center gap-2"
        >
          <ArrowLeft className="w-4 h-4" /> Go to Job Discovery
        </button>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto px-4 py-8 space-y-6">
      {/* Navigation & Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <button
          onClick={onBack}
          className="inline-flex items-center gap-2 text-xs font-medium text-slate-400 hover:text-white transition-colors"
        >
          <ArrowLeft className="w-4 h-4" /> Back to Dashboard
        </button>

        {data && !loading && (
          <div className="flex items-center gap-3">
            <button
              onClick={runTailoring}
              className="px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 border border-slate-700 text-xs font-medium text-slate-200 transition-colors flex items-center gap-1.5"
            >
              <RefreshCw className="w-3.5 h-3.5" /> Re-run Agent Loop
            </button>
            <button
              onClick={() => onStartInterview(job)}
              className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-xs font-semibold text-white shadow-md shadow-indigo-600/20 transition-all flex items-center gap-1.5"
            >
              <FileCheck className="w-3.5 h-3.5" /> Practice Interview for this Role
            </button>
          </div>
        )}
      </div>

      {/* Target Role Context Banner */}
      <div className="bg-slate-800/60 border border-slate-700/60 rounded-xl p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-2">
        <div>
          <span className="text-[11px] font-bold uppercase tracking-wider text-sky-400">
            Targeting Role
          </span>
          <h2 className="text-base font-bold text-white">
            {job?.title} <span className="text-slate-400 font-normal">at</span> {job?.company_name}
          </h2>
        </div>
        <div className="text-xs text-slate-400">
          Location: <span className="text-slate-200">{job?.location || "Remote"}</span>
        </div>
      </div>

      {/* Loading State */}
      {loading && (
        <div className="flex flex-col items-center justify-center py-20 space-y-4">
          <Loader2 className="w-10 h-10 text-sky-400 animate-spin" />
          <div className="text-center space-y-1">
            <p className="text-sm font-medium text-white">
              Tailor & ATS Agents collaborating...
            </p>
            <p className="text-xs text-slate-400">
              Querying pgvector embeddings, tailoring achievement blocks, and checking ATS loop threshold.
            </p>
          </div>
        </div>
      )}

      {/* Error State */}
      {error && !loading && (
        <div className="p-5 rounded-2xl bg-rose-500/10 border border-rose-500/30 text-rose-300 space-y-3">
          <div className="flex items-center gap-3">
            <AlertCircle className="w-5 h-5 text-rose-400" />
            <span className="text-sm font-medium">{error}</span>
          </div>
          <button
            onClick={runTailoring}
            className="text-xs px-4 py-2 bg-rose-500/20 hover:bg-rose-500/30 text-rose-200 rounded-lg transition-colors"
          >
            Retry Tailoring
          </button>
        </div>
      )}

      {/* Results View: ATS Card + CV Preview */}
      {data && !loading && (
        <div className="space-y-6 animate-fadeIn">
          {/* ATS cyclic score card */}
          <ATSCard
            score={data.ats_score}
            feedback={data.ats_feedback}
            revisionCount={data.revision_count}
            onRetry={runTailoring}
          />

          {/* Rendered CV Draft */}
          <CVPreview draft={data.cv_draft} />
        </div>
      )}
    </div>
  );
}
