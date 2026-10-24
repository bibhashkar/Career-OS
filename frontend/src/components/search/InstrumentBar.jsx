import React from "react";
import {
  ShieldCheck,
  Home,
  MapPin,
  DollarSign,
  Compass,
  ArrowUpDown,
  Sparkles,
} from "lucide-react";

export function InstrumentBar({
  searchMode,
  onSearchModeChange,
  workAuthTier,
  onWorkAuthTierChange,
  workplaceModality,
  onWorkplaceModalityChange,
  minBaseSalary,
  onMinBaseSalaryChange,
  maxCommuteMiles,
  onMaxCommuteMilesChange,
  sortBy,
  onSortByChange,
}) {
  return (
    <div className="flex flex-wrap items-center gap-2 py-2.5 px-3 bg-neutral-900/60 backdrop-blur-md border border-neutral-800 rounded-xl text-xs">
      {/* 1. Work Authorization Facet */}
      <div className="flex items-center gap-1.5 bg-neutral-800/80 hover:bg-neutral-800 border border-neutral-700/60 rounded-lg px-2.5 py-1.5 transition-colors">
        <ShieldCheck className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
        <select
          value={workAuthTier}
          onChange={(e) => onWorkAuthTierChange(e.target.value)}
          aria-label="Filter by work authorization"
          className="bg-transparent text-neutral-200 font-medium focus:outline-none cursor-pointer"
        >
          <option value="all" className="bg-neutral-900 text-neutral-200">
            Work Auth: Any
          </option>
          <option value="f1_opt_cpt" className="bg-neutral-900 text-neutral-200">
            F-1 OPT / E-Verify
          </option>
          <option value="h1b_transfer_sponsor" className="bg-neutral-900 text-neutral-200">
            H-1B Sponsor (USCIS)
          </option>
          <option value="domestic_only" className="bg-neutral-900 text-neutral-200">
            Domestic Only (US Citizen/PR)
          </option>
        </select>
      </div>

      {/* 2. Workplace Modality Facet */}
      <div className="flex items-center gap-1.5 bg-neutral-800/80 hover:bg-neutral-800 border border-neutral-700/60 rounded-lg px-2.5 py-1.5 transition-colors">
        <Home className="w-3.5 h-3.5 text-sky-400 shrink-0" />
        <select
          value={workplaceModality}
          onChange={(e) => onWorkplaceModalityChange(e.target.value)}
          aria-label="Filter by workplace modality"
          className="bg-transparent text-neutral-200 font-medium focus:outline-none cursor-pointer"
        >
          <option value="all" className="bg-neutral-900 text-neutral-200">
            Modality: All
          </option>
          <option value="remote" className="bg-neutral-900 text-neutral-200">
            Remote
          </option>
          <option value="hybrid" className="bg-neutral-900 text-neutral-200">
            Hybrid
          </option>
          <option value="on_site" className="bg-neutral-900 text-neutral-200">
            On-Site
          </option>
        </select>
      </div>

      {/* 3. Commute Radius */}
      <div className="flex items-center gap-1.5 bg-neutral-800/80 hover:bg-neutral-800 border border-neutral-700/60 rounded-lg px-2.5 py-1.5 transition-colors">
        <MapPin className="w-3.5 h-3.5 text-rose-400 shrink-0" />
        <select
          value={maxCommuteMiles === null ? "any" : String(maxCommuteMiles)}
          onChange={(e) =>
            onMaxCommuteMilesChange(e.target.value === "any" ? null : Number(e.target.value))
          }
          aria-label="Filter by commute radius"
          className="bg-transparent text-neutral-200 font-medium focus:outline-none cursor-pointer"
        >
          <option value="any" className="bg-neutral-900 text-neutral-200">
            Commute: Any
          </option>
          <option value="10" className="bg-neutral-900 text-neutral-200">
            Within 10 miles
          </option>
          <option value="25" className="bg-neutral-900 text-neutral-200">
            Within 25 miles
          </option>
          <option value="50" className="bg-neutral-900 text-neutral-200">
            Within 50 miles
          </option>
        </select>
      </div>

      {/* 4. Minimum Base Salary */}
      <div className="flex items-center gap-1.5 bg-neutral-800/80 hover:bg-neutral-800 border border-neutral-700/60 rounded-lg px-2.5 py-1.5 transition-colors">
        <DollarSign className="w-3.5 h-3.5 text-amber-400 shrink-0" />
        <select
          value={minBaseSalary === null ? "any" : String(minBaseSalary)}
          onChange={(e) =>
            onMinBaseSalaryChange(e.target.value === "any" ? null : Number(e.target.value))
          }
          aria-label="Filter by minimum base salary"
          className="bg-transparent text-neutral-200 font-medium focus:outline-none cursor-pointer"
        >
          <option value="any" className="bg-neutral-900 text-neutral-200">
            Min Base: Any
          </option>
          <option value="100000" className="bg-neutral-900 text-neutral-200">
            $100k+
          </option>
          <option value="140000" className="bg-neutral-900 text-neutral-200">
            $140k+
          </option>
          <option value="180000" className="bg-neutral-900 text-neutral-200">
            $180k+
          </option>
          <option value="220000" className="bg-neutral-900 text-neutral-200">
            $220k+
          </option>
        </select>
      </div>

      {/* 5. Sort By Control */}
      <div className="flex items-center gap-1.5 bg-neutral-800/80 hover:bg-neutral-800 border border-neutral-700/60 rounded-lg px-2.5 py-1.5 transition-colors">
        <ArrowUpDown className="w-3.5 h-3.5 text-neutral-400 shrink-0" />
        <select
          value={sortBy}
          onChange={(e) => onSortByChange(e.target.value)}
          aria-label="Sort jobs by"
          className="bg-transparent text-neutral-200 font-medium focus:outline-none cursor-pointer"
        >
          <option value="score" className="bg-neutral-900 text-neutral-200">
            Sort: Match Score
          </option>
          <option value="date" className="bg-neutral-900 text-neutral-200">
            Sort: Newest First
          </option>
          <option value="salary" className="bg-neutral-900 text-neutral-200">
            Sort: Highest Salary
          </option>
        </select>
      </div>

      {/* 6. Dual Engine Mode Switch */}
      <div className="ml-auto flex items-center gap-1 bg-neutral-800/80 border border-neutral-700/60 rounded-lg p-0.5">
        <button
          type="button"
          onClick={() => onSearchModeChange("cv_grounded")}
          className={`flex items-center gap-1 px-2.5 py-1 rounded-md font-medium transition-all ${
            searchMode === "cv_grounded"
              ? "bg-cyan-600 text-white shadow-sm"
              : "text-neutral-400 hover:text-neutral-200"
          }`}
          title="Personalized candidate-grounded match scoring (P(Match))"
        >
          <Sparkles className="w-3 h-3" />
          <span>Grounded</span>
        </button>

        <button
          type="button"
          onClick={() => onSearchModeChange("unbiased")}
          className={`flex items-center gap-1 px-2.5 py-1 rounded-md font-medium transition-all ${
            searchMode === "unbiased"
              ? "bg-purple-600 text-white shadow-sm"
              : "text-neutral-400 hover:text-neutral-200"
          }`}
          title="Market Explorer mode: raw discovery without candidate bias"
        >
          <Compass className="w-3 h-3" />
          <span>Explorer</span>
        </button>
      </div>
    </div>
  );
}

