import React from "react";
import {
  X,
  ShieldCheck,
  DollarSign,
  MapPin,
  Calendar,
  TrendingUp,
  Briefcase,
  Layers,
  RotateCcw,
  Check,
} from "lucide-react";

const WORK_AUTH_OPTIONS = [
  {
    value: "all",
    label: "Any Work Authorization",
    desc: "Include all active listings regardless of sponsorship policy",
  },
  {
    value: "f1_opt_cpt",
    label: "F-1 OPT / STEM E-Verify",
    desc: "E-Verify confirmed employers without US citizenship restrictions",
  },
  {
    value: "h1b_transfer_sponsor",
    label: "H-1B Transfer / Sponsor",
    desc: "Verified USCIS H-1B sponsors or explicit sponsorship policies",
  },
  {
    value: "domestic_only",
    label: "Domestic / Citizen / PR",
    desc: "Include roles restricted to US Citizens or Permanent Residents",
  },
];

const SALARY_OPTIONS = [
  { value: null, label: "Any" },
  { value: 100000, label: "$100k+" },
  { value: 140000, label: "$140k+" },
  { value: 180000, label: "$180k+" },
  { value: 220000, label: "$220k+" },
  { value: 260000, label: "$260k+" },
];

const COMMUTE_OPTIONS = [
  { value: null, label: "Any Distance" },
  { value: 10, label: "≤ 10 mi" },
  { value: 25, label: "≤ 25 mi" },
  { value: 50, label: "≤ 50 mi" },
];

const DATE_POSTED_OPTIONS = [
  { value: "", label: "Any Time" },
  { value: "1", label: "Past 24 Hours" },
  { value: "7", label: "Past Week" },
  { value: "14", label: "Past 2 Weeks" },
  { value: "30", label: "Past Month" },
];

const MIN_SCORE_OPTIONS = [
  { value: 0.0, label: "All Relevant (≥ 30%)" },
  { value: 0.5, label: "Moderate+ (≥ 50%)" },
  { value: 0.75, label: "High Match Only (≥ 75%)" },
];

const SENIORITY_PILLS = [
  { value: "intern", label: "Intern" },
  { value: "entry", label: "Entry / New Grad" },
  { value: "junior", label: "Junior" },
  { value: "mid", label: "Mid-Level" },
  { value: "senior", label: "Senior" },
  { value: "staff", label: "Staff" },
  { value: "principal", label: "Principal / Lead" },
];

const INDUSTRY_PILLS = [
  { value: "ai_ml_infra", label: "AI & ML" },
  { value: "fintech", label: "FinTech" },
  { value: "healthtech", label: "HealthTech" },
  { value: "hft_quant_trading", label: "Quant / HFT" },
  { value: "devtools", label: "DevTools & Infra" },
  { value: "cybersecurity", label: "Cybersecurity" },
  { value: "general_saas", label: "Cloud & SaaS" },
  { value: "ecommerce", label: "E-Commerce" },
];

export function SearchFilterModal({
  isOpen,
  onClose,
  workAuthTier,
  onWorkAuthTierChange,
  minBaseSalary,
  onMinBaseSalaryChange,
  maxCommuteMiles,
  onMaxCommuteMilesChange,
  postedWithin,
  onPostedWithinChange,
  minScore,
  onMinScoreChange,
  searchMode = "cv_grounded",
  chips = [],
  onToggleChip,
  onResetAdvancedFilters,
}) {
  if (!isOpen) return null;

  const activeSeniority = new Set(
    chips.filter((c) => c.type === "seniority").map((c) => c.value.toLowerCase())
  );
  const activeIndustries = new Set(
    chips.filter((c) => c.type === "industry").map((c) => c.value.toLowerCase())
  );

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 backdrop-blur-sm p-4"
      role="dialog"
      aria-modal="true"
      aria-label="Advanced search filters"
      data-testid="search-filter-modal"
    >
      <div className="bg-slate-900 border border-slate-700/80 rounded-2xl w-full max-w-2xl max-h-[88vh] flex flex-col shadow-2xl overflow-hidden">
        {/* Modal Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800 bg-slate-900/95">
          <div>
            <h2 className="text-lg font-bold text-white flex items-center gap-2">
              <Layers className="w-5 h-5 text-sky-400" />
              Search Configuration & Filters
            </h2>
            <p className="text-xs text-slate-400">
              Fine-tune work authorization, compensation floors, seniority, and industry verticals.
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            aria-label="Close filter modal"
            className="p-2 rounded-xl text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-6 overflow-y-auto space-y-6 text-xs">
          {/* 1. Work Authorization Tier */}
          <div className="space-y-2.5">
            <label
              htmlFor="modal-work-auth-select"
              className="text-xs font-semibold uppercase tracking-wider text-slate-300 flex items-center gap-1.5"
            >
              <ShieldCheck className="w-4 h-4 text-emerald-400" />
              Work Authorization & Visa Policy
            </label>
            <select
              id="modal-work-auth-select"
              aria-label="Filter by work authorization"
              value={workAuthTier}
              onChange={(e) => onWorkAuthTierChange(e.target.value)}
              className="sr-only"
            >
              {WORK_AUTH_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
              {WORK_AUTH_OPTIONS.map((opt) => {
                const selected = workAuthTier === opt.value;
                return (
                  <button
                    key={opt.value}
                    type="button"
                    onClick={() => onWorkAuthTierChange(opt.value)}
                    className={`text-left p-3 rounded-xl border transition-all ${
                      selected
                        ? "bg-emerald-500/15 border-emerald-500/60 text-white shadow-sm"
                        : "bg-slate-800/60 border-slate-700/70 text-slate-300 hover:border-slate-600"
                    }`}
                  >
                    <div className="flex items-center justify-between font-semibold">
                      <span>{opt.label}</span>
                      {selected && <Check className="w-3.5 h-3.5 text-emerald-400" />}
                    </div>
                    <p className="text-[11px] text-slate-400 mt-1 leading-snug">
                      {opt.desc}
                    </p>
                  </button>
                );
              })}
            </div>
          </div>

          {/* 2. Minimum Base Salary & Commute Radius */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
            <div className="space-y-2">
              <label
                htmlFor="modal-salary-select"
                className="text-xs font-semibold uppercase tracking-wider text-slate-300 flex items-center gap-1.5"
              >
                <DollarSign className="w-4 h-4 text-amber-400" />
                Minimum Base Salary (USD)
              </label>
              <select
                id="modal-salary-select"
                aria-label="Filter by minimum base salary"
                value={minBaseSalary === null ? "any" : String(minBaseSalary)}
                onChange={(e) =>
                  onMinBaseSalaryChange(
                    e.target.value === "any" ? null : Number(e.target.value)
                  )
                }
                className="w-full bg-slate-800/90 border border-slate-700 rounded-xl px-3 py-2.5 text-xs text-white focus:outline-none focus:ring-2 focus:ring-sky-500"
              >
                {SALARY_OPTIONS.map((opt) => (
                  <option
                    key={String(opt.value)}
                    value={opt.value === null ? "any" : String(opt.value)}
                  >
                    {opt.label}
                  </option>
                ))}
              </select>
            </div>

            <div className="space-y-2">
              <label
                htmlFor="modal-commute-select"
                className="text-xs font-semibold uppercase tracking-wider text-slate-300 flex items-center gap-1.5"
              >
                <MapPin className="w-4 h-4 text-rose-400" />
                Max Commute Distance
              </label>
              <select
                id="modal-commute-select"
                aria-label="Filter by commute radius"
                value={maxCommuteMiles === null ? "any" : String(maxCommuteMiles)}
                onChange={(e) =>
                  onMaxCommuteMilesChange(
                    e.target.value === "any" ? null : Number(e.target.value)
                  )
                }
                className="w-full bg-slate-800/90 border border-slate-700 rounded-xl px-3 py-2.5 text-xs text-white focus:outline-none focus:ring-2 focus:ring-sky-500"
              >
                {COMMUTE_OPTIONS.map((opt) => (
                  <option
                    key={String(opt.value)}
                    value={opt.value === null ? "any" : String(opt.value)}
                  >
                    {opt.label}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* 3. Date Posted & Match Probability Floor */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
            <div className="space-y-2">
              <label
                htmlFor="modal-posted-select"
                className="text-xs font-semibold uppercase tracking-wider text-slate-300 flex items-center gap-1.5"
              >
                <Calendar className="w-4 h-4 text-indigo-400" />
                Date Posted
              </label>
              <select
                id="modal-posted-select"
                aria-label="Filter by date posted"
                value={postedWithin || ""}
                onChange={(e) => onPostedWithinChange(e.target.value)}
                className="w-full bg-slate-800/90 border border-slate-700 rounded-xl px-3 py-2.5 text-xs text-white focus:outline-none focus:ring-2 focus:ring-sky-500"
              >
                {DATE_POSTED_OPTIONS.map((opt) => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </select>
            </div>

            <div className="space-y-2">
              <label
                htmlFor="modal-min-score-select"
                className="text-xs font-semibold uppercase tracking-wider text-slate-300 flex items-center gap-1.5"
              >
                <TrendingUp className="w-4 h-4 text-sky-400" />
                Minimum Match Threshold
              </label>
              <select
                id="modal-min-score-select"
                aria-label="Minimum probability band filter"
                value={minScore || 0.0}
                disabled={searchMode === "unbiased"}
                onChange={(e) => onMinScoreChange(parseFloat(e.target.value))}
                className="w-full bg-slate-800/90 border border-slate-700 rounded-xl px-3 py-2.5 text-xs text-white focus:outline-none focus:ring-2 focus:ring-sky-500 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {MIN_SCORE_OPTIONS.map((opt) => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* 4. Seniority Level Multi-Select */}
          {onToggleChip && (
            <div className="space-y-2.5">
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-300 flex items-center gap-1.5">
                <Briefcase className="w-4 h-4 text-amber-400" />
                Target Seniority Levels
              </span>
              <div className="flex flex-wrap gap-2">
                {SENIORITY_PILLS.map((item) => {
                  const isSelected = activeSeniority.has(item.value);
                  return (
                    <button
                      key={item.value}
                      type="button"
                      onClick={() => onToggleChip("seniority", item.value)}
                      className={`px-3 py-1.5 rounded-xl font-medium border transition-all ${
                        isSelected
                          ? "bg-amber-500/20 text-amber-300 border-amber-500/50"
                          : "bg-slate-800/80 text-slate-300 border-slate-700 hover:border-slate-600"
                      }`}
                    >
                      {item.label}
                    </button>
                  );
                })}
              </div>
            </div>
          )}

          {/* 5. Industry Vertical Multi-Select */}
          {onToggleChip && (
            <div className="space-y-2.5">
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-300 flex items-center gap-1.5">
                <Layers className="w-4 h-4 text-purple-400" />
                Industry Verticals
              </span>
              <div className="flex flex-wrap gap-2">
                {INDUSTRY_PILLS.map((item) => {
                  const isSelected = activeIndustries.has(item.value);
                  return (
                    <button
                      key={item.value}
                      type="button"
                      onClick={() => onToggleChip("industry", item.value)}
                      className={`px-3 py-1.5 rounded-xl font-medium border transition-all ${
                        isSelected
                          ? "bg-purple-500/20 text-purple-300 border-purple-500/50"
                          : "bg-slate-800/80 text-slate-300 border-slate-700 hover:border-slate-600"
                      }`}
                    >
                      {item.label}
                    </button>
                  );
                })}
              </div>
            </div>
          )}
        </div>

        {/* Modal Footer */}
        <div className="flex items-center justify-between px-6 py-4 border-t border-slate-800 bg-slate-900/95">
          <button
            type="button"
            onClick={onResetAdvancedFilters}
            className="px-3.5 py-2 rounded-xl border border-slate-700 hover:bg-slate-800 text-xs font-medium text-slate-300 flex items-center gap-1.5 transition-colors"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            Reset Filters
          </button>
          <button
            type="button"
            onClick={onClose}
            className="px-5 py-2 rounded-xl bg-sky-600 hover:bg-sky-500 text-white text-xs font-semibold shadow-md shadow-sky-600/20 transition-all"
          >
            Apply & View Opportunities
          </button>
        </div>
      </div>
    </div>
  );
}

