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
  GraduationCap,
  Award,
  Link as LinkIcon,
  FolderGit2,
  CheckCircle2,
  TrendingUp,
  Upload,
  FileText,
  ChevronDown,
  ChevronUp,
} from "lucide-react";
import {
  getCandidatePersonas,
  updateCandidatePersona,
  deleteCandidatePersona,
  setDefaultPersona,
  createCandidatePersona,
  parseResumeDocument,
  parseResumeText,
  createCVBlock,
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
    seniority_level: "entry",
    years_experience: 0,
    min_salary: "",
    skills: "",
  });
  const [saveLoading, setSaveLoading] = useState(false);
  const [saveError, setSaveError] = useState(null);

  // Resume / CV Ingestion State
  const fileInputRef = React.useRef(null);
  const [parsingResume, setParsingResume] = useState(false);
  const [parseSuccessMsg, setParseSuccessMsg] = useState(null);
  const [parseErrorMsg, setParseErrorMsg] = useState(null);
  const [showPasteText, setShowPasteText] = useState(false);
  const [pastedResumeText, setPastedResumeText] = useState("");
  const [stagedBlocks, setStagedBlocks] = useState([]);
  const [domainExpertise, setDomainExpertise] = useState([]);
  const [semanticProfileSummary, setSemanticProfileSummary] = useState("");

  // Creating new specialized persona state
  const [isCreating, setIsCreating] = useState(false);
  const [createForm, setCreateForm] = useState({
    name: "",
    headline: "",
    target_roles: "",
    target_industries: "",
    seniority_level: "entry",
    years_experience: 0,
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
    setParseSuccessMsg(null);
    setParseErrorMsg(null);
    setStagedBlocks([]);
    setShowPasteText(false);
    setPastedResumeText("");
    const ci = p.career_intelligence || {};
    const edu = ci.education?.[0] || {};
    const links = ci.external_links || {};
    const existingSkills = Array.isArray(p.skills)
      ? p.skills
          .map((s) => (typeof s === "string" ? s : s.skill_name || s.name))
          .filter(Boolean)
          .join(", ")
      : "";

    setEditForm({
      name: p.name || "",
      headline: p.headline || "",
      target_roles: Array.isArray(p.target_roles) ? p.target_roles.join(", ") : "",
      target_industries: Array.isArray(p.target_industries)
        ? p.target_industries.join(", ")
        : "",
      seniority_level: p.seniority_level || "entry",
      years_experience: p.years_experience ?? 0,
      min_salary: p.min_salary || "",
      skills: existingSkills,
      // Candidate Intelligence Dimensions
      degree: edu.degree || "",
      major: edu.major || "",
      institution: edu.institution || "",
      graduation_year: edu.graduation_year || "",
      institution_tier: edu.institution_tier || "standard",
      projects_text: ci.projects?.map((prj) => `${prj.name}: ${prj.description || ""}`).join("\n") || "",
      hackathons_text: ci.hackathons_competitions?.map((h) => `${h.name}${h.rank_or_award ? ` - ${h.rank_or_award}` : ""}`).join("\n") || "",
      awards_text: ci.awards_recognitions?.map((a) => `${a.title}${a.description ? `: ${a.description}` : ""}`).join("\n") || "",
      linkedin_url: links.linkedin_url || "",
      github_url: links.github_url || "",
      leetcode_url: links.leetcode_url || "",
      leetcode_solved: links.leetcode_solved || "",
    });
  }

  function applyParsedDataToForm(data) {
    if (!data) return;
    const parsedYears =
      data.total_years_experience ??
      data.years_experience ??
      data.inferred_years_experience;
    const parsedSeniority = data.seniority_level || data.inferred_seniority_level;
    const parsedRoles = data.target_roles || data.inferred_target_roles;
    const ci = data.career_intelligence || {};
    const edu = data.education?.[0] || ci.education?.[0] || {};
    const links = data.external_links || ci.external_links || {
      linkedin_url: data.linkedin_url,
      github_url: data.github_url,
      leetcode_url: data.leetcode_url,
    };

    if (Array.isArray(data.domain_expertise) && data.domain_expertise.length > 0) {
      setDomainExpertise(data.domain_expertise);
    } else if (Array.isArray(ci.domain_expertise) && ci.domain_expertise.length > 0) {
      setDomainExpertise(ci.domain_expertise);
    }

    if (data.semantic_profile_summary) {
      setSemanticProfileSummary(data.semantic_profile_summary);
    } else if (ci.semantic_profile_summary) {
      setSemanticProfileSummary(ci.semantic_profile_summary);
    }

    setEditForm((prev) => {
      // Merge skills without duplicates
      const existingSkillsList = prev.skills
        ? prev.skills.split(",").map((s) => s.trim()).filter(Boolean)
        : [];
      const newSkillsList = Array.isArray(data.all_skills_flat) && data.all_skills_flat.length > 0
        ? data.all_skills_flat
        : Array.isArray(data.skills)
          ? data.skills
          : [];
      const combinedSkills = Array.from(
        new Set([...existingSkillsList, ...newSkillsList])
      ).join(", ");

      // Target roles
      let rolesStr = prev.target_roles;
      if (Array.isArray(parsedRoles) && parsedRoles.length > 0) {
        rolesStr = parsedRoles.join(", ");
      }

      // Projects
      let projectsStr = prev.projects_text;
      const incomingProjects = data.projects?.length > 0 ? data.projects : ci.projects || [];
      if (Array.isArray(incomingProjects) && incomingProjects.length > 0) {
        projectsStr = incomingProjects
          .map((prj) => `${prj.name}: ${prj.description || prj.name}`)
          .join("\n");
      }

      // Hackathons
      let hackathonsStr = prev.hackathons_text;
      const incomingHackathons =
        data.hackathons_competitions?.length > 0
          ? data.hackathons_competitions
          : ci.hackathons_competitions || data.awards_and_honors || [];
      if (Array.isArray(incomingHackathons) && incomingHackathons.length > 0) {
        hackathonsStr = incomingHackathons
          .map((h) => `${h.name || h.title}${h.rank_or_award ? ` - ${h.rank_or_award}` : ""}`)
          .join("\n");
      }

      // Awards
      let awardsStr = prev.awards_text;
      const incomingAwards =
        data.awards_recognitions?.length > 0
          ? data.awards_recognitions
          : ci.awards_recognitions || data.awards_and_honors || [];
      if (Array.isArray(incomingAwards) && incomingAwards.length > 0) {
        awardsStr = incomingAwards
          .map((a) => `${a.title}${a.description ? `: ${a.description}` : a.event_or_issuer ? `: ${a.event_or_issuer}` : ""}`)
          .join("\n");
      }

      return {
        ...prev,
        headline:
          data.headline ||
          (parsedRoles?.[0] ? `${parsedRoles[0]} Professional` : prev.headline),
        target_roles: rolesStr,
        seniority_level: parsedSeniority || prev.seniority_level || "entry",
        years_experience:
          parsedYears !== undefined && parsedYears !== null
            ? Number(parsedYears)
            : prev.years_experience,
        skills: combinedSkills,
        degree: edu.degree || prev.degree,
        major: edu.major || prev.major,
        institution: edu.institution || prev.institution,
        graduation_year: edu.graduation_year || prev.graduation_year,
        institution_tier: edu.institution_tier || prev.institution_tier,
        projects_text: projectsStr,
        hackathons_text: hackathonsStr,
        awards_text: awardsStr,
        linkedin_url: links.linkedin_url || prev.linkedin_url,
        github_url: links.github_url || prev.github_url,
        leetcode_url: links.leetcode_url || prev.leetcode_url,
        leetcode_solved: links.leetcode_solved || prev.leetcode_solved,
      };
    });

    if (Array.isArray(data.blocks) && data.blocks.length > 0) {
      setStagedBlocks(data.blocks);
    }
  }

  async function handleResumeFileUpload(e) {
    const file = e.target.files?.[0];
    if (!file) return;

    try {
      setParsingResume(true);
      setParseErrorMsg(null);
      setParseSuccessMsg(null);
      const data = await parseResumeDocument(file);
      applyParsedDataToForm(data);
      const blockCount = data.blocks?.length || 0;
      setParseSuccessMsg(
        `Successfully extracted profile data${blockCount > 0 ? ` and ${blockCount} experience blocks` : ""} from ${file.name}. Review below and save.`
      );
    } catch (err) {
      console.error("Resume file parse error:", err);
      setParseErrorMsg(
        err.response?.data?.detail ||
          "Failed to parse resume document. You can paste resume text below."
      );
    } finally {
      setParsingResume(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    }
  }

  async function handleResumePasteSubmit() {
    if (!pastedResumeText || pastedResumeText.trim().length < 20) {
      setParseErrorMsg("Please paste at least 20 characters of resume text.");
      return;
    }

    try {
      setParsingResume(true);
      setParseErrorMsg(null);
      setParseSuccessMsg(null);
      const data = await parseResumeText(pastedResumeText.trim());
      applyParsedDataToForm(data);
      const blockCount = data.blocks?.length || 0;
      setParseSuccessMsg(
        `Successfully parsed resume text${blockCount > 0 ? ` and extracted ${blockCount} blocks` : ""}. Review below and save.`
      );
      setShowPasteText(false);
      setPastedResumeText("");
    } catch (err) {
      console.error("Resume text parse error:", err);
      setParseErrorMsg(
        err.response?.data?.detail ||
          "Failed to parse resume text. Please check format and retry."
      );
    } finally {
      setParsingResume(false);
    }
  }

  function handleCardUploadClick(p) {
    startEditing(p);
    setTimeout(() => {
      if (fileInputRef.current) {
        fileInputRef.current.click();
      }
    }, 100);
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

    const careerIntelligence = {
      ...(editingPersona.career_intelligence || {}),
      education: (editForm.degree || editForm.institution)
        ? [
            {
              degree: editForm.degree.trim(),
              major: editForm.major.trim(),
              institution: editForm.institution.trim(),
              graduation_year: editForm.graduation_year ? Number(editForm.graduation_year) : null,
              institution_tier: editForm.institution_tier || "standard",
            },
          ]
        : (editingPersona.career_intelligence?.education || []),
      external_links: {
        linkedin_url: editForm.linkedin_url?.trim() || null,
        github_url: editForm.github_url?.trim() || null,
        leetcode_url: editForm.leetcode_url?.trim() || null,
        leetcode_solved: editForm.leetcode_solved ? Number(editForm.leetcode_solved) : null,
      },
    };

    if (editForm.projects_text?.trim()) {
      careerIntelligence.projects = editForm.projects_text
        .split("\n")
        .filter(Boolean)
        .map((line) => {
          const parts = line.split(":");
          return {
            name: parts[0]?.trim(),
            description: parts.slice(1).join(":")?.trim() || parts[0]?.trim(),
          };
        });
    }

    if (editForm.hackathons_text?.trim()) {
      careerIntelligence.hackathons_competitions = editForm.hackathons_text
        .split("\n")
        .filter(Boolean)
        .map((line) => ({ name: line.trim() }));
    }

    if (editForm.awards_text?.trim()) {
      careerIntelligence.awards_recognitions = editForm.awards_text
        .split("\n")
        .filter(Boolean)
        .map((line) => {
          const parts = line.split(":");
          return {
            title: parts[0]?.trim(),
            description: parts.slice(1).join(":")?.trim() || "",
          };
        });
    }

    if (domainExpertise && domainExpertise.length > 0) {
      careerIntelligence.domain_expertise = domainExpertise;
    }
    if (semanticProfileSummary) {
      careerIntelligence.semantic_profile_summary = semanticProfileSummary;
    }

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
      career_intelligence: careerIntelligence,
    };

    try {
      const updated = await updateCandidatePersona(editingPersona.id, payload);

      // Persist any staged CV blocks extracted from resume
      if (stagedBlocks.length > 0) {
        for (const block of stagedBlocks) {
          try {
            await createCVBlock({
              category: block.category || "work_experience",
              title: block.title || "Experience",
              organization: block.organization || "",
              content: block.content || "",
              metrics: block.metrics || {},
              skills: block.skills || [],
              persona_ids: [editingPersona.id],
            });
          } catch (blockErr) {
            console.warn("Failed to persist staged CV block:", blockErr);
          }
        }
        setStagedBlocks([]);
      }

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
        seniority_level: "entry",
        years_experience: 0,
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
                {/* Auto-Fill Persona from CV / Resume Section */}
                <div className="p-3.5 rounded-xl bg-gradient-to-r from-sky-950/40 to-indigo-950/40 border border-sky-500/30 space-y-2.5">
                  <div className="flex items-center justify-between flex-wrap gap-2">
                    <div className="flex items-center gap-2.5">
                      <div className="p-2 rounded-lg bg-sky-500/20 text-sky-400">
                        <Upload className="w-4 h-4" />
                      </div>
                      <div>
                        <h4 className="text-xs font-semibold text-white">
                          Auto-Fill Persona from CV / Resume
                        </h4>
                        <p className="text-[10px] text-slate-400">
                          Upload PDF/DOCX/TXT or paste text to auto-populate experience, skills, and education.
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <input
                        type="file"
                        ref={fileInputRef}
                        accept=".pdf,.docx,.txt"
                        onChange={handleResumeFileUpload}
                        className="hidden"
                        id="persona-cv-upload-input"
                        data-testid="persona-cv-file-input"
                      />
                      <label
                        htmlFor="persona-cv-upload-input"
                        className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-sky-600 hover:bg-sky-500 text-white text-xs font-medium cursor-pointer shadow-sm transition-all ${
                          parsingResume ? "opacity-50 pointer-events-none" : ""
                        }`}
                      >
                        {parsingResume ? (
                          <>
                            <Loader2 className="w-3.5 h-3.5 animate-spin" />
                            <span>Parsing...</span>
                          </>
                        ) : (
                          <>
                            <Upload className="w-3.5 h-3.5" />
                            <span>Upload CV / Resume</span>
                          </>
                        )}
                      </label>
                      <button
                        type="button"
                        onClick={() => setShowPasteText((prev) => !prev)}
                        className="inline-flex items-center gap-1 px-2.5 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium border border-slate-700 cursor-pointer"
                        title="Paste Resume Text"
                      >
                        <FileText className="w-3.5 h-3.5" />
                        <span>Paste Text</span>
                        {showPasteText ? (
                          <ChevronUp className="w-3 h-3 text-slate-400" />
                        ) : (
                          <ChevronDown className="w-3 h-3 text-slate-400" />
                        )}
                      </button>
                    </div>
                  </div>

                  {/* Parse Status Feedback */}
                  {parseSuccessMsg && (
                    <div
                      className="p-2 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-300 text-xs flex items-center gap-1.5"
                      data-testid="cv-parse-success"
                    >
                      <CheckCircle2 className="w-3.5 h-3.5 shrink-0 text-emerald-400" />
                      <span>{parseSuccessMsg}</span>
                    </div>
                  )}
                  {parseErrorMsg && (
                    <div
                      className="p-2 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs flex items-center gap-1.5"
                      data-testid="cv-parse-error"
                    >
                      <AlertCircle className="w-3.5 h-3.5 shrink-0 text-rose-400" />
                      <span>{parseErrorMsg}</span>
                    </div>
                  )}

                  {/* Staged CV Blocks info pill */}
                  {stagedBlocks.length > 0 && (
                    <div className="flex items-center gap-1.5 text-[11px] text-sky-300 bg-sky-950/60 px-2.5 py-1 rounded-lg border border-sky-800/60">
                      <Layers className="w-3.5 h-3.5 text-sky-400 shrink-0" />
                      <span>
                        {stagedBlocks.length} career block{stagedBlocks.length === 1 ? "" : "s"} staged from your resume will be attached when you save.
                      </span>
                    </div>
                  )}

                  {/* Business Domain Expertise Pills */}
                  {domainExpertise.length > 0 && (
                    <div className="flex items-center gap-1.5 flex-wrap pt-1" data-testid="domain-expertise-pills">
                      <span className="text-[10px] font-semibold text-slate-400">Detected Business Domains:</span>
                      {domainExpertise.map((de, idx) => (
                        <span
                          key={idx}
                          className="text-[10px] px-2 py-0.5 rounded-full bg-indigo-500/15 text-indigo-300 border border-indigo-500/30 font-medium"
                        >
                          {de.domain} ({de.years_experience}y)
                        </span>
                      ))}
                    </div>
                  )}

                  {/* Collapsible Text Area for Direct Paste */}
                  {showPasteText && (
                    <div className="pt-2 border-t border-slate-800 space-y-2">
                      <textarea
                        rows={4}
                        data-testid="paste-resume-textarea"
                        value={pastedResumeText}
                        onChange={(e) => setPastedResumeText(e.target.value)}
                        placeholder="Paste your raw resume text, LinkedIn profile, or CV contents here..."
                        className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none focus:border-sky-500 font-mono"
                      />
                      <div className="flex justify-end gap-2">
                        <button
                          type="button"
                          onClick={() => {
                            setShowPasteText(false);
                            setPastedResumeText("");
                          }}
                          className="px-2.5 py-1 text-xs text-slate-400 hover:text-slate-200 cursor-pointer"
                        >
                          Cancel
                        </button>
                        <button
                          type="button"
                          data-testid="submit-resume-text-btn"
                          disabled={parsingResume || !pastedResumeText.trim()}
                          onClick={handleResumePasteSubmit}
                          className="px-3 py-1 bg-sky-600 hover:bg-sky-500 text-white rounded-lg text-xs font-medium cursor-pointer disabled:opacity-50 flex items-center gap-1.5"
                        >
                          {parsingResume ? (
                            <>
                              <Loader2 className="w-3 h-3 animate-spin" />
                              <span>Parsing...</span>
                            </>
                          ) : (
                            <span>Parse & Auto-Fill</span>
                          )}
                        </button>
                      </div>
                    </div>
                  )}
                </div>

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
                      <option value="entry">Entry-Level</option>
                      <option value="junior">Junior</option>
                      <option value="mid">Mid-Level</option>
                      <option value="senior">Senior</option>
                      <option value="lead">Lead</option>
                      <option value="staff">Staff</option>
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

                {/* 3. Education & Institution Tier */}
                <div className="pt-2 border-t border-slate-800 space-y-2">
                  <div className="flex items-center gap-1.5 text-xs font-semibold text-slate-300">
                    <GraduationCap className="w-3.5 h-3.5 text-sky-400" />
                    <span>Education & Prestige Tier</span>
                  </div>
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
                    <input
                      type="text"
                      placeholder="Degree (e.g. B.S., M.S.)"
                      value={editForm.degree}
                      onChange={(e) => setEditForm({ ...editForm, degree: e.target.value })}
                      className="px-2.5 py-1.5 bg-slate-900 border border-slate-700 rounded-lg text-xs text-white placeholder-slate-500 focus:outline-none focus:border-sky-500"
                    />
                    <input
                      type="text"
                      placeholder="Major (e.g. Computer Science)"
                      value={editForm.major}
                      onChange={(e) => setEditForm({ ...editForm, major: e.target.value })}
                      className="px-2.5 py-1.5 bg-slate-900 border border-slate-700 rounded-lg text-xs text-white placeholder-slate-500 focus:outline-none focus:border-sky-500"
                    />
                    <input
                      type="text"
                      placeholder="University / Institution"
                      value={editForm.institution}
                      onChange={(e) => setEditForm({ ...editForm, institution: e.target.value })}
                      className="px-2.5 py-1.5 bg-slate-900 border border-slate-700 rounded-lg text-xs text-white placeholder-slate-500 focus:outline-none focus:border-sky-500"
                    />
                  </div>
                  <div className="grid grid-cols-2 gap-2">
                    <input
                      type="number"
                      placeholder="Graduation Year (e.g. 2022)"
                      value={editForm.graduation_year}
                      onChange={(e) => setEditForm({ ...editForm, graduation_year: e.target.value })}
                      className="px-2.5 py-1.5 bg-slate-900 border border-slate-700 rounded-lg text-xs text-white placeholder-slate-500 focus:outline-none focus:border-sky-500"
                    />
                    <select
                      value={editForm.institution_tier}
                      onChange={(e) => setEditForm({ ...editForm, institution_tier: e.target.value })}
                      className="px-2.5 py-1.5 bg-slate-900 border border-slate-700 rounded-lg text-xs text-white focus:outline-none focus:border-sky-500"
                    >
                      <option value="standard">Standard University</option>
                      <option value="tier_2">Tier 2 Top 50 University</option>
                      <option value="tier_1">Tier 1 Target School (MIT, Stanford, CMU, Berkeley...)</option>
                    </select>
                  </div>
                </div>

                {/* 4. Projects & Open Source */}
                <div className="pt-2 border-t border-slate-800 space-y-1.5">
                  <div className="flex items-center gap-1.5 text-xs font-semibold text-slate-300">
                    <FolderGit2 className="w-3.5 h-3.5 text-indigo-400" />
                    <span>Technical Projects & Open Source (Name: Description)</span>
                  </div>
                  <textarea
                    rows={2}
                    value={editForm.projects_text}
                    onChange={(e) => setEditForm({ ...editForm, projects_text: e.target.value })}
                    placeholder="e.g. Distributed Ledger: Built low-latency payment engine in Rust processing 10k ops/sec"
                    className="w-full px-2.5 py-1.5 bg-slate-900 border border-slate-700 rounded-lg text-xs text-white placeholder-slate-500 focus:outline-none focus:border-sky-500"
                  />
                </div>

                {/* 5. Hackathons, LeetCode & Awards */}
                <div className="pt-2 border-t border-slate-800 space-y-1.5">
                  <div className="flex items-center gap-1.5 text-xs font-semibold text-slate-300">
                    <Award className="w-3.5 h-3.5 text-amber-400" />
                    <span>Hackathons, Awards & Competitions (one per line)</span>
                  </div>
                  <textarea
                    rows={2}
                    value={editForm.hackathons_text}
                    onChange={(e) => setEditForm({ ...editForm, hackathons_text: e.target.value })}
                    placeholder="e.g. ETHGlobal San Francisco - 1st Place DeFi Track&#10;LeetCode Top 5% (Rating 2150)"
                    className="w-full px-2.5 py-1.5 bg-slate-900 border border-slate-700 rounded-lg text-xs text-white placeholder-slate-500 focus:outline-none focus:border-sky-500"
                  />
                </div>

                {/* 6. External Links & Compensation Logistics */}
                <div className="pt-2 border-t border-slate-800 space-y-2">
                  <div className="flex items-center gap-1.5 text-xs font-semibold text-slate-300">
                    <LinkIcon className="w-3.5 h-3.5 text-emerald-400" />
                    <span>External Profile Links & Logistics</span>
                  </div>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                    <input
                      type="url"
                      placeholder="LinkedIn URL (https://linkedin.com/in/...)"
                      value={editForm.linkedin_url}
                      onChange={(e) => setEditForm({ ...editForm, linkedin_url: e.target.value })}
                      className="px-2.5 py-1.5 bg-slate-900 border border-slate-700 rounded-lg text-xs text-white placeholder-slate-500 focus:outline-none focus:border-sky-500"
                    />
                    <input
                      type="url"
                      placeholder="GitHub URL (https://github.com/...)"
                      value={editForm.github_url}
                      onChange={(e) => setEditForm({ ...editForm, github_url: e.target.value })}
                      className="px-2.5 py-1.5 bg-slate-900 border border-slate-700 rounded-lg text-xs text-white placeholder-slate-500 focus:outline-none focus:border-sky-500"
                    />
                  </div>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                    <input
                      type="url"
                      placeholder="LeetCode Profile URL"
                      value={editForm.leetcode_url}
                      onChange={(e) => setEditForm({ ...editForm, leetcode_url: e.target.value })}
                      className="px-2.5 py-1.5 bg-slate-900 border border-slate-700 rounded-lg text-xs text-white placeholder-slate-500 focus:outline-none focus:border-sky-500"
                    />
                    <input
                      type="number"
                      placeholder="Min Base Salary USD ($)"
                      value={editForm.min_salary}
                      onChange={(e) => setEditForm({ ...editForm, min_salary: e.target.value })}
                      className="px-2.5 py-1.5 bg-slate-900 border border-slate-700 rounded-lg text-xs text-white placeholder-slate-500 focus:outline-none focus:border-sky-500"
                    />
                  </div>
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
                      <option value="entry">Entry-Level</option>
                      <option value="junior">Junior</option>
                      <option value="mid">Mid-Level</option>
                      <option value="senior">Senior</option>
                      <option value="lead">Lead</option>
                      <option value="staff">Staff</option>
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
                {/* 7-Dimension Profile Completeness Overview Card */}
                {(() => {
                  const defaultPersona = personas.find((p) => p.is_default) || personas[0];
                  const score = defaultPersona?.completeness_score ?? 0;
                  const missing = defaultPersona?.completeness?.missing_steps || [];
                  const isZero = score === 0;

                  return (
                    <div
                      data-testid="profile-completeness-overview"
                      className="p-4 rounded-xl bg-slate-950/80 border border-slate-800 space-y-3"
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <CheckCircle2 className="w-4 h-4 text-sky-400" />
                          <span className="text-xs font-bold text-white uppercase tracking-wider">
                            Candidate Intelligence Completeness
                          </span>
                        </div>
                        <span
                          className={`text-xs font-extrabold px-2.5 py-0.5 rounded-full border ${
                            isZero
                              ? "bg-rose-500/15 text-rose-300 border-rose-500/30"
                              : score >= 75
                                ? "bg-emerald-500/15 text-emerald-300 border-emerald-500/30"
                                : score >= 50
                                  ? "bg-sky-500/15 text-sky-300 border-sky-500/30"
                                  : "bg-amber-500/15 text-amber-300 border-amber-500/30"
                          }`}
                        >
                          {score}% Complete
                        </span>
                      </div>

                      {/* Visual Progress Bar */}
                      <div className="w-full h-2 bg-slate-900 rounded-full overflow-hidden border border-slate-800">
                        <div
                          className={`h-full rounded-full transition-all duration-500 ${
                            isZero
                              ? "bg-rose-500"
                              : score >= 75
                                ? "bg-emerald-500"
                                : score >= 50
                                  ? "bg-sky-500"
                                  : "bg-amber-500"
                          }`}
                          style={{ width: `${Math.max(3, score)}%` }}
                        />
                      </div>

                      {/* Actionable Checklist */}
                      {missing.length > 0 ? (
                        <div className="space-y-1.5 pt-1">
                          <p className="text-[11px] font-semibold text-slate-400">
                            Actionable Checklist to Reach 100% Matching Precision:
                          </p>
                          <div className="space-y-1">
                            {missing.slice(0, 4).map((step, idx) => (
                              <div
                                key={idx}
                                className="flex items-start justify-between gap-2 p-2 rounded-lg bg-slate-900/60 border border-slate-800/80 text-xs text-slate-300"
                              >
                                <div className="flex items-start gap-1.5 min-w-0">
                                  <span className="text-sky-400 font-bold shrink-0">+{step.potential_gain_pct}%</span>
                                  <span className="leading-tight text-[11px] text-slate-300">{step.prompt}</span>
                                </div>
                                {defaultPersona && (
                                  <button
                                    type="button"
                                    onClick={() => startEditing(defaultPersona)}
                                    className="text-[10px] text-sky-400 hover:text-sky-300 font-semibold shrink-0 cursor-pointer"
                                  >
                                    Complete →
                                  </button>
                                )}
                              </div>
                            ))}
                          </div>
                        </div>
                      ) : (
                        <p className="text-xs text-emerald-400 font-medium flex items-center gap-1.5 pt-1">
                          <Check className="w-3.5 h-3.5" /> All candidate intelligence dimensions complete (100%)!
                        </p>
                      )}
                    </div>
                  );
                })()}

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
                                  <Check className="w-2.5 h-2.5" /> Default Profile
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
                            onClick={() => handleCardUploadClick(p)}
                            data-testid={`upload-cv-card-btn-${p.id}`}
                            title="Upload CV to auto-fill this persona"
                            className="px-2.5 py-1.5 rounded-lg border border-sky-500/40 bg-sky-500/10 hover:bg-sky-500/20 text-sky-300 text-xs font-medium flex items-center gap-1.5 transition-colors cursor-pointer"
                          >
                            <Upload className="w-3.5 h-3.5 text-sky-400" />
                            <span>Upload CV</span>
                          </button>

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

