import React, { useState } from "react";
import {
  FolderGit2,
  Plus,
  ExternalLink,
  Github,
  Edit2,
  Trash2,
  CheckCircle,
  AlertCircle,
  X,
} from "lucide-react";

export function ProjectsInitiativesSection({
  projects = [],
  archetype = "technology_engineering",
  onSaveProject,
  onDeleteProject,
}) {
  const [isAdding, setIsAdding] = useState(false);
  const [editingIndex, setEditingIndex] = useState(null);

  const [form, setForm] = useState({
    name: "",
    role: "",
    repository_url: "",
    live_url: "",
    technologies: [],
    description: "",
  });
  const [techInput, setTechInput] = useState("");
  const [error, setError] = useState(null);

  const sectionTitles = {
    technology_engineering: "6A. Technical Projects & Open Source",
    executive_leadership: "6A. Strategic Mandates, Deals & Capital Initiatives",
    marketing_growth: "6A. Flagship Campaigns, Launches & Case Studies",
    product_strategy: "6A. Product Initiatives & Strategic Case Studies",
    finance_fintech: "6A. Financial Initiatives, Deals & Core Systems",
    healthcare_lifesciences: "6A. Clinical Programs, Trials & Initiatives",
    custom_hybrid: "6A. Key Projects, Initiatives & Case Studies",
  };

  const namePlaceholders = {
    technology_engineering: "e.g. Distributed Ledger Engine or OpenTelemetry SDK",
    executive_leadership: "e.g. $45M Series B Fundraising or European Market Expansion",
    marketing_growth: "e.g. Enterprise Rebrand & Demand Gen Engine (3.5x ROAS)",
    product_strategy: "e.g. Multi-Tenant Enterprise Workspace Redesign",
    finance_fintech: "e.g. Automated Multi-State Clearing & Reconciliation Engine",
    healthcare_lifesciences: "e.g. Multi-Site Clinical EHR Interoperability Pipeline",
    custom_hybrid: "e.g. Enterprise Transformation Initiative",
  };

  function openAdd() {
    setForm({
      name: "",
      role: "",
      repository_url: "",
      live_url: "",
      technologies: [],
      description: "",
    });
    setTechInput("");
    setError(null);
    setEditingIndex(null);
    setIsAdding(true);
  }

  function openEdit(idx) {
    const prj = projects[idx];
    setForm({
      name: prj.name || "",
      role: prj.role || "",
      repository_url: prj.repository_url || "",
      live_url: prj.live_url || "",
      technologies: Array.isArray(prj.technologies) ? [...prj.technologies] : [],
      description: prj.description || "",
    });
    setTechInput("");
    setError(null);
    setEditingIndex(idx);
    setIsAdding(true);
  }

  function handleAddTech() {
    const clean = techInput.trim();
    if (clean && !form.technologies.some((t) => t.toLowerCase() === clean.toLowerCase())) {
      setForm({ ...form, technologies: [...form.technologies, clean] });
      setTechInput("");
    }
  }

  function handleRemoveTech(tag) {
    setForm({
      ...form,
      technologies: form.technologies.filter((t) => t.toLowerCase() !== tag.toLowerCase()),
    });
  }

  function handleSave(e) {
    e.preventDefault();
    if (!form.name.trim()) {
      setError("Project or initiative title is required.");
      return;
    }
    if (!form.description.trim()) {
      setError("A concise description of the initiative and its impact is required.");
      return;
    }

    let repoUrl = form.repository_url.trim();
    if (repoUrl && !repoUrl.startsWith("http://") && !repoUrl.startsWith("https://")) {
      repoUrl = `https://${repoUrl}`;
    }

    let liveUrl = form.live_url.trim();
    if (liveUrl && !liveUrl.startsWith("http://") && !liveUrl.startsWith("https://")) {
      liveUrl = `https://${liveUrl}`;
    }

    const payload = {
      ...form,
      name: form.name.trim(),
      role: form.role.trim() || null,
      repository_url: repoUrl || null,
      live_url: liveUrl || null,
      description: form.description.trim(),
    };

    onSaveProject(payload, editingIndex);
    setIsAdding(false);
    setEditingIndex(null);
  }

  const hasMetrics =
    form.description &&
    (/[0-9]/.test(form.description) ||
      form.description.includes("%") ||
      form.description.includes("$"));

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <FolderGit2 className="w-4 h-4 text-emerald-400" />
          <h4 className="text-xs font-bold text-white uppercase tracking-wider">
            {sectionTitles[archetype] || sectionTitles.technology_engineering} ({projects.length})
          </h4>
        </div>
        {!isAdding && (
          <button
            type="button"
            onClick={openAdd}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-emerald-950/80 hover:bg-emerald-900 border border-emerald-800/80 text-emerald-300 text-xs font-semibold cursor-pointer transition-colors"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>Add Initiative / Project</span>
          </button>
        )}
      </div>

      {/* Add / Edit Drawer */}
      {isAdding && (
        <form
          onSubmit={handleSave}
          className="p-4 rounded-xl bg-slate-950 border border-emerald-700/60 space-y-3.5 shadow-2xl"
        >
          <div className="flex items-center justify-between border-b border-slate-800 pb-2">
            <h5 className="text-xs font-bold text-white uppercase tracking-wide">
              {editingIndex !== null ? "Edit Initiative / Project" : "Add New Initiative / Project"}
            </h5>
            <button
              type="button"
              onClick={() => setIsAdding(false)}
              className="text-slate-400 hover:text-white"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          {error && (
            <div className="p-2.5 rounded-lg bg-rose-950/60 border border-rose-800 text-rose-200 text-xs flex items-center gap-2">
              <AlertCircle className="w-4 h-4 text-rose-400 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label className="block text-[11px] font-semibold text-slate-300 mb-1">
                Initiative / Project Title *
              </label>
              <input
                type="text"
                placeholder={namePlaceholders[archetype] || namePlaceholders.technology_engineering}
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                className="w-full px-3 py-1.5 bg-slate-900 border border-slate-700 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500"
              />
            </div>
            <div>
              <label className="block text-[11px] font-semibold text-slate-300 mb-1">
                Your Role / Scope
              </label>
              <input
                type="text"
                placeholder="e.g. Lead Architect, Co-Founder, GTM Lead"
                value={form.role}
                onChange={(e) => setForm({ ...form, role: e.target.value })}
                className="w-full px-3 py-1.5 bg-slate-900 border border-slate-700 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500"
              />
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label className="block text-[11px] font-semibold text-slate-300 mb-1">
                Source Repository / Reference Link
              </label>
              <input
                type="text"
                placeholder="https://github.com/... or documentation URL"
                value={form.repository_url}
                onChange={(e) => setForm({ ...form, repository_url: e.target.value })}
                className="w-full px-3 py-1.5 bg-slate-900 border border-slate-700 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500"
              />
            </div>
            <div>
              <label className="block text-[11px] font-semibold text-slate-300 mb-1">
                Live Deployment / Case Study Link
              </label>
              <input
                type="text"
                placeholder="https://app.example.com or case study URL"
                value={form.live_url}
                onChange={(e) => setForm({ ...form, live_url: e.target.value })}
                className="w-full px-3 py-1.5 bg-slate-900 border border-slate-700 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500"
              />
            </div>
          </div>

          {/* Technologies / Competencies tags */}
          <div>
            <label className="block text-[11px] font-semibold text-slate-300 mb-1">
              Technologies & Core Competencies Used
            </label>
            <div className="flex items-center gap-2 mb-2">
              <input
                type="text"
                placeholder="e.g. Rust, LangGraph, P&L, M&A, HubSpot"
                value={techInput}
                onChange={(e) => setTechInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") {
                    e.preventDefault();
                    handleAddTech();
                  }
                }}
                className="flex-1 px-3 py-1.5 bg-slate-900 border border-slate-700 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500"
              />
              <button
                type="button"
                onClick={handleAddTech}
                className="px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-white text-xs font-medium cursor-pointer"
              >
                Add Tag
              </button>
            </div>
            <div className="flex flex-wrap gap-1.5">
              {form.technologies.map((tech, tIdx) => (
                <span
                  key={tIdx}
                  className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-lg bg-emerald-950/60 border border-emerald-800/80 text-emerald-200 text-xs"
                >
                  <span>{tech}</span>
                  <button
                    type="button"
                    onClick={() => handleRemoveTech(tech)}
                    className="text-emerald-400 hover:text-white"
                  >
                    <X className="w-3 h-3" />
                  </button>
                </span>
              ))}
            </div>
          </div>

          {/* Description & Impact */}
          <div>
            <div className="flex items-center justify-between mb-1">
              <label className="block text-[11px] font-semibold text-slate-300">
                Architecture, Scope & Measurable Impact *
              </label>
              {hasMetrics ? (
                <span className="text-[10px] text-emerald-400 inline-flex items-center gap-1 font-medium">
                  <CheckCircle className="w-3 h-3" /> Quantified impact detected
                </span>
              ) : (
                <span className="text-[10px] text-amber-400/90 inline-flex items-center gap-1">
                  💡 Tip: Include metrics (%, $, throughput, team scale)
                </span>
              )}
            </div>
            <textarea
              rows={3}
              placeholder="Describe the problem, architectural or strategic solution, and verified business/system impact..."
              value={form.description}
              onChange={(e) => setForm({ ...form, description: e.target.value })}
              className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-xl text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-emerald-500 leading-relaxed"
            />
          </div>

          <div className="flex items-center justify-end gap-2 pt-2 border-t border-slate-800">
            <button
              type="button"
              onClick={() => setIsAdding(false)}
              className="px-3.5 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold cursor-pointer"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-4 py-1.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold cursor-pointer"
            >
              {editingIndex !== null ? "Save Changes" : "Save Initiative"}
            </button>
          </div>
        </form>
      )}

      {/* Project Cards List */}
      <div className="space-y-2.5">
        {projects.length > 0 ? (
          projects.map((prj, pIdx) => (
            <div
              key={pIdx}
              className="p-3.5 rounded-xl bg-slate-950/80 border border-slate-800/90 hover:border-slate-700 space-y-2 text-xs transition-all"
            >
              <div className="flex items-start justify-between gap-2">
                <div>
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="font-bold text-white text-sm">{prj.name}</span>
                    {prj.role && (
                      <span className="text-[10px] px-2 py-0.5 rounded-md bg-slate-900 text-slate-400 border border-slate-800 font-medium">
                        {prj.role}
                      </span>
                    )}
                  </div>
                  <div className="flex items-center gap-3 mt-1 text-[11px] text-slate-400">
                    {prj.repository_url && (
                      <a
                        href={prj.repository_url}
                        target="_blank"
                        rel="noreferrer"
                        className="inline-flex items-center gap-1 text-sky-400 hover:underline"
                      >
                        <Github className="w-3 h-3" />
                        <span>Source / Repo</span>
                      </a>
                    )}
                    {prj.live_url && (
                      <a
                        href={prj.live_url}
                        target="_blank"
                        rel="noreferrer"
                        className="inline-flex items-center gap-1 text-emerald-400 hover:underline"
                      >
                        <ExternalLink className="w-3 h-3" />
                        <span>Live Deployment</span>
                      </a>
                    )}
                  </div>
                </div>

                <div className="flex items-center gap-1.5">
                  <button
                    type="button"
                    onClick={() => openEdit(pIdx)}
                    className="p-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 text-slate-400 hover:text-white transition-colors cursor-pointer"
                    title="Edit Initiative"
                  >
                    <Edit2 className="w-3.5 h-3.5" />
                  </button>
                  <button
                    type="button"
                    onClick={() => onDeleteProject(pIdx)}
                    className="p-1.5 rounded-lg bg-slate-900 hover:bg-rose-950/60 text-slate-400 hover:text-rose-400 transition-colors cursor-pointer"
                    title="Delete Initiative"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>

              <p className="text-slate-300 leading-relaxed text-xs">{prj.description}</p>

              {Array.isArray(prj.technologies) && prj.technologies.length > 0 && (
                <div className="flex flex-wrap gap-1 pt-1">
                  {prj.technologies.map((t, idx) => (
                    <span
                      key={idx}
                      className="px-2 py-0.5 rounded-md bg-slate-900 text-slate-400 text-[10px] font-mono border border-slate-850"
                    >
                      {t}
                    </span>
                  ))}
                </div>
              )}
            </div>
          ))
        ) : (
          <p className="text-xs text-slate-500 italic py-2">
            No independent projects or flagship initiatives logged yet.
          </p>
        )}
      </div>
    </div>
  );
}

