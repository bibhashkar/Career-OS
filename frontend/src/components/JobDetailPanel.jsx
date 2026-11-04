import React, { useState, useMemo } from "react";
import {
  MapPin,
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
  ListOrdered,
  ChevronDown,
  ChevronRight,
  Target,
  Gift,
  Copy,
  CheckCheck,
  AlertTriangle,
} from "lucide-react";
import {
  parseJobDescription,
  tokenizeHighlightedText,
} from "../utils/jobDescriptionParser";
import { formatWorkplaceType } from "../utils/statusBadges";
import { formatRelativeTime } from "../utils/dateUtils";

/**
 * Renders text with inline keyword and skill highlight spans.
 */
function renderHighlightedSpans(text, matchedSkills = [], missingSkills = []) {
  const segments = tokenizeHighlightedText(text, matchedSkills, missingSkills);
  return segments.map((seg, idx) => {
    if (seg.type === "matched") {
      return (
        <mark
          key={idx}
          className="bg-emerald-500/20 text-emerald-300 font-semibold px-1 py-0.5 rounded border border-emerald-500/30 font-sans"
        >
          {seg.text}
        </mark>
      );
    }
    if (seg.type === "missing") {
      return (
        <mark
          key={idx}
          className="bg-amber-500/20 text-amber-300 font-semibold px-1 py-0.5 rounded border border-amber-500/30 font-sans"
        >
          {seg.text}
        </mark>
      );
    }
    if (seg.type === "yoe") {
      return (
        <span
          key={idx}
          className="text-sky-300 font-bold bg-sky-950/80 px-1 py-0.5 rounded border border-sky-800/50 font-sans"
        >
          {seg.text}
        </span>
      );
    }
    return <React.Fragment key={idx}>{seg.text}</React.Fragment>;
  });
}

export function JobDetailPanel({
  match,
  searchMode = "cv_grounded",
  profileReady = true,
  onOpenProfileModal,
  onTailorCV,
  onStartInterview,
  onOpenDiagnostics,
}) {
  const [viewMode, setViewMode] = useState("smart"); // "smart" | "formatted" | "raw"
  const [expandedBoilerplates, setExpandedBoilerplates] = useState({});
  const [copiedRaw, setCopiedRaw] = useState(false);
  const [selectedPostingIndex, setSelectedPostingIndex] = useState(0);
  const [showLocationMenu, setShowLocationMenu] = useState(false);

  React.useEffect(() => {
    setSelectedPostingIndex(0);
    setShowLocationMenu(false);
  }, [match?.job_id]);

  const locationPostings = match?.location_postings || [];
  const hasMultipleLocations = locationPostings.length > 1;
  const activePosting = hasMultipleLocations
    ? locationPostings[selectedPostingIndex] || locationPostings[0]
    : null;
  const activeApplyUrl = activePosting?.apply_url || match?.apply_url;

  const parsed = useMemo(
    () => parseJobDescription(match?.raw_description || ""),
    [match?.raw_description],
  );

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
    profileReady &&
    match.match_score !== null &&
    match.match_score !== undefined;
  const matchPct = isGrounded ? Math.round(match.match_score * 100) : null;
  const isHigh = match.probability_band === "high";
  const isModerate = match.probability_band === "moderate";
  const breakdown = match.breakdown || null;
  const factorStatuses = breakdown?.factor_status || {};

  const factorBars = breakdown
    ? [
        {
          label: "Skills Alignment",
          weight: "25%",
          value: breakdown.skill_score ?? breakdown.s_skills ?? 0,
          status: factorStatuses.skills,
        },
        {
          label: "Semantic Top-3",
          weight: "25%",
          value: breakdown.semantic_score ?? breakdown.s_semantic ?? 0,
          status: factorStatuses.semantic,
        },
        {
          label: "Seniority Fit",
          weight: "15%",
          value: breakdown.seniority_score ?? breakdown.s_seniority ?? 0,
          status: factorStatuses.seniority,
        },
        {
          label: "Domain & Context",
          weight: "15%",
          value: breakdown.context_score ?? breakdown.archetype_score ?? breakdown.s_domain ?? 0,
          status: factorStatuses.domain,
        },
        {
          label: "Compensation Fit",
          weight: "10%",
          value: breakdown.comp_score ?? breakdown.s_comp ?? 1.0,
          status: factorStatuses.comp,
        },
        {
          label: "Posting Freshness",
          weight: "10%",
          value: breakdown.freshness_booster ?? 0,
          status: factorStatuses.freshness,
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
        {/* Role Title at the Very Top */}
        <div>
          <h2 className="text-xl font-bold text-white leading-snug">
            {match.title}
          </h2>
          <div className="flex flex-wrap items-center gap-2 text-xs text-slate-300 mt-1.5">
            <span className="font-semibold text-sky-300">
              {match.company_name}
            </span>
            <span className="text-slate-500">•</span>
            {hasMultipleLocations ? (
              <span className="flex items-center gap-1 text-slate-300">
                <MapPin className="w-3.5 h-3.5 text-sky-400 shrink-0" />
                <span className="font-semibold text-sky-300">{locationPostings.length} Locations</span>
                <span className="text-slate-400">({activePosting?.location || match.location})</span>
              </span>
            ) : (
              <span className="flex items-center gap-1 text-slate-400">
                <MapPin className="w-3.5 h-3.5 text-slate-500 shrink-0" />
                {match.location}
              </span>
            )}
            {match.workplace_type && (
              <>
                <span className="text-slate-500">•</span>
                <span className="text-[11px] font-semibold px-2 py-0.5 rounded-md bg-slate-800 text-slate-300 border border-slate-700">
                  {formatWorkplaceType(match.workplace_type)}
                </span>
              </>
            )}
            {match.posted_at && (
              <span className="text-[11px] font-medium text-slate-400 flex items-center gap-1">
                <Clock className="w-3 h-3 text-slate-500 shrink-0" />
                {formatRelativeTime(match.posted_at)}
              </span>
            )}
            {(activePosting?.salary_range || match.salary_range) && (
              <>
                <span className="text-slate-500">•</span>
                <span className="text-[11px] font-bold px-2 py-0.5 rounded-md bg-emerald-500/10 text-emerald-300 border border-emerald-500/20">
                  {activePosting?.salary_range || match.salary_range}
                </span>
              </>
            )}
            {match.department && (
              <>
                <span className="text-slate-500">•</span>
                <span className="text-slate-400">Dept: {match.department}</span>
              </>
            )}
          </div>

          {/* Interactive Multi-Location Pill Chips */}
          {hasMultipleLocations && (
            <div
              data-testid="location-pill-chips"
              className="flex flex-wrap items-center gap-1.5 mt-2.5 pt-2 border-t border-slate-800/80"
            >
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 mr-1 flex items-center gap-1">
                <MapPin className="w-3 h-3 text-sky-400" /> Locations:
              </span>
              {locationPostings.map((p, idx) => {
                const isSelected = idx === selectedPostingIndex;
                return (
                  <button
                    key={idx}
                    type="button"
                    onClick={() => setSelectedPostingIndex(idx)}
                    className={`text-[11px] font-medium px-2 py-0.5 rounded-lg border transition-all flex items-center gap-1.5 ${
                      isSelected
                        ? "bg-sky-500/20 text-sky-200 border-sky-400/50 shadow-sm shadow-sky-500/10"
                        : "bg-slate-800/80 hover:bg-slate-700/80 text-slate-400 hover:text-slate-200 border-slate-700/60"
                    }`}
                  >
                    <span>{p.location}</span>
                    {p.is_primary && (
                      <span className="text-[9px] px-1 py-0.2 rounded bg-sky-500/30 text-sky-300 font-semibold">
                        Primary
                      </span>
                    )}
                    {p.salary_range && (
                      <span className="text-[10px] text-emerald-400">
                        {p.salary_range}
                      </span>
                    )}
                  </button>
                );
              })}
            </div>
          )}
        </div>

        {/* Action CTA Bar */}
        <div className="flex flex-wrap items-center gap-2 pt-0.5 relative">
          {activeApplyUrl && (
            <div className="relative inline-flex items-center">
              <a
                href={activeApplyUrl}
                target="_blank"
                rel="noopener noreferrer"
                data-testid={`apply-link-${match.job_id}`}
                className={`px-4 py-2 text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition-all flex items-center gap-1.5 ${
                  hasMultipleLocations ? "rounded-l-xl border-r-0" : "rounded-xl"
                }`}
              >
                <ExternalLink className="w-3.5 h-3.5" />
                <span>
                  Apply{hasMultipleLocations ? ` (${activePosting?.location || "Selected"})` : ""}
                </span>
              </a>

              {hasMultipleLocations && (
                <button
                  type="button"
                  onClick={() => setShowLocationMenu((prev) => !prev)}
                  data-testid="location-selector-trigger"
                  aria-label="Select location"
                  className="px-2.5 py-2 text-xs font-semibold rounded-r-xl bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white border border-slate-700 transition-all flex items-center gap-1"
                >
                  <span className="text-[11px] font-medium text-sky-400">
                    {locationPostings.length} Locs
                  </span>
                  <ChevronDown className="w-3.5 h-3.5 text-slate-400" />
                </button>
              )}

              {/* Location Popover Menu */}
              {hasMultipleLocations && showLocationMenu && (
                <div
                  data-testid="location-dropdown-menu"
                  className="absolute left-0 top-full mt-1.5 w-72 max-h-60 overflow-y-auto bg-slate-900 border border-slate-700/90 rounded-xl shadow-2xl z-50 p-1.5 space-y-1"
                >
                  <div className="px-2 py-1 text-[10px] font-bold text-slate-400 uppercase tracking-wider border-b border-slate-800 flex items-center justify-between">
                    <span>Available Regions ({locationPostings.length})</span>
                    <span className="text-slate-500 font-normal">Direct ATS Apply</span>
                  </div>
                  {locationPostings.map((posting, idx) => {
                    const isSelected = idx === selectedPostingIndex;
                    return (
                      <div
                        key={idx}
                        className={`group flex items-center justify-between p-2 rounded-lg text-xs transition-colors cursor-pointer ${
                          isSelected
                            ? "bg-sky-950/70 border border-sky-800/60 text-white"
                            : "hover:bg-slate-800/80 text-slate-300 border border-transparent"
                        }`}
                        onClick={() => {
                          setSelectedPostingIndex(idx);
                          setShowLocationMenu(false);
                        }}
                      >
                        <div className="flex flex-col min-w-0 pr-2">
                          <div className="flex items-center gap-1.5 truncate">
                            <MapPin className="w-3 h-3 text-sky-400 shrink-0" />
                            <span className="font-semibold truncate">
                              {posting.location}
                            </span>
                            {posting.is_primary && (
                              <span className="text-[9px] px-1 py-0.2 rounded bg-sky-500/20 text-sky-300 border border-sky-500/30">
                                Primary
                              </span>
                            )}
                          </div>
                          {posting.salary_range && (
                            <span className="text-[10px] text-emerald-400 pl-4.5">
                              {posting.salary_range}
                            </span>
                          )}
                        </div>
                        <a
                          href={posting.apply_url || activeApplyUrl}
                          target="_blank"
                          rel="noopener noreferrer"
                          onClick={(e) => e.stopPropagation()}
                          className="shrink-0 p-1 rounded-md bg-slate-800 group-hover:bg-sky-600 text-slate-300 group-hover:text-white transition-colors"
                          title={`Direct apply for ${posting.location}`}
                        >
                          <ExternalLink className="w-3 h-3" />
                        </a>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
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
        </div>
      </div>

      {/* Single Continuous Scrollable Body (NO nested scrollbar!) */}
      <div
        data-testid="job-detail-scroll-body"
        className="flex-1 overflow-y-auto p-5 space-y-5"
      >
        {/* Cold-Start / Profile Required Card */}
        {!profileReady && (
          <div
            data-testid="profile-required-grounded-card"
            className="p-4 rounded-xl bg-slate-900/80 border border-amber-500/30 space-y-3"
          >
            <div className="flex items-start gap-3">
              <div className="p-2 rounded-xl bg-amber-500/20 text-amber-300 border border-amber-500/30 shrink-0 mt-0.5">
                <AlertTriangle className="w-4 h-4" />
              </div>
              <div className="space-y-1">
                <h4 className="text-xs font-bold text-white uppercase tracking-wider">
                  Profile Required for Grounded Matching
                </h4>
                <p className="text-xs text-slate-300 leading-relaxed">
                  Because you haven't shared your skills or profile with us yet, personalized match percentages, scoring factor breakdowns, and skill gap analysis cannot be calculated.
                </p>
                {onOpenProfileModal && (
                  <div className="pt-2">
                    <button
                      type="button"
                      onClick={onOpenProfileModal}
                      data-testid="detail-open-profile-btn"
                      className="px-3 py-1.5 rounded-lg bg-sky-600 hover:bg-sky-500 text-white font-semibold text-xs transition-all shadow-sm flex items-center gap-1.5 cursor-pointer"
                    >
                      <Sparkles className="w-3.5 h-3.5" />
                      <span>Upload CV / Add Skills (+10% to unlock)</span>
                    </button>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Grounded Mode Inline Match Intelligence */}
        {isGrounded && (
          <div className="space-y-4 bg-slate-900/70 border border-slate-700/60 rounded-xl p-4">
            <div className="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-slate-800/80">
              <div className="flex items-center gap-2">
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-300 flex items-center gap-1.5">
                  <Layers className="w-3.5 h-3.5 text-sky-400" />
                  Match Breakdown & Skill Alignment
                </h3>
                {breakdown?.d_core !== undefined && breakdown.d_core < 1.0 && (
                  <span className="text-[11px] text-amber-300 font-medium bg-amber-500/10 px-2 py-0.5 rounded border border-amber-500/20">
                    Core Multiplier: {Number(breakdown.d_core).toFixed(2)}x
                  </span>
                )}
              </div>

              {/* Match Probability Badge & Diagnostics Trigger in Section */}
              <div className="flex items-center gap-2">
                <span
                  className={`text-xs font-extrabold px-3 py-1 rounded-lg flex items-center gap-1.5 shadow-sm ${
                    isHigh
                      ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/40"
                      : isModerate
                        ? "bg-amber-500/20 text-amber-400 border border-amber-500/40"
                        : "bg-sky-500/20 text-sky-300 border border-sky-500/40"
                  }`}
                >
                  <TrendingUp className="w-3.5 h-3.5" />
                  {matchPct}% Probability of Match
                </span>

                {onOpenDiagnostics && (
                  <button
                    type="button"
                    onClick={() => onOpenDiagnostics(match)}
                    title="Decompose acceptance probability factors"
                    className="px-3 py-1 text-xs font-semibold rounded-lg border border-sky-500/40 bg-sky-500/10 hover:bg-sky-500/20 text-sky-300 transition-all flex items-center gap-1.5 shadow-sm"
                  >
                    <Sparkles className="w-3.5 h-3.5 text-sky-400" />
                    <span>Why this match?</span>
                  </button>
                )}
              </div>
            </div>

            {/* 6-Factor Mini Progress Bars */}
            {factorBars.length > 0 && (
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                {factorBars.map((f) => {
                  const pct = Math.round(
                    Math.min(1, Math.max(0, f.value)) * 100,
                  );
                  const isUnstated = f.status === "unstated_in_job" || f.status === "unstated_in_profile";
                  const isMissingBlocks = f.status === "missing_cv_blocks";
                  return (
                    <div
                      key={f.label}
                      className="bg-slate-800/80 border border-slate-700/60 rounded-lg p-2.5 space-y-1.5"
                    >
                      <div className="flex items-center justify-between text-[11px]">
                        <span className="text-slate-400 truncate">
                          {f.label}
                        </span>
                        {isUnstated ? (
                          <span className="text-[10px] font-semibold text-slate-400 bg-slate-700/60 px-1.5 py-0.5 rounded">
                            Unstated
                          </span>
                        ) : isMissingBlocks ? (
                          <span className="text-[10px] font-semibold text-amber-300 bg-amber-500/10 px-1.5 py-0.5 rounded">
                            0% (No Blocks)
                          </span>
                        ) : (
                          <span className="font-bold text-slate-200">{pct}%</span>
                        )}
                      </div>
                      <div className="w-full h-1.5 bg-slate-950 rounded-full overflow-hidden">
                        <div
                          className={`h-full rounded-full ${
                            isUnstated
                              ? "bg-slate-700"
                              : isMissingBlocks
                                ? "bg-amber-500"
                                : pct >= 75
                                  ? "bg-emerald-500"
                                  : pct >= 50
                                    ? "bg-sky-500"
                                    : "bg-amber-500"
                          }`}
                          style={{ width: isUnstated ? "0%" : `${pct}%` }}
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

        {/* Dual-Mode Role Description & Requirements Section */}
        <div className="space-y-3" data-testid="job-detail-raw-description">
          <div className="flex flex-wrap items-center justify-between gap-2 pt-2 border-t border-slate-700/60">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-300 flex items-center gap-1.5">
              <FileText className="w-3.5 h-3.5 text-sky-400" />
              Role Description & Requirements
            </h3>

            {/* View Mode Segmented Controls */}
            <div className="flex items-center gap-1 bg-slate-900/90 border border-slate-700/80 rounded-xl p-0.5 text-xs">
              <button
                type="button"
                onClick={() => setViewMode("smart")}
                data-testid="view-mode-smart-btn"
                className={`flex items-center gap-1 px-2.5 py-1 rounded-lg font-medium transition-all ${
                  viewMode === "smart"
                    ? "bg-sky-600 text-white shadow-sm"
                    : "text-slate-400 hover:text-slate-200"
                }`}
                title="Skimmable summary cards with skill alignment & key highlights"
              >
                <Sparkles className="w-3 h-3 text-sky-300" />
                <span>Smart Brief</span>
              </button>

              <button
                type="button"
                onClick={() => setViewMode("formatted")}
                data-testid="view-mode-formatted-btn"
                className={`flex items-center gap-1 px-2.5 py-1 rounded-lg font-medium transition-all ${
                  viewMode === "formatted"
                    ? "bg-sky-600 text-white shadow-sm"
                    : "text-slate-400 hover:text-slate-200"
                }`}
                title="Typography-enhanced full posting with in-text skill highlights"
              >
                <Layers className="w-3 h-3" />
                <span>Full Formatted</span>
              </button>

              <button
                type="button"
                onClick={() => setViewMode("raw")}
                data-testid="view-mode-raw-btn"
                className={`flex items-center gap-1 px-2 py-1 rounded-lg font-medium transition-all ${
                  viewMode === "raw"
                    ? "bg-slate-700 text-white shadow-sm"
                    : "text-slate-500 hover:text-slate-300"
                }`}
                title="Verbatim unmodified ATS job description"
              >
                <span>Raw ATS</span>
              </button>
            </div>
          </div>

          {!match.raw_description ? (
            <div className="text-xs text-slate-400 italic bg-slate-900/40 border border-slate-800 rounded-xl p-4">
              Full job description text is available on the company application
              page.
            </div>
          ) : viewMode === "smart" ? (
            /* ============================================================== */
            /* VIEW 1: SMART BRIEF (4 MODULAR SCANNABLE CARDS)                */
            /* ============================================================== */
            <div data-testid="job-smart-brief" className="space-y-4">
              {/* Card 1: 30-Second Snapshot & Mission */}
              <div className="bg-slate-900/70 border border-slate-700/60 rounded-xl p-4 space-y-3">
                <div className="flex items-center justify-between">
                  <h4 className="text-xs font-bold uppercase tracking-wider text-sky-400 flex items-center gap-1.5">
                    <Sparkles className="w-3.5 h-3.5" />
                    30-Second Role Snapshot
                  </h4>
                  {parsed.yearsExperience && (
                    <span className="text-[11px] font-bold text-sky-300 bg-sky-950/80 px-2 py-0.5 rounded-md border border-sky-800/60">
                      {parsed.yearsExperience}
                    </span>
                  )}
                </div>
                <p className="text-xs text-slate-200 leading-relaxed">
                  {parsed.summary ||
                    match.raw_description.slice(0, 280) + "..."}
                </p>

                {/* Quick Chips */}
                <div className="flex flex-wrap items-center gap-2 pt-1 text-[11px] text-slate-300">
                  <span className="px-2 py-0.5 rounded-lg bg-slate-800 border border-slate-700 flex items-center gap-1">
                    <MapPin className="w-3 h-3 text-slate-400" />
                    {match.location}
                  </span>
                  {match.workplace_type && (
                    <span className="px-2 py-0.5 rounded-lg bg-slate-800 border border-slate-700 font-semibold text-[10px] text-slate-200">
                      {formatWorkplaceType(match.workplace_type)}
                    </span>
                  )}
                  {match.posted_at && (
                    <span className="px-2 py-0.5 rounded-lg bg-slate-800 border border-slate-700 flex items-center gap-1 text-slate-400">
                      <Clock className="w-3 h-3 text-slate-500" />
                      {formatRelativeTime(match.posted_at)}
                    </span>
                  )}
                  {match.salary_range && (
                    <span className="px-2 py-0.5 rounded-lg bg-emerald-500/10 text-emerald-300 border border-emerald-500/20 font-medium">
                      {match.salary_range}
                    </span>
                  )}
                  {match.department && (
                    <span className="px-2 py-0.5 rounded-lg bg-slate-800 border border-slate-700">
                      Dept: {match.department}
                    </span>
                  )}
                </div>
              </div>

              {/* Card 2: Core Responsibilities */}
              {parsed.responsibilities.length > 0 && (
                <div className="bg-slate-900/70 border border-slate-700/60 rounded-xl p-4 space-y-2.5">
                  <h4 className="text-xs font-bold uppercase tracking-wider text-slate-300 flex items-center gap-1.5">
                    <ListOrdered className="w-3.5 h-3.5 text-indigo-400" />
                    Core Responsibilities (What You'll Do)
                  </h4>
                  <ul className="space-y-1.5 text-xs text-slate-300">
                    {parsed.responsibilities.slice(0, 6).map((resp, rIdx) => (
                      <li
                        key={rIdx}
                        className="flex items-start gap-2 leading-relaxed"
                      >
                        <span className="mt-1.5 w-1.5 h-1.5 rounded-full bg-indigo-400 shrink-0" />
                        <span>
                          {renderHighlightedSpans(
                            resp,
                            match.matched_skills,
                            match.missing_dealbreakers,
                          )}
                        </span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Card 3: Skill Match & Gap Analysis OR Extracted Job Requirements */}
              {isGrounded ? (
                <div className="bg-slate-900/70 border border-slate-700/60 rounded-xl p-4 space-y-3">
                  <h4 className="text-xs font-bold uppercase tracking-wider text-slate-300 flex items-center gap-1.5">
                    <Target className="w-3.5 h-3.5 text-emerald-400" />
                    Skill Match & Gap Analysis
                  </h4>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
                    {/* Confirmed Candidate Strengths */}
                    <div className="bg-slate-800/70 border border-emerald-500/20 rounded-lg p-3 space-y-1.5">
                      <div className="flex items-center justify-between text-[11px] font-semibold text-emerald-300">
                        <span className="flex items-center gap-1">
                          <CheckCircle2 className="w-3 h-3 text-emerald-400" />
                          Your Matched Skills ({match.matched_skills?.length || 0})
                        </span>
                      </div>
                      {match.matched_skills?.length > 0 ? (
                        <div className="flex flex-wrap gap-1 pt-1">
                          {match.matched_skills.map((s, idx) => (
                            <span
                              key={idx}
                              className="text-[10px] px-2 py-0.5 rounded-md bg-emerald-500/15 text-emerald-300 border border-emerald-500/30 font-medium"
                            >
                              {s}
                            </span>
                          ))}
                        </div>
                      ) : (
                        <p className="text-[11px] text-slate-400 italic">
                          No direct keyword overlap found.
                        </p>
                      )}
                    </div>

                    {/* Missing Dealbreaker Skills / Prep Topics */}
                    <div className="bg-slate-800/70 border border-amber-500/20 rounded-lg p-3 space-y-1.5">
                      <div className="flex items-center justify-between text-[11px] font-semibold text-amber-300">
                        <span className="flex items-center gap-1">
                          <AlertTriangle className="w-3 h-3 text-amber-400" />
                          Missing Dealbreakers ({match.missing_dealbreakers?.length || 0})
                        </span>
                      </div>
                      {match.missing_dealbreakers?.length > 0 ? (
                        <div className="space-y-1.5 pt-1">
                          <div className="flex flex-wrap gap-1">
                            {match.missing_dealbreakers.map((m, idx) => (
                              <span
                                key={idx}
                                className="text-[10px] px-2 py-0.5 rounded-md bg-amber-500/15 text-amber-300 border border-amber-500/30 font-medium"
                              >
                                {m}
                              </span>
                            ))}
                          </div>
                          <p className="text-[10px] text-slate-400">
                            💡 Tip: Highlight equivalent experience or project transferability during interview prep.
                          </p>
                        </div>
                      ) : (
                        <p className="text-[11px] text-emerald-400/90 font-medium flex items-center gap-1 pt-1">
                          <CheckCheck className="w-3.5 h-3.5" /> All critical skills verified!
                        </p>
                      )}
                    </div>
                  </div>
                </div>
              ) : (
                <div className="bg-slate-900/70 border border-slate-700/60 rounded-xl p-4 space-y-3">
                  <h4 className="text-xs font-bold uppercase tracking-wider text-slate-300 flex items-center gap-1.5">
                    <Briefcase className="w-3.5 h-3.5 text-sky-400" />
                    Extracted Job Requirements
                  </h4>
                  <div className="space-y-2 text-xs">
                    {/* Required Skills */}
                    <div>
                      <span className="text-[11px] font-semibold text-slate-400 block mb-1">
                        Required Technical & Domain Skills:
                      </span>
                      <div className="flex flex-wrap gap-1">
                        {(match.ats_requirements?.required_skills?.length > 0
                          ? match.ats_requirements.required_skills
                          : [...(match.matched_skills || []), ...(match.missing_dealbreakers || [])]
                        ).map((s, idx) => (
                          <span
                            key={idx}
                            className="text-[10px] px-2 py-0.5 rounded-md bg-slate-800 text-slate-200 border border-slate-700 font-medium"
                          >
                            {s}
                          </span>
                        ))}
                      </div>
                    </div>

                    {/* Preferred Skills */}
                    {match.ats_requirements?.preferred_skills?.length > 0 && (
                      <div className="pt-2 border-t border-slate-800">
                        <span className="text-[11px] font-semibold text-slate-400 block mb-1">
                          Preferred / Bonus Skills:
                        </span>
                        <div className="flex flex-wrap gap-1">
                          {match.ats_requirements.preferred_skills.map((s, idx) => (
                            <span
                              key={idx}
                              className="text-[10px] px-2 py-0.5 rounded-md bg-indigo-500/10 text-indigo-300 border border-indigo-500/20"
                            >
                              {s}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Card 4: Benefits & Perks */}
              {parsed.benefits.length > 0 && (
                <div className="bg-slate-900/70 border border-slate-700/60 rounded-xl p-4 space-y-2">
                  <h4 className="text-xs font-bold uppercase tracking-wider text-slate-300 flex items-center gap-1.5">
                    <Gift className="w-3.5 h-3.5 text-pink-400" />
                    Benefits & Perks
                  </h4>
                  <ul className="space-y-1 text-xs text-slate-300">
                    {parsed.benefits.map((b, bIdx) => (
                      <li
                        key={bIdx}
                        className="flex items-start gap-2 leading-relaxed"
                      >
                        <span className="mt-1.5 w-1.5 h-1.5 rounded-full bg-pink-400 shrink-0" />
                        <span>{b}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          ) : viewMode === "formatted" ? (
            /* ============================================================== */
            /* VIEW 2: FULL FORMATTED (ENHANCED SCANNABLE DOCUMENT)           */
            /* ============================================================== */
            <div data-testid="job-full-formatted" className="space-y-4">
              {parsed.sections.map((section, sIdx) => {
                // If it's a legal / EEO boilerplate, render collapsible accordion!
                if (section.isBoilerplate) {
                  const isExpanded = !!expandedBoilerplates[sIdx];
                  return (
                    <div
                      key={sIdx}
                      className="border border-slate-800 rounded-xl bg-slate-900/40 overflow-hidden text-xs"
                    >
                      <button
                        type="button"
                        onClick={() =>
                          setExpandedBoilerplates((prev) => ({
                            ...prev,
                            [sIdx]: !prev[sIdx],
                          }))
                        }
                        className="w-full flex items-center justify-between p-3.5 text-left text-slate-400 hover:text-slate-200 transition-colors cursor-pointer"
                      >
                        <span className="font-semibold flex items-center gap-2">
                          <ShieldCheck className="w-3.5 h-3.5 text-slate-500" />
                          {section.title}
                        </span>
                        <span className="flex items-center gap-1 text-[11px] text-slate-500">
                          {isExpanded ? "Collapse" : "Expand statement"}
                          {isExpanded ? (
                            <ChevronDown className="w-3.5 h-3.5" />
                          ) : (
                            <ChevronRight className="w-3.5 h-3.5" />
                          )}
                        </span>
                      </button>
                      {isExpanded && (
                        <div className="p-4 pt-1 border-t border-slate-800/80 text-slate-300 leading-relaxed whitespace-pre-line text-xs">
                          {section.content}
                        </div>
                      )}
                    </div>
                  );
                }

                // Normal formatted section card with in-text keyword highlighting
                return (
                  <div
                    key={sIdx}
                    className="bg-slate-900/60 border border-slate-800/80 rounded-xl p-4 sm:p-5 space-y-2.5 shadow-sm"
                  >
                    <h4 className="text-xs font-bold uppercase tracking-wider text-sky-400 border-b border-slate-800/60 pb-1.5">
                      {section.title}
                    </h4>

                    {section.bullets.length > 0 ? (
                      <ul className="space-y-1.5 text-xs text-slate-200">
                        {section.bullets.map((b, bIdx) => (
                          <li
                            key={bIdx}
                            className="flex items-start gap-2 leading-relaxed"
                          >
                            <span className="mt-1.5 w-1.5 h-1.5 rounded-full bg-sky-400 shrink-0" />
                            <span className="max-w-[70ch]">
                              {renderHighlightedSpans(
                                b,
                                match.matched_skills,
                                match.missing_dealbreakers,
                              )}
                            </span>
                          </li>
                        ))}
                      </ul>
                    ) : (
                      <div className="text-xs text-slate-200 leading-relaxed whitespace-pre-line max-w-[70ch]">
                        {renderHighlightedSpans(
                          section.content,
                          match.matched_skills,
                          match.missing_dealbreakers,
                        )}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          ) : (
            /* ============================================================== */
            /* VIEW 3: RAW ATS MONOSPACE TEXT                                 */
            /* ============================================================== */
            <div data-testid="job-raw-ats" className="space-y-2">
              <div className="flex items-center justify-between text-[11px] text-slate-400">
                <span>Verbatim ATS Listing Text</span>
                <button
                  type="button"
                  onClick={() => {
                    navigator.clipboard.writeText(match.raw_description || "");
                    setCopiedRaw(true);
                    setTimeout(() => setCopiedRaw(false), 2000);
                  }}
                  className="flex items-center gap-1 hover:text-white px-2 py-0.5 rounded bg-slate-800 border border-slate-700 transition-colors cursor-pointer"
                >
                  {copiedRaw ? (
                    <>
                      <CheckCheck className="w-3 h-3 text-emerald-400" /> Copied
                    </>
                  ) : (
                    <>
                      <Copy className="w-3 h-3" /> Copy Raw Text
                    </>
                  )}
                </button>
              </div>
              <div className="text-xs text-slate-300 font-mono leading-relaxed whitespace-pre-line bg-slate-900/80 border border-slate-800 rounded-xl p-4 shadow-inner">
                {match.raw_description}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
