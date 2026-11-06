import React, { useState, useEffect, useCallback } from "react";
import {
  Shield,
  Activity,
  Server,
  Database,
  Cpu,
  RefreshCw,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  Clock,
  Play,
  RotateCcw,
  Trash2,
  Plus,
  ExternalLink,
  Layers,
  Users,
  Coins,
  Radio,
  Flame,
  Search,
  MapPin,
  DollarSign,
  ShieldCheck,
  ChevronDown,
  ChevronUp,
  PlusCircle,
  Loader2,
  Copy,
  Check,
  X,
  ArrowRight,
  HardDrive,
} from "lucide-react";
import {
  getAdminOverview,
  registerATSBoard,
  syncBoard,
  syncAllBoards,
  retryFailedTasks,
  purgeFailedTasks,
  resetCircuitBreaker,
  flushMatchCache,
  updateUserStatus,
  searchJobs,
  crossCheckJob,
} from "../services/api";
import { CompanyDossierCard } from "../components/CompanyDossierCard";
import { JobProvenanceBadge } from "../components/JobProvenanceBadge";
import { AddJobModal } from "../components/AddJobModal";
import { getStatusBadgeClass } from "../utils/statusBadges";

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

function formatBytes(bytes) {
  if (!bytes || bytes === 0) return "0 B";
  const k = 1024;
  const sizes = ["B", "KB", "MB", "GB", "TB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`;
}

export function AdminDashboard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState(null);
  const [actionSuccess, setActionSuccess] = useState(null);
  const [activeTab, setActiveTab] = useState("crawlers"); // 'crawlers' | 'system' | 'ai' | 'users' | 'traces' | 'storage'

  // 360° Observability trace & drawer state
  const [selectedTrace, setSelectedTrace] = useState(null);
  const [copiedTraceId, setCopiedTraceId] = useState(null);
  const [traceFilter, setTraceFilter] = useState("");

  const handleCopy = (text, id) => {
    if (!text) return;
    navigator.clipboard?.writeText(text);
    setCopiedTraceId(id);
    setTimeout(() => setCopiedTraceId(null), 2000);
  };

  // New Board Modal state
  const [isAddBoardOpen, setIsAddBoardOpen] = useState(false);
  const [boardForm, setBoardForm] = useState({
    company_name: "",
    provider: "greenhouse",
    board_token: "",
    industry: "healthtech",
    sync_now: true,
  });
  const [submittingBoard, setSubmittingBoard] = useState(false);

  // User search/filter
  const [userSearch, setUserSearch] = useState("");

  // Job Ingestion & Live ATS Search state
  const [isAddJobOpen, setIsAddJobOpen] = useState(false);
  const [atsQuery, setAtsQuery] = useState("");
  const [atsLocation, setAtsLocation] = useState("");
  const [atsVisaRequired, setAtsVisaRequired] = useState(false);
  const [atsJobs, setAtsJobs] = useState([]);
  const [atsLoading, setAtsLoading] = useState(false);
  const [atsError, setAtsError] = useState(null);
  const [atsSearched, setAtsSearched] = useState(false);
  const [expandedJobId, setExpandedJobId] = useState(null);
  const [crossCheckingIds, setCrossCheckingIds] = useState(new Set());

  const fetchOverview = useCallback(async (isSilent = false) => {
    if (!isSilent) setRefreshing(true);
    try {
      const res = await getAdminOverview();
      setData(res);
      setError(null);
    } catch (err) {
      console.error("Failed to load admin overview:", err);
      const msg =
        err.response?.status === 403
          ? "Access Denied: You do not have administrator permissions."
          : err.response?.data?.detail || "Failed to load telemetry data.";
      setError(msg);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    fetchOverview();
    const interval = setInterval(() => {
      fetchOverview(true);
    }, 15000); // 15s auto-refresh
    return () => clearInterval(interval);
  }, [fetchOverview]);

  // Close drawer on Escape key for keyboard accessibility (WCAG 2.1.2)
  useEffect(() => {
    function handleKeyDown(e) {
      if (e.key === "Escape" && selectedTrace) {
        setSelectedTrace(null);
      }
    }
    if (selectedTrace) {
      window.addEventListener("keydown", handleKeyDown);
      return () => window.removeEventListener("keydown", handleKeyDown);
    }
  }, [selectedTrace]);

  const showNotification = (msg) => {
    setActionSuccess(msg);
    setTimeout(() => setActionSuccess(null), 4000);
  };

  const handleSyncBoard = async (boardId, companyName) => {
    try {
      await syncBoard(boardId);
      showNotification(`Triggered immediate crawl for ${companyName}.`);
      fetchOverview(true);
    } catch (err) {
      alert(err.response?.data?.detail || "Failed to trigger board sync.");
    }
  };

  const handleSyncAllBoards = async () => {
    if (!window.confirm("Enqueue sync tasks for all active ATS boards?"))
      return;
    try {
      const res = await syncAllBoards();
      showNotification(`Enqueued sync for ${res.enqueued_count} boards.`);
      fetchOverview(true);
    } catch (err) {
      alert(err.response?.data?.detail || "Failed to enqueue bulk sync.");
    }
  };

  const handleRetryFailed = async () => {
    try {
      const res = await retryFailedTasks();
      showNotification(`Enqueued ${res.retried_count} failed tasks for retry.`);
      fetchOverview(true);
    } catch (err) {
      alert(err.response?.data?.detail || "Failed to retry tasks.");
    }
  };

  const handlePurgeFailed = async () => {
    if (!window.confirm("Permanently purge all failed ingestion queue tasks?"))
      return;
    try {
      const res = await purgeFailedTasks();
      showNotification(`Purged ${res.purged_count} failed tasks.`);
      fetchOverview(true);
    } catch (err) {
      alert(err.response?.data?.detail || "Failed to purge tasks.");
    }
  };

  const handleResetBreaker = async (provider) => {
    try {
      await resetCircuitBreaker(provider);
      showNotification(`Circuit breaker for ${provider} has been reset.`);
      fetchOverview(true);
    } catch (err) {
      alert(err.response?.data?.detail || "Failed to reset circuit breaker.");
    }
  };

  const handleFlushCache = async () => {
    if (
      !window.confirm(
        "Flush all cached candidate match scores? Candidates will re-rank on next search.",
      )
    )
      return;
    try {
      const res = await flushMatchCache();
      showNotification(`Flushed ${res.flushed_count} cached match scores.`);
      fetchOverview(true);
    } catch (err) {
      alert(err.response?.data?.detail || "Failed to flush match cache.");
    }
  };

  const handleToggleUserActive = async (userId, currentActive) => {
    try {
      await updateUserStatus(userId, { is_active: !currentActive });
      showNotification("User account status updated.");
      fetchOverview(true);
    } catch (err) {
      alert(err.response?.data?.detail || "Failed to update user.");
    }
  };

  const handleToggleUserRole = async (userId, currentRole) => {
    const nextRole = currentRole === "admin" ? "candidate" : "admin";
    if (!window.confirm(`Change this user's role to '${nextRole}'?`)) return;
    try {
      await updateUserStatus(userId, { role: nextRole });
      showNotification(`User role changed to ${nextRole}.`);
      fetchOverview(true);
    } catch (err) {
      alert(err.response?.data?.detail || "Failed to change user role.");
    }
  };

  const handleCreateBoard = async (e) => {
    e.preventDefault();
    setSubmittingBoard(true);
    try {
      await registerATSBoard({
        company_name: boardForm.company_name,
        provider: boardForm.provider,
        slug: boardForm.board_token,
        board_token: boardForm.board_token,
        industry: boardForm.industry,
        crawl_now: boardForm.sync_now,
      });
      showNotification(
        `Registered and queued board: ${boardForm.company_name}`,
      );
      setIsAddBoardOpen(false);
      setBoardForm({
        company_name: "",
        provider: "greenhouse",
        board_token: "",
        industry: "healthtech",
        sync_now: true,
      });
      fetchOverview(true);
    } catch (err) {
      alert(err.response?.data?.detail || "Failed to register board.");
    } finally {
      setSubmittingBoard(false);
    }
  };

  const handleAtsSearch = async (overrideQuery, overrideLoc) => {
    const q = overrideQuery !== undefined ? overrideQuery : atsQuery;
    const loc = overrideLoc !== undefined ? overrideLoc : atsLocation;
    if (!q.trim() && !loc.trim()) {
      setAtsJobs([]);
      setAtsError(null);
      setAtsSearched(false);
      return;
    }
    setAtsLoading(true);
    setAtsError(null);
    setAtsSearched(true);
    try {
      const res = await searchJobs(q.trim(), loc.trim(), atsVisaRequired);
      setAtsJobs(res?.jobs || []);
    } catch (err) {
      setAtsError(
        err.response?.data?.detail || "Failed to search external ATS boards. Please retry.",
      );
    } finally {
      setAtsLoading(false);
    }
  };

  const handleAtsCrossCheck = async (jobId) => {
    setCrossCheckingIds((prev) => new Set(prev).add(jobId));
    try {
      const res = await crossCheckJob(jobId);
      if (res.verification) {
        setAtsJobs((prev) =>
          prev.map((j) =>
            j.id === jobId ? { ...j, verification: res.verification } : j,
          ),
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

  const handleJobImported = (newJob) => {
    setAtsJobs((prev) => [newJob, ...prev]);
    showNotification("Job imported successfully into database catalog.");
    fetchOverview(true);
  };

  if (loading) {
    return (
      <div className="min-h-[70vh] flex flex-col items-center justify-center p-8 text-slate-400">
        <RefreshCw className="w-8 h-8 animate-spin text-sky-400 mb-4" />
        <p className="text-sm font-medium">
          Loading telemetry and system status...
        </p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-4xl mx-auto px-6 py-12">
        <div className="p-6 rounded-2xl bg-rose-500/10 border border-rose-500/20 text-rose-300">
          <div className="flex items-center gap-3 mb-2">
            <AlertTriangle className="w-6 h-6 text-rose-400" />
            <h2 className="text-lg font-bold">Administrative Access Error</h2>
          </div>
          <p className="text-sm">{error}</p>
        </div>
      </div>
    );
  }

  const {
    current_operator,
    system_health,
    crawler_pipeline,
    catalog_breakdown,
    ai_cost_and_quotas,
    users = [],
    table_storage = [],
    recent_traces = [],
  } = data || {};

  const filteredTraces = recent_traces.filter((t) => {
    if (!traceFilter.trim()) return true;
    const q = traceFilter.toLowerCase();
    return (
      t.path?.toLowerCase().includes(q) ||
      t.client_action?.toLowerCase().includes(q) ||
      t.correlation_id?.toLowerCase().includes(q) ||
      t.trace_id?.toLowerCase().includes(q) ||
      String(t.status_code).includes(q)
    );
  });

  const filteredUsers = users.filter((u) => {
    if (!userSearch) return true;
    const q = userSearch.toLowerCase();
    return (
      u.email?.toLowerCase().includes(q) ||
      u.full_name?.toLowerCase().includes(q) ||
      u.role?.toLowerCase().includes(q)
    );
  });

  return (
    <div className="max-w-7xl mx-auto px-6 py-8 space-y-8 animate-in fade-in duration-200">
      {/* Toast Notification */}
      {actionSuccess && (
        <div className="fixed bottom-6 right-6 z-50 p-4 rounded-xl bg-emerald-500/90 text-white shadow-xl flex items-center gap-2 backdrop-blur-md text-xs font-semibold animate-in slide-in-from-bottom duration-150">
          <CheckCircle2 className="w-4 h-4 text-emerald-100" />
          <span>{actionSuccess}</span>
        </div>
      )}

      {/* Top Banner / Operator Identity */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-5 rounded-2xl bg-gradient-to-r from-slate-900 via-slate-800/80 to-slate-900 border border-slate-700/60 shadow-xl">
        <div className="flex items-center gap-4">
          <div className="p-3 rounded-2xl bg-amber-500/10 border border-amber-500/30 text-amber-400 shadow-inner">
            <Shield className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center gap-2.5">
              <h1 className="text-xl font-bold tracking-tight text-white">
                Admin Control Plane & Observability
              </h1>
              <span className="text-[10px] font-extrabold uppercase px-2 py-0.5 rounded bg-amber-500/20 text-amber-300 border border-amber-500/40">
                Operator Console
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-0.5">
              Logged in as{" "}
              <strong className="text-slate-200">
                {current_operator?.email}
              </strong>{" "}
              ({current_operator?.role}) • Real-time crawler, pipeline & cost
              telemetry
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2.5">
          {system_health?.grafana_url && (
            <a
              href={system_health.grafana_url}
              target="_blank"
              rel="noreferrer"
              className="flex items-center gap-1.5 px-3 py-2 rounded-xl bg-orange-500/10 hover:bg-orange-500/20 text-orange-300 border border-orange-500/30 text-xs font-medium transition-all"
            >
              <Activity className="w-3.5 h-3.5 text-orange-400" />
              <span>Grafana LGTM</span>
              <ExternalLink className="w-3 h-3 text-orange-400" />
            </a>
          )}
          {system_health?.phoenix_url && (
            <a
              href={system_health.phoenix_url}
              target="_blank"
              rel="noreferrer"
              className="flex items-center gap-1.5 px-3 py-2 rounded-xl bg-indigo-500/10 hover:bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 text-xs font-medium transition-all"
            >
              <Activity className="w-3.5 h-3.5" />
              <span>Arize Phoenix</span>
              <ExternalLink className="w-3 h-3 text-indigo-400" />
            </a>
          )}
          <button
            onClick={() => fetchOverview()}
            disabled={refreshing}
            className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 text-xs font-medium transition-all cursor-pointer shadow-sm"
          >
            <RefreshCw
              className={`w-3.5 h-3.5 ${refreshing ? "animate-spin text-sky-400" : ""}`}
            />
            <span>{refreshing ? "Refreshing..." : "Refresh"}</span>
          </button>
        </div>
      </div>

      {/* KPI Stats Ribbon */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* DB & Uptime */}
        <div className="p-4 rounded-2xl bg-slate-850/60 border border-slate-800 shadow-md">
          <div className="flex items-center justify-between text-xs text-slate-400 mb-2">
            <span className="font-medium flex items-center gap-1.5">
              <Database className="w-3.5 h-3.5 text-sky-400" /> Database &
              Health
            </span>
            <span
              className={`inline-flex items-center gap-1 text-[10px] font-bold px-1.5 py-0.5 rounded ${
                system_health?.database_status === "healthy"
                  ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                  : "bg-rose-500/10 text-rose-400 border border-rose-500/20"
              }`}
            >
              {system_health?.database_status === "healthy" ? (
                <CheckCircle2 className="w-3 h-3" />
              ) : (
                <XCircle className="w-3 h-3" />
              )}
              {system_health?.database_status?.toUpperCase()}
            </span>
          </div>
          <div className="text-2xl font-black text-white">
            {system_health?.database_latency_ms}{" "}
            <span className="text-xs font-normal text-slate-400">ms ping</span>
          </div>
          <div className="mt-2 text-[11px] text-slate-400 flex items-center justify-between">
            <span>
              Pool: {system_health?.connection_pool?.checked_out}/
              {system_health?.connection_pool?.pool_size} active
            </span>
            <span>
              Uptime: {Math.floor((system_health?.uptime_seconds || 0) / 60)}m
            </span>
          </div>
        </div>

        {/* Crawler Queue Depth */}
        <div className="p-4 rounded-2xl bg-slate-850/60 border border-slate-800 shadow-md">
          <div className="flex items-center justify-between text-xs text-slate-400 mb-2">
            <span className="font-medium flex items-center gap-1.5">
              <Radio className="w-3.5 h-3.5 text-indigo-400" /> Crawler Queue
            </span>
            <span className="text-[10px] font-semibold text-slate-400">
              {crawler_pipeline?.queue?.completed || 0} completed
            </span>
          </div>
          <div className="flex items-baseline gap-2">
            <div className="text-2xl font-black text-white">
              {(crawler_pipeline?.queue?.pending || 0) +
                (crawler_pipeline?.queue?.processing || 0)}
            </div>
            <span className="text-xs text-slate-400 font-medium">in queue</span>
          </div>
          <div className="mt-2 text-[11px] text-slate-400 flex items-center gap-3">
            <span className="text-amber-400 font-medium">
              {crawler_pipeline?.queue?.pending || 0} pending
            </span>
            <span className="text-sky-400 font-medium">
              {crawler_pipeline?.queue?.processing || 0} running
            </span>
            <span className="text-rose-400 font-medium">
              {crawler_pipeline?.queue?.failed || 0} failed
            </span>
          </div>
        </div>

        {/* Catalog Breakdown */}
        <div className="p-4 rounded-2xl bg-slate-850/60 border border-slate-800 shadow-md">
          <div className="flex items-center justify-between text-xs text-slate-400 mb-2">
            <span className="font-medium flex items-center gap-1.5">
              <Layers className="w-3.5 h-3.5 text-emerald-400" /> Active Catalog
            </span>
            <span className="text-[10px] font-semibold text-slate-400">
              {catalog_breakdown?.total_dossiers || 0} companies
            </span>
          </div>
          <div className="text-2xl font-black text-white">
            {catalog_breakdown?.active_jobs || 0}
            <span className="text-xs font-normal text-slate-400 ml-1.5">
              live jobs
            </span>
          </div>
          <div className="mt-2 text-[11px] text-slate-400 flex items-center justify-between">
            <span>{catalog_breakdown?.closed_jobs || 0} archived</span>
            <span className="text-sky-400">
              {catalog_breakdown?.cached_matches || 0} cached matches
            </span>
          </div>
        </div>

        {/* AI Spend & Quotas */}
        <div className="p-4 rounded-2xl bg-slate-850/60 border border-slate-800 shadow-md">
          <div className="flex items-center justify-between text-xs text-slate-400 mb-2">
            <span className="font-medium flex items-center gap-1.5">
              <Coins className="w-3.5 h-3.5 text-amber-400" /> AI Usage & Cost
            </span>
            <span className="text-[10px] font-bold text-amber-400">Today</span>
          </div>
          <div className="text-2xl font-black text-white">
            ${(ai_cost_and_quotas?.total_estimated_cost_usd || 0).toFixed(4)}
          </div>
          <div className="mt-2 text-[11px] text-slate-400 flex items-center justify-between">
            <span>
              {(
                (ai_cost_and_quotas?.total_tokens_consumed || 0) / 1000
              ).toFixed(1)}
              k tokens
            </span>
            <span className="text-emerald-400 font-medium">Bounded Budget</span>
          </div>
        </div>
      </div>

      {/* Tabs Navigation */}
      <div className="flex items-center gap-2 border-b border-slate-800 pb-2">
        <button
          onClick={() => setActiveTab("crawlers")}
          className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold transition-all cursor-pointer ${
            activeTab === "crawlers"
              ? "bg-sky-600 text-white shadow-md shadow-sky-600/20"
              : "text-slate-400 hover:text-white hover:bg-slate-800"
          }`}
        >
          <Radio className="w-4 h-4" /> Crawlers & Pipeline (
          {crawler_pipeline?.tracked_boards?.length || 0})
        </button>

        <button
          onClick={() => setActiveTab("system")}
          className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold transition-all cursor-pointer ${
            activeTab === "system"
              ? "bg-sky-600 text-white shadow-md shadow-sky-600/20"
              : "text-slate-400 hover:text-white hover:bg-slate-800"
          }`}
        >
          <Cpu className="w-4 h-4" /> System Health & Crashes
          {system_health?.recent_crashes?.length > 0 && (
            <span className="w-2 h-2 rounded-full bg-rose-500 animate-pulse" />
          )}
        </button>

        <button
          onClick={() => setActiveTab("ai")}
          className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold transition-all cursor-pointer ${
            activeTab === "ai"
              ? "bg-sky-600 text-white shadow-md shadow-sky-600/20"
              : "text-slate-400 hover:text-white hover:bg-slate-800"
          }`}
        >
          <Flame className="w-4 h-4" /> AI Quotas & Telemetry
        </button>

        <button
          onClick={() => setActiveTab("users")}
          className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold transition-all cursor-pointer ${
            activeTab === "users"
              ? "bg-sky-600 text-white shadow-md shadow-sky-600/20"
              : "text-slate-400 hover:text-white hover:bg-slate-800"
          }`}
        >
          <Users className="w-4 h-4" /> User Accounts ({users.length})
        </button>

        <button
          onClick={() => setActiveTab("ingest")}
          className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold transition-all cursor-pointer ${
            activeTab === "ingest"
              ? "bg-sky-600 text-white shadow-md shadow-sky-600/20"
              : "text-slate-400 hover:text-white hover:bg-slate-800"
          }`}
        >
          <Search className="w-4 h-4" /> Job Ingestion & ATS Search
        </button>

        <button
          onClick={() => setActiveTab("traces")}
          className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold transition-all cursor-pointer ${
            activeTab === "traces"
              ? "bg-sky-600 text-white shadow-md shadow-sky-600/20"
              : "text-slate-400 hover:text-white hover:bg-slate-800"
          }`}
        >
          <Layers className="w-4 h-4" /> 360° Trace Stream ({recent_traces.length})
        </button>

        <button
          onClick={() => setActiveTab("storage")}
          className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold transition-all cursor-pointer ${
            activeTab === "storage"
              ? "bg-sky-600 text-white shadow-md shadow-sky-600/20"
              : "text-slate-400 hover:text-white hover:bg-slate-800"
          }`}
        >
          <Database className="w-4 h-4" /> DB & Vector Storage ({table_storage.length})
        </button>
      </div>

      {/* ==================================================================== */}
      {/* TAB 1: CRAWLERS & INGESTION PIPELINE */}
      {/* ==================================================================== */}
      {activeTab === "crawlers" && (
        <div className="space-y-6 animate-in fade-in duration-150">
          {/* Quick Action Ribbon */}
          <div className="flex flex-wrap items-center justify-between gap-4 p-4 rounded-2xl bg-slate-800/40 border border-slate-800">
            <div>
              <h3 className="text-sm font-bold text-white">
                Crawler Pipeline Operations
              </h3>
              <p className="text-xs text-slate-400">
                Trigger synchronization sweeps, register portals, or retry
                failed queue tasks
              </p>
            </div>
            <div className="flex flex-wrap items-center gap-2.5">
              <button
                type="button"
                onClick={() => setIsAddJobOpen(true)}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-gradient-to-r from-sky-600 to-indigo-600 hover:from-sky-500 hover:to-indigo-500 text-white text-xs font-semibold shadow-sm transition-all cursor-pointer"
              >
                <PlusCircle className="w-3.5 h-3.5" /> Import Job (URL / Text)
              </button>
              <button
                onClick={() => setIsAddBoardOpen(true)}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-sky-600 hover:bg-sky-500 text-white text-xs font-semibold shadow-sm transition-all cursor-pointer"
              >
                <Plus className="w-3.5 h-3.5" /> Add ATS Board
              </button>
              <button
                onClick={handleSyncAllBoards}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-700 hover:bg-slate-600 text-white text-xs font-semibold shadow-sm transition-all cursor-pointer"
              >
                <Play className="w-3.5 h-3.5 text-emerald-400" /> Sync All
                Boards
              </button>
              <button
                onClick={handleRetryFailed}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-700 hover:bg-slate-600 text-white text-xs font-semibold shadow-sm transition-all cursor-pointer"
              >
                <RotateCcw className="w-3.5 h-3.5 text-amber-400" /> Retry
                Failed ({crawler_pipeline?.queue?.failed || 0})
              </button>
              <button
                onClick={handlePurgeFailed}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-rose-500/10 hover:bg-rose-500/20 text-rose-300 border border-rose-500/30 text-xs font-semibold transition-all cursor-pointer"
              >
                <Trash2 className="w-3.5 h-3.5 text-rose-400" /> Purge Failed
              </button>
            </div>
          </div>

          {/* Tracked ATS Boards */}
          <div className="rounded-2xl bg-slate-850/60 border border-slate-800 overflow-hidden shadow-md">
            <div className="p-4 border-b border-slate-800 flex items-center justify-between">
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <Radio className="w-4 h-4 text-sky-400" /> Tracked Company
                Career Portals
              </h3>
              <span className="text-xs text-slate-400">
                {crawler_pipeline?.tracked_boards?.length || 0} registered
              </span>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-900/80 text-slate-400 border-b border-slate-800 uppercase tracking-wider text-[10px]">
                  <tr>
                    <th className="px-4 py-3">Company</th>
                    <th className="px-4 py-3">Provider</th>
                    <th className="px-4 py-3">Slug / Token</th>
                    <th className="px-4 py-3">Industry</th>
                    <th className="px-4 py-3">Status</th>
                    <th className="px-4 py-3">Last Synced</th>
                    <th className="px-4 py-3 text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {crawler_pipeline?.tracked_boards?.map((b) => (
                    <tr
                      key={b.id}
                      className="hover:bg-slate-800/40 transition-colors"
                    >
                      <td className="px-4 py-3 font-semibold text-white">
                        {b.company_name}
                      </td>
                      <td className="px-4 py-3">
                        <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-800 border border-slate-700 uppercase">
                          {b.provider}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-slate-300 font-mono text-[11px]">
                        {b.slug}
                      </td>
                      <td className="px-4 py-3">
                        <span className="px-2 py-0.5 rounded text-[10px] font-medium bg-sky-500/10 text-sky-400 border border-sky-500/20">
                          {b.industry}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        {b.consecutive_failures > 0 ? (
                          <span className="text-rose-400 flex items-center gap-1 font-semibold">
                            <AlertTriangle className="w-3.5 h-3.5" />{" "}
                            {b.consecutive_failures} fails
                          </span>
                        ) : (
                          <span className="text-emerald-400 flex items-center gap-1 font-semibold">
                            <CheckCircle2 className="w-3.5 h-3.5" /> Healthy
                          </span>
                        )}
                      </td>
                      <td className="px-4 py-3 text-slate-400">
                        {b.last_synced_at
                          ? new Date(b.last_synced_at).toLocaleString([], {
                              month: "short",
                              day: "numeric",
                              hour: "2-digit",
                              minute: "2-digit",
                            })
                          : "Never"}
                      </td>
                      <td className="px-4 py-3 text-right">
                        <button
                          onClick={() => handleSyncBoard(b.id, b.company_name)}
                          className="px-2.5 py-1 rounded-lg bg-sky-600/20 hover:bg-sky-600 text-sky-300 hover:text-white border border-sky-500/30 text-[11px] font-semibold transition-all cursor-pointer"
                        >
                          Sync Now
                        </button>
                      </td>
                    </tr>
                  ))}
                  {(!crawler_pipeline?.tracked_boards ||
                    crawler_pipeline.tracked_boards.length === 0) && (
                    <tr>
                      <td
                        colSpan="7"
                        className="text-center py-6 text-slate-500"
                      >
                        No company career portals registered yet. Click "Add ATS
                        Board" above.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>

          {/* Recent Ingestion Runs */}
          <div className="rounded-2xl bg-slate-850/60 border border-slate-800 overflow-hidden shadow-md">
            <div className="p-4 border-b border-slate-800">
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <Clock className="w-4 h-4 text-emerald-400" /> Recent
                Synchronization Batches
              </h3>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-900/80 text-slate-400 border-b border-slate-800 uppercase tracking-wider text-[10px]">
                  <tr>
                    <th className="px-4 py-3">Board / Slug</th>
                    <th className="px-4 py-3">Provider</th>
                    <th className="px-4 py-3">Status</th>
                    <th className="px-4 py-3">Fetched</th>
                    <th className="px-4 py-3">New</th>
                    <th className="px-4 py-3">Updated</th>
                    <th className="px-4 py-3">Duration</th>
                    <th className="px-4 py-3">Executed At</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {crawler_pipeline?.recent_runs?.map((r) => (
                    <tr
                      key={r.id}
                      className="hover:bg-slate-800/40 transition-colors"
                    >
                      <td className="px-4 py-3 font-medium text-white">
                        {r.board_slug}
                      </td>
                      <td className="px-4 py-3 uppercase text-[10px] text-slate-400">
                        {r.provider}
                      </td>
                      <td className="px-4 py-3">
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-bold ${getStatusBadgeClass(
                            r.status,
                          )}`}
                        >
                          {r.status}
                        </span>
                      </td>
                      <td className="px-4 py-3 font-semibold text-white">
                        {r.fetched_count}
                      </td>
                      <td className="px-4 py-3 text-emerald-400 font-semibold">
                        +{r.new_count}
                      </td>
                      <td className="px-4 py-3 text-sky-400 font-semibold">
                        {r.updated_count}
                      </td>
                      <td className="px-4 py-3 text-slate-400">
                        {r.duration_ms} ms
                      </td>
                      <td className="px-4 py-3 text-slate-400">
                        {new Date(r.created_at).toLocaleTimeString([], {
                          hour: "2-digit",
                          minute: "2-digit",
                          second: "2-digit",
                        })}
                      </td>
                    </tr>
                  ))}
                  {(!crawler_pipeline?.recent_runs ||
                    crawler_pipeline.recent_runs.length === 0) && (
                    <tr>
                      <td
                        colSpan="8"
                        className="text-center py-6 text-slate-500"
                      >
                        No recent sync batches recorded.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* ==================================================================== */}
      {/* TAB 2: SYSTEM HEALTH, CRASHES & CIRCUIT BREAKERS */}
      {/* ==================================================================== */}
      {activeTab === "system" && (
        <div className="space-y-6 animate-in fade-in duration-150">
          {/* Circuit Breakers */}
          <div>
            <h3 className="text-sm font-bold text-white mb-3 flex items-center gap-2">
              <Server className="w-4 h-4 text-sky-400" /> External Adapter
              Circuit Breakers
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {ai_cost_and_quotas?.circuit_breakers?.map((cb) => (
                <div
                  key={cb.provider}
                  className="p-4 rounded-2xl bg-slate-850/60 border border-slate-800 shadow-md flex flex-col justify-between"
                >
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <span className="font-bold text-sm text-white uppercase">
                        {cb.provider}
                      </span>
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                          cb.is_circuit_open
                            ? "bg-rose-500/20 text-rose-300 border border-rose-500/30 animate-pulse"
                            : "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                        }`}
                      >
                        {cb.is_circuit_open
                          ? "TRIPPED (OPEN)"
                          : "NORMAL (CLOSED)"}
                      </span>
                    </div>
                    <p className="text-xs text-slate-400">
                      Failure Count:{" "}
                      <strong className="text-slate-200">
                        {cb.failure_count}
                      </strong>
                    </p>
                    {cb.last_error_message && (
                      <p className="text-[11px] text-rose-300 mt-2 line-clamp-2 bg-rose-500/5 p-1.5 rounded border border-rose-500/10">
                        {cb.last_error_message}
                      </p>
                    )}
                  </div>
                  <div className="mt-4 pt-3 border-t border-slate-800">
                    <button
                      onClick={() => handleResetBreaker(cb.provider)}
                      className="w-full py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold border border-slate-700 transition-all cursor-pointer flex items-center justify-center gap-1.5"
                    >
                      <RotateCcw className="w-3.5 h-3.5 text-sky-400" /> Reset
                      Breaker
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Recent Crashes & Exceptions */}
          <div className="rounded-2xl bg-slate-850/60 border border-slate-800 overflow-hidden shadow-md">
            <div className="p-4 border-b border-slate-800 flex items-center justify-between">
              <div>
                <h3 className="text-sm font-bold text-white flex items-center gap-2">
                  <AlertTriangle className="w-4 h-4 text-rose-400" /> Recent
                  System Exceptions & Crashes
                </h3>
                <p className="text-xs text-slate-400 mt-0.5">
                  Captured unhandled 5xx exceptions and HTTP error events from
                  in-memory ring buffer
                </p>
              </div>
              <span className="text-xs text-slate-400">
                {system_health?.recent_crashes?.length || 0} recorded
              </span>
            </div>

            <div className="divide-y divide-slate-800/60">
              {system_health?.recent_crashes?.map((err, idx) => (
                <div
                  key={idx}
                  className="p-4 hover:bg-slate-800/30 transition-colors"
                >
                  <div className="flex items-center justify-between gap-4 mb-1.5">
                    <div className="flex items-center gap-2">
                      <span className="px-2 py-0.5 rounded bg-rose-500/20 text-rose-300 border border-rose-500/30 text-[10px] font-bold">
                        {err.method || "ERR"} {err.path || "System"}
                      </span>
                      <span className="font-mono text-xs text-slate-400">
                        cid: {err.correlation_id || "none"}
                      </span>
                    </div>
                    <span className="text-[11px] text-slate-500">
                      {err.timestamp
                        ? new Date(err.timestamp).toLocaleString()
                        : "Just now"}
                    </span>
                  </div>
                  <p className="text-xs font-mono text-rose-300 bg-rose-950/20 p-2.5 rounded-xl border border-rose-500/10 break-all">
                    {err.error}
                  </p>
                </div>
              ))}
              {(!system_health?.recent_crashes ||
                system_health.recent_crashes.length === 0) && (
                <div className="p-8 text-center text-slate-500">
                  <CheckCircle2 className="w-8 h-8 text-emerald-400/50 mx-auto mb-2" />
                  <p className="text-xs font-medium">
                    Zero crashes recorded. System operating normally.
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* ==================================================================== */}
      {/* TAB 3: AI QUOTAS & TELEMETRY */}
      {/* ==================================================================== */}
      {activeTab === "ai" && (
        <div className="space-y-6 animate-in fade-in duration-150">
          {/* Quota Utilization Cards */}
          <div>
            <h3 className="text-sm font-bold text-white mb-3 flex items-center gap-2">
              <Coins className="w-4 h-4 text-amber-400" /> Daily Provider Quotas
              & Token Consumption
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {ai_cost_and_quotas?.daily_usages?.map((u) => {
                const pct = Math.min(
                  100,
                  Math.round((u.call_count / (u.max_calls || 1)) * 100),
                );
                return (
                  <div
                    key={u.provider}
                    className="p-5 rounded-2xl bg-slate-850/60 border border-slate-800 shadow-md space-y-3"
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-sm text-white uppercase">
                        {u.provider}
                      </span>
                      <span className="text-xs font-semibold text-amber-400">
                        ${(u.estimated_cost_usd || 0).toFixed(4)}
                      </span>
                    </div>
                    <div>
                      <div className="flex items-center justify-between text-xs text-slate-400 mb-1">
                        <span>Daily Calls</span>
                        <span>
                          {u.call_count} / {u.max_calls} ({pct}%)
                        </span>
                      </div>
                      <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden">
                        <div
                          className={`h-full rounded-full transition-all duration-300 ${
                            pct > 80
                              ? "bg-rose-500"
                              : pct > 50
                                ? "bg-amber-500"
                                : "bg-sky-500"
                          }`}
                          style={{ width: `${pct}%` }}
                        />
                      </div>
                    </div>
                    <div className="text-[11px] text-slate-400 flex items-center justify-between pt-2 border-t border-slate-800/80">
                      <span>
                        In: {((u.input_tokens || 0) / 1000).toFixed(1)}k tokens
                      </span>
                      <span>
                        Out: {((u.output_tokens || 0) / 1000).toFixed(1)}k
                        tokens
                      </span>
                    </div>
                  </div>
                );
              })}
              {(!ai_cost_and_quotas?.daily_usages ||
                ai_cost_and_quotas.daily_usages.length === 0) && (
                <div className="p-6 rounded-2xl bg-slate-850/40 border border-slate-800 col-span-3 text-center text-slate-500 text-xs">
                  No LLM usage events recorded for today's billing period.
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* ==================================================================== */}
      {/* TAB 4: USERS & MATCH CACHE MANAGEMENT */}
      {/* ==================================================================== */}
      {activeTab === "users" && (
        <div className="space-y-6 animate-in fade-in duration-150">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-4 rounded-2xl bg-slate-800/40 border border-slate-800">
            <div>
              <h3 className="text-sm font-bold text-white">
                Cache & User Operations
              </h3>
              <p className="text-xs text-slate-400">
                Invalidate stale match scores or manage account activation and
                permissions
              </p>
            </div>
            <button
              onClick={handleFlushCache}
              className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-amber-500/10 hover:bg-amber-500/20 text-amber-300 border border-amber-500/30 text-xs font-semibold transition-all cursor-pointer shadow-sm"
            >
              <RotateCcw className="w-3.5 h-3.5 text-amber-400" />
              <span>
                Flush Match Cache ({catalog_breakdown?.cached_matches || 0})
              </span>
            </button>
          </div>

          {/* User Accounts Table */}
          <div className="rounded-2xl bg-slate-850/60 border border-slate-800 overflow-hidden shadow-md">
            <div className="p-4 border-b border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <Users className="w-4 h-4 text-sky-400" /> Registered Candidate
                & Operator Accounts
              </h3>
              <div className="relative">
                <Search className="w-3.5 h-3.5 absolute left-3 top-2.5 text-slate-400" />
                <input
                  type="text"
                  placeholder="Filter users..."
                  value={userSearch}
                  onChange={(e) => setUserSearch(e.target.value)}
                  className="pl-8 pr-3 py-1.5 bg-slate-900 border border-slate-700 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none focus:border-sky-500"
                />
              </div>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-900/80 text-slate-400 border-b border-slate-800 uppercase tracking-wider text-[10px]">
                  <tr>
                    <th className="px-4 py-3">User</th>
                    <th className="px-4 py-3">Role</th>
                    <th className="px-4 py-3">Status</th>
                    <th className="px-4 py-3">Personas</th>
                    <th className="px-4 py-3">CV Blocks</th>
                    <th className="px-4 py-3">Last Login</th>
                    <th className="px-4 py-3 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {filteredUsers.map((u) => (
                    <tr
                      key={u.id}
                      className="hover:bg-slate-800/40 transition-colors"
                    >
                      <td className="px-4 py-3">
                        <div className="font-semibold text-white">
                          {u.full_name || "Unnamed"}
                        </div>
                        <div className="text-[11px] text-slate-400 font-mono">
                          {u.email}
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                            u.role === "admin"
                              ? "bg-amber-500/20 text-amber-300 border border-amber-500/40"
                              : "bg-slate-800 text-slate-300 border border-slate-700"
                          }`}
                        >
                          {u.role}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-semibold ${
                            u.is_active
                              ? "text-emerald-400 bg-emerald-500/10 border border-emerald-500/20"
                              : "text-rose-400 bg-rose-500/10 border border-rose-500/20"
                          }`}
                        >
                          {u.is_active ? "Active" : "Suspended"}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-slate-300 font-semibold">
                        {u.personas_count}
                      </td>
                      <td className="px-4 py-3 text-slate-300 font-semibold">
                        {u.cv_blocks_count}
                      </td>
                      <td className="px-4 py-3 text-slate-400 text-[11px]">
                        {u.last_login_at
                          ? new Date(u.last_login_at).toLocaleString([], {
                              month: "short",
                              day: "numeric",
                              hour: "2-digit",
                              minute: "2-digit",
                            })
                          : "Never"}
                      </td>
                      <td className="px-4 py-3 text-right space-x-2">
                        <button
                          onClick={() => handleToggleUserRole(u.id, u.role)}
                          className="px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 text-[10px] font-medium transition-all cursor-pointer"
                        >
                          {u.role === "admin" ? "Demote" : "Make Admin"}
                        </button>
                        <button
                          onClick={() =>
                            handleToggleUserActive(u.id, u.is_active)
                          }
                          className={`px-2 py-1 rounded text-[10px] font-medium transition-all cursor-pointer ${
                            u.is_active
                              ? "bg-rose-500/10 hover:bg-rose-500/20 text-rose-300 border border-rose-500/30"
                              : "bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-300 border border-emerald-500/30"
                          }`}
                        >
                          {u.is_active ? "Suspend" : "Activate"}
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* ==================================================================== */}
      {/* TAB 5: JOB INGESTION & DIRECT ATS SEARCH */}
      {/* ==================================================================== */}
      {activeTab === "ingest" && (
        <div className="space-y-6 animate-in fade-in duration-200">
          {/* Header & Quick Ingest Actions */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-5 rounded-2xl bg-slate-900 border border-slate-800">
            <div>
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <Search className="w-5 h-5 text-sky-400" /> Direct ATS Hunting & Job Ingestion
              </h3>
              <p className="text-xs text-slate-400 mt-1">
                Directly query live external ATS career boards (JSearch, Greenhouse, Ashby) or manually ingest job postings via URL or raw description.
              </p>
            </div>
            <button
              onClick={() => setIsAddJobOpen(true)}
              className="flex items-center gap-2 px-4 py-2 rounded-xl bg-gradient-to-r from-sky-500 to-indigo-600 hover:from-sky-400 hover:to-indigo-500 text-white text-xs font-bold shadow-lg shadow-sky-500/20 transition-all cursor-pointer whitespace-nowrap self-start sm:self-auto"
            >
              <PlusCircle className="w-4 h-4" /> Import Job (URL / Text)
            </button>
          </div>

          {/* Search Controls Card */}
          <div className="p-5 rounded-2xl bg-slate-900 border border-slate-800 space-y-4">
            <form
              onSubmit={(e) => {
                e.preventDefault();
                handleAtsSearch();
              }}
              className="grid grid-cols-1 md:grid-cols-12 gap-3"
            >
              <div className="relative md:col-span-5">
                <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                <input
                  type="text"
                  placeholder="Job title, keywords, or company..."
                  value={atsQuery}
                  onChange={(e) => setAtsQuery(e.target.value)}
                  className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-slate-800 border border-slate-700 text-sm text-slate-100 placeholder-slate-400 focus:outline-none focus:border-sky-500 focus:ring-1 focus:ring-sky-500 transition-all"
                />
              </div>

              <div className="relative md:col-span-4">
                <MapPin className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                <input
                  type="text"
                  placeholder="Location or 'Remote'..."
                  value={atsLocation}
                  onChange={(e) => setAtsLocation(e.target.value)}
                  className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-slate-800 border border-slate-700 text-sm text-slate-100 placeholder-slate-400 focus:outline-none focus:border-sky-500 focus:ring-1 focus:ring-sky-500 transition-all"
                />
              </div>

              <div className="flex items-center justify-between md:justify-end gap-3 md:col-span-3">
                <label className="flex items-center gap-2 cursor-pointer text-xs text-slate-300 select-none">
                  <input
                    type="checkbox"
                    checked={atsVisaRequired}
                    onChange={(e) => setAtsVisaRequired(e.target.checked)}
                    className="rounded border-slate-700 text-sky-600 focus:ring-sky-500 cursor-pointer"
                  />
                  <span>Visa Required</span>
                </label>

                <button
                  type="submit"
                  disabled={atsLoading}
                  className="px-5 py-2.5 rounded-xl bg-sky-600 hover:bg-sky-500 disabled:opacity-50 text-white text-xs font-bold transition-all shadow-md shadow-sky-600/20 cursor-pointer flex items-center gap-2"
                >
                  {atsLoading ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <Search className="w-4 h-4" />
                  )}
                  Search ATS
                </button>
              </div>
            </form>

            {/* Keyword Chips */}
            <div className="flex flex-wrap items-center gap-1.5 pt-2 border-t border-slate-800/80">
              <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider mr-1">
                Suggested:
              </span>
              {SAMPLE_KEYWORDS.map((kw, idx) => (
                <button
                  key={idx}
                  type="button"
                  onClick={() => {
                    setAtsQuery(kw.query);
                    handleAtsSearch(kw.query, atsLocation);
                  }}
                  className="px-2.5 py-1 rounded-lg text-xs font-medium bg-slate-800/80 hover:bg-slate-700 text-slate-300 hover:text-white border border-slate-700/60 transition-all cursor-pointer"
                >
                  {kw.label}
                </button>
              ))}
            </div>
          </div>

          {/* Results Area */}
          {atsLoading && (
            <div className="p-12 text-center rounded-2xl bg-slate-900 border border-slate-800">
              <Loader2 className="w-8 h-8 animate-spin text-sky-400 mx-auto mb-3" />
              <p className="text-sm font-medium text-slate-300">
                Searching real-time ATS postings across external providers...
              </p>
              <p className="text-xs text-slate-500 mt-1">
                Querying live search API with rate-limiting and deduplication.
              </p>
            </div>
          )}

          {atsError && (
            <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs flex items-center justify-between">
              <div className="flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 text-rose-400" />
                <span>{atsError}</span>
              </div>
              <button
                onClick={() => handleAtsSearch()}
                className="px-3 py-1 bg-rose-500/20 hover:bg-rose-500/30 text-rose-200 rounded font-medium cursor-pointer"
              >
                Retry
              </button>
            </div>
          )}

          {!atsLoading && atsSearched && atsJobs.length === 0 && !atsError && (
            <div className="p-12 text-center rounded-2xl bg-slate-900 border border-slate-800">
              <Search className="w-8 h-8 text-slate-600 mx-auto mb-3" />
              <h4 className="text-sm font-bold text-white mb-1">
                No ATS Postings Found
              </h4>
              <p className="text-xs text-slate-400 max-w-sm mx-auto mb-4">
                No active roles matched your query. Try broadening your keywords, clearing location filters, or manually importing via URL.
              </p>
              <button
                onClick={() => setIsAddJobOpen(true)}
                className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 text-xs font-semibold cursor-pointer"
              >
                Import Custom Job
              </button>
            </div>
          )}

          {!atsLoading && atsJobs.length > 0 && (
            <div className="space-y-3">
              <div className="flex items-center justify-between text-xs text-slate-400 px-1">
                <span>
                  Found <strong className="text-slate-200">{atsJobs.length}</strong> postings
                </span>
              </div>

              <div className="space-y-3">
                {atsJobs.map((job) => {
                  const isExpanded = expandedJobId === job.id;
                  const isCrossChecking = crossCheckingIds.has(job.id);
                  const hasDossier = !!job.company_dossier;

                  return (
                    <div
                      key={job.id}
                      className="p-5 rounded-2xl bg-slate-900 border border-slate-800 hover:border-slate-700/80 transition-all space-y-4"
                    >
                      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
                        <div className="space-y-1.5">
                          <div className="flex flex-wrap items-center gap-2">
                            <h4 className="text-base font-bold text-white hover:text-sky-400 transition-colors">
                              <a
                                href={job.apply_url || job.url}
                                target="_blank"
                                rel="noreferrer"
                              >
                                {job.title}
                              </a>
                            </h4>
                            <JobProvenanceBadge provenance={job.provenance} />
                            {job.visa_sponsorship_status === "available" && (
                              <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
                                Visa Sponsored
                              </span>
                            )}
                          </div>

                          <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-slate-400">
                            <span className="font-semibold text-slate-200">
                              {job.company_name}
                            </span>
                            {job.location && (
                              <span className="flex items-center gap-1 text-slate-400">
                                <MapPin className="w-3.5 h-3.5 text-slate-500" />
                                {job.location}
                              </span>
                            )}
                            {(job.salary_min || job.salary_max) && (
                              <span className="flex items-center gap-1 text-emerald-400 font-medium">
                                <DollarSign className="w-3.5 h-3.5 text-emerald-500" />
                                {job.salary_currency || "$"}
                                {job.salary_min?.toLocaleString()} - {job.salary_currency || "$"}
                                {job.salary_max?.toLocaleString()}
                              </span>
                            )}
                          </div>
                        </div>

                        {/* Action Buttons */}
                        <div className="flex flex-wrap items-center gap-2">
                          <button
                            onClick={() => handleAtsCrossCheck(job.id)}
                            disabled={isCrossChecking}
                            title="Cross-check listing against secondary aggregator"
                            className="px-3 py-1.5 text-xs font-medium rounded-xl border border-slate-700 hover:bg-slate-800 text-slate-300 transition-colors flex items-center gap-1.5 disabled:opacity-50 cursor-pointer"
                          >
                            {isCrossChecking ? (
                              <Loader2 className="w-3.5 h-3.5 animate-spin text-sky-400" />
                            ) : (
                              <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
                            )}
                            Cross-Check
                          </button>

                          {hasDossier && (
                            <button
                              onClick={() =>
                                setExpandedJobId(isExpanded ? null : job.id)
                              }
                              className="px-3 py-1.5 text-xs font-medium rounded-xl border border-slate-700 hover:bg-slate-800 text-slate-300 transition-colors flex items-center gap-1.5 cursor-pointer"
                            >
                              Company Intel
                              {isExpanded ? (
                                <ChevronUp className="w-3.5 h-3.5" />
                              ) : (
                                <ChevronDown className="w-3.5 h-3.5" />
                              )}
                            </button>
                          )}

                          <a
                            href={job.apply_url || job.url}
                            target="_blank"
                            rel="noreferrer"
                            className="px-3.5 py-1.5 text-xs font-bold rounded-xl bg-sky-600 hover:bg-sky-500 text-white transition-all shadow-md shadow-sky-600/20 flex items-center gap-1.5"
                          >
                            View ATS Posting
                          </a>
                        </div>
                      </div>

                      {/* Skills tags */}
                      {job.ats_requirements?.required_skills?.length > 0 && (
                        <div className="flex flex-wrap gap-1.5 pt-1">
                          {job.ats_requirements.required_skills.map((skill, sIdx) => (
                            <span
                              key={sIdx}
                              className="text-[11px] px-2.5 py-0.5 rounded-full bg-slate-800 text-slate-300 border border-slate-700/60"
                            >
                              {skill}
                            </span>
                          ))}
                        </div>
                      )}

                      {/* Expanded Company Dossier View */}
                      {isExpanded && hasDossier && (
                        <div className="pt-2 animate-in fade-in duration-150">
                          <CompanyDossierCard
                            dossier={job.company_dossier}
                            onDossierUpdated={(updated) => {
                              setAtsJobs((prev) =>
                                prev.map((j) =>
                                  j.id === job.id
                                    ? { ...j, company_dossier: updated }
                                    : j,
                                ),
                              );
                            }}
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

      {/* ==================================================================== */}
      {/* TAB: 360° TRACE WATERFALL & LIVE STREAM */}
      {/* ==================================================================== */}
      {activeTab === "traces" && (
        <div className="space-y-6 animate-in fade-in duration-150">
          {/* Header & Filter Controls */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-4 rounded-2xl bg-slate-850/60 border border-slate-800">
            <div>
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <Layers className="w-4 h-4 text-sky-400" />
                Live 360° Transaction & Execution Stream
              </h3>
              <p className="text-xs text-slate-400 mt-0.5">
                End-to-end telemetry correlated from frontend UI click across FastAPI, SQLAlchemy queries, and LLM calls.
              </p>
            </div>
            <div className="flex items-center gap-3">
              <div className="relative">
                <Search className="w-3.5 h-3.5 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
                <input
                  type="text"
                  placeholder="Filter by action, path, or trace..."
                  value={traceFilter}
                  onChange={(e) => setTraceFilter(e.target.value)}
                  className="pl-8 pr-3 py-1.5 text-xs rounded-xl bg-slate-900 border border-slate-700 text-slate-200 placeholder-slate-500 focus:outline-none focus:border-sky-500 w-64"
                />
              </div>
              <span className="text-[11px] font-mono text-slate-400 bg-slate-800 px-2 py-1 rounded-lg border border-slate-700">
                {recent_traces.length} traces buffered
              </span>
            </div>
          </div>

          {/* Trace Stream Table */}
          <div className="rounded-2xl bg-slate-850/60 border border-slate-800 overflow-hidden shadow-md">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs text-slate-300">
                <thead className="bg-slate-800/60 text-slate-400 uppercase text-[10px] font-semibold tracking-wider border-b border-slate-800">
                  <tr>
                    <th className="px-4 py-3">Timestamp</th>
                    <th className="px-4 py-3">Client UI Action</th>
                    <th className="px-4 py-3">HTTP Endpoint</th>
                    <th className="px-4 py-3">Status</th>
                    <th className="px-4 py-3">Latency</th>
                    <th className="px-4 py-3">Correlation / Trace ID</th>
                    <th className="px-4 py-3 text-right">360° Inspect</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/50">
                  {filteredTraces.length === 0 ? (
                    <tr>
                      <td colSpan={7} className="px-4 py-8 text-center text-slate-500 text-xs">
                        No HTTP traces match the active filter.
                      </td>
                    </tr>
                  ) : (
                    filteredTraces.map((tr, idx) => {
                      const isSuccess = tr.status_code >= 200 && tr.status_code < 400;
                      const isClientErr = tr.status_code >= 400 && tr.status_code < 500;
                      const timeStr = new Date(tr.timestamp * 1000).toLocaleTimeString();
                      return (
                        <tr key={tr.correlation_id || idx} className="hover:bg-slate-800/40 transition-colors">
                          <td className="px-4 py-3 font-mono text-[11px] text-slate-400 whitespace-nowrap">
                            {timeStr}
                          </td>
                          <td className="px-4 py-3">
                            <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-md bg-sky-500/10 text-sky-300 border border-sky-500/20 font-mono text-[11px]">
                              {tr.client_action || "api_call"}
                            </span>
                          </td>
                          <td className="px-4 py-3 font-mono text-[11px] text-slate-200">
                            <span className="text-slate-400 font-bold mr-1.5">{tr.method}</span>
                            {tr.path}
                          </td>
                          <td className="px-4 py-3">
                            <span
                              className={`inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold ${
                                isSuccess
                                  ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                                  : isClientErr
                                  ? "bg-amber-500/10 text-amber-400 border border-amber-500/20"
                                  : "bg-rose-500/10 text-rose-400 border border-rose-500/20"
                              }`}
                            >
                              {tr.status_code}
                            </span>
                          </td>
                          <td className="px-4 py-3 font-mono text-[11px]">
                            <span
                              className={
                                tr.duration_ms > 1000
                                  ? "text-rose-400 font-bold"
                                  : tr.duration_ms > 200
                                  ? "text-amber-400"
                                  : "text-emerald-400"
                              }
                            >
                              {tr.duration_ms} ms
                            </span>
                          </td>
                          <td className="px-4 py-3 font-mono text-[11px] text-slate-400">
                            <div className="flex items-center gap-1.5">
                              <span className="truncate max-w-[120px]">{tr.trace_id || tr.correlation_id}</span>
                              <button
                                onClick={() => handleCopy(tr.trace_id || tr.correlation_id, tr.correlation_id)}
                                className="p-1 hover:text-white transition-colors cursor-pointer"
                                title="Copy ID"
                              >
                                {copiedTraceId === tr.correlation_id ? (
                                  <Check className="w-3 h-3 text-emerald-400" />
                                ) : (
                                  <Copy className="w-3 h-3 text-slate-500" />
                                )}
                              </button>
                            </div>
                          </td>
                          <td className="px-4 py-3 text-right">
                            <button
                              onClick={() => setSelectedTrace(tr)}
                              className="px-2.5 py-1 rounded-lg bg-sky-600/20 hover:bg-sky-600/40 text-sky-300 border border-sky-500/30 text-xs font-medium transition-all cursor-pointer"
                            >
                              Details →
                            </button>
                          </td>
                        </tr>
                      );
                    })
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* ==================================================================== */}
      {/* TAB: DATABASE & VECTOR STORAGE HEATMAP */}
      {/* ==================================================================== */}
      {activeTab === "storage" && (
        <div className="space-y-6 animate-in fade-in duration-150">
          {/* Storage Aggregates */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="p-4 rounded-2xl bg-slate-850/60 border border-slate-800 shadow-md">
              <div className="text-xs text-slate-400 mb-1 flex items-center gap-1.5">
                <HardDrive className="w-3.5 h-3.5 text-sky-400" /> Total Database Size
              </div>
              <div className="text-2xl font-black text-white">
                {formatBytes(table_storage.reduce((acc, t) => acc + (t.total_bytes || 0), 0))}
              </div>
              <div className="mt-1 text-[11px] text-slate-400">
                Data + All Primary & Vector Indexes
              </div>
            </div>

            <div className="p-4 rounded-2xl bg-slate-850/60 border border-slate-800 shadow-md">
              <div className="text-xs text-slate-400 mb-1 flex items-center gap-1.5">
                <Layers className="w-3.5 h-3.5 text-indigo-400" /> Total Index Footprint
              </div>
              <div className="text-2xl font-black text-white">
                {formatBytes(table_storage.reduce((acc, t) => acc + (t.index_bytes || 0), 0))}
              </div>
              <div className="mt-1 text-[11px] text-slate-400">
                Includes pgvector HNSW cosine embeddings
              </div>
            </div>

            <div className="p-4 rounded-2xl bg-slate-850/60 border border-slate-800 shadow-md">
              <div className="text-xs text-slate-400 mb-1 flex items-center gap-1.5">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" /> Live Tuples
              </div>
              <div className="text-2xl font-black text-white">
                {table_storage.reduce((acc, t) => acc + (t.live_rows || 0), 0).toLocaleString()}
              </div>
              <div className="mt-1 text-[11px] text-emerald-400 font-medium">
                Active catalog records & sessions
              </div>
            </div>

            <div className="p-4 rounded-2xl bg-slate-850/60 border border-slate-800 shadow-md">
              <div className="text-xs text-slate-400 mb-1 flex items-center gap-1.5">
                <AlertTriangle className="w-3.5 h-3.5 text-amber-400" /> Dead Tuples (Bloat)
              </div>
              <div className="text-2xl font-black text-white">
                {table_storage.reduce((acc, t) => acc + (t.dead_rows || 0), 0).toLocaleString()}
              </div>
              <div className="mt-1 text-[11px] text-slate-400">
                Vacuum reclaimed on next cycle
              </div>
            </div>
          </div>

          {/* Tables Storage & Bloat Detail */}
          <div className="rounded-2xl bg-slate-850/60 border border-slate-800 overflow-hidden shadow-md">
            <div className="p-4 border-b border-slate-800 flex items-center justify-between">
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <Database className="w-4 h-4 text-sky-400" />
                PostgreSQL Catalog Tables, Indexes & Row Operations
              </h3>
              <span className="text-xs text-slate-400">
                Introspected from pg_stat_user_tables
              </span>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs text-slate-300">
                <thead className="bg-slate-800/60 text-slate-400 uppercase text-[10px] font-semibold tracking-wider border-b border-slate-800">
                  <tr>
                    <th className="px-4 py-3">Table Name</th>
                    <th className="px-4 py-3">Live Rows</th>
                    <th className="px-4 py-3">Dead Rows</th>
                    <th className="px-4 py-3">Table Data Size</th>
                    <th className="px-4 py-3">Index Size</th>
                    <th className="px-4 py-3">Total Size</th>
                    <th className="px-4 py-3">Scan Ratio (Idx / Seq)</th>
                    <th className="px-4 py-3">Writes (Ins / Upd / Del)</th>
                    <th className="px-4 py-3 text-right">Health Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/50">
                  {table_storage.length === 0 ? (
                    <tr>
                      <td colSpan={9} className="px-4 py-8 text-center text-slate-400">
                        <Database className="w-8 h-8 text-slate-500 mx-auto mb-2" />
                        <p className="font-medium text-sm text-slate-300">
                          PostgreSQL storage metrics unavailable
                        </p>
                        <p className="text-xs text-slate-500 mt-1">
                          Physical table sizes and bloat stats require an active PostgreSQL connection with pg_stat_user_tables privileges.
                        </p>
                      </td>
                    </tr>
                  ) : (
                    table_storage.map((tbl) => {
                      const totalRows = (tbl.live_rows || 0) + (tbl.dead_rows || 0);
                      const isBloated = tbl.dead_rows > 100 && totalRows > 0 && (tbl.dead_rows / totalRows) > 0.2;
                      return (
                        <tr key={tbl.table_name} className="hover:bg-slate-800/40 transition-colors">
                          <td className="px-4 py-3 font-mono font-bold text-white">
                            {tbl.table_name}
                          </td>
                          <td className="px-4 py-3 font-mono">
                            {(tbl.live_rows || 0).toLocaleString()}
                          </td>
                          <td className="px-4 py-3 font-mono text-slate-400">
                            {(tbl.dead_rows || 0).toLocaleString()}
                          </td>
                          <td className="px-4 py-3 font-mono text-slate-300">
                            {formatBytes(tbl.table_bytes)}
                          </td>
                          <td className="px-4 py-3 font-mono text-indigo-300">
                            {formatBytes(tbl.index_bytes)}
                          </td>
                          <td className="px-4 py-3 font-mono font-bold text-white">
                            {formatBytes(tbl.total_bytes)}
                          </td>
                          <td className="px-4 py-3 font-mono text-[11px] text-slate-400">
                            {tbl.idx_scan || 0} / {tbl.seq_scan || 0}
                          </td>
                          <td className="px-4 py-3 font-mono text-[11px] text-slate-400">
                            +{tbl.inserts || 0} / ~{tbl.updates || 0} / -{tbl.deletes || 0}
                          </td>
                          <td className="px-4 py-3 text-right">
                            <span
                              className={`inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold ${
                                isBloated
                                  ? "bg-amber-500/10 text-amber-400 border border-amber-500/20"
                                  : "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                              }`}
                            >
                              {isBloated ? "Vacuum Rec." : "Optimized"}
                            </span>
                          </td>
                        </tr>
                      );
                    })
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* ==================================================================== */}
      {/* MODAL: REGISTER ATS CAREERS PORTAL */}
      {/* ==================================================================== */}
      {isAddBoardOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-in fade-in duration-150">
          <div className="relative w-full max-w-md bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl overflow-hidden p-6">
            <h2 className="text-base font-bold text-white mb-1">
              Register ATS Company Careers Board
            </h2>
            <p className="text-xs text-slate-400 mb-4">
              Add a public company careers portal to the continuous crawler
              index
            </p>

            <form onSubmit={handleCreateBoard} className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">
                  Company Name
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Tempus AI"
                  value={boardForm.company_name}
                  onChange={(e) =>
                    setBoardForm({ ...boardForm, company_name: e.target.value })
                  }
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none focus:border-sky-500"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">
                  ATS Provider
                </label>
                <select
                  value={boardForm.provider}
                  onChange={(e) =>
                    setBoardForm({ ...boardForm, provider: e.target.value })
                  }
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-xl text-xs text-white focus:outline-none focus:border-sky-500"
                >
                  <option value="greenhouse">Greenhouse</option>
                  <option value="lever">Lever</option>
                  <option value="ashby">Ashby</option>
                  <option value="workable">Workable</option>
                  <option value="smartrecruiters">SmartRecruiters</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">
                  Board Token / Slug
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. tempus or jobs.ashbyhq.com/tempus"
                  value={boardForm.board_token}
                  onChange={(e) =>
                    setBoardForm({ ...boardForm, board_token: e.target.value })
                  }
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-xl text-xs text-white placeholder-slate-500 font-mono focus:outline-none focus:border-sky-500"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">
                  Industry Sector
                </label>
                <select
                  value={boardForm.industry}
                  onChange={(e) =>
                    setBoardForm({ ...boardForm, industry: e.target.value })
                  }
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-xl text-xs text-white focus:outline-none focus:border-sky-500"
                >
                  <option value="healthtech">Healthtech</option>
                  <option value="fintech">Fintech</option>
                  <option value="ai_ml">AI / Machine Learning</option>
                  <option value="biotech">Biotech & Life Sciences</option>
                  <option value="climate">Climate & Energy</option>
                  <option value="enterprise_saas">Enterprise SaaS</option>
                  <option value="security">Cybersecurity</option>
                </select>
              </div>

              <div className="flex items-center gap-2 pt-1">
                <input
                  type="checkbox"
                  id="syncNow"
                  checked={boardForm.sync_now}
                  onChange={(e) =>
                    setBoardForm({ ...boardForm, sync_now: e.target.checked })
                  }
                  className="rounded border-slate-700 text-sky-600 focus:ring-sky-500 cursor-pointer"
                />
                <label
                  htmlFor="syncNow"
                  className="text-xs text-slate-300 cursor-pointer select-none"
                >
                  Enqueue immediate synchronization job
                </label>
              </div>

              <div className="flex items-center justify-end gap-2 pt-3">
                <button
                  type="button"
                  onClick={() => setIsAddBoardOpen(false)}
                  className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium transition-all cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submittingBoard}
                  className="px-4 py-2 rounded-xl bg-sky-600 hover:bg-sky-500 text-white text-xs font-bold shadow-md shadow-sky-600/20 transition-all cursor-pointer disabled:opacity-50"
                >
                  {submittingBoard ? "Registering..." : "Register & Sync"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ==================================================================== */}
      {/* MODAL: DIRECT JOB IMPORT (URL / RAW TEXT) */}
      {/* ==================================================================== */}
      <AddJobModal
        isOpen={isAddJobOpen}
        onClose={() => setIsAddJobOpen(false)}
        onJobAdded={handleJobImported}
      />

      {/* ==================================================================== */}
      {/* SLIDE-OVER EXECUTION DRAWER */}
      {/* ==================================================================== */}
      {selectedTrace && (
        <div
          role="dialog"
          aria-modal="true"
          aria-label="360 Execution Trace Details"
          className="fixed inset-0 z-50 overflow-hidden"
        >
          {/* Backdrop */}
          <div
            className="absolute inset-0 bg-black/60 backdrop-blur-sm transition-opacity cursor-pointer"
            onClick={() => setSelectedTrace(null)}
          />

          <div className="fixed inset-y-0 right-0 max-w-full flex pl-10">
            <div className="w-screen max-w-xl bg-slate-900 border-l border-slate-800 shadow-2xl flex flex-col">
              {/* Drawer Header */}
              <div className="p-6 border-b border-slate-800 flex items-center justify-between">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs uppercase font-extrabold px-2 py-0.5 rounded bg-sky-500/20 text-sky-300 border border-sky-500/30">
                      360° Execution Trace
                    </span>
                    <span
                      className={`text-xs font-bold px-2 py-0.5 rounded ${
                        selectedTrace.status_code >= 200 && selectedTrace.status_code < 400
                          ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30"
                          : "bg-rose-500/20 text-rose-300 border border-rose-500/30"
                      }`}
                    >
                      {selectedTrace.status_code}
                    </span>
                  </div>
                  <h2 className="text-lg font-bold text-white mt-1">
                    {selectedTrace.client_action || "api_call"}
                  </h2>
                </div>
                <button
                  onClick={() => setSelectedTrace(null)}
                  aria-label="Close execution trace drawer"
                  className="p-2 rounded-xl text-slate-400 hover:text-white hover:bg-slate-800 transition-colors cursor-pointer"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              {/* Drawer Content */}
              <div className="flex-1 overflow-y-auto p-6 space-y-6 text-xs text-slate-300">
                {/* 1. Lifecycle Waterfall Breadcrumbs */}
                <div>
                  <h4 className="text-xs uppercase font-bold text-slate-400 tracking-wider mb-3">
                    Execution Lifecycle Breadcrumb
                  </h4>
                  <div className="space-y-3">
                    <div className="p-3 rounded-xl bg-slate-850 border border-slate-800 flex items-start gap-3">
                      <div className="w-6 h-6 rounded-lg bg-sky-500/20 text-sky-400 flex items-center justify-center font-bold text-xs shrink-0">
                        1
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="font-semibold text-white">Client UI Action</div>
                        <div className="font-mono text-[11px] text-sky-300 truncate">
                          {selectedTrace.client_action}
                        </div>
                      </div>
                    </div>

                    <div className="flex justify-center text-slate-600">
                      <ArrowRight className="w-4 h-4 rotate-90" />
                    </div>

                    <div className="p-3 rounded-xl bg-slate-850 border border-slate-800 flex items-start gap-3">
                      <div className="w-6 h-6 rounded-lg bg-emerald-500/20 text-emerald-400 flex items-center justify-center font-bold text-xs shrink-0">
                        2
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="font-semibold text-white">FastAPI Dispatch</div>
                        <div className="font-mono text-[11px] text-emerald-300">
                          {selectedTrace.method} {selectedTrace.path} ({selectedTrace.duration_ms}ms)
                        </div>
                      </div>
                    </div>

                    <div className="flex justify-center text-slate-600">
                      <ArrowRight className="w-4 h-4 rotate-90" />
                    </div>

                    <div className="p-3 rounded-xl bg-slate-850 border border-slate-800 flex items-start gap-3">
                      <div className="w-6 h-6 rounded-lg bg-indigo-500/20 text-indigo-400 flex items-center justify-center font-bold text-xs shrink-0">
                        3
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="font-semibold text-white">SQLAlchemy & Storage Introspection</div>
                        <div className="text-[11px] text-slate-400">
                          Query execution & transaction hooks (see Tempo for span breakdown)
                        </div>
                      </div>
                    </div>

                    <div className="flex justify-center text-slate-600">
                      <ArrowRight className="w-4 h-4 rotate-90" />
                    </div>

                    <div className="p-3 rounded-xl bg-slate-850 border border-slate-800 flex items-start gap-3">
                      <div className="w-6 h-6 rounded-lg bg-amber-500/20 text-amber-400 flex items-center justify-center font-bold text-xs shrink-0">
                        4
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="font-semibold text-white">LangGraph & LLM Callbacks</div>
                        <div className="text-[11px] text-slate-400">
                          Agent node spans & token attribution (if invoked; see Tempo / Phoenix)
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                {/* 2. Correlation & Distributed Context */}
                <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 font-mono space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-slate-400 text-[11px]">Trace ID (OTel W3C):</span>
                    <button
                      onClick={() => handleCopy(selectedTrace.trace_id, "drawer-trace")}
                      className="text-sky-400 hover:text-sky-300 flex items-center gap-1 text-[11px] cursor-pointer"
                    >
                      {copiedTraceId === "drawer-trace" ? "Copied" : "Copy"}
                    </button>
                  </div>
                  <div className="text-white text-[11px] truncate bg-slate-900 p-2 rounded border border-slate-800">
                    {selectedTrace.trace_id || "N/A"}
                  </div>

                  <div className="flex items-center justify-between pt-2">
                    <span className="text-slate-400 text-[11px]">Correlation ID:</span>
                    <button
                      onClick={() => handleCopy(selectedTrace.correlation_id, "drawer-corr")}
                      className="text-sky-400 hover:text-sky-300 flex items-center gap-1 text-[11px] cursor-pointer"
                    >
                      {copiedTraceId === "drawer-corr" ? "Copied" : "Copy"}
                    </button>
                  </div>
                  <div className="text-white text-[11px] truncate bg-slate-900 p-2 rounded border border-slate-800">
                    {selectedTrace.correlation_id}
                  </div>
                </div>

                {/* 3. Deep-Link External Launchpads */}
                <div>
                  <h4 className="text-xs uppercase font-bold text-slate-400 tracking-wider mb-3">
                    External Telemetry Cockpits
                  </h4>
                  <div className="grid grid-cols-1 gap-2.5">
                    {system_health?.grafana_url && (
                      <>
                        <a
                          href={`${system_health.grafana_url}/explore?left=%5B%22now-1h%22,%22now%22,%22tempo%22,%7B%22query%22:%22${selectedTrace.trace_id}%22%7D%5D`}
                          target="_blank"
                          rel="noreferrer"
                          className="flex items-center justify-between p-3 rounded-xl bg-slate-850 hover:bg-slate-800 border border-slate-800 hover:border-orange-500/40 text-slate-200 transition-all group"
                        >
                          <div className="flex items-center gap-2.5">
                            <Activity className="w-4 h-4 text-orange-400" />
                            <div>
                              <div className="font-semibold text-white">View Waterfall in Grafana Tempo</div>
                              <div className="text-[11px] text-slate-400">Open distributed span graph</div>
                            </div>
                          </div>
                          <ExternalLink className="w-3.5 h-3.5 text-slate-500 group-hover:text-orange-400 transition-colors" />
                        </a>
                      </>
                    )}

                    {system_health?.phoenix_url && (
                      <a
                        href={`${system_health.phoenix_url}/projects`}
                        target="_blank"
                        rel="noreferrer"
                        className="flex items-center justify-between p-3 rounded-xl bg-slate-850 hover:bg-slate-800 border border-slate-800 hover:border-indigo-500/40 text-slate-200 transition-all group"
                      >
                        <div className="flex items-center gap-2.5">
                          <Flame className="w-4 h-4 text-indigo-400" />
                          <div>
                            <div className="font-semibold text-white">Inspect Prompts & Evals in Arize Phoenix</div>
                            <div className="text-[11px] text-slate-400">LLM token spend & hallucinations</div>
                          </div>
                        </div>
                        <ExternalLink className="w-3.5 h-3.5 text-slate-500 group-hover:text-indigo-400 transition-colors" />
                      </a>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default AdminDashboard;
