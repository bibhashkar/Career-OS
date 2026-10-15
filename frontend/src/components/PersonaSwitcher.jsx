import React, { useState, useEffect, useRef } from "react";
import { ChevronDown, Globe, Sparkles, Plus, Award, Check } from "lucide-react";
import { getCandidatePersonas, setDefaultPersona } from "../services/api";

export function PersonaSwitcher({ activePersonaId, onPersonaChange, onOpenAudit }) {
  const [personas, setPersonas] = useState([]);
  const [isOpen, setIsOpen] = useState(false);
  const [loading, setLoading] = useState(false);
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
      setLoading(true);
      const data = await getCandidatePersonas();
      setPersonas(data || []);
    } catch (err) {
      console.error("Failed to load candidate personas:", err);
    } finally {
      setLoading(false);
    }
  }

  const activePersona =
    personas.find((p) => p.id === activePersonaId) ||
    personas.find((p) => p.is_default) ||
    personas[0] || {
      id: "universal",
      name: "Universal Profile",
      is_common_persona: true,
    };

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
        className="flex items-center gap-2 bg-slate-800/90 hover:bg-slate-700/90 text-slate-200 px-3 py-1.5 rounded-xl border border-slate-700/80 text-xs font-medium transition-all shadow-sm"
        title="Switch active career persona lens"
      >
        {activePersona.is_common_persona ? (
          <Globe className="w-3.5 h-3.5 text-sky-400" />
        ) : (
          <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
        )}
        <span className="font-semibold text-slate-100 max-w-[140px] truncate">
          {activePersona.name}
        </span>
        <ChevronDown
          className={`w-3 h-3 text-slate-400 transition-transform ${
            isOpen ? "rotate-180" : ""
          }`}
        />
      </button>

      {isOpen && (
        <div className="absolute right-0 mt-2 w-72 bg-slate-900 border border-slate-800 rounded-2xl shadow-xl shadow-black/50 z-50 overflow-hidden backdrop-blur-md">
          <div className="p-3 border-b border-slate-800/80 bg-slate-800/40">
            <p className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">
              Target Career Personas
            </p>
            <p className="text-[11px] text-slate-500 mt-0.5">
              Switch lens to recalculate match probabilities
            </p>
          </div>

          <div className="max-h-60 overflow-y-auto p-1.5 space-y-1">
            {personas.map((p) => {
              const isSelected = p.id === activePersona.id;
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
                      <span>{p.skill_count} skills</span>
                      <span>•</span>
                      <span>{p.block_count} blocks</span>
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
                className="flex items-center gap-1.5 text-slate-400 hover:text-sky-400 font-medium px-2 py-1 rounded-lg transition-colors"
              >
                <Award className="w-3.5 h-3.5" /> 360° Audit
              </button>
            )}
            <a
              href="/onboarding"
              className="flex items-center gap-1 text-sky-400 hover:text-sky-300 font-semibold px-2 py-1 rounded-lg transition-colors"
            >
              <Plus className="w-3.5 h-3.5" /> New Persona
            </a>
          </div>
        </div>
      )}
    </div>
  );
}

export default PersonaSwitcher;

