import React, { useState, useEffect, useRef } from "react";
import { Search, X, Building, Stethoscope, Zap, Briefcase, Home, Loader2 } from "lucide-react";
import { parseSearchQuery } from "../../services/api";

const TYPE_ICONS = {
  company: Building,
  industry: Stethoscope,
  skill: Zap,
  seniority: Briefcase,
  modality: Home,
};

const TYPE_COLORS = {
  company: "bg-blue-500/10 text-blue-400 border-blue-500/20",
  industry: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
  skill: "bg-purple-500/10 text-purple-400 border-purple-500/20",
  seniority: "bg-amber-500/10 text-amber-400 border-amber-500/20",
  modality: "bg-sky-500/10 text-sky-400 border-sky-500/20",
};

export function TokenizedOmnibar({
  rawQuery,
  onQueryChange,
  chips,
  onAddChip,
  onRemoveChip,
  onClearAll,
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
          items.push({ type: "company", value: c, label: `Company: ${c.charAt(0).toUpperCase() + c.slice(1)}` });
        });
        (parsed.target_industries || []).forEach((ind) => {
          items.push({ type: "industry", value: ind, label: `Vertical: ${ind.charAt(0).toUpperCase() + ind.slice(1)}` });
        });
        (parsed.seniority_levels || []).forEach((sen) => {
          items.push({ type: "seniority", value: sen, label: `Level: ${sen.charAt(0).toUpperCase() + sen.slice(1)}` });
        });
        (parsed.must_have_skills || []).forEach((s) => {
          items.push({ type: "skill", value: s, label: `Skill: ${s}` });
        });
        if (parsed.workplace_modality) {
          items.push({
            type: "modality",
            value: parsed.workplace_modality,
            label: `Modality: ${parsed.workplace_modality.charAt(0).toUpperCase() + parsed.workplace_modality.slice(1)}`,
          });
        }

        // Filter out already active chips
        const activeVals = new Set(chips.map((c) => `${c.type}:${c.value.toLowerCase()}`));
        const filtered = items.filter((item) => !activeVals.has(`${item.type}:${item.value.toLowerCase()}`));

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
    if (e.key === "Backspace" && !inputValue && chips.length > 0) {
      // Remove rightmost chip
      const lastChip = chips[chips.length - 1];
      onRemoveChip(lastChip.id);
    } else if (e.key === "Enter") {
      e.preventDefault();
      if (suggestions.length > 0) {
        // Convert top suggestion into chip
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
    onAddChip(suggestion);
    // Remove the recognized entity token from text input
    const cleaned = inputValue
      .replace(new RegExp(`\\b${suggestion.value}\\b`, "gi"), "")
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
        className="flex flex-wrap items-center gap-1.5 w-full min-h-[46px] px-3.5 py-1.5 bg-neutral-900/90 border border-neutral-700/80 rounded-xl shadow-inner focus-within:border-cyan-500/80 focus-within:ring-2 focus-within:ring-cyan-500/20 transition-all cursor-text"
        onClick={() => inputRef.current && inputRef.current.focus()}
      >
        <Search className="w-4 h-4 text-neutral-400 mr-1 shrink-0" />

        {/* Tokenized Entity Chips */}
        {chips.map((chip) => {
          const IconComponent = TYPE_ICONS[chip.type] || Zap;
          const colorClass = TYPE_COLORS[chip.type] || "bg-neutral-800 text-neutral-300 border-neutral-700";

          return (
            <span
              key={chip.id}
              className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-md text-xs font-medium border ${colorClass} transition-all animate-fadeIn`}
            >
              <IconComponent className="w-3 h-3 shrink-0" />
              <span>{chip.label || chip.value}</span>
              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation();
                  onRemoveChip(chip.id);
                }}
                className="hover:text-white p-0.5 rounded transition-colors"
                aria-label={`Remove ${chip.label}`}
              >
                <X className="w-3 h-3" />
              </button>
            </span>
          );
        })}

        {/* Free Text Input */}
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
          placeholder={
            chips.length === 0
              ? "Type company, skills, vertical (e.g. 'Stripe HealthTech Kubernetes')..."
              : "Search query..."
          }
          aria-label="Search company, job title, or keywords"
          data-testid="matches-search-input"
          className="flex-1 min-w-[140px] bg-transparent text-sm text-neutral-100 placeholder-neutral-500 focus:outline-none"
        />

        {/* Action Controls */}
        <div className="flex items-center gap-1 ml-auto shrink-0">
          {isLoadingSuggestions && (
            <Loader2 className="w-3.5 h-3.5 text-neutral-400 animate-spin mr-1" />
          )}

          {(chips.length > 0 || inputValue) && (
            <button
              type="button"
              onClick={(e) => {
                e.stopPropagation();
                setInputValue("");
                onClearAll();
              }}
              className="p-1 text-neutral-400 hover:text-neutral-200 rounded-md transition-colors"
              title="Clear search and all active chips"
              aria-label="Clear omnibar"
            >
              <X className="w-4 h-4" />
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
            className="px-3 py-1 bg-cyan-600 hover:bg-cyan-500 disabled:opacity-50 text-white text-xs font-semibold rounded-lg shadow-sm transition-colors"
          >
            {isSearching ? "Searching..." : "Search"}
          </button>
        </div>
      </div>

      {/* Autocomplete Suggestions Dropdown */}
      {showDropdown && suggestions.length > 0 && (
        <div className="absolute left-0 right-0 top-full mt-1.5 z-50 bg-neutral-900 border border-neutral-700/90 rounded-xl shadow-2xl overflow-hidden py-1">
          <div className="px-3 py-1.5 text-[10px] font-semibold tracking-wider text-neutral-400 uppercase border-b border-neutral-800">
            Detected Facet Tokens — Press Enter to Add
          </div>
          <div className="max-h-60 overflow-y-auto">
            {suggestions.map((item, idx) => {
              const IconComp = TYPE_ICONS[item.type] || Zap;
              const colorClass = TYPE_COLORS[item.type] || "text-neutral-300";

              return (
                <button
                  key={`${item.type}-${item.value}-${idx}`}
                  type="button"
                  onClick={() => handleSelectSuggestion(item)}
                  className="flex items-center justify-between w-full px-3.5 py-2 text-left hover:bg-neutral-800/80 transition-colors group"
                >
                  <div className="flex items-center gap-2">
                    <IconComp className={`w-3.5 h-3.5 ${colorClass}`} />
                    <span className="text-xs font-medium text-neutral-200 group-hover:text-white">
                      {item.label}
                    </span>
                  </div>
                  <span className="text-[10px] text-neutral-400 bg-neutral-800 px-1.5 py-0.5 rounded">
                    + Add Chip
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