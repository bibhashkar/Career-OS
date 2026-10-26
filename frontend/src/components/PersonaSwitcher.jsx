import React, { useState, useEffect, useRef } from "react";
import { ChevronDown, Globe, Sparkles, Layers, Award, Check, UserCheck, AlertCircle } from "lucide-react";
import { getCandidatePersonas, setDefaultPersona } from "../services/api";

export function PersonaSwitcher({
  activePersonaId,
  onPersonaChange,
  onOpenAudit,
  onManagePersonas,
}) {
  const [personas, setPersonas] = useState([]);
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef(null);

  useEffect(() => {
    loadPersonas();
  }, []);

  // Close dropdown on click outside
  useEffect(() => {
    function handleClickOutside(event) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  async function loadPersonas() {
    try {
      const data = await getCandidatePersonas();
      setPersonas(data || []);
    } catch (err) {
      if (err.code !== "ERR_NETWORK") {
        console.warn("Failed to load candidate personas:", err.message || err);
      }
      setPersonas([
        {
          id: "universal",
          name: "My Career Profile",
          is_common_persona: true,
          is_default: true,
          completeness_score: 0,
        },
      ]);
    }
  }

  const activePersona =
    personas.find((p) => p.id === activePersonaId) ||
    personas.find((p) => p.is_default) ||
    personas[0] || {
      id: "universal",
      name: "My Career Profile",
      is_common_persona: true,
      completeness_score: 0,
    };

  const completenessScore = activePersona?.completeness_score ?? 0;
  const isProfileEmpty = completenessScore === 0;

  async function handleSelect(persona) {
    setIsOpen(false);
    try {
      await setDefaultPersona(persona.id);
      if (onPersonaChange) {
        onPersonaChange(persona);
      }
      loadPersonas();
    } catch (err) {
      console.error("Failed to set default persona:", err);
    }
  }

  return (
    <div className="relative" ref={dropdownRef}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        data-testid="persona-switcher-btn"
        className="flex items-center gap-2 bg-slate-800/90 hover:bg-slate-700/90 text-slate-200 px-3 py-1.5 rounded-xl border border-slate-700/80 text-xs font-medium transition-all shadow-sm cursor-pointer"
        title="Switch active career persona lens"
      >
        <Sparkles className="w-3.5 h-3.5 text-sky-400" />
        <span className="font-semibold text-slate-100 max-w-[150px] truncate">
          {activePersona.name || "My Career Profile"}
        </span>

        {/* Completeness Pill */}
        <span
          className={`text-[10px] font-bold px-1.5 py-0.5 rounded-full border ${
            isProfileEmpty
              ? "bg-rose-500/10 text-rose-300 border-rose-500/20"
              : completenessScore >= 75
                ? "bg-emerald-500/15 text-emerald-300 border-emerald-500/30"
                : completenessScore >= 50
                  ? "bg-sky-500/15 text-sky-300 border-sky-500/30"
                  : "bg-amber-500/15 text-amber-300 border-amber-500/30"
          }`}
        >
          {completenessScore}% Complete
        </span>

        <ChevronDown
          className={`w-3 h-3 text-slate-400 transition-transform ${
            isOpen ? "rotate-180" : ""
          }`}
        />
      </button>

      {isOpen && (
        <div className="absolute right-0 mt-2 w-80 bg-slate-900 border border-slate-800 rounded-2xl shadow-xl shadow-black/50 z-50 overflow-hidden backdrop-blur-md animate-in fade-in duration-100">
          <div className="p-3 border-b border-slate-800/80 bg-slate-800/40">
            <div className="flex items-center justify-between">
              <p className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">
                Target Career Personas
              </p>
              <span className="text-[10px] text-slate-400 font-medium">
                Single Profile Mode
              </span>
            </div>
            <p className="text-[11px] text-slate-400 mt-0.5">
              Candidate intelligence powers grounded match probabilities
            </p>

            {/* Completeness Bar in Dropdown */}
            <div className="mt-2.5 pt-2 border-t border-slate-800/60">
              <div className="flex items-center justify-between text-[11px] mb-1">
                <span className="text-slate-300 font-medium flex items-center gap-1">
                  <UserCheck className="w-3 h-3 text-sky-400" /> Profile Completeness
                </span>
                <span className={`font-bold ${
                  isProfileEmpty
                    ? "text-rose-400"
                    : completenessScore >= 75
                      ? "text-emerald-400"
                      : "text-amber-400"
                }`}>
                  {completenessScore}%
                </span>
              </div>
              <div className="w-full h-1.5 bg-slate-950 rounded-full overflow-hidden">
                <div
                  className={`h-full rounded-full transition-all duration-300 ${
                    isProfileEmpty
                      ? "bg-rose-500"
                      : completenessScore >= 75
                        ? "bg-emerald-500"
                        : completenessScore >= 50
                          ? "bg-sky-500"
                          : "bg-amber-500"
                  }`}
                  style={{ width: `${Math.max(4, completenessScore)}%` }}
                />
              </div>
              {isProfileEmpty && (
                <p className="text-[10px] text-rose-300 mt-1 flex items-center gap-1">
                  <AlertCircle className="w-2.5 h-2.5 shrink-0" />
                  0% shared: Grounded mode locked until profile updated
                </p>
              )}
            </div>
          </div>

          <div className="max-h-60 overflow-y-auto p-1.5 space-y-1">
            {personas.map((p) => {
              const isSelected = p.id === activePersona.id;
              const pScore = p.completeness_score ?? completenessScore;
              return (
                <button
                  key={p.id}
                  onClick={() => handleSelect(p)}
                  className={`w-full flex items-start gap-2.5 p-2 rounded-xl text-left transition-all ${
                    isSelected
                      ? "bg-sky-500/15 border border-sky-500/30 text-white"
                      : "hover:bg-slate-800 text-slate-300"
                  }`}
                >
                  <div className="mt-0.5">
                    {p.is_common_persona ? (
                      <Globe className="w-4 h-4 text-sky-400" />
                    ) : (
                      <Sparkles className="w-4 h-4 text-indigo-400" />
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-semibold truncate">
                        {p.name}
                      </span>
                      {isSelected && (
                        <Check className="w-3.5 h-3.5 text-sky-400" />
                      )}
                    </div>
                    <p className="text-[11px] text-slate-400 truncate mt-0.5">
                      {p.headline || `${p.seniority_level} • ${p.years_experience}y exp`}
                    </p>
                    <div className="flex items-center gap-2 mt-1 text-[10px] text-slate-500">
                      <span>{p.skill_count || 0} skills</span>
                      <span>•</span>
                      <span>{p.block_count || 0} blocks</span>
                      <span>•</span>
                      <span className="text-sky-400 font-medium">{pScore}% complete</span>
                    </div>
                  </div>
                </button>
              );
            })}
          </div>

          <div className="p-2 border-t border-slate-800/80 bg-slate-900/80 flex items-center justify-between text-xs">
            {onOpenAudit && (
              <button
                onClick={() => {
                  setIsOpen(false);
                  onOpenAudit();
                }}
                className="flex items-center gap-1.5 text-slate-400 hover:text-sky-400 font-medium px-2 py-1 rounded-lg transition-colors cursor-pointer"
              >
                <Award className="w-3.5 h-3.5" /> 360° Audit
              </button>
            )}
            {onManagePersonas && (
              <button
                onClick={() => {
                  setIsOpen(false);
                  onManagePersonas();
                }}
                data-testid="manage-personas-trigger-btn"
                className="flex items-center gap-1.5 text-sky-400 hover:text-sky-300 font-semibold px-2 py-1 rounded-lg transition-colors cursor-pointer"
              >
                <Layers className="w-3.5 h-3.5" /> Manage Profile & Completeness
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export default PersonaSwitcher;

