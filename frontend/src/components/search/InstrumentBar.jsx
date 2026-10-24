import React from "react";
import {
  ShieldCheck,
  Home,
  MapPin,
  DollarSign,
  Calendar,
  TrendingUp,
} from "lucide-react";

export function InstrumentBar({
  workAuthTier,
  onWorkAuthTierChange,
  workplaceModality,
  onWorkplaceModalityChange,
  maxCommuteMiles,
  onMaxCommuteMilesChange,
  minBaseSalary,
  onMinBaseSalaryChange,
  postedWithin,
  onPostedWithinChange,
  minScore,
  onMinScoreChange,
  searchMode = "cv_grounded",
}) {
  return (
    <div
      data-testid="search-filters-row"
      className="flex flex-wrap items-center gap-2 py-2 px-3 bg-slate-900/60 border border-slate-700/60 rounded-xl text-xs"
    >
      {/* 1. Work Authorization Facet */}
      <div className="flex items-center gap-1.5 bg-slate-800/90 hover:bg-slate-800 border border-slate-700/80 rounded-lg px-2.5 py-1.5 transition-colors">
        <ShieldCheck className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
        <select
          value={workAuthTier}
          onChange={(e) => onWorkAuthTierChange(e.target.value)}
          aria-label="Filter by work authorization"
          className="bg-transparent text-slate-200 font-medium focus:outline-none cursor-pointer"
        >
          <option value="all" className="bg-slate-900 text-slate-200">
            Work Auth: Any
          </option>
          <option value="f1_opt_cpt" className="bg-slate-900 text-slate-200">
            F-1 OPT / E-Verify
          </option>
          <option value="h1b_transfer_sponsor" className="bg-slate-900 text-slate-200">
            H-1B Sponsor (USCIS)
          </option>
          <option value="domestic_only" className="bg-slate-900 text-slate-200">
            Domestic Only (US Citizen/PR)
          </option>
        </select>
      </div>

      {/* 2. Workplace Modality Facet */}
      <div className="flex items-center gap-1.5 bg-slate-800/90 hover:bg-slate-800 border border-slate-700/80 rounded-lg px-2.5 py-1.5 transition-colors">
        <Home className="w-3.5 h-3.5 text-sky-400 shrink-0" />
        <select
          value={workplaceModality}
          onChange={(e) => onWorkplaceModalityChange(e.target.value)}
          aria-label="Filter by workplace modality"
          className="bg-transparent text-slate-200 font-medium focus:outline-none cursor-pointer"
        >
          <option value="all" className="bg-slate-900 text-slate-200">
            All Workplaces
          </option>
          <option value="remote" className="bg-slate-900 text-slate-200">
            Remote Only
          </option>
          <option value="hybrid" className="bg-slate-900 text-slate-200">
            Hybrid
          </option>
          <option value="on_site" className="bg-slate-900 text-slate-200">
            On-Site Only
          </option>
        </select>
      </div>

      {/* 3. Commute Radius */}
      <div className="flex items-center gap-1.5 bg-slate-800/90 hover:bg-slate-800 border border-slate-700/80 rounded-lg px-2.5 py-1.5 transition-colors">
        <MapPin className="w-3.5 h-3.5 text-rose-400 shrink-0" />
        <select
          value={maxCommuteMiles === null ? "any" : String(maxCommuteMiles)}
          onChange={(e) =>
            onMaxCommuteMilesChange(e.target.value === "any" ? null : Number(e.target.value))
          }
          aria-label="Filter by commute radius"
          className="bg-transparent text-slate-200 font-medium focus:outline-none cursor-pointer"
        >
          <option value="any" className="bg-slate-900 text-slate-200">
            Commute: Any
          </option>
          <option value="10" className="bg-slate-900 text-slate-200">
            Within 10 miles
          </option>
          <option value="25" className="bg-slate-900 text-slate-200">
            Within 25 miles
          </option>
          <option value="50" className="bg-slate-900 text-slate-200">
            Within 50 miles
          </option>
        </select>
      </div>

      {/* 4. Minimum Base Salary */}
      <div className="flex items-center gap-1.5 bg-slate-800/90 hover:bg-slate-800 border border-slate-700/80 rounded-lg px-2.5 py-1.5 transition-colors">
        <DollarSign className="w-3.5 h-3.5 text-amber-400 shrink-0" />
        <select
          value={minBaseSalary === null ? "any" : String(minBaseSalary)}
          onChange={(e) =>
            onMinBaseSalaryChange(e.target.value === "any" ? null : Number(e.target.value))
          }
          aria-label="Filter by minimum base salary"
          className="bg-transparent text-slate-200 font-medium focus:outline-none cursor-pointer"
        >
          <option value="any" className="bg-slate-900 text-slate-200">
            Min Base: Any
          </option>
          <option value="100000" className="bg-slate-900 text-slate-200">
            $100k+
          </option>
          <option value="140000" className="bg-slate-900 text-slate-200">
            $140k+
          </option>
          <option value="180000" className="bg-slate-900 text-slate-200">
            $180k+
          </option>
          <option value="220000" className="bg-slate-900 text-slate-200">
            $220k+
          </option>
        </select>
      </div>

      {/* 5. Date Posted */}
      {onPostedWithinChange && (
        <div className="flex items-center gap-1.5 bg-slate-800/90 hover:bg-slate-800 border border-slate-700/80 rounded-lg px-2.5 py-1.5 transition-colors">
          <Calendar className="w-3.5 h-3.5 text-indigo-400 shrink-0" />
          <select
            value={postedWithin || ""}
            onChange={(e) => onPostedWithinChange(e.target.value)}
            aria-label="Filter by date posted"
            className="bg-transparent text-slate-200 font-medium focus:outline-none cursor-pointer"
          >
            <option value="" className="bg-slate-900 text-slate-200">
              Any Time
            </option>
            <option value="1" className="bg-slate-900 text-slate-200">
              Past 24 Hours
            </option>
            <option value="7" className="bg-slate-900 text-slate-200">
              Past Week
            </option>
            <option value="14" className="bg-slate-900 text-slate-200">
              Past 2 Weeks
            </option>
            <option value="30" className="bg-slate-900 text-slate-200">
              Past Month
            </option>
          </select>
        </div>
      )}

      {/* 6. Minimum Probability Band */}
      {onMinScoreChange && (
        <div
          className={`flex items-center gap-1.5 bg-slate-800/90 border border-slate-700/80 rounded-lg px-2.5 py-1.5 transition-colors ${
            searchMode === "unbiased" ? "opacity-50" : "hover:bg-slate-800"
          }`}
        >
          <TrendingUp className="w-3.5 h-3.5 text-sky-400 shrink-0" />
          <select
            value={minScore || 0.0}
            onChange={(e) => onMinScoreChange(parseFloat(e.target.value))}
            disabled={searchMode === "unbiased"}
            aria-label="Minimum probability band filter"
            title={
              searchMode === "unbiased"
                ? "Probability bands apply only in Grounded mode"
                : "Filter by minimum match probability"
            }
            className="bg-transparent text-slate-200 font-medium focus:outline-none cursor-pointer disabled:cursor-not-allowed"
          >
            <option value={0.0} className="bg-slate-900 text-slate-200">
              All Probability Bands
            </option>
            <option value={0.5} className="bg-slate-900 text-slate-200">
              Moderate+ (≥ 50%)
            </option>
            <option value={0.75} className="bg-slate-900 text-slate-200">
              High Probability Only (≥ 75%)
            </option>
          </select>
        </div>
      )}
    </div>
  );
}
