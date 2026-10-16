import React, { useState, useEffect, useCallback } from "react";
import {
  X,
  Globe,
  Sparkles,
  Lock,
  Edit2,
  Trash2,
  Check,
  Plus,
  AlertCircle,
  Loader2,
  Briefcase,
  Calendar,
  Layers,
  ArrowLeft,
} from "lucide-react";
import {
  getCandidatePersonas,
  updateCandidatePersona,
  deleteCandidatePersona,
  setDefaultPersona,
  createCandidatePersona,
} from "../services/api";

export function PersonaManagementModal({
  isOpen,
  onClose,
  activePersonaId,
  onPersonaSelect,
  onPersonasChanged,
}) {
  const [personas, setPersonas] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Editing state: persona object being edited, or null
  const [editingPersona, setEditingPersona] = useState(null);
  const [editForm, setEditForm] = useState({
    name: "",
    headline: "",
    target_roles: "",
    target_industries: "",
    seniority_level: "mid",
    years_experience: 0,
    min_salary: "",
    skills: "",
  });
  const [saveLoading, setSaveLoading] = useState(false);
  const [saveError, setSaveError] = useState(null);

  // Creating new specialized persona state
  const [isCreating, setIsCreating] = useState(false);
  const [createForm, setCreateForm] = useState({
    name: "",
    headline: "",
    target_roles: "",
    target_industries: "",
    seniority_level: "mid",
    years_experience: 3,
    skills: "",
  });
  const [createLoading, setCreateLoading] = useState(false);
  const [createError, setCreateError] = useState(null);

  const isModifying = Boolean(editingPersona || isCreating);

  const handleBackToList = () => {
    setEditingPersona(null);
    setIsCreating(false);
    setSaveError(null);
    setCreateError(null);
  };

  const loadPersonas = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await getCandidatePersonas();
      setPersonas(data || []);
      if (onPersonasChanged) onPersonasChanged(data || []);
    } catch (err) {
      console.error("Failed to load personas:", err);
      setError("Unable to load candidate personas. Please try again.");
    } finally {
      setLoading(false);
    }
  }, [onPersonasChanged]);

  useEffect(() => {
    if (isOpen) {
      loadPersonas();
      setEditingPersona(null);
      setIsCreating(false);
      setError(null);
      setSaveError(null);
      setCreateError(null);
    }
  }, [isOpen, loadPersonas]);

  function startEditing(p) {
    setEditingPersona(p);
    setIsCreating(false);
    setSaveError(null);
    setEditForm({
      name: p.name || "",
      headline: p.headline || "",
      target_roles: Array.isArray(p.target_roles) ? p.target_roles.join(", ") : "",
      target_industries: Array.isArray(p.target_industries)
        ? p.target_industries.join(", ")
        : "",
      seniority_level: p.seniority_level || "mid",
      years_experience: p.years_experience || 0,
      min_salary: p.min_salary || "",
      skills: "",
    });
  }

  async function handleSaveEdit(e) {
    e.preventDefault();
    if (!editingPersona) return;

    setSaveLoading(true);
    setSaveError(null);

    const rolesList = editForm.target_roles
      .split(",")
      .map((r) => r.trim())
      .filter(Boolean);

    const industriesList = editForm.target_industries
      .split(",")
      .map((i) => i.trim())
      .filter(Boolean);

    const skillsList = editForm.skills
      .split(",")
      .map((s) => s.trim())
      .filter(Boolean);

    const payload = {
      name: editingPersona.is_common_persona
        ? editingPersona.name
        : editForm.name.trim(),
      headline: editForm.headline.trim() || null,
      target_roles: rolesList,
      target_industries: industriesList,
      seniority_level: editForm.seniority_level,
      years_experience: Number(editForm.years_experience) || 0,
      min_salary: editForm.min_salary ? Number(editForm.min_salary) : null,
      skills: skillsList,
    };

    try {
      const updated = await updateCandidatePersona(editingPersona.id, payload);
      setEditingPersona(null);
      await loadPersonas();
      if (onPersonaSelect && updated.id === activePersonaId) {
        onPersonaSelect(updated);
      }
    } catch (err) {
      console.error("Failed to update persona:", err);
      const msg =
        err.response?.data?.detail || "Failed to update persona. Please try again.";
      setSaveError(msg);
    } finally {
      setSaveLoading(false);
    }
  }

  async function handleCreatePersona(e) {
    e.preventDefault();
    setCreateLoading(true);
    setCreateError(null);

    const cleanName = createForm.name.trim();
    if (!cleanName) {
      setCreateError("Persona name is required.");
      setCreateLoading(false);
      return;
    }

    const rolesList = createForm.target_roles
      .split(",")
      .map((r) => r.trim())
      .filter(Boolean);

    const industriesList = createForm.target_industries
      .split(",")
      .map((i) => i.trim())
      .filter(Boolean);

    const skillsList = createForm.skills
      .split(",")
      .map((s) => s.trim())
      .filter(Boolean);

    const payload = {
      name: cleanName,
      headline: createForm.headline.trim() || null,
      target_roles: rolesList,
      target_industries: industriesList,
      seniority_level: createForm.seniority_level,
      years_experience: Number(createForm.years_experience) || 0,
      skills: skillsList,
    };

    try {
      const created = await createCandidatePersona(payload);
      setIsCreating(false);
      setCreateForm({
        name: "",
        headline: "",
        target_roles: "",
        target_industries: "",
        seniority_level: "mid",
        years_experience: 3,
        skills: "",
      });
      await loadPersonas();
      if (onPersonaSelect) onPersonaSelect(created);
    } catch (err) {
      console.error("Failed to create persona:", err);
      const msg =
        err.response?.data?.detail || "Failed to create persona. Please try again.";
      setCreateError(msg);
    } finally {
      setCreateLoading(false);
    }
  }

  async function handleSetDefault(p) {
    try {
      await setDefaultPersona(p.id);
      await loadPersonas();
      if (onPersonaSelect) onPersonaSelect(p);
    } catch (err) {
      console.error("Failed to set default persona:", err);
    }
  }

  async function handleDelete(p) {
    if (p.is_common_persona) return;
    const confirmMsg = `Are you sure you want to delete the specialized persona "${p.name}"? This action cannot be undone.`;
    if (!window.confirm(confirmMsg)) return;

    try {
      await deleteCandidatePersona(p.id);
      await loadPersonas();
    } catch (err) {
      console.error("Failed to delete persona:", err);
      const msg =
        err.response?.data?.detail || "Failed to delete persona. Please try again.";
      if (typeof window !== "undefined" && window.alert) {
        window.alert(msg);
      }
    }
  }

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-in fade-in duration-150"
      data-testid="persona-management-modal"
    >
      <div className="relative w-full max-w-2xl bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="flex items-center justify-between p-5 border-b border-slate-800 bg-slate-900/60 shrink-0">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-xl bg-gradient-to-tr from-sky-500/20 to-indigo-500/20 text-sky-400 border border-sky-500/30">
              <Layers className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-base font-bold text-white flex items-center gap-2">
                Candidate Career Personas
                <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-slate-800 text-slate-300 border border-slate-700">
                  {personas.length} {personas.length === 1 ? "Persona" : "Personas"}
                </span>
              </h2>
              <p className="text-xs text-slate-400">
                {editingPersona
                  ? `Editing: ${editingPersona.name}`
                  : isCreating
                  ? "Define a new specialized career track"
                  : "Manage your Universal Profile baseline and specialized target career tracks"}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            data-testid="close-persona-modal-btn"
            className="p-1.5 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800 transition-colors cursor-pointer"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Content Body */}
        <div className="overflow-y-auto p-5 space-y-4 flex-1">
          {error && (
            <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs flex items-center gap-2">
              <AlertCircle className="w-4 h-4 shrink-0 text-rose-400" />
              <span>{error}</span>
            </div>
          )}

          {/* Form: Edit Persona */}
          {editingPersona && (
            <div
              className="p-4 rounded-xl bg-slate-950/80 border border-sky-500/30 space-y-3.5 shadow-lg"
              data-testid="edit-persona-form"
            >
              <div className="flex items-center justify-between border-b border-slate-800 pb-2.5">
                <div className="flex items-center gap-2">
                  <Edit2 className="w-4 h-4 text-sky-400" />
                  <span className="text-xs font-bold text-white">
                    {editingPersona.is_common_persona
                      ? "Edit Universal Profile Settings"
                      : `Edit & Rename: ${editingPersona.name}`}
                  </span>
                </div>
                <button
                  type="button"
                  onClick={handleBackToList}
                  className="text-xs text-slate-400 hover:text-slate-200 cursor-pointer"
                >
                  Cancel
                </button>
              </div>

              {saveError && (
                <div
                  className="p-2.5 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs flex items-start gap-2"
                  data-testid="edit-persona-error"
                >
                  <AlertCircle className="w-4 h-4 shrink-0 mt-0.5 text-rose-400" />
                  <span>{saveError}</span>
                </div>
              )}

              <form onSubmit={handleSaveEdit} className="space-y-3">
                <div>
                  <div className="flex items-center justify-between mb-1">
                    <label className="text-xs font-medium text-slate-300">
                      Persona Name
                    </label>
                    {editingPersona.is_common_persona && (
                      <span className="flex items-center gap-1 text-[10px] text-amber-400 font-medium">
                        <Lock className="w-3 h-3" /> System Locked Name
                      </span>
                    )}
                  </div>
                  <input
                    type="text"
                    required
                    data-testid="edit-persona-name-input"
                    disabled={editingPersona.is_common_persona}
                    value={
                      editingPersona.is_common_persona
                        ? editingPersona.name
                        : editForm.name
                    }
                    onChange={(e) =>
                      setEditForm({ ...editForm, name: e.target.value })
                    }
                    placeholder="e.g. AI Platform Engineer"
                    className={`w-full px-3 py-2 bg-slate-900 border rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none ${
                      editingPersona.is_common_persona
                        ? "border-slate-800 opacity-70 cursor-not-allowed"
                        : "border-slate-700 focus:border-sky-500"
                    }`}
                  />
                  {editingPersona.is_common_persona && (
                    <p className="text-[10px] text-slate-500 mt-1">
                      The Universal Profile is your primary cross-functional baseline and
                      its title is managed by the system.
                    </p>
                  )}
                </div>

                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">
                    Headline
                  </label>
                  <input
                    type="text"
                    data-testid="edit-persona-headline-input"
                    value={editForm.headline}
                    onChange={(e) =>
                      setEditForm({ ...editForm, headline: e.target.value })
                    }
                    placeholder="e.g. Distributed Model Serving & Large-Scale Inference"
                    className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none focus:border-sky-500"
                  />
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-medium text-slate-300 mb-1">
                      Seniority Level
                    </label>
                    <select
                      value={editForm.seniority_level}
                      onChange={(e) =>
                        setEditForm({ ...editForm, seniority_level: e.target.value })
                      }
                      className="w-full px-2.5 py-2 bg-slate-900 border border-slate-700 rounded-xl text-xs text-white focus:outline-none focus:border-sky-500"
                    >
                      <option value="junior">Junior</option>
                      <option value="mid">Mid-Level</option>
                      <option value="senior">Senior</option>
                      <option value="lead">Lead</option>
                      <option value="principal">Principal</option>
                      <option value="executive">Executive</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-xs font-medium text-slate-300 mb-1">
                      Years Experience
                    </label>
                    <input
                      type="number"
                      min={0}
                      max={50}
                      value={editForm.years_experience}
                      onChange={(e) =>
                        setEditForm({
                          ...editForm,
                          years_experience: Number(e.target.value),
                        })
                      }
                      className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-xl text-xs text-white focus:outline-none focus:border-sky-500"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">
                    Target Job Roles (comma-separated)
                  </label>
                  <input
                    type="text"
                    value={editForm.target_roles}
                    onChange={(e) =>
                      setEditForm({ ...editForm, target_roles: e.target.value })
                    }
                    placeholder="e.g. AI Platform Engineer, MLOps Engineer"
                    className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none focus:border-sky-500"
                  />
                </div>

                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">
                    Add Core Skills (comma-separated)
                  </label>
                  <input
                    type="text"
                    value={editForm.skills}
                    onChange={(e) =>
                      setEditForm({ ...editForm, skills: e.target.value })
                    }
                    placeholder="e.g. PyTorch, vLLM, Triton"
                    className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none focus:border-sky-500"
                  />
                </div>

                <div className="flex items-center justify-end gap-2 pt-1">
                  <button
                    type="button"
                    onClick={handleBackToList}
                    className="px-3 py-1.5 rounded-lg border border-slate-700 hover:bg-slate-800 text-slate-300 text-xs font-medium cursor-pointer"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    data-testid="save-persona-btn"
                    disabled={saveLoading}
                    className="px-4 py-1.5 rounded-lg bg-sky-600 hover:bg-sky-500 text-white text-xs font-semibold shadow-md shadow-sky-500/20 disabled:opacity-50 flex items-center gap-1.5 cursor-pointer"
                  >
                    {saveLoading && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
                    <span>Save Changes</span>
                  </button>
                </div>
              </form>
            </div>
          )}

          {/* Form: Create Specialized Persona */}
          {isCreating && (
            <div
              className="p-4 rounded-xl bg-slate-950/80 border border-indigo-500/30 space-y-3.5 shadow-lg"
              data-testid="create-persona-form"
            >
              <div className="flex items-center justify-between border-b border-slate-800 pb-2.5">
                <div className="flex items-center gap-2">
                  <Sparkles className="w-4 h-4 text-indigo-400" />
                  <span className="text-xs font-bold text-white">
                    Create Specialized Career Persona
                  </span>
                </div>
                <button
                  type="button"
                  onClick={handleBackToList}
                  className="text-xs text-slate-400 hover:text-slate-200 cursor-pointer"
                >
                  Cancel
                </button>
              </div>

              {createError && (
                <div
                  className="p-2.5 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs flex items-start gap-2"
                  data-testid="create-persona-error"
                >
                  <AlertCircle className="w-4 h-4 shrink-0 mt-0.5 text-rose-400" />
                  <span>{createError}</span>
                </div>
              )}

              <form onSubmit={handleCreatePersona} className="space-y-3">
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">
                    Persona Name (must be unique)
                  </label>
                  <input
                    type="text"
                    required
                    data-testid="create-persona-name-input"
                    value={createForm.name}
                    onChange={(e) =>
                      setCreateForm({ ...createForm, name: e.target.value })
                    }
                    placeholder="e.g. AI Platform Engineer"
                    className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500"
                  />
                </div>

                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">
                    Headline
                  </label>
                  <input
                    type="text"
                    value={createForm.headline}
                    onChange={(e) =>
                      setCreateForm({ ...createForm, headline: e.target.value })
                    }
                    placeholder="e.g. Distributed Model Serving & Large-Scale Inference"
                    className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500"
                  />
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-medium text-slate-300 mb-1">
                      Seniority Level
                    </label>
                    <select
                      value={createForm.seniority_level}
                      onChange={(e) =>
                        setCreateForm({
                          ...createForm,
                          seniority_level: e.target.value,
                        })
                      }
                      className="w-full px-2.5 py-2 bg-slate-900 border border-slate-700 rounded-xl text-xs text-white focus:outline-none focus:border-indigo-500"
                    >
                      <option value="junior">Junior</option>
                      <option value="mid">Mid-Level</option>
                      <option value="senior">Senior</option>
                      <option value="lead">Lead</option>
                      <option value="principal">Principal</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-xs font-medium text-slate-300 mb-1">
                      Years Experience
                    </label>
                    <input
                      type="number"
                      min={0}
                      max={50}
                      value={createForm.years_experience}
                      onChange={(e) =>
                        setCreateForm({
                          ...createForm,
                          years_experience: Number(e.target.value),
                        })
                      }
                      className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-xl text-xs text-white focus:outline-none focus:border-indigo-500"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">
                    Target Roles (comma-separated)
                  </label>
                  <input
                    type="text"
                    value={createForm.target_roles}
                    onChange={(e) =>
                      setCreateForm({ ...createForm, target_roles: e.target.value })
                    }
                    placeholder="e.g. AI Platform Engineer, MLOps Engineer"
                    className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500"
                  />
                </div>

                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">
                    Core Skills (comma-separated)
                  </label>
                  <input
                    type="text"
                    value={createForm.skills}
                    onChange={(e) =>
                      setCreateForm({ ...createForm, skills: e.target.value })
                    }
                    placeholder="e.g. PyTorch, vLLM, Ray"
                    className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500"
                  />
                </div>

                <div className="flex items-center justify-end gap-2 pt-1">
                  <button
                    type="button"
                    onClick={handleBackToList}
                    className="px-3 py-1.5 rounded-lg border border-slate-700 hover:bg-slate-800 text-slate-300 text-xs font-medium cursor-pointer"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    data-testid="submit-create-persona-btn"
                    disabled={createLoading}
                    className="px-4 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-md shadow-indigo-500/20 disabled:opacity-50 flex items-center gap-1.5 cursor-pointer"
                  >
                    {createLoading && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
                    <span>Create Persona</span>
                  </button>
                </div>
              </form>
            </div>
          )}

          {/* Persona List (Hidden when actively modifying or creating a persona) */}
          {!isModifying && (
            loading ? (
              <div className="py-12 flex flex-col items-center justify-center gap-2 text-slate-400">
                <Loader2 className="w-6 h-6 animate-spin text-sky-400" />
                <p className="text-xs">Loading personas...</p>
              </div>
            ) : (
              <div className="space-y-3" data-testid="persona-list">
                {personas.map((p) => {
                  const isActive = p.id === activePersonaId;
                  return (
                    <div
                      key={p.id}
                      data-testid={`persona-card-${p.id}`}
                      className={`p-4 rounded-xl border transition-all ${
                        p.is_default
                          ? "bg-slate-800/80 border-sky-500/40 shadow-sm"
                          : "bg-slate-800/40 border-slate-800 hover:border-slate-700"
                      }`}
                    >
                      <div className="flex items-start justify-between gap-3">
                        <div className="flex items-start gap-3">
                          <div className="mt-1 p-2 rounded-xl bg-slate-900 border border-slate-700/80 text-sky-400">
                            {p.is_common_persona ? (
                              <Globe className="w-4 h-4 text-sky-400" />
                            ) : (
                              <Sparkles className="w-4 h-4 text-indigo-400" />
                            )}
                          </div>

                          <div>
                            <div className="flex items-center gap-2 flex-wrap">
                              <h3 className="text-sm font-bold text-white">
                                {p.name}
                              </h3>
                              {p.is_common_persona && (
                                <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-sky-500/10 text-sky-400 border border-sky-500/20">
                                  Universal Baseline
                                </span>
                              )}
                              {p.is_default && (
                                <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 flex items-center gap-1">
                                  <Check className="w-2.5 h-2.5" /> Default Lens
                                </span>
                              )}
                              {isActive && !p.is_default && (
                                <span className="text-[10px] font-medium px-2 py-0.5 rounded-full bg-slate-700 text-slate-300">
                                  Currently Active
                                </span>
                              )}
                            </div>

                            <p className="text-xs text-slate-300 mt-1">
                              {p.headline || "No headline configured"}
                            </p>

                            <div className="flex items-center gap-3 mt-2 text-[11px] text-slate-400 flex-wrap">
                              <span className="flex items-center gap-1">
                                <Briefcase className="w-3 h-3 text-slate-500" />
                                <span className="capitalize">{p.seniority_level}</span>
                              </span>
                              <span>•</span>
                              <span className="flex items-center gap-1">
                                <Calendar className="w-3 h-3 text-slate-500" />
                                <span>{p.years_experience}y experience</span>
                              </span>
                              <span>•</span>
                              <span>{p.skill_count} skills</span>
                              <span>•</span>
                              <span>{p.block_count} achievement blocks</span>
                            </div>

                            {p.target_roles?.length > 0 && (
                              <div className="flex items-center gap-1.5 mt-2 flex-wrap">
                                {p.target_roles.map((role, idx) => (
                                  <span
                                    key={idx}
                                    className="text-[10px] px-2 py-0.5 rounded bg-slate-900 border border-slate-700/60 text-slate-300"
                                  >
                                    {role}
                                  </span>
                                ))}
                              </div>
                            )}
                          </div>
                        </div>

                        {/* Card Action Controls */}
                        <div className="flex items-center gap-1.5 shrink-0">
                          <button
                            type="button"
                            onClick={() => startEditing(p)}
                            data-testid={`edit-persona-btn-${p.id}`}
                            title="Edit settings"
                            className="px-2.5 py-1.5 rounded-lg border border-slate-700 hover:bg-slate-700 text-slate-200 text-xs font-medium flex items-center gap-1.5 transition-colors cursor-pointer"
                          >
                            <Edit2 className="w-3.5 h-3.5" />
                            <span>Edit</span>
                          </button>

                          {!p.is_default && (
                            <button
                              type="button"
                              onClick={() => handleSetDefault(p)}
                              data-testid={`set-default-btn-${p.id}`}
                              title="Set as login default"
                              className="px-2.5 py-1.5 rounded-lg bg-slate-900 hover:bg-slate-700 text-slate-300 text-xs font-medium border border-slate-700 transition-colors cursor-pointer"
                            >
                              Set Default
                            </button>
                          )}

                          {!p.is_common_persona && (
                            <button
                              type="button"
                              onClick={() => handleDelete(p)}
                              data-testid={`delete-persona-btn-${p.id}`}
                              title="Delete persona"
                              className="p-1.5 rounded-lg hover:bg-rose-500/20 text-slate-400 hover:text-rose-400 transition-colors cursor-pointer"
                            >
                              <Trash2 className="w-3.5 h-3.5" />
                            </button>
                          )}
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            )
          )}
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-slate-800 bg-slate-900/60 flex items-center justify-between shrink-0">
          {isModifying ? (
            <button
              type="button"
              onClick={handleBackToList}
              data-testid="back-to-persona-list-btn"
              className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl border border-slate-700 hover:bg-slate-800 text-slate-300 hover:text-white text-xs font-medium transition-colors cursor-pointer"
            >
              <ArrowLeft className="w-3.5 h-3.5" />
              <span>Back to Persona List</span>
            </button>
          ) : (
            <>
              <button
                type="button"
                onClick={() => {
                  setIsCreating(true);
                  setEditingPersona(null);
                }}
                data-testid="add-persona-btn"
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-sm transition-all cursor-pointer"
              >
                <Plus className="w-3.5 h-3.5" />
                <span>Add Specialized Persona</span>
              </button>

              <button
                type="button"
                onClick={onClose}
                className="px-4 py-1.5 rounded-xl border border-slate-700 hover:bg-slate-800 text-slate-300 text-xs font-medium transition-colors cursor-pointer"
              >
                Done
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

export default PersonaManagementModal;

