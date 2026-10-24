import React, { useState, useEffect, useRef } from "react";
import { Search, X, Building, Stethoscope, Zap, Briefcase, Home, Loader2 } from "lucide-react";
import { parseSearchQuery } from "../../services/api";

export const CHIP_TYPE_ICONS = {
  company: Building,
  industry: Stethoscope,
  skill: Zap,
  seniority: Briefcase,
  modality: Home,
};

export const CHIP_TYPE_COLORS = {
  company: "bg-blue-500/10 text-blue-300 border-blue-500/20",
  industry: "bg-emerald-500/10 text-emerald-300 border-emerald-500/20",
  skill: "bg-purple-500/10 text-purple-300 border-purple-500/20",
  seniority: "bg-amber-500/10 text-amber-300 border-amber-500/20",
  modality: "bg-sky-500/10 text-sky-300 border-sky-500/20",
};

const INDUSTRY_LABELS = {
  healthtech: "HealthTech",
  healthcare_it: "Healthcare IT",
  fintech: "FinTech",
  ecommerce: "E-Commerce",
  devtools: "DevTools",
  cybersecurity: "Cybersecurity",
  ai_ml: "AI / ML",
  general_saas: "General SaaS",
  biotech: "BioTech",
  edtech: "EdTech",
  govtech: "GovTech",
  insurtech: "InsurTech",
};

const MODALITY_LABELS = {
  remote: "Remote Only",
  hybrid: "Hybrid",
  on_site: "On-Site Only",
};

export function formatEntityLabel(type, value) {
  if (!value) return "";
  const raw = String(value).trim();
  const lower = raw.toLowerCase();

  if (type === "industry") {
    if (INDUSTRY_LABELS[lower]) return INDUSTRY_LABELS[lower];
    return raw
      .split(/[_\s]+/)
      .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
      .join(" ");
  }

  if (type === "modality") {
    return MODALITY_LABELS[lower] || raw.charAt(0).toUpperCase() + raw.slice(1);
  }

  if (type === "company" || type === "seniority") {
    return raw
      .split(/[_\s]+/)
      .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
      .join(" ");
  }

  return raw;
}

export function TokenizedOmnibar({
  rawQuery,
  onQueryChange,
  chips = [],
  onAddChip,
  onSelectModality,
  onSearch,
  isSearching = false,
}) {
  const [inputValue, setInputValue] = useState(rawQuery || "");
  const [suggestions, setSuggestions] = useState([]);
  const [isLoadingSuggestions, setIsLoadingSuggestions] = useState(false);
  const [showDropdown, setShowDropdown] = useState(false);
  const inputRef = useRef(null);
  const containerRef = useRef(null);

  // Sync internal input value if parent rawQuery changes externally
  useEffect(() => {
    setInputValue(rawQuery || "");
  }, [rawQuery]);

  // Debounced token extraction for autocomplete suggestions
  useEffect(() => {
    const trimmed = inputValue.trim();
    if (!trimmed || trimmed.length < 2) {
      setSuggestions([]);
      setShowDropdown(false);
      return;
    }

    const timer = setTimeout(async () => {
      try {
        setIsLoadingSuggestions(true);
        const parsed = await parseSearchQuery(trimmed);
        const items = [];

        (parsed.companies || []).forEach((c) => {
          items.push({
            type: "company",
            value: c,
            label: formatEntityLabel("company", c),
            category: "Company",
          });
        });
        (parsed.target_industries || []).forEach((ind) => {
          items.push({
            type: "industry",
            value: ind,
            label: formatEntityLabel("industry", ind),
            category: "Industry",
          });
        });
        (parsed.seniority_levels || []).forEach((sen) => {
          items.push({
            type: "seniority",
            value: sen,
            label: formatEntityLabel("seniority", sen),
            category: "Seniority",
          });
        });
        (parsed.must_have_skills || []).forEach((s) => {
          items.push({
            type: "skill",
            value: s,
            label: formatEntityLabel("skill", s),
            category: "Skill",
          });
        });
        if (parsed.workplace_modality) {
          items.push({
            type: "modality",
            value: parsed.workplace_modality,
            label: formatEntityLabel("modality", parsed.workplace_modality),
            category: "Workplace",
          });
        }

        // Filter out already active chips
        const activeVals = new Set(chips.map((c) => `${c.type}:${c.value.toLowerCase()}`));
        const filtered = items.filter(
          (item) => !activeVals.has(`${item.type}:${item.value.toLowerCase()}`)
        );

        setSuggestions(filtered);
        setShowDropdown(filtered.length > 0);
      } catch {
        setSuggestions([]);
      } finally {
        setIsLoadingSuggestions(false);
      }
    }, 250);

    return () => clearTimeout(timer);
  }, [inputValue, chips]);

  // Click outside listener to close dropdown
  useEffect(() => {
    function handleClickOutside(event) {
      if (containerRef.current && !containerRef.current.contains(event.target)) {
        setShowDropdown(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleKeyDown = (e) => {
    if (e.key === "Enter") {
      e.preventDefault();
      if (suggestions.length > 0 && showDropdown) {
        handleSelectSuggestion(suggestions[0]);
      } else {
        setShowDropdown(false);
        onQueryChange(inputValue);
        if (onSearch) onSearch();
      }
    } else if (e.key === "Escape") {
      setShowDropdown(false);
    }
  };

  const handleSelectSuggestion = (suggestion) => {
    if (suggestion.type === "modality" && onSelectModality) {
      onSelectModality(suggestion.value);
    } else if (onAddChip) {
      onAddChip({
        type: suggestion.type,
        value: suggestion.value,
        label: suggestion.label,
      });
    }

    // Remove the recognized entity token from text input
    const cleaned = inputValue
      .replace(new RegExp(`\\b${suggestion.value.replace(/_/g, "[_\\s-]?")}\\b`, "gi"), "")
      .replace(/\s+/g, " ")
      .trim();
    setInputValue(cleaned);
    onQueryChange(cleaned);
    setShowDropdown(false);
    if (inputRef.current) inputRef.current.focus();
  };

  return (
    <div ref={containerRef} className="relative w-full">
      <div
        className="flex items-center gap-2 w-full min-h-[42px] px-3.5 py-1.5 bg-slate-900/90 border border-slate-700 rounded-xl focus-within:border-sky-500 focus-within:ring-2 focus-within:ring-sky-500/20 transition-all cursor-text"
        onClick={() => inputRef.current && inputRef.current.focus()}
      >
        <Search className="w-4 h-4 text-slate-400 shrink-0" />

        {/* Free Text Input (unobstructed — chips render in dedicated row below) */}
        <input
          ref={inputRef}
          type="text"
          value={inputValue}
          onChange={(e) => {
            setInputValue(e.target.value);
            onQueryChange(e.target.value);
          }}
          onKeyDown={handleKeyDown}
          onFocus={() => {
            if (suggestions.length > 0) setShowDropdown(true);
          }}
          placeholder="Search company, skills, industry, or keywords (e.g. 'Stripe HealthTech Kubernetes')..."
          aria-label="Search company, job title, or keywords"
          data-testid="matches-search-input"
          className="flex-1 min-w-[140px] bg-transparent text-xs text-white placeholder-slate-500 focus:outline-none"
        />

        {/* Action Controls */}
        <div className="flex items-center gap-1.5 ml-auto shrink-0">
          {isLoadingSuggestions && (
            <Loader2 className="w-3.5 h-3.5 text-slate-400 animate-spin" />
          )}

          {inputValue && (
            <button
              type="button"
              onClick={(e) => {
                e.stopPropagation();
                setInputValue("");
                onQueryChange("");
              }}
              className="p-1 text-slate-400 hover:text-slate-200 rounded-md transition-colors"
              title="Clear search input"
              aria-label="Clear omnibar"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          )}

          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation();
              onQueryChange(inputValue);
              if (onSearch) onSearch();
            }}
            disabled={isSearching}
            className="px-3 py-1 bg-sky-600 hover:bg-sky-500 disabled:opacity-50 text-white text-xs font-semibold rounded-lg shadow-sm transition-colors"
          >
            {isSearching ? "Searching..." : "Search"}
          </button>
        </div>
      </div>

      {/* Autocomplete Suggestions Dropdown */}
      {showDropdown && suggestions.length > 0 && (
        <div className="absolute left-0 right-0 top-full mt-1.5 z-50 bg-slate-900 border border-slate-700 rounded-xl shadow-2xl overflow-hidden py-1">
          <div className="px-3 py-1.5 text-[10px] font-semibold tracking-wider text-slate-400 uppercase border-b border-slate-800">
            Detected Facets — Press Enter to Apply
          </div>
          <div className="max-h-60 overflow-y-auto">
            {suggestions.map((item, idx) => {
              const IconComp = CHIP_TYPE_ICONS[item.type] || Zap;
              const colorClass = CHIP_TYPE_COLORS[item.type] || "text-slate-300";

              return (
                <button
                  key={`${item.type}-${item.value}-${idx}`}
                  type="button"
                  onClick={() => handleSelectSuggestion(item)}
                  className="flex items-center justify-between w-full px-3.5 py-2 text-left hover:bg-slate-800/80 transition-colors group"
                >
                  <div className="flex items-center gap-2">
                    <IconComp className="w-3.5 h-3.5 text-sky-400" />
                    <span className="text-xs font-medium text-slate-200 group-hover:text-white">
                      {item.label}
                    </span>
                    <span
                      className={`text-[10px] px-1.5 py-0.5 rounded border ${colorClass}`}
                    >
                      {item.category}
                    </span>
                  </div>
                  <span className="text-[10px] text-slate-400 bg-slate-800 px-1.5 py-0.5 rounded">
                    + Add Filter
                  </span>
                </button>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
