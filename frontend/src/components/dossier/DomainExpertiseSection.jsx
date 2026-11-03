import React, { useState } from "react";
import {
  Compass,
  Plus,
  ShieldCheck,
  Edit2,
  Trash2,
  AlertCircle,
  X,
  Sparkles,
} from "lucide-react";

const REGULATORY_PRESETS = [
  "HIPAA",
  "SOC2",
  "PCI-DSS",
  "GDPR",
  "CCPA",
  "SOX",
  "FDA",
  "FHIR",
  "HL7",
  "DICOM",
  "ISO-27001",
  "FedRAMP",
  "AML / KYC",
  "EDI / X12",
];

export function DomainExpertiseSection({
  domainExpertise = [],
  headline = "",
  yearsExperience = 0,
  targetRoles = [],
  workExperience = [],
  semanticSummary = "",
  onSaveDomain,
  onDeleteDomain,
  onUpdateSummary,
}) {
  const [isAdding, setIsAdding] = useState(false);
  const [editingIndex, setEditingIndex] = useState(null);

  const [form, setForm] = useState({
    domain: "",
    years_experience: 1.0,
    regulatory_frameworks: [],
    core_competencies: [],
  });
  const [regInput, setRegInput] = useState("");
  const [compInput, setCompInput] = useState("");
  const [error, setError] = useState(null);

  function openAdd() {
    setForm({
      domain: "",
      years_experience: 1.0,
      regulatory_frameworks: [],
      core_competencies: [],
    });
    setRegInput("");
    setCompInput("");
    setError(null);
    setEditingIndex(null);
    setIsAdding(true);
  }

  function openEdit(idx) {
    const de = domainExpertise[idx];
    setForm({
      domain: de.domain || "",
      years_experience: Number(de.years_experience) || 1.0,
      regulatory_frameworks: Array.isArray(de.regulatory_frameworks)
        ? [...de.regulatory_frameworks]
        : [],
      core_competencies: Array.isArray(de.core_competencies)
        ? [...de.core_competencies]
        : [],
    });
    setRegInput("");
    setCompInput("");
    setError(null);
    setEditingIndex(idx);
    setIsAdding(true);
  }

  function handleAddFramework(tag) {
    const clean = (tag || regInput).trim();
    if (clean && !form.regulatory_frameworks.some((f) => f.toLowerCase() === clean.toLowerCase())) {
      setForm({
        ...form,
        regulatory_frameworks: [...form.regulatory_frameworks, clean],
      });
      setRegInput("");
    }
  }

  function handleRemoveFramework(tag) {
    setForm({
      ...form,
      regulatory_frameworks: form.regulatory_frameworks.filter(
        (f) => f.toLowerCase() !== tag.toLowerCase()
      ),
    });
  }

  function handleAddCompetency() {
    const clean = compInput.trim();
    if (clean && !form.core_competencies.some((c) => c.toLowerCase() === clean.toLowerCase())) {
      setForm({
        ...form,
        core_competencies: [...form.core_competencies, clean],
      });
      setCompInput("");
    }
  }

  function handleRemoveCompetency(tag) {
    setForm({
      ...form,
      core_competencies: form.core_competencies.filter(
        (c) => c.toLowerCase() !== tag.toLowerCase()
      ),
    });
  }

  function handleSave(e) {
    e.preventDefault();
    if (!form.domain.trim()) {
      setError("Industry domain vertical name is required.");
      return;
    }

    const payload = {
      ...form,
      domain: form.domain.trim(),
      years_experience: Number(form.years_experience) || 0.5,
    };

    onSaveDomain(payload, editingIndex);
    setIsAdding(false);
    setEditingIndex(null);
  }

  function handleRefreshSummary() {
    const primaryRole = targetRoles[0] || "Executive & Professional";
    const topDomains = domainExpertise.map((d) => d.domain).slice(0, 3).join(", ");
    const regList = Array.from(
      new Set(domainExpertise.flatMap((d) => d.regulatory_frameworks || []))
    ).slice(0, 4);

    const companies = Array.from(
      new Set(workExperience.map((w) => w.company_name).filter(Boolean))
    ).slice(0, 3);

    let summary = `${headline || primaryRole} with ${yearsExperience}+ years of proven leadership across ${
      topDomains || "high-growth business domains"
    }.`;

    if (companies.length > 0) {
      summary += ` Track record driving organizational velocity and high-impact deliverables at ${companies.join(", ")}.`;
    }

    if (regList.length > 0) {
      summary += ` Deep domain governance and operational execution backed by strict compliance expertise (${regList.join(", ")}).`;
    }

    onUpdateSummary(summary);
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <span className="text-[11px] font-semibold text-slate-300">
            Industry Domain Verticals ({domainExpertise.length})
          </span>
          <p className="text-[11px] text-slate-400">
            Qualifies your background against mandatory industry & regulatory job requirements
          </p>
        </div>
        {!isAdding && (
          <button
            type="button"
            onClick={openAdd}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-sky-950/80 hover:bg-sky-900 border border-sky-800/80 text-sky-300 text-xs font-semibold cursor-pointer transition-colors"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>Add Domain Vertical</span>
          </button>
        )}
      </div>

      {/* Add / Edit Drawer */}
      {isAdding && (
        <form
          onSubmit={handleSave}
          className="p-4 rounded-xl bg-slate-950 border border-sky-700/60 space-y-3.5 shadow-2xl"
        >
          <div className="flex items-center justify-between border-b border-slate-800 pb-2">
            <h5 className="text-xs font-bold text-white uppercase tracking-wide">
              {editingIndex !== null ? "Edit Domain Vertical" : "Add Domain Vertical"}
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

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div className="sm:col-span-2">
              <label className="block text-[11px] font-semibold text-slate-300 mb-1">
                Business Domain / Industry Vertical *
              </label>
              <input
                type="text"
                placeholder="e.g. HealthTech, FinTech, Enterprise SaaS, Biotech, E-Commerce"
                value={form.domain}
                onChange={(e) => setForm({ ...form, domain: e.target.value })}
                className="w-full px-3 py-1.5 bg-slate-900 border border-slate-700 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none focus:border-sky-500"
              />
            </div>
            <div>
              <label className="block text-[11px] font-semibold text-slate-300 mb-1">
                Years of Domain Experience
              </label>
              <input
                type="number"
                step="0.5"
                min="0.5"
                max="40"
                value={form.years_experience}
                onChange={(e) => setForm({ ...form, years_experience: e.target.value })}
                className="w-full px-3 py-1.5 bg-slate-900 border border-slate-700 rounded-xl text-xs text-white focus:outline-none focus:border-sky-500"
              />
            </div>
          </div>

          {/* Regulatory & Compliance Frameworks */}
          <div>
            <label className="block text-[11px] font-semibold text-slate-300 mb-1">
              Regulatory, Compliance & Standards Frameworks
            </label>
            <div className="flex flex-wrap gap-1 mb-2">
              {REGULATORY_PRESETS.map((preset) => (
                <button
                  key={preset}
                  type="button"
                  onClick={() => handleAddFramework(preset)}
                  className="px-2 py-0.5 rounded-md bg-slate-900 hover:bg-slate-800 text-slate-400 hover:text-white border border-slate-800 text-[10px] cursor-pointer"
                >
                  + {preset}
                </button>
              ))}
            </div>
            <div className="flex items-center gap-2 mb-2">
              <input
                type="text"
                placeholder="Type custom standard (e.g. NPI, CAN-SPAM) and press Enter"
                value={regInput}
                onChange={(e) => setRegInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") {
                    e.preventDefault();
                    handleAddFramework();
                  }
                }}
                className="flex-1 px-3 py-1.5 bg-slate-900 border border-slate-700 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none focus:border-sky-500"
              />
              <button
                type="button"
                onClick={() => handleAddFramework()}
                className="px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-white text-xs font-medium cursor-pointer"
              >
                Add Framework
              </button>
            </div>
            <div className="flex flex-wrap gap-1.5">
              {form.regulatory_frameworks.map((fw, fIdx) => (
                <span
                  key={fIdx}
                  className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-lg bg-sky-950/60 border border-sky-800/80 text-sky-200 text-xs"
                >
                  <ShieldCheck className="w-3 h-3 text-sky-400" />
                  <span>{fw}</span>
                  <button
                    type="button"
                    onClick={() => handleRemoveFramework(fw)}
                    className="text-sky-400 hover:text-white"
                  >
                    <X className="w-3 h-3" />
                  </button>
                </span>
              ))}
            </div>
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
              className="px-4 py-1.5 rounded-xl bg-sky-600 hover:bg-sky-500 text-white text-xs font-semibold cursor-pointer"
            >
              {editingIndex !== null ? "Save Changes" : "Save Domain Vertical"}
            </button>
          </div>
        </form>
      )}

      {/* Domain Cards List */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-2.5">
        {domainExpertise.length > 0 ? (
          domainExpertise.map((de, idx) => (
            <div
              key={idx}
              className="p-3.5 rounded-xl bg-slate-950/80 border border-slate-800/90 hover:border-slate-700 flex flex-col justify-between text-xs space-y-2 transition-all"
            >
              <div className="flex items-start justify-between gap-2">
                <div>
                  <span className="font-bold text-white text-sm">{de.domain}</span>
                  <div className="text-[11px] text-slate-400 mt-0.5">
                    {de.years_experience} Years Verified Depth
                  </div>
                </div>

                <div className="flex items-center gap-1.5">
                  <button
                    type="button"
                    onClick={() => openEdit(idx)}
                    className="p-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 text-slate-400 hover:text-white transition-colors cursor-pointer"
                    title="Edit Domain Vertical"
                  >
                    <Edit2 className="w-3.5 h-3.5" />
                  </button>
                  <button
                    type="button"
                    onClick={() => onDeleteDomain(idx)}
                    className="p-1.5 rounded-lg bg-slate-900 hover:bg-rose-950/60 text-slate-400 hover:text-rose-400 transition-colors cursor-pointer"
                    title="Delete Domain Vertical"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>

              {Array.isArray(de.regulatory_frameworks) && de.regulatory_frameworks.length > 0 && (
                <div className="flex flex-wrap gap-1 pt-1 border-t border-slate-900">
                  {de.regulatory_frameworks.map((reg, rIdx) => (
                    <span
                      key={rIdx}
                      className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-sky-950/60 border border-sky-800/60 text-sky-300 text-[10px] font-medium"
                    >
                      <ShieldCheck className="w-2.5 h-2.5" />
                      <span>{reg}</span>
                    </span>
                  ))}
                </div>
              )}
            </div>
          ))
        ) : (
          <div className="col-span-2 p-3 rounded-xl bg-slate-950/50 border border-dashed border-slate-800 text-center">
            <p className="text-xs text-slate-500 italic">
              No specific industry verticals declared yet. Click "+ Add Domain Vertical" to specify FinTech, HealthTech, SaaS, or Biotech background.
            </p>
          </div>
        )}
      </div>

      {/* Grounded Semantic Executive Summary */}
      <div className="pt-3 border-t border-slate-800/80 space-y-2">
        <div className="flex items-center justify-between">
          <div>
            <label className="block text-xs font-bold text-white uppercase tracking-wider">
              Grounded Semantic Profile Summary
            </label>
            <p className="text-[11px] text-slate-400">
              High-density executive synthesis consumed by semantic matching models
            </p>
          </div>
          <button
            type="button"
            onClick={handleRefreshSummary}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 border border-slate-700 text-sky-300 text-xs font-semibold cursor-pointer transition-colors"
          >
            <Sparkles className="w-3.5 h-3.5 text-amber-400" />
            <span>Refresh from Dossier</span>
          </button>
        </div>

        <textarea
          rows={3}
          value={semanticSummary}
          onChange={(e) => onUpdateSummary(e.target.value)}
          placeholder="Synthesizing career trajectory, top domain verticals, and verified proof points..."
          className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-xs text-slate-300 focus:outline-none focus:border-sky-500 leading-relaxed font-mono"
        />
      </div>
    </div>
  );
}

