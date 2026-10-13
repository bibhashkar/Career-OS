import React, { useState, useEffect } from "react";
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
} from "lucide-react";
import { searchJobs, crossCheckJob } from "../services/api";
import { CompanyDossierCard } from "../components/CompanyDossierCard";
import { JobProvenanceBadge } from "../components/JobProvenanceBadge";
import { AddJobModal } from "../components/AddJobModal";

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

export function Dashboard({ onSelectJob, onStartInterview }) {
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

  const fetchJobs = React.useCallback(
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

  useEffect(() => {
    if (query.trim() || location.trim()) {
      fetchJobs();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

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
            Discover verified career-site roles, analyze employer tech stacks, and import custom job postings directly from ATS URLs.
          </p>
        </div>
        <button
          onClick={() => setIsAddModalOpen(true)}
          className="self-start md:self-auto px-4 py-2.5 bg-gradient-to-r from-sky-600 to-indigo-600 hover:from-sky-500 hover:to-indigo-500 text-white font-medium rounded-xl text-sm transition-all shadow-md shadow-sky-600/20 flex items-center gap-2"
        >
          <PlusCircle className="w-4 h-4" /> Import Job
        </button>
      </div>

      {/* Search & Constraint Filter Bar */}
      <form
        onSubmit={handleSearchSubmit}
        aria-label="Job search and filter form"
        className="bg-slate-800/90 border border-slate-700/80 rounded-2xl p-4 shadow-xl grid grid-cols-1 md:grid-cols-4 gap-3 items-center"
      >
        <div className="relative md:col-span-2">
          <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-3.5" aria-hidden="true" />
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
          <MapPin className="w-4 h-4 text-slate-400 absolute left-3.5 top-3.5" aria-hidden="true" />
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
              <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" aria-hidden="true" /> H-1B / Visa
            </span>
          </label>

          <button
            type="submit"
            disabled={loading}
            aria-label={loading ? "Searching jobs" : "Search jobs"}
            className="px-5 py-2.5 bg-sky-600 hover:bg-sky-500 disabled:bg-slate-700 text-white font-medium rounded-xl text-sm transition-all shadow-md shadow-sky-600/20 flex items-center gap-2 focus:outline-none focus:ring-2 focus:ring-sky-400"
          >
            {loading ? <Loader2 className="w-4 h-4 animate-spin" aria-hidden="true" /> : "Search"}
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
              {hasSearched ? "No matching roles found" : "Ready to explore open positions?"}
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
              Matched Roles ({jobs.length})
            </h2>
            <span className="text-xs text-slate-500">Ranked by Hunter agent affinity</span>
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
                        {(job.ats_requirements?.visa_sponsorship || job.visa_sponsorship === "yes") && (
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
                        onDossierUpdated={(updated) => handleDossierUpdated(job.id, updated)}
                      />
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Ingestion Modal */}
      <AddJobModal
        isOpen={isAddModalOpen}
        onClose={() => setIsAddModalOpen(false)}
        onJobAdded={handleJobAdded}
      />
    </div>
  );
}
