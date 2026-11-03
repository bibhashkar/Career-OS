import React, { useState } from "react";
import {
  Trophy,
  Plus,
  ExternalLink,
  Edit2,
  Trash2,
  AlertCircle,
  X,
  Award,
} from "lucide-react";

export function AwardsDistinctionsSection({
  awards = [],
  archetype = "technology_engineering",
  onSaveAward,
  onDeleteAward,
}) {
  const [isAdding, setIsAdding] = useState(false);
  const [editingIndex, setEditingIndex] = useState(null);

  const [form, setForm] = useState({
    title: "",
    event_or_issuer: "",
    date_str: "",
    category: "award",
    description: "",
    url: "",
  });
  const [error, setError] = useState(null);

  const sectionTitles = {
    technology_engineering: "6B. Competitions, Hackathons & Honors",
    executive_leadership: "6B. Board Appointments, Keynotes & Executive Distinctions",
    marketing_growth: "6B. Industry Awards, Speaking & Published Work",
    product_strategy: "6B. Product Honors, Patents & Keynotes",
    finance_fintech: "6B. Certifications, Distinctions & Industry Honors",
    healthcare_lifesciences: "6B. Publications, Grants, Fellowships & Honors",
    custom_hybrid: "6B. Awards, Distinctions & Recognitions",
  };

  const titlePlaceholders = {
    technology_engineering: "e.g. 1st Place Winner - ETHGlobal or US Patent #11,234,567",
    executive_leadership: "e.g. Board Member - FinTech Advisory Council or Keynote Speaker",
    marketing_growth: "e.g. Cannes Lions Gold Winner or Effie Award for B2B Growth",
    product_strategy: "e.g. Product of the Year (ProductHunt #1) or Patent Filed",
    finance_fintech: "e.g. Chartered Financial Analyst (CFA) or Deal of the Year",
    healthcare_lifesciences: "e.g. Lead Author - NEJM Clinical Trial Publication or NIH Grant",
    custom_hybrid: "e.g. Industry Excellence Award or Keynote Distinction",
  };

  function openAdd() {
    setForm({
      title: "",
      event_or_issuer: "",
      date_str: "",
      category: "award",
      description: "",
      url: "",
    });
    setError(null);
    setEditingIndex(null);
    setIsAdding(true);
  }

  function openEdit(idx) {
    const aw = awards[idx];
    setForm({
      title: aw.title || "",
      event_or_issuer: aw.event_or_issuer || "",
      date_str: aw.date_str || "",
      category: aw.category || "award",
      description: aw.description || "",
      url: aw.url || "",
    });
    setError(null);
    setEditingIndex(idx);
    setIsAdding(true);
  }

  function handleSave(e) {
    e.preventDefault();
    if (!form.title.trim()) {
      setError("Award or distinction title is required.");
      return;
    }

    let url = form.url.trim();
    if (url && !url.startsWith("http://") && !url.startsWith("https://")) {
      url = `https://${url}`;
    }

    const payload = {
      ...form,
      title: form.title.trim(),
      event_or_issuer: form.event_or_issuer.trim() || null,
      date_str: form.date_str.trim() || null,
      description: form.description.trim() || null,
      url: url || null,
    };

    onSaveAward(payload, editingIndex);
    setIsAdding(false);
    setEditingIndex(null);
  }

  return (
    <div className="space-y-3 pt-3 border-t border-slate-800/80">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Trophy className="w-4 h-4 text-amber-400" />
          <h4 className="text-xs font-bold text-white uppercase tracking-wider">
            {sectionTitles[archetype] || sectionTitles.technology_engineering} ({awards.length})
          </h4>
        </div>
        {!isAdding && (
          <button
            type="button"
            onClick={openAdd}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-amber-950/80 hover:bg-amber-900 border border-amber-800/80 text-amber-300 text-xs font-semibold cursor-pointer transition-colors"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>Add Honor / Distinction</span>
          </button>
        )}
      </div>

      {/* Add / Edit Drawer */}
      {isAdding && (
        <form
          onSubmit={handleSave}
          className="p-4 rounded-xl bg-slate-950 border border-amber-700/60 space-y-3.5 shadow-2xl"
        >
          <div className="flex items-center justify-between border-b border-slate-800 pb-2">
            <h5 className="text-xs font-bold text-white uppercase tracking-wide">
              {editingIndex !== null ? "Edit Honor / Distinction" : "Add New Honor / Distinction"}
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
                Title / Placement *
              </label>
              <input
                type="text"
                placeholder={titlePlaceholders[archetype] || titlePlaceholders.technology_engineering}
                value={form.title}
                onChange={(e) => setForm({ ...form, title: e.target.value })}
                className="w-full px-3 py-1.5 bg-slate-900 border border-slate-700 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none focus:border-amber-500"
              />
            </div>
            <div>
              <label className="block text-[11px] font-semibold text-slate-300 mb-1">
                Category
              </label>
              <select
                value={form.category}
                onChange={(e) => setForm({ ...form, category: e.target.value })}
                className="w-full px-3 py-1.5 bg-slate-900 border border-slate-700 rounded-xl text-xs text-white focus:outline-none focus:border-amber-500 cursor-pointer"
              >
                <option value="award">Industry Award / Honor</option>
                <option value="hackathon">Hackathon / Competition</option>
                <option value="board">Board Seat / Governance</option>
                <option value="patent">Patent / Intellectual Property</option>
                <option value="publication">Research Paper / Publication</option>
                <option value="speaking">Keynote / Conference Speaking</option>
              </select>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div>
              <label className="block text-[11px] font-semibold text-slate-300 mb-1">
                Issuing Organization / Event
              </label>
              <input
                type="text"
                placeholder="e.g. IEEE, MIT, Forbes, Cannes, SEC"
                value={form.event_or_issuer}
                onChange={(e) => setForm({ ...form, event_or_issuer: e.target.value })}
                className="w-full px-3 py-1.5 bg-slate-900 border border-slate-700 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none focus:border-amber-500"
              />
            </div>
            <div>
              <label className="block text-[11px] font-semibold text-slate-300 mb-1">
                Date / Year
              </label>
              <input
                type="text"
                placeholder="e.g. 2024 or Nov 2023"
                value={form.date_str}
                onChange={(e) => setForm({ ...form, date_str: e.target.value })}
                className="w-full px-3 py-1.5 bg-slate-900 border border-slate-700 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none focus:border-amber-500"
              />
            </div>
            <div>
              <label className="block text-[11px] font-semibold text-slate-300 mb-1">
                Verification / Reference Link
              </label>
              <input
                type="text"
                placeholder="https://..."
                value={form.url}
                onChange={(e) => setForm({ ...form, url: e.target.value })}
                className="w-full px-3 py-1.5 bg-slate-900 border border-slate-700 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none focus:border-amber-500"
              />
            </div>
          </div>

          <div>
            <label className="block text-[11px] font-semibold text-slate-300 mb-1">
              Achievement Details & Context
            </label>
            <textarea
              rows={2}
              placeholder="Highlight the distinction criteria, scope of competition or honor, and recognized outcome..."
              value={form.description}
              onChange={(e) => setForm({ ...form, description: e.target.value })}
              className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-xl text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-amber-500 leading-relaxed"
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
              className="px-4 py-1.5 rounded-xl bg-amber-600 hover:bg-amber-500 text-white text-xs font-semibold cursor-pointer"
            >
              {editingIndex !== null ? "Save Changes" : "Save Honor"}
            </button>
          </div>
        </form>
      )}

      {/* Awards Cards List */}
      <div className="space-y-2.5">
        {awards.length > 0 ? (
          awards.map((aw, aIdx) => (
            <div
              key={aIdx}
              className="p-3.5 rounded-xl bg-slate-950/80 border border-slate-800/90 hover:border-slate-700 space-y-1.5 text-xs transition-all"
            >
              <div className="flex items-start justify-between gap-2">
                <div>
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="font-bold text-white text-sm">{aw.title}</span>
                    {aw.category && (
                      <span className="text-[10px] uppercase tracking-wider px-2 py-0.5 rounded-md bg-amber-950/60 text-amber-300 border border-amber-800/60 font-semibold">
                        {aw.category}
                      </span>
                    )}
                  </div>
                  <div className="flex items-center gap-2 mt-1 text-[11px] text-slate-400">
                    {aw.event_or_issuer && (
                      <span className="text-slate-300 font-medium">{aw.event_or_issuer}</span>
                    )}
                    {aw.date_str && (
                      <span className="text-slate-500">• {aw.date_str}</span>
                    )}
                    {aw.url && (
                      <a
                        href={aw.url}
                        target="_blank"
                        rel="noreferrer"
                        className="inline-flex items-center gap-1 text-sky-400 hover:underline ml-1"
                      >
                        <ExternalLink className="w-3 h-3" />
                        <span>Link</span>
                      </a>
                    )}
                  </div>
                </div>

                <div className="flex items-center gap-1.5">
                  <button
                    type="button"
                    onClick={() => openEdit(aIdx)}
                    className="p-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 text-slate-400 hover:text-white transition-colors cursor-pointer"
                    title="Edit Distinction"
                  >
                    <Edit2 className="w-3.5 h-3.5" />
                  </button>
                  <button
                    type="button"
                    onClick={() => onDeleteAward(aIdx)}
                    className="p-1.5 rounded-lg bg-slate-900 hover:bg-rose-950/60 text-slate-400 hover:text-rose-400 transition-colors cursor-pointer"
                    title="Delete Distinction"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>

              {aw.description && (
                <p className="text-slate-300 leading-relaxed text-xs pt-1">{aw.description}</p>
              )}
            </div>
          ))
        ) : (
          <p className="text-xs text-slate-500 italic py-2">
            No awards, honors, publications, or competitive distinctions logged yet.
          </p>
        )}
      </div>
    </div>
  );
}

