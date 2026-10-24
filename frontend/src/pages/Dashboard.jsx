import React, { useState, useEffect, useCallback } from "react";
import { useSearchParams } from "react-router-dom";
import {
  Search,
  MapPin,
  DollarSign,
  ShieldCheck,
  ChevronDown,
  ChevronUp,
  FileText,
  MessageSquare,
  AlertCircle,
  Loader2,
  Briefcase,
  PlusCircle,
  CheckCircle2,
  Sparkles,
  TrendingUp,
  RefreshCw,
  ExternalLink,
  Clock,
  X,
  Compass,
  ArrowUpDown,
  Zap,
} from "lucide-react";
import {
  searchJobs,
  crossCheckJob,
  getJobMatches,
} from "../services/api";
import { CompanyDossierCard } from "../components/CompanyDossierCard";
import { JobProvenanceBadge } from "../components/JobProvenanceBadge";
import { AddJobModal } from "../components/AddJobModal";
import { JobDiagnosticModal } from "../components/JobDiagnosticModal";
import {
  TokenizedOmnibar,
  CHIP_TYPE_ICONS,
  CHIP_TYPE_COLORS,
  formatEntityLabel,
} from "../components/search/TokenizedOmnibar";
import { InstrumentBar } from "../components/search/InstrumentBar";
import { EmptyStateRelaxer } from "../components/search/EmptyStateRelaxer";

const SAMPLE_KEYWORDS = [
  { label: "Software Developer", query: "Software Developer" },
  { label: "Frontend Developer", query: "Frontend Developer" },
  { label: "Backend Engineer", query: "Backend Engineer" },
  { label: "Full Stack Engineer", query: "Full Stack" },
  { label: "AI / ML Engineer", query: "AI Engineer" },
  { label: "OpenAI", query: "OpenAI" },
  { label: "Stripe", query: "Stripe" },
  { label: "Cloudflare", query: "Cloudflare" },
  { label: "Spotify", query: "Spotify" },
  { label: "Ramp", query: "Ramp" },
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
}) {
  const [searchParams, setSearchParams] = useSearchParams();

  // Helper to read initial state from URL search params or localStorage
  const getInitialParam = (key, fallback) => {
    const fromUrl = searchParams.get(key);
    if (fromUrl !== null) return fromUrl;
    try {
      const saved = localStorage.getItem(FILTER_STORAGE_KEY);
      if (saved) {
        const parsed = JSON.parse(saved);
        if (parsed[key] !== undefined && parsed[key] !== null) return parsed[key];
      }
    } catch {
      // ignore JSON parse error
    }
    return fallback;
  };

  // Tab Mode: 'matches' (High-Probability Matches) | 'search' (Direct ATS Search)
  const [activeTab, setActiveTab] = useState(() => getInitialParam("tab", defaultTab));

  // --- Matches Tab State (ADR-008 Engine) ---
  const [matches, setMatches] = useState([]);
  const [matchesLoading, setMatchesLoading] = useState(false);
  const [matchesError, setMatchesError] = useState(null);
  const [totalMatches, setTotalMatches] = useState(0);

  // Filter states
  const [searchQuery, setSearchQuery] = useState(() => getInitialParam("q", ""));
  const [locationFilter, setLocationFilter] = useState(() => getInitialParam("loc", ""));
  const [modalityFilter, setModalityFilter] = useState(() => getInitialParam("modality", ""));
  const [postedWithinFilter, setPostedWithinFilter] = useState(() => getInitialParam("posted", ""));
  const [minScoreFilter, setMinScoreFilter] = useState(() => {
    const val = parseFloat(getInitialParam("min_score", "0.0"));
    return isNaN(val) ? 0.0 : val;
  });
  const [sortBy, setSortBy] = useState(() => getInitialParam("sort", "score"));
  const [selectedJobForDiag, setSelectedJobForDiag] = useState(null);

  // Command-Facet Omnibar & Discovery Engine States (Spec v1.0.0)
  const [searchMode, setSearchMode] = useState(() => getInitialParam("mode", "cv_grounded"));
  const [workAuthTier, setWorkAuthTier] = useState(() => {
    const auth = getInitialParam("auth", "");
    if (auth) return auth;
    // Backward-compatible migration if legacy 'visa=true' was set
    if (getInitialParam("visa", "false") === "true") return "h1b_transfer_sponsor";
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
        const parsed = typeof savedChips === "string" ? JSON.parse(decodeURIComponent(savedChips)) : savedChips;
        return Array.isArray(parsed) ? parsed : [];
      } catch {
        return [];
      }
    }
    return [];
  });
  const [diagnostics, setDiagnostics] = useState(null);

  const handleAddChip = (chip) => {
    if (chip.type === "modality") {
      setModalityFilter(chip.value === "all" ? "" : chip.value);
      return;
    }
    setChips((prev) => {
      if (prev.some((c) => c.type === chip.type && c.value.toLowerCase() === chip.value.toLowerCase())) {
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

  const handleRemoveChip = (chipId) => {
    setChips((prev) => prev.filter((c) => c.id !== chipId));
  };

  const handleApplyRelaxation = (patch) => {
    if (!patch) return;
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
      setModalityFilter(patch.workplace_modality === "all" ? "" : patch.workplace_modality);
    }
    if ("must_have_skills" in patch) {
      setChips((prev) => prev.filter((c) => c.type !== "skill"));
    }
    if ("companies" in patch) {
      setChips((prev) => prev.filter((c) => c.type !== "company"));
    }
    if ("raw_query" in patch) {
      setSearchQuery("");
    }
    setDiagnostics(null);
  };

  // --- Search Tab State (Direct ATS Hunter) ---
  const [query, setQuery] = useState("");
  const [location, setLocation] = useState("");
  const [visaRequired, setVisaRequired] = useState(false);
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [expandedJobId, setExpandedJobId] = useState(null);
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [crossCheckingIds, setCrossCheckingIds] = useState(new Set());
  const [hasSearched, setHasSearched] = useState(false);

  // Synchronize filter state to URL search parameters and localStorage
  useEffect(() => {
    const params = new URLSearchParams();
    if (activeTab && activeTab !== "matches") params.set("tab", activeTab);
    if (searchQuery.trim()) params.set("q", searchQuery.trim());
    if (locationFilter.trim()) params.set("loc", locationFilter.trim());
    if (modalityFilter) params.set("modality", modalityFilter);
    if (postedWithinFilter) params.set("posted", postedWithinFilter);
    if (minScoreFilter > 0) params.set("min_score", String(minScoreFilter));
    if (sortBy && sortBy !== "score") params.set("sort", sortBy);
    if (searchMode && searchMode !== "cv_grounded") params.set("mode", searchMode);
    if (workAuthTier && workAuthTier !== "all") params.set("auth", workAuthTier);
    if (minBaseSalary !== null) params.set("salary", String(minBaseSalary));
    if (maxCommuteMiles !== null) params.set("commute", String(maxCommuteMiles));
    if (chips.length > 0) params.set("chips", encodeURIComponent(JSON.stringify(chips)));

    try {
      const savedState = {
        tab: activeTab,
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
      };
      localStorage.setItem(FILTER_STORAGE_KEY, JSON.stringify(savedState));
    } catch {
      // ignore
    }

    setSearchParams(params, { replace: true });
  }, [
    activeTab,
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
    setSearchParams,
  ]);

  const handleClearFilters = () => {
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

  // Fetch Ranked Matches for active persona
  const fetchMatches = useCallback(async () => {
    if (typeof getJobMatches !== "function") return;
    setMatchesLoading(true);
    setMatchesError(null);
    try {
      const params = {
        page: 1,
        page_size: 25,
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
      setMatches(res?.jobs || []);
      setTotalMatches(res?.total_count || 0);
      setDiagnostics(res?.diagnostics || null);
    } catch (err) {
      if (err.code !== "ERR_NETWORK") {
        console.warn("Failed to fetch job matches:", err);
      }
      setMatchesError(
        err.response?.data?.detail ||
          "Unable to compute candidate job matches. Ensure database has active listings."
      );
    } finally {
      setMatchesLoading(false);
    }
  }, [
    activePersona,
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
    if (activeTab === "matches") {
      const timer = setTimeout(() => {
        fetchMatches();
      }, 250);
      return () => clearTimeout(timer);
    }
  }, [activeTab, fetchMatches]);

  // Direct ATS Search Handler
  const fetchJobs = useCallback(
    async (overrideQuery, overrideLocation) => {
      const q = overrideQuery !== undefined ? overrideQuery : query;
      const loc = overrideLocation !== undefined ? overrideLocation : location;

      if (!q.trim() && !loc.trim()) {
        setJobs([]);
        setError(null);
        setLoading(false);
        setHasSearched(false);
        return;
      }

      setLoading(true);
      setError(null);
      setHasSearched(true);
      try {
        const data = await searchJobs(q.trim(), loc.trim(), visaRequired);
        setJobs(data.jobs || []);
      } catch (err) {
        setError(
          err.response?.data?.detail || "Failed to search job boards. Please retry."
        );
      } finally {
        setLoading(false);
      }
    },
    [query, location, visaRequired]
  );

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    if (!query.trim() && !location.trim()) {
      setJobs([]);
      setError(null);
      setHasSearched(false);
      return;
    }
    fetchJobs();
  };

  const handleApplyKeyword = (sampleQuery) => {
    setQuery(sampleQuery);
    fetchJobs(sampleQuery);
  };

  const toggleDossier = (jobId) => {
    setExpandedJobId(expandedJobId === jobId ? null : jobId);
  };

  const handleJobAdded = (newJob) => {
    setJobs((prev) => [newJob, ...prev]);
  };

  const handleCrossCheck = async (jobId) => {
    setCrossCheckingIds((prev) => new Set(prev).add(jobId));
    try {
      const res = await crossCheckJob(jobId);
      if (res.verification) {
        setJobs((prev) =>
          prev.map((j) =>
            j.id === jobId ? { ...j, verification: res.verification } : j
          )
        );
      }
    } catch (err) {
      console.warn("Cross check failed for job:", jobId, err);
    } finally {
      setCrossCheckingIds((prev) => {
        const next = new Set(prev);
        next.delete(jobId);
        return next;
      });
    }
  };

  const handleDossierUpdated = (jobId, updatedDossier) => {
    setJobs((prev) =>
      prev.map((j) =>
        j.id === jobId ? { ...j, company_dossier: updatedDossier } : j
      )
    );
  };

  return (
    <div className="max-w-6xl mx-auto px-4 py-8 space-y-8">
      {/* Header Banner */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div className="space-y-2">
          <h1 className="text-3xl font-bold tracking-tight text-white flex items-center gap-2">
            <Briefcase className="w-8 h-8 text-sky-400" /> Career Intelligence & Hunter
          </h1>
          <p className="text-sm text-slate-400 max-w-2xl">
            Rank verified career opportunities using our ADR-008 Bayesian matching engine,
            or search and ingest live ATS boards directly.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setIsAddModalOpen(true)}
            className="px-4 py-2.5 bg-gradient-to-r from-sky-600 to-indigo-600 hover:from-sky-500 hover:to-indigo-500 text-white font-medium rounded-xl text-sm transition-all shadow-md shadow-sky-600/20 flex items-center gap-2"
          >
            <PlusCircle className="w-4 h-4" /> Import Job
          </button>
        </div>
      </div>

      {/* Dual-Mode Tab Navigation */}
      <div className="flex items-center justify-between border-b border-slate-800 pb-3">
        <div className="flex items-center gap-2 bg-slate-800/80 p-1 rounded-xl border border-slate-700/60">
          <button
            onClick={() => setActiveTab("matches")}
            className={`px-4 py-2 rounded-lg text-xs font-semibold transition-all flex items-center gap-2 ${
              activeTab === "matches"
                ? "bg-sky-600 text-white shadow-md shadow-sky-600/20"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            <Sparkles className="w-3.5 h-3.5 text-sky-300" />
            High-Probability Matches
            {totalMatches > 0 && (
              <span className="px-1.5 py-0.2 rounded-full text-[10px] bg-sky-900/80 text-sky-200 border border-sky-400/30">
                {totalMatches}
              </span>
            )}
          </button>

          <button
            onClick={() => setActiveTab("search")}
            className={`px-4 py-2 rounded-lg text-xs font-semibold transition-all flex items-center gap-2 ${
              activeTab === "search"
                ? "bg-sky-600 text-white shadow-md shadow-sky-600/20"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            <Search className="w-3.5 h-3.5 text-sky-300" />
            Direct ATS Search & Ingest
          </button>
        </div>

        {activeTab === "matches" && (
          <div className="hidden sm:flex items-center gap-2 text-xs text-slate-400">
            <span>Lens:</span>
            <span className="font-semibold text-sky-300 bg-sky-950/60 px-2.5 py-1 rounded-lg border border-sky-800/50">
              {activePersona ? activePersona.name : "Universal Profile"}
            </span>
          </div>
        )}
      </div>

      {/* ============================================================== */}
      {/* TAB 1: HIGH-PROBABILITY MATCHES (ADR-008 RERANKER)              */}
      {/* ============================================================== */}
      {activeTab === "matches" && (
        <div className="space-y-6">
          {/* Match Filter Controls */}
          <div className="bg-slate-800/90 border border-slate-700/80 rounded-2xl p-4 shadow-xl space-y-3">
            {/* Row 1: Search Inputs (Search bar gets 70% width, Location gets 30% width on md+) */}
            <div className="grid grid-cols-1 md:grid-cols-12 gap-3 items-center">
              <div className="md:col-span-8 lg:col-span-9">
                <TokenizedOmnibar
                  rawQuery={searchQuery}
                  onQueryChange={setSearchQuery}
                  chips={chips}
                  onAddChip={handleAddChip}
                  onSelectModality={(mod) =>
                    setModalityFilter(mod === "all" ? "" : mod)
                  }
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
                  onChange={(e) => setLocationFilter(e.target.value)}
                  list="location-presets"
                  placeholder="City, State, or Country..."
                  aria-label="Filter by city, state, country, or region"
                  data-testid="matches-location-input"
                  className="w-full min-h-[42px] pl-10 pr-8 py-2 bg-slate-900/90 border border-slate-700 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-sky-500"
                />
                {locationFilter && (
                  <button
                    onClick={() => setLocationFilter("")}
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
                      onClick={() => setLocationFilter("")}
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
                      onClick={() => setWorkAuthTier("all")}
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
                      onClick={() => setModalityFilter("")}
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
                      onClick={() => setMaxCommuteMiles(null)}
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
                      onClick={() => setMinBaseSalary(null)}
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
                      Past {postedWithinFilter === "1" ? "24h" : `${postedWithinFilter}d`}
                    </span>
                    <button
                      type="button"
                      onClick={() => setPostedWithinFilter("")}
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
                      onClick={() => setMinScoreFilter(0.0)}
                      className="hover:text-white p-0.5"
                      aria-label="Remove probability band filter"
                    >
                      <X className="w-3 h-3" />
                    </button>
                  </span>
                )}
              </div>
            )}

            {/* Row 2: Unified Search Filters Row */}
            <InstrumentBar
              workAuthTier={workAuthTier}
              onWorkAuthTierChange={setWorkAuthTier}
              workplaceModality={modalityFilter || "all"}
              onWorkplaceModalityChange={(m) =>
                setModalityFilter(m === "all" ? "" : m)
              }
              maxCommuteMiles={maxCommuteMiles}
              onMaxCommuteMilesChange={setMaxCommuteMiles}
              minBaseSalary={minBaseSalary}
              onMinBaseSalaryChange={setMinBaseSalary}
              postedWithin={postedWithinFilter}
              onPostedWithinChange={setPostedWithinFilter}
              minScore={minScoreFilter}
              onMinScoreChange={setMinScoreFilter}
              searchMode={searchMode}
            />

            {/* Row 3: Dedicated Sorting, Engine Mode & Actions Row */}
            <div
              data-testid="sorting-controls-row"
              className="flex flex-wrap items-center justify-between gap-3 pt-1 border-t border-slate-700/50"
            >
              {/* Left: Dual Engine Mode Switch */}
              <div className="flex items-center gap-2">
                <span className="text-xs text-slate-400">Mode:</span>
                <div className="flex items-center gap-1 bg-slate-900/90 border border-slate-700/80 rounded-xl p-0.5 text-xs">
                  <button
                    type="button"
                    onClick={() => setSearchMode("cv_grounded")}
                    className={`flex items-center gap-1 px-2.5 py-1 rounded-lg font-medium transition-all ${
                      searchMode === "cv_grounded"
                        ? "bg-sky-600 text-white shadow-sm"
                        : "text-slate-400 hover:text-slate-200"
                    }`}
                    title="Personalized candidate-grounded match scoring (P(Match))"
                  >
                    <Sparkles className="w-3 h-3" />
                    <span>Grounded</span>
                  </button>

                  <button
                    type="button"
                    onClick={() => setSearchMode("unbiased")}
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
              </div>

              {/* Right: Unified Sort & Actions */}
              <div className="flex flex-wrap items-center gap-2">
                <div className="flex items-center gap-1.5 text-xs text-slate-400">
                  <ArrowUpDown className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                  <span>Sort:</span>
                  <select
                    value={sortBy}
                    onChange={(e) => setSortBy(e.target.value)}
                    aria-label="Sort match opportunities"
                    className="bg-slate-900/90 border border-slate-700 rounded-xl px-2.5 py-1.5 text-xs text-white focus:outline-none focus:ring-2 focus:ring-sky-500 cursor-pointer"
                  >
                    <option value="score">Best Match</option>
                    <option value="date">Most Recent</option>
                    <option value="salary">Highest Salary</option>
                  </select>
                </div>

                {activeFilterCount > 0 && (
                  <button
                    onClick={handleClearFilters}
                    title="Reset all filters to defaults"
                    className="px-2.5 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-slate-200 text-xs font-medium rounded-xl border border-slate-700 transition-colors"
                  >
                    Clear All
                  </button>
                )}

                <button
                  onClick={fetchMatches}
                  disabled={matchesLoading}
                  className="px-3 py-1.5 bg-slate-700/60 hover:bg-slate-700 text-slate-200 text-xs font-medium rounded-xl transition-colors flex items-center gap-1.5"
                >
                  <RefreshCw
                    className={`w-3.5 h-3.5 ${matchesLoading ? "animate-spin" : ""}`}
                  />
                  Re-Score
                </button>
              </div>
            </div>
          </div>

          {/* Loading State */}
          {matchesLoading && (
            <div className="flex flex-col items-center justify-center py-16 space-y-3">
              <Loader2 className="w-8 h-8 text-sky-400 animate-spin" />
              <p className="text-sm text-slate-400">
                Executing ADR-008 two-stage retrieval & Bayesian reranker...
              </p>
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

          {/* Matches List */}
          {!matchesLoading && !matchesError && matches.length > 0 && (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-400">
                  Ranked Match Opportunities ({matches.length})
                </h2>
                <span className="text-xs text-slate-500">
                  Calculated with Bayesian uncertainty gate & signal boosters
                </span>
              </div>

              <div className="grid grid-cols-1 gap-4">
                {matches.map((match) => {
                  const matchPct = Math.round(match.match_score * 100);
                  const isHigh = match.probability_band === "high";
                  const isModerate = match.probability_band === "moderate";

                  return (
                    <div
                      key={match.job_id}
                      className="bg-slate-800/80 border border-slate-700/70 rounded-2xl p-6 hover:border-slate-600/80 transition-all shadow-md space-y-4"
                    >
                      <div className="flex flex-col md:flex-row md:items-start justify-between gap-4">
                        {/* Title, Company, Meta */}
                        <div className="space-y-2">
                          <div className="flex flex-wrap items-center gap-2.5">
                            {/* Match Score Badge */}
                            <span
                              className={`text-xs font-extrabold px-3 py-1 rounded-xl shadow-sm flex items-center gap-1 ${
                                isHigh
                                  ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/40"
                                  : isModerate
                                  ? "bg-amber-500/20 text-amber-400 border border-amber-500/40"
                                  : "bg-rose-500/20 text-rose-400 border border-rose-500/40"
                              }`}
                            >
                              <TrendingUp className="w-3.5 h-3.5" />
                              {matchPct}% Match
                            </span>

                            {match.apply_url ? (
                              <a
                                href={match.apply_url}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="text-lg font-bold text-white hover:text-sky-300 transition-colors inline-flex items-center gap-1.5 group"
                                title="Open original job posting in new tab"
                              >
                                <span>{match.title}</span>
                                <ExternalLink className="w-4 h-4 text-slate-500 group-hover:text-sky-400 transition-colors shrink-0" />
                              </a>
                            ) : (
                              <h3 className="text-lg font-bold text-white">
                                {match.title}
                              </h3>
                            )}

                            {match.workplace_type && (
                              <span className="text-[10px] font-semibold uppercase px-2 py-0.5 rounded bg-slate-900 text-slate-300 border border-slate-700">
                                {match.workplace_type}
                              </span>
                            )}

                            {match.posted_at && (
                              <span
                                title={`Posted on ${new Date(match.posted_at).toLocaleString()}`}
                                className="text-[10px] font-medium px-2 py-0.5 rounded bg-slate-900 text-slate-400 border border-slate-700 flex items-center gap-1"
                              >
                                <Clock className="w-3 h-3 text-slate-500" />
                                {formatRelativeTime(match.posted_at)}
                              </span>
                            )}

                            {match.visa_sponsorship === "yes" && (
                              <span className="text-[10px] uppercase font-bold px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
                                Visa Sponsored
                              </span>
                            )}

                            {match.breakdown?.g_prob < 1.0 && (
                              <span className="text-[10px] font-semibold px-2 py-0.5 rounded bg-amber-500/10 text-amber-300 border border-amber-500/30">
                                Bayesian {(match.breakdown.g_prob).toFixed(2)}x Gate
                              </span>
                            )}
                          </div>

                          <div className="flex items-center gap-3 text-xs text-slate-400">
                            <span className="font-medium text-slate-300">
                              {match.company_name}
                            </span>
                            <span>•</span>
                            <span className="flex items-center gap-1">
                              <MapPin className="w-3.5 h-3.5 text-slate-500" />
                              {match.location}
                            </span>
                            {match.salary_range && (
                              <>
                                <span>•</span>
                                <span className="flex items-center gap-1 text-emerald-400/90 font-medium">
                                  <DollarSign className="w-3.5 h-3.5" />
                                  {match.salary_range}
                                </span>
                              </>
                            )}
                          </div>
                        </div>

                        {/* Action Buttons */}
                        <div className="flex flex-wrap items-center gap-2">
                          <button
                            onClick={() => setSelectedJobForDiag(match)}
                            title="Decompose acceptance probability factors"
                            className="px-3.5 py-2 text-xs font-semibold rounded-xl border border-sky-500/40 bg-sky-500/10 hover:bg-sky-500/20 text-sky-300 transition-all flex items-center gap-1.5 shadow-sm"
                          >
                            <Sparkles className="w-3.5 h-3.5 text-sky-400" />
                            Why this match?
                          </button>

                          <button
                            onClick={() => onSelectJob(normalizeJobMatch(match))}
                            className="px-4 py-2 text-xs font-semibold rounded-xl bg-sky-600 hover:bg-sky-500 text-white transition-all shadow-md shadow-sky-600/20 flex items-center gap-1.5"
                          >
                            <FileText className="w-3.5 h-3.5" /> Tailor CV
                          </button>

                          <button
                            onClick={() => onStartInterview(normalizeJobMatch(match))}
                            className="px-4 py-2 text-xs font-semibold rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white transition-all shadow-md shadow-indigo-600/20 flex items-center gap-1.5"
                          >
                            <MessageSquare className="w-3.5 h-3.5" /> Mock Interview
                          </button>

                          {match.apply_url && (
                            <a
                              href={match.apply_url}
                              target="_blank"
                              rel="noopener noreferrer"
                              data-testid={`apply-link-${match.job_id}`}
                              title="Open original job application in new tab"
                              className="px-3.5 py-2 text-xs font-semibold rounded-xl bg-emerald-600/90 hover:bg-emerald-500 text-white transition-all shadow-md shadow-emerald-600/20 flex items-center gap-1.5 cursor-pointer"
                            >
                              <ExternalLink className="w-3.5 h-3.5" />
                              <span>Apply</span>
                            </a>
                          )}
                        </div>
                      </div>

                      {/* Matched Skills & Missing Dealbreakers Chips */}
                      <div className="space-y-2 pt-2 border-t border-slate-750">
                        <div className="flex flex-wrap items-center gap-1.5">
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
                              Equiv: {eq.candidate_has} → {eq.job_requested}
                            </span>
                          ))}
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      )}

      {/* ============================================================== */}
      {/* TAB 2: DIRECT ATS SEARCH & INGEST                               */}
      {/* ============================================================== */}
      {activeTab === "search" && (
        <div className="space-y-6">
          {/* Search & Constraint Filter Bar */}
          <form
            onSubmit={handleSearchSubmit}
            aria-label="Job search and filter form"
            className="bg-slate-800/90 border border-slate-700/80 rounded-2xl p-4 shadow-xl grid grid-cols-1 md:grid-cols-4 gap-3 items-center"
          >
            <div className="relative md:col-span-2">
              <Search
                className="w-4 h-4 text-slate-400 absolute left-3.5 top-3.5"
                aria-hidden="true"
              />
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                aria-label="Target role or skills query"
                placeholder="Target role or skills (e.g. Senior AI Engineer)"
                className="w-full pl-10 pr-4 py-2.5 bg-slate-900/90 border border-slate-700 rounded-xl text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-sky-500 focus:border-transparent"
              />
            </div>

            <div className="relative">
              <MapPin
                className="w-4 h-4 text-slate-400 absolute left-3.5 top-3.5"
                aria-hidden="true"
              />
              <input
                type="text"
                value={location}
                onChange={(e) => setLocation(e.target.value)}
                aria-label="Job location query"
                placeholder="Location (e.g. Remote)"
                className="w-full pl-10 pr-4 py-2.5 bg-slate-900/90 border border-slate-700 rounded-xl text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-sky-500 focus:border-transparent"
              />
            </div>

            <div className="flex items-center justify-between md:justify-end gap-4">
              <label className="flex items-center gap-2 text-xs font-medium text-slate-300 cursor-pointer">
                <input
                  type="checkbox"
                  checked={visaRequired}
                  onChange={(e) => setVisaRequired(e.target.checked)}
                  aria-label="Require H-1B or Visa sponsorship"
                  className="w-4 h-4 rounded bg-slate-900 border-slate-600 text-sky-500 focus:ring-sky-500"
                />
                <span className="flex items-center gap-1">
                  <ShieldCheck
                    className="w-3.5 h-3.5 text-emerald-400"
                    aria-hidden="true"
                  />{" "}
                  H-1B / Visa
                </span>
              </label>

              <button
                type="submit"
                disabled={loading}
                aria-label={loading ? "Searching jobs" : "Search jobs"}
                className="px-5 py-2.5 bg-sky-600 hover:bg-sky-500 disabled:bg-slate-700 text-white font-medium rounded-xl text-sm transition-all shadow-md shadow-sky-600/20 flex items-center gap-2 focus:outline-none focus:ring-2 focus:ring-sky-400"
              >
                {loading ? (
                  <Loader2 className="w-4 h-4 animate-spin" aria-hidden="true" />
                ) : (
                  "Search"
                )}
              </button>
            </div>
          </form>

          {/* 3-State Lifecycle Views */}
          {loading && (
            <div className="flex flex-col items-center justify-center py-16 space-y-3">
              <Loader2 className="w-8 h-8 text-sky-400 animate-spin" />
              <p className="text-sm text-slate-400">
                Scanning local synced ATS boards and enriching company tech stacks...
              </p>
            </div>
          )}

          {error && !loading && (
            <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <AlertCircle className="w-5 h-5 text-rose-400" />
                <span className="text-sm">{error}</span>
              </div>
              <button
                onClick={fetchJobs}
                className="text-xs px-3 py-1.5 bg-rose-500/20 hover:bg-rose-500/30 rounded-lg text-rose-200 transition-colors"
              >
                Retry Search
              </button>
            </div>
          )}

          {!loading && !error && jobs.length === 0 && (
            <div className="bg-slate-800/40 border border-slate-700/60 rounded-2xl p-8 text-center space-y-6">
              <div className="w-14 h-14 rounded-2xl bg-sky-500/10 border border-sky-500/20 text-sky-400 mx-auto flex items-center justify-center shadow-lg">
                <Sparkles className="w-7 h-7" />
              </div>

              <div className="space-y-2 max-w-md mx-auto">
                <h3 className="text-lg font-bold text-white">
                  {hasSearched
                    ? "No matching roles found"
                    : "Ready to explore open positions?"}
                </h3>
                <p className="text-xs text-slate-400 leading-relaxed">
                  {hasSearched
                    ? "We couldn't find any positions matching your search. Try one of the popular keywords below or import a direct job posting URL."
                    : "Search across 2,200+ verified live job listings from top tech companies. Try searching for a role title, tech stack, or company name."}
                </p>
              </div>

              <div className="space-y-3">
                <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">
                  Suggested Search Keywords
                </span>
                <div className="flex flex-wrap items-center justify-center gap-2 max-w-xl mx-auto">
                  {SAMPLE_KEYWORDS.map((item, idx) => (
                    <button
                      key={idx}
                      type="button"
                      onClick={() => handleApplyKeyword(item.query)}
                      className="px-3.5 py-1.5 rounded-xl bg-slate-900 hover:bg-sky-600/20 text-slate-300 hover:text-sky-300 border border-slate-700 hover:border-sky-500/50 text-xs font-medium transition-all shadow-sm"
                    >
                      {item.label}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Matched Job Cards */}
          {!loading && !error && jobs.length > 0 && (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-400">
                  Direct ATS Roles ({jobs.length})
                </h2>
                <span className="text-xs text-slate-500">
                  Ranked by keyword and provenance affinity
                </span>
              </div>

              <div className="grid grid-cols-1 gap-4">
                {jobs.map((job) => {
                  const isExpanded = expandedJobId === job.id;
                  const hasDossier = !!job.company_dossier;
                  const isCrossChecking = crossCheckingIds.has(job.id);

                  return (
                    <div
                      key={job.id}
                      className="bg-slate-800/80 border border-slate-700/70 rounded-2xl p-6 hover:border-slate-600/80 transition-all shadow-md space-y-4"
                    >
                      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                        <div className="space-y-2">
                          <div className="flex flex-wrap items-center gap-2">
                            <h3 className="text-lg font-bold text-white">{job.title}</h3>
                            <JobProvenanceBadge job={job} />
                            {(job.ats_requirements?.visa_sponsorship ||
                              job.visa_sponsorship === "yes") && (
                              <span className="text-[10px] uppercase font-bold px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
                                Visa Sponsored
                              </span>
                            )}
                          </div>
                          <div className="flex items-center gap-3 text-xs text-slate-400">
                            <span className="font-medium text-slate-300">
                              {job.company_name}
                            </span>
                            <span>•</span>
                            <span className="flex items-center gap-1">
                              <MapPin className="w-3.5 h-3.5 text-slate-500" />
                              {job.location}
                            </span>
                            {job.salary_range && (
                              <>
                                <span>•</span>
                                <span className="flex items-center gap-1 text-emerald-400/90 font-medium">
                                  <DollarSign className="w-3.5 h-3.5" />
                                  {job.salary_range}
                                </span>
                              </>
                            )}
                          </div>
                        </div>

                        {/* Action Buttons */}
                        <div className="flex flex-wrap items-center gap-2">
                          <button
                            onClick={() => handleCrossCheck(job.id)}
                            disabled={isCrossChecking}
                            title="Cross-check listing against secondary aggregator"
                            className="px-3 py-2 text-xs font-medium rounded-xl border border-slate-700 hover:bg-slate-700/60 text-slate-300 transition-colors flex items-center gap-1.5 disabled:opacity-50"
                          >
                            {isCrossChecking ? (
                              <Loader2 className="w-3.5 h-3.5 animate-spin text-sky-400" />
                            ) : (
                              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                            )}
                            Cross-Check
                          </button>

                          {hasDossier && (
                            <button
                              onClick={() => toggleDossier(job.id)}
                              className="px-3.5 py-2 text-xs font-medium rounded-xl border border-slate-700 hover:bg-slate-700/60 text-slate-300 transition-colors flex items-center gap-1.5"
                            >
                              Company Intel
                              {isExpanded ? (
                                <ChevronUp className="w-3.5 h-3.5" />
                              ) : (
                                <ChevronDown className="w-3.5 h-3.5" />
                              )}
                            </button>
                          )}

                          <button
                            onClick={() => onSelectJob(job)}
                            className="px-4 py-2 text-xs font-semibold rounded-xl bg-sky-600 hover:bg-sky-500 text-white transition-all shadow-md shadow-sky-600/20 flex items-center gap-1.5"
                          >
                            <FileText className="w-3.5 h-3.5" /> Tailor CV
                          </button>

                          <button
                            onClick={() => onStartInterview(job)}
                            className="px-4 py-2 text-xs font-semibold rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white transition-all shadow-md shadow-indigo-600/20 flex items-center gap-1.5"
                          >
                            <MessageSquare className="w-3.5 h-3.5" /> Mock Interview
                          </button>
                        </div>
                      </div>

                      {/* Skills tags */}
                      {job.ats_requirements?.required_skills?.length > 0 && (
                        <div className="flex flex-wrap gap-1.5 pt-1">
                          {job.ats_requirements.required_skills.map((skill, sIdx) => (
                            <span
                              key={sIdx}
                              className="text-[11px] px-2.5 py-0.5 rounded-full bg-slate-900 text-slate-300 border border-slate-700/60"
                            >
                              {skill}
                            </span>
                          ))}
                        </div>
                      )}

                      {/* Expanded Company Dossier View */}
                      {isExpanded && hasDossier && (
                        <div className="pt-2 animate-fadeIn">
                          <CompanyDossierCard
                            dossier={job.company_dossier}
                            onDossierUpdated={(updated) =>
                              handleDossierUpdated(job.id, updated)
                            }
                          />
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Ingestion Modal */}
      <AddJobModal
        isOpen={isAddModalOpen}
        onClose={() => setIsAddModalOpen(false)}
        onJobAdded={handleJobAdded}
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
