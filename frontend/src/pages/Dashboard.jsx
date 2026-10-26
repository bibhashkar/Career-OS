import React, { useState, useEffect, useCallback } from "react";
import { useSearchParams } from "react-router-dom";
import {
  Search,
  MapPin,
  ChevronDown,
  ChevronUp,
  ChevronLeft,
  ChevronRight,
  FileText,
  MessageSquare,
  AlertCircle,
  Loader2,
  Briefcase,
  CheckCircle2,
  Sparkles,
  TrendingUp,
  RefreshCw,
  Clock,
  X,
  Compass,
  ArrowUpDown,
  Zap,
  SlidersHorizontal,
  Home,
  Lock,
  Upload,
  PlusCircle,
  ShieldCheck,
} from "lucide-react";
import { getJobMatches } from "../services/api";
import { JobProvenanceBadge } from "../components/JobProvenanceBadge";
import { JobDiagnosticModal } from "../components/JobDiagnosticModal";
import { JobDetailPanel } from "../components/JobDetailPanel";
import {
  TokenizedOmnibar,
  CHIP_TYPE_ICONS,
  CHIP_TYPE_COLORS,
  formatEntityLabel,
} from "../components/search/TokenizedOmnibar";
import { SearchFilterModal } from "../components/search/SearchFilterModal";
import { EmptyStateRelaxer } from "../components/search/EmptyStateRelaxer";
import { formatWorkplaceType } from "../utils/statusBadges";

const PAGE_SIZE = 15;

/**
 * Builds an array of page numbers and ellipsis tokens for pagination.
 * e.g. [1, 2, 3] or [1, 2, 3, 4, 5, "...", 12]
 */
export function generatePaginationPages(currentPage, totalPages, maxVisible = 5) {
  if (totalPages <= 1) return [1];
  if (totalPages <= 7) {
    return Array.from({ length: totalPages }, (_, i) => i + 1);
  }
  if (currentPage <= 4) {
    return [1, 2, 3, 4, 5, "...", totalPages];
  }
  if (currentPage >= totalPages - 3) {
    return [
      1,
      "...",
      totalPages - 4,
      totalPages - 3,
      totalPages - 2,
      totalPages - 1,
      totalPages,
    ];
  }
  return [
    1,
    "...",
    currentPage - 1,
    currentPage,
    currentPage + 1,
    "...",
    totalPages,
  ];
}

const QUICK_MODALITIES = [
  { value: "", label: "All Workplaces" },
  { value: "remote", label: "Remote" },
  { value: "hybrid", label: "Hybrid" },
  { value: "on_site", label: "On-Site" },
];

function normalizeJobMatch(match) {
  return {
    id: match.job_id,
    title: match.title,
    company_name: match.company_name,
    location: match.location,
    workplace_type: match.workplace_type,
    salary_range: match.salary_range,
    visa_sponsorship: match.visa_sponsorship,
    apply_url: match.apply_url,
    ats_requirements: {
      required_skills: [
        ...(match.matched_skills || []),
        ...(match.missing_dealbreakers || []),
      ],
      visa_sponsorship: match.visa_sponsorship === "yes",
    },
  };
}

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

const FILTER_STORAGE_KEY = "career_os_feed_filters";

export function Dashboard({
  onSelectJob,
  onStartInterview,
  activePersona,
  defaultTab = "matches",
  onOpenProfileModal,
}) {
  const [searchParams, setSearchParams] = useSearchParams();

  // Helper to read initial state from URL search params or localStorage
  const getInitialParam = useCallback(
    (key, fallback) => {
      const fromUrl = searchParams.get(key);
      if (fromUrl !== null) return fromUrl;
      try {
        const saved = localStorage.getItem(FILTER_STORAGE_KEY);
        if (saved) {
          const parsed = JSON.parse(saved);
          if (parsed[key] !== undefined && parsed[key] !== null)
            return parsed[key];
        }
      } catch {
        // ignore JSON parse error
      }
      return fallback;
    },
    [searchParams],
  );

  // --- Matches State (ADR-008 Engine) ---
  const [matches, setMatches] = useState([]);
  const [matchesLoading, setMatchesLoading] = useState(false);
  const [matchesError, setMatchesError] = useState(null);
  const [totalMatches, setTotalMatches] = useState(0);
  const [page, setPage] = useState(1);
  const [selectedMatchId, setSelectedMatchId] = useState(() =>
    getInitialParam("selected", null),
  );
  const [selectedJob, setSelectedJob] = useState(null);
  const [isFilterModalOpen, setIsFilterModalOpen] = useState(false);

  // Candidate Intelligence & Cold-Start State
  const [profileReady, setProfileReady] = useState(false);
  const [profileStatusReason, setProfileStatusReason] = useState("");
  const [completenessData, setCompletenessData] = useState(null);

  // Filter states
  const [searchQuery, setSearchQuery] = useState(() =>
    getInitialParam("q", ""),
  );
  const [locationFilter, setLocationFilter] = useState(() =>
    getInitialParam("loc", ""),
  );
  const [modalityFilter, setModalityFilter] = useState(() =>
    getInitialParam("modality", ""),
  );
  const [postedWithinFilter, setPostedWithinFilter] = useState(() =>
    getInitialParam("posted", ""),
  );
  const [minScoreFilter, setMinScoreFilter] = useState(() => {
    const val = parseFloat(getInitialParam("min_score", "0.0"));
    return isNaN(val) ? 0.0 : val;
  });
  const [sortBy, setSortBy] = useState(() => getInitialParam("sort", "score"));
  const [selectedJobForDiag, setSelectedJobForDiag] = useState(null);

  // Command-Facet Omnibar & Discovery Engine States (Spec v1.0.0)
  const [searchMode, setSearchMode] = useState(() =>
    getInitialParam("mode", "cv_grounded"),
  );
  const [workAuthTier, setWorkAuthTier] = useState(() => {
    const auth = getInitialParam("auth", "");
    if (auth) return auth;
    if (getInitialParam("visa", "false") === "true")
      return "h1b_transfer_sponsor";
    return "all";
  });
  const [minBaseSalary, setMinBaseSalary] = useState(() => {
    const s = getInitialParam("salary", "");
    return s ? Number(s) : null;
  });
  const [maxCommuteMiles, setMaxCommuteMiles] = useState(() => {
    const c = getInitialParam("commute", "");
    return c ? Number(c) : null;
  });
  const [chips, setChips] = useState(() => {
    const savedChips = getInitialParam("chips", "");
    if (savedChips) {
      try {
        const parsed =
          typeof savedChips === "string"
            ? JSON.parse(decodeURIComponent(savedChips))
            : savedChips;
        return Array.isArray(parsed) ? parsed : [];
      } catch {
        return [];
      }
    }
    return [];
  });
  const [diagnostics, setDiagnostics] = useState(null);

  const handleAddChip = (chip) => {
    setPage(1);
    setSelectedJob(null);
    if (chip.type === "modality") {
      setModalityFilter(chip.value === "all" ? "" : chip.value);
      return;
    }
    setChips((prev) => {
      if (
        prev.some(
          (c) =>
            c.type === chip.type &&
            c.value.toLowerCase() === chip.value.toLowerCase(),
        )
      ) {
        return prev;
      }
      return [
        ...prev,
        {
          ...chip,
          label: formatEntityLabel(chip.type, chip.value),
          id: chip.id || `${chip.type}-${Date.now()}`,
        },
      ];
    });
  };

  const handleToggleChip = (type, value) => {
    setPage(1);
    setSelectedJob(null);
    setChips((prev) => {
      const exists = prev.find(
        (c) => c.type === type && c.value.toLowerCase() === value.toLowerCase(),
      );
      if (exists) {
        return prev.filter((c) => c.id !== exists.id);
      }
      return [
        ...prev,
        {
          id: `${type}-${value}-${Date.now()}`,
          type,
          value,
          label: formatEntityLabel(type, value),
        },
      ];
    });
  };

  const handleRemoveChip = (chipId) => {
    setPage(1);
    setSelectedJob(null);
    setChips((prev) => prev.filter((c) => c.id !== chipId));
  };

  const handleApplyRelaxation = (patch) => {
    if (!patch) return;
    setPage(1);
    setSelectedJob(null);
    if ("work_auth_tier" in patch) {
      setWorkAuthTier(patch.work_auth_tier);
    }
    if ("max_commute_miles" in patch) {
      setMaxCommuteMiles(patch.max_commute_miles);
    }
    if ("min_base_salary_usd" in patch) {
      setMinBaseSalary(patch.min_base_salary_usd);
    }
    if ("workplace_modality" in patch) {
      setModalityFilter(
        patch.workplace_modality === "all" ? "" : patch.workplace_modality,
      );
    }
    if ("must_have_skills" in patch) {
      setChips((prev) => prev.filter((c) => c.type !== "skill"));
    }
    if ("companies" in patch) {
      setChips((prev) => prev.filter((c) => c.type !== "company"));
    }
    if ("industries" in patch || "target_industries" in patch) {
      setChips((prev) => prev.filter((c) => c.type !== "industry"));
    }
    if ("raw_query" in patch) {
      setSearchQuery("");
    }
    setDiagnostics(null);
  };

  // Synchronize filter state to URL search parameters and localStorage
  useEffect(() => {
    const params = new URLSearchParams();
    if (searchQuery.trim()) params.set("q", searchQuery.trim());
    if (locationFilter.trim()) params.set("loc", locationFilter.trim());
    if (modalityFilter) params.set("modality", modalityFilter);
    if (postedWithinFilter) params.set("posted", postedWithinFilter);
    if (minScoreFilter > 0) params.set("min_score", String(minScoreFilter));
    if (sortBy && sortBy !== "score") params.set("sort", sortBy);
    if (searchMode && searchMode !== "cv_grounded")
      params.set("mode", searchMode);
    if (workAuthTier && workAuthTier !== "all")
      params.set("auth", workAuthTier);
    if (minBaseSalary !== null) params.set("salary", String(minBaseSalary));
    if (maxCommuteMiles !== null)
      params.set("commute", String(maxCommuteMiles));
    if (selectedMatchId)
      params.set("selected", selectedMatchId);
    if (chips.length > 0)
      params.set("chips", encodeURIComponent(JSON.stringify(chips)));

    try {
      const savedState = {
        q: searchQuery,
        loc: locationFilter,
        modality: modalityFilter,
        posted: postedWithinFilter,
        min_score: minScoreFilter,
        sort: sortBy,
        mode: searchMode,
        auth: workAuthTier,
        salary: minBaseSalary,
        commute: maxCommuteMiles,
        chips,
        selected: selectedMatchId,
      };
      localStorage.setItem(FILTER_STORAGE_KEY, JSON.stringify(savedState));
    } catch {
      // ignore
    }

    setSearchParams(params, { replace: true });
  }, [
    searchQuery,
    locationFilter,
    modalityFilter,
    postedWithinFilter,
    minScoreFilter,
    sortBy,
    searchMode,
    workAuthTier,
    minBaseSalary,
    maxCommuteMiles,
    chips,
    selectedMatchId,
    setSearchParams,
  ]);

  const handleClearFilters = () => {
    setPage(1);
    setSelectedJob(null);
    setSearchQuery("");
    setLocationFilter("");
    setModalityFilter("");
    setPostedWithinFilter("");
    setMinScoreFilter(0.0);
    setSortBy("score");
    setSearchMode("cv_grounded");
    setWorkAuthTier("all");
    setMinBaseSalary(null);
    setMaxCommuteMiles(null);
    setChips([]);
    setDiagnostics(null);
    try {
      localStorage.removeItem(FILTER_STORAGE_KEY);
    } catch {
      // ignore
    }
  };

  const handleResetAdvancedFilters = () => {
    setPage(1);
    setSelectedJob(null);
    setWorkAuthTier("all");
    setMinBaseSalary(null);
    setMaxCommuteMiles(null);
    setPostedWithinFilter("");
    setMinScoreFilter(0.0);
    setChips((prev) =>
      prev.filter((c) => c.type !== "seniority" && c.type !== "industry"),
    );
  };

  const activeFilterCount =
    (searchQuery.trim() ? 1 : 0) +
    (locationFilter.trim() ? 1 : 0) +
    (modalityFilter ? 1 : 0) +
    (postedWithinFilter ? 1 : 0) +
    (minScoreFilter > 0 ? 1 : 0) +
    (sortBy !== "score" ? 1 : 0) +
    (workAuthTier !== "all" ? 1 : 0) +
    (minBaseSalary !== null ? 1 : 0) +
    (maxCommuteMiles !== null ? 1 : 0) +
    (searchMode !== "cv_grounded" ? 1 : 0) +
    chips.length;

  const advancedFilterCount =
    (workAuthTier !== "all" ? 1 : 0) +
    (minBaseSalary !== null ? 1 : 0) +
    (maxCommuteMiles !== null ? 1 : 0) +
    (postedWithinFilter ? 1 : 0) +
    (minScoreFilter > 0 ? 1 : 0) +
    chips.filter((c) => c.type === "seniority" || c.type === "industry").length;

  // Fetch Ranked Matches for active persona
  const fetchMatches = useCallback(async () => {
    if (typeof getJobMatches !== "function") return;
    setMatchesLoading(true);
    setMatchesError(null);
    try {
      const params = {
        page,
        page_size: PAGE_SIZE,
        min_score: minScoreFilter,
        sort_by: sortBy,
        search_mode: searchMode,
      };
      if (activePersona?.id && activePersona.id !== "universal") {
        params.persona_id = activePersona.id;
      }
      if (searchQuery.trim()) {
        params.q = searchQuery.trim();
      }
      if (locationFilter.trim()) {
        params.location = locationFilter.trim();
      }
      if (modalityFilter) {
        params.modality = modalityFilter;
      }
      if (postedWithinFilter) {
        params.posted_within = parseInt(postedWithinFilter, 10);
      }
      if (workAuthTier && workAuthTier !== "all") {
        params.work_auth_tier = workAuthTier;
      }
      if (minBaseSalary !== null) {
        params.min_base_salary_usd = minBaseSalary;
      }
      if (maxCommuteMiles !== null) {
        params.max_commute_miles = maxCommuteMiles;
      }
      const companyChips = chips
        .filter((c) => c.type === "company")
        .map((c) => c.value);
      if (companyChips.length > 0) {
        params.companies = companyChips;
      }
      const indChips = chips
        .filter((c) => c.type === "industry")
        .map((c) => c.value);
      if (indChips.length > 0) {
        params.industries = indChips;
      }
      const senChips = chips
        .filter((c) => c.type === "seniority")
        .map((c) => c.value);
      if (senChips.length > 0) {
        params.seniority = senChips;
      }
      const skillChips = chips
        .filter((c) => c.type === "skill")
        .map((c) => c.value);
      if (skillChips.length > 0) {
        params.must_have_skills = skillChips;
      }

      const res = await getJobMatches(params);
      const nextJobs = res?.jobs || [];
      setMatches(nextJobs);
      setTotalMatches(res?.total_count || 0);
      setDiagnostics(res?.diagnostics || null);
      if (res?.profile_ready !== undefined) {
        setProfileReady(Boolean(res.profile_ready));
        if (!res.profile_ready) {
          setSearchMode("unbiased");
        }
      } else {
        const hasScore = nextJobs.some(
          (j) => j.match_score !== null && j.match_score !== undefined,
        );
        setProfileReady(hasScore);
      }
      if (res?.profile_status_reason !== undefined) {
        setProfileStatusReason(res.profile_status_reason);
      }
      if (res?.completeness !== undefined) {
        setCompletenessData(res.completeness);
      }
      if (nextJobs.length === 0) {
        setSelectedMatchId(null);
        setSelectedJob(null);
      } else {
        setSelectedJob((prevJob) => {
          if (!prevJob) {
            const urlSelected = new URLSearchParams(window.location.search).get("selected");
            const foundUrl = urlSelected
              ? nextJobs.find((j) => j.job_id === urlSelected)
              : null;
            const chosen = foundUrl || nextJobs[0];
            setSelectedMatchId(chosen.job_id);
            return chosen;
          }
          const inNext = nextJobs.find((j) => j.job_id === prevJob.job_id);
          if (inNext) {
            setSelectedMatchId(inNext.job_id);
            return inNext;
          }
          // Retain selectedJob across page transitions so candidate doesn't lose reading context
          return prevJob;
        });
      }
    } catch (err) {
      if (err.code !== "ERR_NETWORK") {
        console.warn("Failed to fetch job matches:", err);
      }
      setMatchesError(
        err.response?.data?.detail ||
          "Unable to compute candidate job matches. Ensure database has active listings.",
      );
    } finally {
      setMatchesLoading(false);
    }
  }, [
    activePersona,
    page,
    searchQuery,
    locationFilter,
    modalityFilter,
    postedWithinFilter,
    minScoreFilter,
    sortBy,
    searchMode,
    workAuthTier,
    minBaseSalary,
    maxCommuteMiles,
    chips,
  ]);

  // Load matches with debounce when activePersona or filters change
  useEffect(() => {
    const timer = setTimeout(() => {
      fetchMatches();
    }, 250);
    return () => clearTimeout(timer);
  }, [fetchMatches]);

  // Keyboard arrow navigation for opportunity split-view list
  useEffect(() => {
    if (matches.length === 0) return;

    const handleKeyDown = (e) => {
      const tag = document.activeElement?.tagName?.toLowerCase();
      if (
        tag === "input" ||
        tag === "textarea" ||
        tag === "select" ||
        document.activeElement?.isContentEditable
      ) {
        return;
      }

      if (e.key === "ArrowDown") {
        e.preventDefault();
        setSelectedMatchId((currId) => {
          const idx = matches.findIndex((m) => m.job_id === currId);
          const nextIdx = idx === -1 ? 0 : Math.min(matches.length - 1, idx + 1);
          const target = matches[nextIdx];
          if (target) {
            setSelectedJob(target);
            return target.job_id;
          }
          return currId;
        });
      } else if (e.key === "ArrowUp") {
        e.preventDefault();
        setSelectedMatchId((currId) => {
          const idx = matches.findIndex((m) => m.job_id === currId);
          const prevIdx = idx === -1 ? 0 : Math.max(0, idx - 1);
          const target = matches[prevIdx];
          if (target) {
            setSelectedJob(target);
            return target.job_id;
          }
          return currId;
        });
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [matches]);

  const selectedMatch =
    selectedJob ||
    matches.find((m) => m.job_id === selectedMatchId) ||
    matches[0] ||
    null;
  const totalPages = Math.max(1, Math.ceil(totalMatches / PAGE_SIZE));
  const showingFrom = totalMatches === 0 ? 0 : (page - 1) * PAGE_SIZE + 1;
  const showingTo = Math.min(page * PAGE_SIZE, totalMatches);

  return (
    <div className="max-w-7xl mx-auto px-4 py-3 space-y-3 h-full flex flex-col min-h-0 w-full">
      {/* Top Header Bar */}
      <div className="flex items-center justify-between gap-3 pb-3 border-b border-slate-800/80">
        <div className="flex items-center gap-3">
          <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-white flex items-center gap-2">
            <Briefcase className="w-6 h-6 text-sky-400" /> Jobs
          </h1>
        </div>
      </div>

      <div className="space-y-6">
          {/* Brief Daily Search & Filter Bar */}
          <div className="bg-slate-800/90 border border-slate-700/80 rounded-2xl p-4 shadow-xl space-y-3">
            {/* Row 1: Search Inputs (Search bar gets 70% width, Location gets 30% width on md+) */}
            <div className="grid grid-cols-1 md:grid-cols-12 gap-3 items-center">
              <div className="md:col-span-8 lg:col-span-9">
                <TokenizedOmnibar
                  rawQuery={searchQuery}
                  onQueryChange={(val) => {
                    setPage(1);
                    setSearchQuery(val);
                  }}
                  chips={chips}
                  onAddChip={handleAddChip}
                  onSelectModality={(mod) => {
                    setPage(1);
                    setModalityFilter(mod === "all" ? "" : mod);
                  }}
                  onSearch={fetchMatches}
                  isSearching={matchesLoading}
                />
              </div>

              {/* Compact City, State, Country & Region Filter */}
              <div className="relative md:col-span-4 lg:col-span-3">
                <MapPin className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2 pointer-events-none" />
                <input
                  type="text"
                  value={locationFilter}
                  onChange={(e) => {
                    setPage(1);
                    setLocationFilter(e.target.value);
                  }}
                  list="location-presets"
                  placeholder="City, State, or Country..."
                  aria-label="Filter by city, state, country, or region"
                  data-testid="matches-location-input"
                  className="w-full min-h-[42px] pl-10 pr-8 py-2 bg-slate-900/90 border border-slate-700 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-sky-500"
                />
                {locationFilter && (
                  <button
                    onClick={() => {
                      setPage(1);
                      setLocationFilter("");
                    }}
                    aria-label="Clear location filter"
                    className="absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-200"
                  >
                    <X className="w-3.5 h-3.5" />
                  </button>
                )}
                <datalist id="location-presets">
                  <option value="San Francisco, CA" />
                  <option value="New York, NY" />
                  <option value="Seattle, WA" />
                  <option value="California" />
                  <option value="United States" />
                  <option value="London, UK" />
                  <option value="United Kingdom" />
                  <option value="Europe" />
                  <option value="North America" />
                  <option value="Remote" />
                </datalist>
              </div>
            </div>

            {/* Row 1b: Chips & Active Filter Pills Row (Directly Under Omnibar) */}
            {(chips.length > 0 ||
              locationFilter.trim() ||
              modalityFilter ||
              workAuthTier !== "all" ||
              maxCommuteMiles !== null ||
              minBaseSalary !== null ||
              postedWithinFilter ||
              minScoreFilter > 0) && (
              <div
                data-testid="omnibar-chips-row"
                className="flex flex-wrap items-center gap-1.5 pt-0.5 text-xs"
              >
                {/* Tokenized Entity Chips (Clean labels without "Vertical:" prefix) */}
                {chips.map((chip) => {
                  const IconComp = CHIP_TYPE_ICONS[chip.type] || Zap;
                  const colorClass =
                    CHIP_TYPE_COLORS[chip.type] ||
                    "bg-slate-800 text-slate-300 border-slate-700";
                  const cleanLabel = formatEntityLabel(chip.type, chip.value);

                  return (
                    <span
                      key={chip.id}
                      className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-lg text-xs font-medium border ${colorClass} transition-all`}
                    >
                      <IconComp className="w-3 h-3 shrink-0" />
                      <span>{cleanLabel}</span>
                      <button
                        type="button"
                        onClick={() => handleRemoveChip(chip.id)}
                        className="hover:text-white p-0.5 rounded transition-colors"
                        aria-label={`Remove ${cleanLabel}`}
                      >
                        <X className="w-3 h-3" />
                      </button>
                    </span>
                  );
                })}

                {/* Active Facet Pills */}
                {locationFilter.trim() && (
                  <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-lg text-xs font-medium bg-indigo-500/10 text-indigo-300 border border-indigo-500/20">
                    <MapPin className="w-3 h-3 shrink-0" />
                    <span>{locationFilter.trim()}</span>
                    <button
                      type="button"
                      onClick={() => {
                        setPage(1);
                        setLocationFilter("");
                      }}
                      className="hover:text-white p-0.5"
                      aria-label="Remove location filter"
                    >
                      <X className="w-3 h-3" />
                    </button>
                  </span>
                )}

                {workAuthTier !== "all" && (
                  <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-lg text-xs font-medium bg-emerald-500/10 text-emerald-300 border border-emerald-500/20">
                    <ShieldCheck className="w-3 h-3 shrink-0" />
                    <span>
                      {workAuthTier === "f1_opt_cpt"
                        ? "F-1 OPT / E-Verify"
                        : workAuthTier === "h1b_transfer_sponsor"
                          ? "H-1B Sponsor"
                          : "Domestic Only"}
                    </span>
                    <button
                      type="button"
                      onClick={() => {
                        setPage(1);
                        setWorkAuthTier("all");
                      }}
                      className="hover:text-white p-0.5"
                      aria-label="Remove work auth filter"
                    >
                      <X className="w-3 h-3" />
                    </button>
                  </span>
                )}

                {modalityFilter && (
                  <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-lg text-xs font-medium bg-sky-500/10 text-sky-300 border border-sky-500/20">
                    <span>{formatEntityLabel("modality", modalityFilter)}</span>
                    <button
                      type="button"
                      onClick={() => {
                        setPage(1);
                        setModalityFilter("");
                      }}
                      className="hover:text-white p-0.5"
                      aria-label="Remove workplace modality filter"
                    >
                      <X className="w-3 h-3" />
                    </button>
                  </span>
                )}

                {maxCommuteMiles !== null && (
                  <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-lg text-xs font-medium bg-rose-500/10 text-rose-300 border border-rose-500/20">
                    <span>Within {maxCommuteMiles} mi</span>
                    <button
                      type="button"
                      onClick={() => {
                        setPage(1);
                        setMaxCommuteMiles(null);
                      }}
                      className="hover:text-white p-0.5"
                      aria-label="Remove commute filter"
                    >
                      <X className="w-3 h-3" />
                    </button>
                  </span>
                )}

                {minBaseSalary !== null && (
                  <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-lg text-xs font-medium bg-amber-500/10 text-amber-300 border border-amber-500/20">
                    <span>${Math.round(minBaseSalary / 1000)}k+</span>
                    <button
                      type="button"
                      onClick={() => {
                        setPage(1);
                        setMinBaseSalary(null);
                      }}
                      className="hover:text-white p-0.5"
                      aria-label="Remove minimum salary filter"
                    >
                      <X className="w-3 h-3" />
                    </button>
                  </span>
                )}

                {postedWithinFilter && (
                  <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-lg text-xs font-medium bg-slate-700/60 text-slate-300 border border-slate-600">
                    <span>
                      Past{" "}
                      {postedWithinFilter === "1"
                        ? "24h"
                        : `${postedWithinFilter}d`}
                    </span>
                    <button
                      type="button"
                      onClick={() => {
                        setPage(1);
                        setPostedWithinFilter("");
                      }}
                      className="hover:text-white p-0.5"
                      aria-label="Remove posted date filter"
                    >
                      <X className="w-3 h-3" />
                    </button>
                  </span>
                )}

                {minScoreFilter > 0 && (
                  <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-lg text-xs font-medium bg-amber-500/10 text-amber-300 border border-amber-500/20">
                    <span>≥ {Math.round(minScoreFilter * 100)}% Match</span>
                    <button
                      type="button"
                      onClick={() => {
                        setPage(1);
                        setMinScoreFilter(0.0);
                      }}
                      className="hover:text-white p-0.5"
                      aria-label="Remove probability band filter"
                    >
                      <X className="w-3 h-3" />
                    </button>
                  </span>
                )}
              </div>
            )}

            {/* Consolidated Daily Search & Filter Controls */}
            <div className="flex flex-wrap items-center justify-between gap-2.5 pt-2 border-t border-slate-700/50 text-xs">
              {/* Left: Engine Mode Switch & Quick Workplace Modality Pills */}
              <div
                data-testid="search-filters-row"
                className="flex flex-wrap items-center gap-2"
              >
                {/* Dual Engine Mode Switch */}
                <div className="flex items-center gap-1 bg-slate-900/90 border border-slate-700/80 rounded-xl p-0.5 text-xs">
                  <button
                    type="button"
                    onClick={() => {
                      if (!profileReady) {
                        if (onOpenProfileModal) onOpenProfileModal();
                        return;
                      }
                      setPage(1);
                      setSearchMode("cv_grounded");
                    }}
                    className={`flex items-center gap-1 px-2.5 py-1 rounded-lg font-medium transition-all ${
                      !profileReady
                        ? "text-slate-500 hover:text-amber-300 cursor-pointer"
                        : searchMode === "cv_grounded"
                          ? "bg-sky-600 text-white shadow-sm"
                          : "text-slate-400 hover:text-slate-200"
                    }`}
                    title={
                      !profileReady
                        ? "Grounded matching locked: upload CV or add skills to activate personalized matching (0% complete)"
                        : "Personalized candidate-grounded match scoring (P(Match))"
                    }
                  >
                    {!profileReady ? (
                      <Lock className="w-3 h-3 text-amber-400" />
                    ) : (
                      <Sparkles className="w-3 h-3" />
                    )}
                    <span>Grounded{!profileReady ? " (Locked)" : ""}</span>
                  </button>

                  <button
                    type="button"
                    onClick={() => {
                      setPage(1);
                      setSearchMode("unbiased");
                    }}
                    className={`flex items-center gap-1 px-2.5 py-1 rounded-lg font-medium transition-all ${
                      searchMode === "unbiased"
                        ? "bg-indigo-600 text-white shadow-sm"
                        : "text-slate-400 hover:text-slate-200"
                    }`}
                    title="Market Explorer mode: raw discovery without candidate bias"
                  >
                    <Compass className="w-3 h-3" />
                    <span>Explorer</span>
                  </button>
                </div>

                <div className="h-4 w-px bg-slate-700/60 hidden sm:block" />

                {/* Quick Workplace Modality Pills */}
                <div className="flex flex-wrap items-center gap-1">
                  <Home className="w-3.5 h-3.5 text-sky-400 shrink-0 mr-0.5" />
                  {QUICK_MODALITIES.map((item) => {
                    const isSelected = modalityFilter === item.value;
                    return (
                      <button
                        key={item.value || "all"}
                        type="button"
                        onClick={() => {
                          setPage(1);
                          setModalityFilter(item.value);
                        }}
                        className={`px-2.5 py-1 rounded-lg font-medium transition-all ${
                          isSelected
                            ? "bg-sky-600 text-white shadow-sm"
                            : "bg-slate-800/80 text-slate-300 hover:text-white border border-slate-700/70"
                        }`}
                      >
                        {item.label}
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Right: Sort, All Filters Modal Trigger & Actions */}
              <div
                data-testid="sorting-controls-row"
                className="flex flex-wrap items-center gap-2"
              >
                <div className="flex items-center gap-1.5 text-xs text-slate-400">
                  <ArrowUpDown className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                  <span className="hidden sm:inline">Sort:</span>
                  <select
                    value={sortBy}
                    onChange={(e) => {
                      setPage(1);
                      setSortBy(e.target.value);
                    }}
                    aria-label="Sort match opportunities"
                    className="bg-slate-900/90 border border-slate-700 rounded-xl px-2.5 py-1 text-xs text-white focus:outline-none focus:ring-2 focus:ring-sky-500 cursor-pointer"
                  >
                    <option value="score">Best Match</option>
                    <option value="date">Most Recent</option>
                    <option value="salary">Highest Salary</option>
                  </select>
                </div>

                <button
                  type="button"
                  onClick={() => setIsFilterModalOpen(true)}
                  data-testid="open-filter-modal-btn"
                  className={`px-2.5 py-1 rounded-xl font-semibold border transition-all flex items-center gap-1.5 ${
                    advancedFilterCount > 0
                      ? "bg-sky-500/15 text-sky-300 border-sky-500/50"
                      : "bg-slate-800/90 hover:bg-slate-800 text-slate-200 border-slate-700"
                  }`}
                >
                  <SlidersHorizontal className="w-3.5 h-3.5 text-sky-400" />
                  <span>All Filters</span>
                  {advancedFilterCount > 0 && (
                    <span className="px-1.5 py-0.2 rounded-full text-[10px] bg-sky-500 text-white font-bold">
                      {advancedFilterCount}
                    </span>
                  )}
                </button>

                {activeFilterCount > 0 && (
                  <button
                    onClick={handleClearFilters}
                    title="Reset all filters to defaults"
                    className="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-slate-200 text-xs font-medium rounded-xl border border-slate-700 transition-colors"
                  >
                    Clear All
                  </button>
                )}

                <button
                  onClick={fetchMatches}
                  disabled={matchesLoading}
                  className="px-2.5 py-1 bg-slate-700/60 hover:bg-slate-700 text-slate-200 text-xs font-medium rounded-xl transition-colors flex items-center gap-1.5"
                >
                  <RefreshCw
                    className={`w-3.5 h-3.5 ${matchesLoading ? "animate-spin" : ""}`}
                  />
                  <span className="hidden sm:inline">Re-Score</span>
                </button>
              </div>
            </div>
          </div>

          {/* Loading State: Initial load when no matches exist */}
          {matchesLoading && matches.length === 0 && (
            <div className="flex flex-col items-center justify-center py-16 space-y-3">
              <Loader2 className="w-8 h-8 text-sky-400 animate-spin" />
              <p className="text-sm text-slate-400">
                Executing ADR-008 two-stage retrieval & Bayesian reranker...
              </p>
            </div>
          )}

          {/* Cold-Start / 0% Profile Guidance Banner */}
          {!profileReady && (
            <div
              data-testid="cold-start-banner"
              className="p-4 rounded-2xl bg-gradient-to-r from-amber-500/10 via-slate-900 to-sky-500/10 border border-amber-500/30 flex flex-col md:flex-row items-start md:items-center justify-between gap-4 shadow-lg shrink-0"
            >
              <div className="flex items-start gap-3">
                <div className="p-2 rounded-xl bg-amber-500/20 text-amber-300 border border-amber-500/30 mt-0.5">
                  <AlertCircle className="w-5 h-5 shrink-0" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-white flex items-center gap-2">
                    <span>Explorer Mode Active</span>
                    <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-amber-500/20 text-amber-300 border border-amber-500/30">
                      Profile Incomplete (0% Shared)
                    </span>
                  </h3>
                  <p className="text-xs text-slate-300 mt-1 leading-relaxed max-w-3xl">
                    Because you haven't shared your skills or profile with us yet, we cannot calculate personalized match scores or show the best-matched jobs for your background. You are currently browsing in Explorer Mode. Upload your CV or add your skills to unlock personalized Grounded matching.
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-2 shrink-0 w-full md:w-auto">
                <button
                  type="button"
                  onClick={onOpenProfileModal}
                  data-testid="cold-start-upload-cv-btn"
                  className="flex-1 md:flex-none px-3.5 py-2 rounded-xl bg-sky-600 hover:bg-sky-500 text-white font-semibold text-xs transition-all shadow-md flex items-center justify-center gap-1.5 cursor-pointer"
                >
                  <Upload className="w-3.5 h-3.5" />
                  <span>Upload CV / Paste Resume</span>
                </button>
                <button
                  type="button"
                  onClick={onOpenProfileModal}
                  data-testid="cold-start-add-skills-btn"
                  className="flex-1 md:flex-none px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 font-semibold text-xs transition-all flex items-center justify-center gap-1.5 cursor-pointer"
                >
                  <PlusCircle className="w-3.5 h-3.5 text-sky-400" />
                  <span>Add Skills</span>
                </button>
              </div>
            </div>
          )}

          {/* Profile Ready with Incomplete Checklist Nudge (10% - 99%) */}
          {profileReady && completenessData && completenessData.completeness_score < 100 && (
            <div className="px-3.5 py-2 rounded-xl bg-sky-950/40 border border-sky-800/40 flex items-center justify-between gap-3 text-xs text-slate-300 shrink-0">
              <div className="flex items-center gap-2 truncate">
                <Sparkles className="w-4 h-4 text-sky-400 shrink-0" />
                <span className="truncate">
                  Career Profile is <strong className="text-sky-300 font-bold">{completenessData.completeness_score}% complete</strong>.
                  {completenessData.missing_steps?.length > 0 && (
                    <span className="text-slate-400 ml-1.5 hidden sm:inline">
                      Next: {completenessData.missing_steps[0].prompt}
                    </span>
                  )}
                </span>
              </div>
              <button
                type="button"
                onClick={onOpenProfileModal}
                className="text-sky-400 hover:text-sky-300 font-semibold text-[11px] whitespace-nowrap cursor-pointer hover:underline"
              >
                Boost Accuracy →
              </button>
            </div>
          )}

          {/* Error State */}
          {matchesError && !matchesLoading && (
            <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <AlertCircle className="w-5 h-5 text-rose-400" />
                <span className="text-sm">{matchesError}</span>
              </div>
              <button
                onClick={fetchMatches}
                className="text-xs px-3 py-1.5 bg-rose-500/20 hover:bg-rose-500/30 rounded-lg text-rose-200 transition-colors"
              >
                Retry
              </button>
            </div>
          )}

          {/* Empty Matches State */}
          {!matchesLoading && !matchesError && matches.length === 0 && (
            <EmptyStateRelaxer
              diagnostics={diagnostics}
              onApplyRelaxation={handleApplyRelaxation}
              onResetFilters={handleClearFilters}
            />
          )}

          {/* Master-Detail Split-Pane Opportunities View (Preserved During Pagination) */}
          {(!matchesLoading || matches.length > 0) &&
            !matchesError &&
            matches.length > 0 && (
              <div className="flex-1 min-h-0 flex flex-col space-y-2">
                <div
                  data-testid="matches-split-pane"
                  className="flex-1 min-h-0 grid grid-cols-1 lg:grid-cols-12 gap-5 items-stretch overflow-hidden"
                >
                  {/* LEFT PANEL (5 cols): Equal-height Flex Container with Scrollable Opportunity List + Pinned Pagination */}
                  <div
                    className="lg:col-span-5 h-full min-h-0 flex flex-col bg-slate-900/60 border border-slate-800 rounded-2xl overflow-hidden p-3"
                    data-testid="matches-left-list"
                  >
                    {/* Left Panel Header Counter */}
                    <div className="shrink-0 flex items-center justify-between pb-2 border-b border-slate-800/80 mb-2">
                      <h2 className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                        {searchMode === "unbiased"
                          ? `Market Opportunities (${totalMatches})`
                          : `Ranked Matches (${totalMatches})`}
                      </h2>
                      <span
                        className="text-[11px] text-slate-500"
                        data-testid="pagination-summary"
                      >
                        Showing {showingFrom}–{showingTo} of {totalMatches} (max{" "}
                        {PAGE_SIZE} per page)
                      </span>
                    </div>

                    {/* Scrollable Match Cards List with Subtle Pagination Loading Overlay */}
                    <div className="relative flex-1 overflow-y-auto pr-1 space-y-2">
                      {matchesLoading && (
                        <div className="absolute inset-0 bg-slate-900/60 backdrop-blur-[1px] z-10 flex items-center justify-center rounded-xl pointer-events-none">
                          <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-800 border border-slate-700 text-xs text-sky-300 shadow-lg">
                            <Loader2 className="w-3.5 h-3.5 animate-spin" />
                            <span>Updating matches...</span>
                          </div>
                        </div>
                      )}
                      {matches.map((match) => {
                        const isSelected =
                          selectedMatch?.job_id === match.job_id;
                        const showScore =
                          profileReady &&
                          searchMode !== "unbiased" &&
                          match.match_score !== null &&
                          match.match_score !== undefined;
                        const matchPct = showScore
                          ? Math.round(match.match_score * 100)
                          : null;
                        const isHigh = match.probability_band === "high";
                        const isModerate = match.probability_band === "moderate";

                        return (
                          <div
                            key={match.job_id}
                            role="button"
                            tabIndex={0}
                            onClick={() => {
                              setSelectedMatchId(match.job_id);
                              setSelectedJob(match);
                            }}
                            onKeyDown={(e) => {
                              if (e.key === "Enter" || e.key === " ") {
                                e.preventDefault();
                                setSelectedMatchId(match.job_id);
                                setSelectedJob(match);
                              }
                            }}
                            data-testid={`match-card-${match.job_id}`}
                            className={`text-left rounded-xl p-3 border transition-all cursor-pointer space-y-2 ${
                              isSelected
                                ? "bg-slate-800/95 border-sky-500 ring-1 ring-sky-500/40 shadow-md shadow-sky-950/50"
                                : "bg-slate-800/50 border-slate-700/60 hover:bg-slate-800/80 hover:border-slate-600"
                            }`}
                          >
                            <div className="flex items-start justify-between gap-2">
                              <div className="space-y-0.5 min-w-0">
                                <h3 className="text-xs font-bold text-white leading-snug truncate">
                                  {match.title}
                                </h3>
                                <p className="text-[11px] font-medium text-sky-300 truncate">
                                  {match.company_name}
                                </p>
                              </div>

                              {showScore && (
                                <span
                                  className={`shrink-0 text-[10px] font-extrabold px-2 py-0.5 rounded-md flex items-center gap-1 ${
                                    isHigh
                                      ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/40"
                                      : isModerate
                                        ? "bg-amber-500/20 text-amber-400 border border-amber-500/40"
                                        : "bg-sky-500/20 text-sky-300 border border-sky-500/40"
                                  }`}
                                >
                                  <TrendingUp className="w-2.5 h-2.5" />
                                  {matchPct}% Match
                                </span>
                              )}
                            </div>

                            <div className="flex flex-wrap items-center gap-2 text-[10px] text-slate-400">
                              <span className="flex items-center gap-1">
                                <MapPin className="w-2.5 h-2.5 text-slate-500 shrink-0" />
                                {match.location}
                              </span>
                              {match.workplace_type && (
                                <span className="px-1.5 py-0.2 rounded bg-slate-900 text-slate-300 border border-slate-700 text-[9px] font-semibold">
                                  {formatWorkplaceType(match.workplace_type)}
                                </span>
                              )}
                              {match.posted_at && (
                                <span className="flex items-center gap-1 text-slate-400">
                                  <Clock className="w-2.5 h-2.5 text-slate-500 shrink-0" />
                                  {formatRelativeTime(match.posted_at)}
                                </span>
                              )}
                              {match.salary_range && (
                                <span className="text-emerald-400 font-medium">
                                  {match.salary_range}
                                </span>
                              )}
                            </div>

                            {/* Top 3 Matched Skills Preview */}
                            {showScore && match.matched_skills?.length > 0 && (
                              <div className="flex flex-wrap items-center gap-1 pt-0.5">
                                {match.matched_skills
                                  .slice(0, 3)
                                  .map((s, idx) => (
                                    <span
                                      key={idx}
                                      className="text-[9px] px-1.5 py-0.2 rounded-full bg-emerald-500/10 text-emerald-300 border border-emerald-500/20"
                                    >
                                      {s}
                                    </span>
                                  ))}
                                {match.matched_skills.length > 3 && (
                                  <span className="text-[9px] text-slate-500">
                                    +{match.matched_skills.length - 3} more
                                  </span>
                                )}
                              </div>
                            )}
                          </div>
                        );
                      })}
                    </div>

                    {/* Pinned Pagination Footer Bar with Interactive Multi-Page Numbered Buttons */}
                    {totalPages > 1 && (
                      <div
                        data-testid="matches-pagination"
                        className="shrink-0 flex items-center justify-between pt-2 mt-2 border-t border-slate-800 text-xs"
                      >
                        <button
                          type="button"
                          disabled={page <= 1}
                          onClick={() => setPage((p) => Math.max(1, p - 1))}
                          aria-label="Previous"
                          className="px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 disabled:opacity-40 disabled:cursor-not-allowed text-slate-200 font-medium border border-slate-700 flex items-center gap-1 transition-colors text-xs"
                        >
                          <ChevronLeft className="w-3 h-3" />
                          <span className="hidden sm:inline">Previous</span>
                        </button>

                        {/* Numbered Page Buttons with Direct Jumping */}
                        <div className="flex items-center gap-1">
                          {generatePaginationPages(page, totalPages).map(
                            (item, idx) => {
                              if (item === "...") {
                                return (
                                  <span
                                    key={`ellipsis-${idx}`}
                                    className="px-1 text-slate-500 font-bold select-none text-xs"
                                  >
                                    ...
                                  </span>
                                );
                              }
                              const isCurrent = item === page;
                              return (
                                <button
                                  key={`page-${item}`}
                                  type="button"
                                  onClick={() => setPage(item)}
                                  aria-label={`Page ${item}`}
                                  aria-current={isCurrent ? "page" : undefined}
                                  className={`min-w-[28px] h-7 px-1.5 rounded-lg text-xs font-semibold transition-all ${
                                    isCurrent
                                      ? "bg-sky-600 text-white shadow-sm shadow-sky-600/30"
                                      : "bg-slate-800/80 hover:bg-slate-700 text-slate-300 hover:text-white border border-slate-700/60"
                                  }`}
                                >
                                  {item}
                                </button>
                              );
                            },
                          )}
                        </div>

                        <button
                          type="button"
                          disabled={page >= totalPages}
                          onClick={() =>
                            setPage((p) => Math.min(totalPages, p + 1))
                          }
                          aria-label="Next"
                          className="px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 disabled:opacity-40 disabled:cursor-not-allowed text-slate-200 font-medium border border-slate-700 flex items-center gap-1 transition-colors text-xs"
                        >
                          <span className="hidden sm:inline">Next</span>
                          <ChevronRight className="w-3 h-3" />
                        </button>
                      </div>
                    )}
                  </div>

                {/* RIGHT PANEL (7 cols): Full Height Job Detail Panel */}
                <div className="lg:col-span-7 h-full min-h-0 overflow-hidden">
                  <JobDetailPanel
                    match={selectedMatch}
                    searchMode={searchMode}
                    profileReady={profileReady}
                    profileStatusReason={profileStatusReason}
                    completeness={completenessData}
                    onOpenProfileModal={onOpenProfileModal}
                    onTailorCV={(m) => onSelectJob(normalizeJobMatch(m))}
                    onStartInterview={(m) =>
                      onStartInterview(normalizeJobMatch(m))
                    }
                    onOpenDiagnostics={(m) => setSelectedJobForDiag(m)}
                  />
                </div>
              </div>
            </div>
          )}
        </div>

      {/* Detailed Search Filter Configuration Modal */}
      <SearchFilterModal
        isOpen={isFilterModalOpen}
        onClose={() => setIsFilterModalOpen(false)}
        workAuthTier={workAuthTier}
        onWorkAuthTierChange={(val) => {
          setPage(1);
          setWorkAuthTier(val);
        }}
        minBaseSalary={minBaseSalary}
        onMinBaseSalaryChange={(val) => {
          setPage(1);
          setMinBaseSalary(val);
        }}
        maxCommuteMiles={maxCommuteMiles}
        onMaxCommuteMilesChange={(val) => {
          setPage(1);
          setMaxCommuteMiles(val);
        }}
        postedWithin={postedWithinFilter}
        onPostedWithinChange={(val) => {
          setPage(1);
          setPostedWithinFilter(val);
        }}
        minScore={minScoreFilter}
        onMinScoreChange={(val) => {
          setPage(1);
          setMinScoreFilter(val);
        }}
        searchMode={searchMode}
        chips={chips}
        onToggleChip={handleToggleChip}
        onResetAdvancedFilters={handleResetAdvancedFilters}
      />

      {/* Tier 1 Job Diagnostic Modal */}
      {selectedJobForDiag && (
        <JobDiagnosticModal
          jobId={selectedJobForDiag.job_id}
          jobTitle={selectedJobForDiag.title}
          companyName={selectedJobForDiag.company_name}
          applyUrl={selectedJobForDiag.apply_url}
          personaId={activePersona?.id}
          onClose={() => setSelectedJobForDiag(null)}
          onTailorCV={() => {
            const match = selectedJobForDiag;
            setSelectedJobForDiag(null);
            onSelectJob(normalizeJobMatch(match));
          }}
          onStartInterview={() => {
            const match = selectedJobForDiag;
            setSelectedJobForDiag(null);
            onStartInterview(normalizeJobMatch(match));
          }}
        />
      )}
    </div>
  );
}
