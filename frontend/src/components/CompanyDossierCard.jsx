import React, { useState } from "react";
import { Building2, Cpu, Newspaper, Briefcase, Sparkles, RefreshCw } from "lucide-react";
import { refreshCompanyIntel } from "../services/api";

export function CompanyDossierCard({ dossier, onDossierUpdated }) {
  const [refreshing, setRefreshing] = useState(false);
  const [statusMsg, setStatusMsg] = useState(null);

  if (!dossier) return null;

  const handleRefresh = async () => {
    setRefreshing(true);
    setStatusMsg(null);
    try {
      const res = await refreshCompanyIntel(dossier.company_name);
      if (res.dossier && onDossierUpdated) {
        onDossierUpdated(res.dossier);
      }
      setStatusMsg(res.message || (res.refreshed ? "Refreshed!" : "Cooldown active"));
    } catch {
      setStatusMsg("Refresh failed");
    } finally {
      setRefreshing(false);
      setTimeout(() => setStatusMsg(null), 4000);
    }
  };

  return (
    <div className="bg-slate-800/80 border border-slate-700/80 rounded-xl p-5 shadow-lg space-y-4">
      <div className="flex items-center justify-between border-b border-slate-700/60 pb-3">
        <div className="flex items-center space-x-3">
          <div className="p-2 bg-sky-500/10 text-sky-400 rounded-lg">
            <Building2 className="w-5 h-5" />
          </div>
          <div>
            <h4 className="text-base font-semibold text-slate-100">
              {dossier.company_name}
            </h4>
            <span className="text-xs text-slate-400">
              {dossier.industry || "Technology"} • {dossier.domain || "company.com"}
            </span>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {statusMsg && (
            <span className="text-[11px] text-slate-400 italic animate-fadeIn">
              {statusMsg}
            </span>
          )}
          <button
            onClick={handleRefresh}
            disabled={refreshing}
            title="Refresh company intelligence"
            className="p-1.5 rounded-lg border border-slate-700 hover:bg-slate-700/60 text-slate-400 hover:text-sky-300 transition-colors disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? "animate-spin text-sky-400" : ""}`} />
          </button>
          <span className="text-xs font-medium px-2.5 py-1 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 flex items-center gap-1">
            <Sparkles className="w-3 h-3" /> Intel Verified
          </span>
        </div>
      </div>

      {/* Tech Stack Badges */}
      <div>
        <div className="text-xs font-semibold uppercase tracking-wider text-slate-400 flex items-center gap-1.5 mb-2">
          <Cpu className="w-3.5 h-3.5 text-sky-400" /> Core Tech Stack
        </div>
        <div className="flex flex-wrap gap-1.5">
          {dossier.tech_stack?.map((tech, idx) => (
            <span
              key={idx}
              className="text-xs px-2.5 py-1 rounded-md bg-slate-900/90 text-sky-300 border border-slate-700 font-mono"
            >
              {tech}
            </span>
          ))}
        </div>
      </div>

      {/* Business Model */}
      {dossier.business_model && (
        <div>
          <div className="text-xs font-semibold uppercase tracking-wider text-slate-400 flex items-center gap-1.5 mb-1">
            <Briefcase className="w-3.5 h-3.5 text-amber-400" /> Business Model
          </div>
          <p className="text-xs text-slate-300 leading-relaxed">
            {dossier.business_model}
          </p>
        </div>
      )}

      {/* Recent News */}
      {dossier.recent_news?.length > 0 && (
        <div>
          <div className="text-xs font-semibold uppercase tracking-wider text-slate-400 flex items-center gap-1.5 mb-2">
            <Newspaper className="w-3.5 h-3.5 text-indigo-400" /> Recent Intelligence
          </div>
          <ul className="space-y-1.5">
            {dossier.recent_news.map((item, idx) => (
              <li
                key={idx}
                className="text-xs text-slate-300 bg-slate-900/50 p-2 rounded border border-slate-700/50 flex justify-between items-center"
              >
                <span>{item.title}</span>
                {item.source && (
                  <span className="text-[10px] text-slate-400 font-medium ml-2">
                    {item.source}
                  </span>
                )}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
