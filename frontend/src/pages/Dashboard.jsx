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
} from "lucide-react";
import { searchJobs } from "../services/api";
import { CompanyDossierCard } from "../components/CompanyDossierCard";

export function Dashboard({ onSelectJob, onStartInterview }) {
  const [query, setQuery] = useState("AI Systems Engineer");
  const [location, setLocation] = useState("Remote");
  const [visaRequired, setVisaRequired] = useState(true);
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [expandedJobId, setExpandedJobId] = useState(null);

  const fetchJobs = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await searchJobs(query, location, visaRequired);
      setJobs(data.jobs || []);
    } catch (err) {
      setError(
        err.response?.data?.detail || "Failed to search job boards. Please retry."
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchJobs();
  }, []);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    fetchJobs();
  };

  const toggleDossier = (jobId) => {
    setExpandedJobId(expandedJobId === jobId ? null : jobId);
  };

  return (
    <div className="max-w-6xl mx-auto px-4 py-8 space-y-8">
      {/* Header Banner */}
      <div className="space-y-2">
        <h1 className="text-3xl font-bold tracking-tight text-white flex items-center gap-2">
          <Briefcase className="w-8 h-8 text-sky-400" /> Career Intelligence & Hunter
        </h1>
        <p className="text-sm text-slate-400 max-w-2xl">
          Discover target roles, analyze employer tech stacks, and simulate ATS compatibility loops with multi-agent orchestration.
        </p>
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
            Hunter & Intel agents scanning job boards and researching tech stacks...
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
        <div className="text-center py-16 text-slate-500 space-y-2">
          <p className="text-base font-medium text-slate-400">No jobs matched your criteria.</p>
          <p className="text-xs">Try broadening your search query or unchecking the visa filter.</p>
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

              return (
                <div
                  key={job.id}
                  className="bg-slate-800/80 border border-slate-700/70 rounded-2xl p-6 hover:border-slate-600/80 transition-all shadow-md space-y-4"
                >
                  <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <h3 className="text-lg font-bold text-white">{job.title}</h3>
                        {job.ats_requirements?.visa_sponsorship && (
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
                    <div className="flex items-center gap-2">
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
                      <CompanyDossierCard dossier={job.company_dossier} />
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
