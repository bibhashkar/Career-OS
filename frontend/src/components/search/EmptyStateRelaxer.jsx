import React from "react";
import { AlertCircle, Zap, RefreshCw, SlidersHorizontal } from "lucide-react";

export function EmptyStateRelaxer({
  diagnostics,
  onApplyRelaxation,
  onResetFilters,
}) {
  const primary = diagnostics?.primary_bottleneck;
  const secondary = (diagnostics?.all_relaxations || []).filter(
    (r) => r.restrictive_facet !== primary?.restrictive_facet
  );

  return (
    <div className="flex flex-col items-center justify-center py-12 px-6 bg-neutral-900/60 border border-neutral-800 rounded-2xl text-center max-w-2xl mx-auto my-6 animate-fadeIn">
      <div className="w-12 h-12 rounded-full bg-amber-500/10 border border-amber-500/20 flex items-center justify-center text-amber-400 mb-4">
        <AlertCircle className="w-6 h-6" />
      </div>

      <h3 className="text-base font-semibold text-neutral-100 mb-1">
        No Exact Matches for Current Criteria
      </h3>
      <p className="text-xs text-neutral-400 max-w-md mb-6 leading-relaxed">
        {primary?.message ||
          "Your current combination of facet filters, keywords, and work authorization criteria yielded zero listings."}
      </p>

      {/* Primary One-Click Relaxation Action */}
      {primary && (
        <div className="flex flex-col items-center gap-2 mb-6 w-full max-w-sm">
          <button
            type="button"
            onClick={() => onApplyRelaxation(primary.relaxed_patch)}
            className="flex items-center justify-center gap-2 w-full px-4 py-2.5 bg-gradient-to-r from-amber-600 to-amber-500 hover:from-amber-500 hover:to-amber-400 text-white font-medium text-xs rounded-xl shadow-lg shadow-amber-500/10 transition-all hover:scale-[1.01]"
          >
            <Zap className="w-4 h-4 fill-white" />
            <span>{primary.action_label}</span>
          </button>
        </div>
      )}

      {/* Secondary Alternative Relaxations */}
      {secondary.length > 0 && (
        <div className="flex flex-col items-center gap-2 mb-6 w-full">
          <span className="text-[11px] font-medium text-neutral-500 uppercase tracking-wider">
            Alternative Relaxations:
          </span>
          <div className="flex flex-wrap items-center justify-center gap-1.5">
            {secondary.map((rel, idx) => (
              <button
                key={`${rel.restrictive_facet}-${idx}`}
                type="button"
                onClick={() => onApplyRelaxation(rel.relaxed_patch)}
                className="px-2.5 py-1 bg-neutral-800 hover:bg-neutral-700/80 border border-neutral-700/80 text-neutral-300 hover:text-white text-xs rounded-lg transition-colors"
              >
                {rel.action_label}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Fallback Reset All Filters */}
      <button
        type="button"
        onClick={onResetFilters}
        className="flex items-center gap-1.5 text-xs text-neutral-400 hover:text-neutral-200 transition-colors underline underline-offset-4"
      >
        <RefreshCw className="w-3.5 h-3.5" />
        <span>Reset All Filters to Broadest Scope</span>
      </button>
    </div>
  );
}

