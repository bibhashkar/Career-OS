import { useState, useEffect, useCallback, useRef } from "react";
import { useSearchParams } from "react-router-dom";

export function useSearchSync() {
  const [searchParams, setSearchParams] = useSearchParams();

  // Helper to parse initial chips from URL or query
  const getInitialState = () => {
    const mode = searchParams.get("search_mode") || "cv_grounded";
    const auth = searchParams.get("work_auth_tier") || "all";
    const mod = searchParams.get("modality") || "all";
    const sort = searchParams.get("sort_by") || "score";
    const sal = searchParams.get("min_salary") ? Number(searchParams.get("min_salary")) : null;
    const commute = searchParams.get("max_commute") ? Number(searchParams.get("max_commute")) : null;
    const q = searchParams.get("q") || "";

    // Parse any serialized chips in URL
    let initialChips = [];
    const chipsParam = searchParams.get("chips");
    if (chipsParam) {
      try {
        initialChips = JSON.parse(decodeURIComponent(chipsParam));
      } catch {
        initialChips = [];
      }
    }

    return {
      searchMode: mode,
      workAuthTier: auth,
      workplaceModality: mod,
      sortBy: sort,
      minBaseSalary: sal,
      maxCommuteMiles: commute,
      rawQuery: q,
      chips: initialChips,
    };
  };

  const initial = getInitialState();
  const [searchMode, setSearchMode] = useState(initial.searchMode);
  const [workAuthTier, setWorkAuthTier] = useState(initial.workAuthTier);
  const [workplaceModality, setWorkplaceModality] = useState(initial.workplaceModality);
  const [sortBy, setSortBy] = useState(initial.sortBy);
  const [minBaseSalary, setMinBaseSalary] = useState(initial.minBaseSalary);
  const [maxCommuteMiles, setMaxCommuteMiles] = useState(initial.maxCommuteMiles);
  const [rawQuery, setRawQuery] = useState(initial.rawQuery);
  const [chips, setChips] = useState(initial.chips);
  const [diagnostics, setDiagnostics] = useState(null);

  // Debounced URL Search Params Sync
  const isInitialMount = useRef(true);
  useEffect(() => {
    if (isInitialMount.current) {
      isInitialMount.current = false;
      return;
    }

    const timer = setTimeout(() => {
      const nextParams = new URLSearchParams();

      if (searchMode !== "cv_grounded") nextParams.set("search_mode", searchMode);
      if (workAuthTier !== "all") nextParams.set("work_auth_tier", workAuthTier);
      if (workplaceModality !== "all") nextParams.set("modality", workplaceModality);
      if (sortBy !== "score") nextParams.set("sort_by", sortBy);
      if (minBaseSalary !== null) nextParams.set("min_salary", String(minBaseSalary));
      if (maxCommuteMiles !== null) nextParams.set("max_commute", String(maxCommuteMiles));
      if (rawQuery.trim()) nextParams.set("q", rawQuery.trim());
      if (chips.length > 0) nextParams.set("chips", encodeURIComponent(JSON.stringify(chips)));

      setSearchParams(nextParams, { replace: true });
    }, 300);

    return () => clearTimeout(timer);
  }, [
    searchMode,
    workAuthTier,
    workplaceModality,
    sortBy,
    minBaseSalary,
    maxCommuteMiles,
    rawQuery,
    chips,
    setSearchParams,
  ]);

  const addChip = useCallback((chip) => {
    setChips((prev) => {
      // Prevent duplicates with same type and value
      if (prev.some((c) => c.type === chip.type && c.value.toLowerCase() === chip.value.toLowerCase())) {
        return prev;
      }
      return [...prev, { ...chip, id: chip.id || `${chip.type}-${Date.now()}-${Math.random()}` }];
    });
  }, []);

  const removeChip = useCallback((chipId) => {
    setChips((prev) => prev.filter((c) => c.id !== chipId));
  }, []);

  const clearAllFilters = useCallback(() => {
    setSearchMode("cv_grounded");
    setWorkAuthTier("all");
    setWorkplaceModality("all");
    setSortBy("score");
    setMinBaseSalary(null);
    setMaxCommuteMiles(null);
    setRawQuery("");
    setChips([]);
    setDiagnostics(null);
  }, []);

  const applyRelaxation = useCallback((relaxedPatch) => {
    if (!relaxedPatch) return;

    if ("work_auth_tier" in relaxedPatch) {
      setWorkAuthTier(relaxedPatch.work_auth_tier);
    }
    if ("max_commute_miles" in relaxedPatch) {
      setMaxCommuteMiles(relaxedPatch.max_commute_miles);
    }
    if ("min_base_salary_usd" in relaxedPatch) {
      setMinBaseSalary(relaxedPatch.min_base_salary_usd);
    }
    if ("workplace_modality" in relaxedPatch) {
      setWorkplaceModality(relaxedPatch.workplace_modality);
    }
    if ("must_have_skills" in relaxedPatch) {
      setChips((prev) => prev.filter((c) => c.type !== "skill"));
    }
    if ("companies" in relaxedPatch) {
      setChips((prev) => prev.filter((c) => c.type !== "company"));
    }
    if ("raw_query" in relaxedPatch) {
      setRawQuery("");
    }
    setDiagnostics(null);
  }, []);

  return {
    searchMode,
    setSearchMode,
    workAuthTier,
    setWorkAuthTier,
    workplaceModality,
    setWorkplaceModality,
    sortBy,
    setSortBy,
    minBaseSalary,
    setMinBaseSalary,
    maxCommuteMiles,
    setMaxCommuteMiles,
    rawQuery,
    setRawQuery,
    chips,
    addChip,
    removeChip,
    clearAllFilters,
    diagnostics,
    setDiagnostics,
    applyRelaxation,
  };
}

