import React from "react";
import { ShieldCheck, CheckCircle2, AlertTriangle, UserCheck, HelpCircle } from "lucide-react";

export function JobProvenanceBadge({ job }) {
  if (!job) return null;

  const dataOrigin = job.data_origin || "legacy";
  const confidence = job.source_confidence || "medium";
  const verification = job.verification;

  return (
    <div className="flex flex-wrap items-center gap-1.5">
      {/* Primary Provenance Source Badge */}
      {dataOrigin === "manual" ? (
        <span
          data-testid="badge-manual"
          className="text-[10px] font-semibold px-2 py-0.5 rounded bg-purple-500/10 text-purple-300 border border-purple-500/30 flex items-center gap-1"
        >
          <UserCheck className="w-3 h-3 text-purple-400" /> Manual Import
        </span>
      ) : dataOrigin === "demo" ? (
        <span
          data-testid="badge-demo"
          className="text-[10px] font-semibold px-2 py-0.5 rounded bg-slate-700/60 text-slate-300 border border-slate-600/50 flex items-center gap-1"
        >
          <HelpCircle className="w-3 h-3 text-slate-400" /> Demo Role
        </span>
      ) : confidence === "high" || dataOrigin === "live" ? (
        <span
          data-testid="badge-verified-ats"
          className="text-[10px] font-semibold px-2 py-0.5 rounded bg-sky-500/10 text-sky-300 border border-sky-500/30 flex items-center gap-1"
        >
          <ShieldCheck className="w-3 h-3 text-sky-400" /> Verified Careers Site
        </span>
      ) : (
        <span
          data-testid="badge-aggregator"
          className="text-[10px] font-semibold px-2 py-0.5 rounded bg-amber-500/10 text-amber-300 border border-amber-500/30 flex items-center gap-1"
        >
          <AlertTriangle className="w-3 h-3 text-amber-400" /> Aggregator / Unverified
        </span>
      )}

      {/* Secondary Verification Badge */}
      {verification?.status === "verified" && (
        <span
          data-testid="badge-cross-checked-verified"
          className="text-[10px] font-semibold px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-300 border border-emerald-500/30 flex items-center gap-1"
        >
          <CheckCircle2 className="w-3 h-3 text-emerald-400" /> Cross-Checked
        </span>
      )}

      {verification?.status === "discrepancy" && (
        <span
          data-testid="badge-cross-checked-discrepancy"
          className="text-[10px] font-semibold px-2 py-0.5 rounded bg-rose-500/10 text-rose-300 border border-rose-500/30 flex items-center gap-1"
          title="Differences detected between ATS and secondary aggregator data"
        >
          <AlertTriangle className="w-3 h-3 text-rose-400" /> Discrepancy Found
        </span>
      )}
    </div>
  );
}
