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
} from "../services/api";
import { getStatusBadgeClass } from "../utils/statusBadges";

export function AdminDashboard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState(null);
  const [actionSuccess, setActionSuccess] = useState(null);
  const [activeTab, setActiveTab] = useState("crawlers"); // 'crawlers' | 'system' | 'ai' | 'users'

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
  } = data || {};

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
    </div>
  );
}

export default AdminDashboard;
