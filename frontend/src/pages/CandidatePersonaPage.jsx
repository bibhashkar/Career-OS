import React, { useState, useEffect, useCallback, useRef } from "react";
import {
  User,
  Layers,
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
  ExternalLink,
  Shield,
  MapPin,
  Clock,
  DollarSign,
  Copy,
  CheckCheck,
  X,
  FileSearch,
  Eye,
  Database,
  Tag,
  ArrowRight,
  RefreshCw,
} from "lucide-react";
import {
  getCandidatePersonas,
  updateCandidatePersona,
  deleteCandidatePersona,
  setDefaultPersona,
  createCandidatePersona,
  parseResumeDocument,
  parseResumeText,
  getCVBlocks,
  createCVBlock,
  updateCVBlock,
  deleteCVBlock,
} from "../services/api";

const VISA_STATUS_OPTIONS = [
  "Citizen",
  "Green Card / Permanent Resident",
  "H-1B",
  "F-1 OPT / STEM OPT",
  "TN Visa",
  "UK Skilled Worker",
  "Canada LMIA / PR",
  "Australia Subclass 482",
  "Requires Sponsorship",
  "None",
];

const SENIORITY_LEVELS = [
  { value: "entry", label: "Entry-Level (0-2y)" },
  { value: "junior", label: "Junior (1-3y)" },
  { value: "mid", label: "Mid-Level (3-5y)" },
  { value: "senior", label: "Senior (5-8y)" },
  { value: "lead", label: "Lead (7-10y)" },
  { value: "staff", label: "Staff (10-14y)" },
  { value: "principal", label: "Principal (14+y)" },
  { value: "executive", label: "Executive / VP" },
];

const SKILL_CATEGORIES = [
  { key: "system_architecture", label: "System Architecture & Patterns" },
  { key: "backend_and_frameworks", label: "Backend & Distributed Frameworks" },
  { key: "ai_and_infrastructure", label: "AI, RAG & Vector Infrastructure" },
  { key: "databases_and_caching", label: "Databases, Storage & Caching" },
  { key: "cloud_and_devops", label: "Cloud, DevOps & CI/CD" },
  { key: "frontend_and_ui", label: "Frontend & Web Architecture" },
  { key: "security_and_compliance", label: "Security, Governance & Compliance" },
  { key: "testing_and_qa", label: "Testing, Observability & QA" },
];

export function CandidatePersonaPage({ activePersona, onPersonaChange }) {
  // Personas State
  const [personas, setPersonas] = useState([]);
  const [selectedPersonaId, setSelectedPersonaId] = useState(activePersona?.id || null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Form State for active persona
  const [dossierForm, setDossierForm] = useState({
    name: "",
    full_name: "",
    email: "",
    phone: "",
    headline: "",
    seniority_level: "mid",
    years_experience: 0,
    min_salary: "",
    target_roles: [],
    target_industries: [],
    skills: [],
    skills_matrix: {},
    visa_status: "Citizen",
    preferred_locations: ["Remote"],
    remote_preference: "Remote",
    linkedin_url: "",
    github_url: "",
    portfolio_url: "",
    leetcode_url: "",
    leetcode_solved: "",
    domain_expertise: [],
    education: [],
    work_experience: [],
    projects: [],
    awards_recognitions: [],
    semantic_profile_summary: "",
    source_provenance: {},
  });

  // CVBlocks persisted in DB for candidate
  const [persistedBlocks, setPersistedBlocks] = useState([]);
  const [loadingBlocks, setLoadingBlocks] = useState(false);

  // Editing CVBlock modal/inline state
  const [editingBlock, setEditingBlock] = useState(null);
  const [blockForm, setBlockForm] = useState({
    title: "",
    organization: "",
    category: "experience",
    content: "",
    skills: "",
    metrics: {},
  });

  // New item modal/inline state
  const [editingRoleIndex, setEditingRoleIndex] = useState(null);
  const [roleForm, setRoleForm] = useState({
    company_name: "",
    job_title: "",
    location: "Remote",
    is_remote: true,
    start_date: "",
    end_date: "Present",
    seniority_level: "senior",
    industry_domain: "Cloud & Distributed Systems",
  });

  const [editingEduIndex, setEditingEduIndex] = useState(null);
  const [eduForm, setEduForm] = useState({
    degree: "Master of Science",
    major: "Computer Science",
    institution: "",
    institution_tier: "standard",
    graduation_year: 2025,
    gpa: "",
    honors: "",
  });

  // Ingestion & Parsing State
  const fileInputRef = useRef(null);
  const [parsingResume, setParsingResume] = useState(false);
  const [parseError, setParseError] = useState(null);
  const [stagedReview, setStagedReview] = useState(null); // When document parsed but not yet saved
  const [showPasteModal, setShowPasteModal] = useState(false);
  const [pastedText, setPastedText] = useState("");

  // Slide-over Raw Text Inspector Drawer
  const [showRawInspector, setShowRawInspector] = useState(false);
  const [copiedRawText, setCopiedRawText] = useState(false);

  // Creating specialized persona modal
  const [isCreatingTrack, setIsCreatingTrack] = useState(false);
  const [newTrackName, setNewTrackName] = useState("");
  const [newTrackHeadline, setNewTrackHeadline] = useState("");

  // Saving state
  const [saveLoading, setSaveLoading] = useState(false);
  const [saveSuccessMsg, setSaveSuccessMsg] = useState(null);
  const [saveErrorMsg, setSaveErrorMsg] = useState(null);

  // Inputs for adding tags
  const [newRoleTag, setNewRoleTag] = useState("");
  const [newSkillTag, setNewSkillTag] = useState("");
  const [newLocationTag, setNewLocationTag] = useState("");

  const currentPersona = personas.find((p) => p.id === selectedPersonaId) || personas[0] || null;

  // 1. Fetch Personas and CVBlocks
  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const [pData, bData] = await Promise.all([
        getCandidatePersonas(),
        getCVBlocks().catch(() => []),
      ]);
      setPersonas(pData || []);
      setPersistedBlocks(bData || []);

      const active =
        pData.find((p) => p.id === selectedPersonaId) ||
        pData.find((p) => p.is_default) ||
        pData[0];
      if (active) {
        setSelectedPersonaId(active.id);
        populateFormFromPersona(active, bData || []);
      }
    } catch (err) {
      console.error("Failed to load candidate personas:", err);
      setError("Unable to load candidate dossier data. Please retry.");
    } finally {
      setLoading(false);
    }
  }, [selectedPersonaId]);

  useEffect(() => {
    loadData();
  }, []);

  // When selected persona changes, populate form
  function populateFormFromPersona(p, blocks = persistedBlocks) {
    if (!p) return;
    const ci = p.career_intelligence || {};
    const links = ci.external_links || {};
    const prov = ci.source_provenance || {};

    const rawSkillsList = Array.isArray(p.skills)
      ? p.skills.map((s) => (typeof s === "string" ? s : s.skill_name || s.name)).filter(Boolean)
      : [];

    const pii = ci.contact_pii || {};

    setDossierForm({
      name: p.name || "",
      full_name: p.full_name || pii.full_name || "",
      email: p.email || pii.email || "",
      phone: p.phone || pii.phone || "",
      headline: p.headline || "",
      seniority_level: p.seniority_level || "mid",
      years_experience: p.years_experience ?? 0,
      min_salary: p.min_salary || "",
      target_roles: Array.isArray(p.target_roles) ? p.target_roles : [],
      target_industries: Array.isArray(p.target_industries) ? p.target_industries : [],
      skills: rawSkillsList,
      skills_matrix: ci.skills_matrix || {},
      visa_status: p.visa_status || "Citizen",
      preferred_locations: Array.isArray(p.preferred_locations) && p.preferred_locations.length > 0
        ? p.preferred_locations
        : ["Remote"],
      remote_preference: p.remote_preference || "Remote",
      linkedin_url: links.linkedin_url || "",
      github_url: links.github_url || "",
      portfolio_url: links.portfolio_url || "",
      leetcode_url: links.leetcode_url || "",
      leetcode_solved: links.leetcode_solved || "",
      domain_expertise: Array.isArray(ci.domain_expertise) ? ci.domain_expertise : [],
      education: Array.isArray(ci.education) ? ci.education : [],
      work_experience: Array.isArray(ci.work_experience) ? ci.work_experience : [],
      projects: Array.isArray(ci.projects) ? ci.projects : [],
      awards_recognitions: Array.isArray(ci.awards_recognitions) ? ci.awards_recognitions : [],
      semantic_profile_summary: ci.semantic_profile_summary || "",
      source_provenance: prov,
    });
  }

  function handleSelectPersona(p) {
    setSelectedPersonaId(p.id);
    populateFormFromPersona(p);
    setStagedReview(null);
    setSaveSuccessMsg(null);
    setSaveErrorMsg(null);
    if (onPersonaChange) onPersonaChange(p);
  }

  // 2. Handle File Upload (Resume / CV)
  async function handleFileUpload(e) {
    const file = e.target.files?.[0];
    if (!file) return;

    try {
      setParsingResume(true);
      setParseError(null);
      const parsed = await parseResumeDocument(file);
      applyParsedDossier(parsed, file.name);
    } catch (err) {
      console.error("Resume file parse error:", err);
      setParseError(err.response?.data?.detail || "Failed to parse resume. Try pasting text.");
    } finally {
      setParsingResume(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  }

  // 3. Handle Text Paste Submit
  async function handlePasteSubmit() {
    if (!pastedText || pastedText.trim().length < 20) {
      setParseError("Please paste at least 20 characters of resume or LinkedIn text.");
      return;
    }

    try {
      setParsingResume(true);
      setParseError(null);
      const parsed = await parseResumeText(pastedText.trim());
      applyParsedDossier(parsed, "Pasted Text Import");
      setShowPasteModal(false);
      setPastedText("");
    } catch (err) {
      console.error("Resume text parse error:", err);
      setParseError(err.response?.data?.detail || "Failed to parse text. Please check format.");
    } finally {
      setParsingResume(false);
    }
  }

  // Apply parsed extraction into staged state
  function applyParsedDossier(data, sourceLabel) {
    if (!data) return;
    const ci = data.career_intelligence || {};
    const links = data.external_links || ci.external_links || {
      linkedin_url: data.linkedin_url,
      github_url: data.github_url,
      leetcode_url: data.leetcode_url,
    };

    const extractedName = data.full_name && data.full_name !== "Candidate" ? data.full_name : null;
    const extractedEmail = data.email || null;
    const extractedPhone = data.phone || null;

    const newSkills = Array.isArray(data.all_skills_flat) && data.all_skills_flat.length > 0
      ? data.all_skills_flat
      : Array.isArray(data.skills)
        ? data.skills
        : [];

    const combinedSkills = Array.from(new Set([...dossierForm.skills, ...newSkills]));
    const combinedRoles = Array.from(new Set([...dossierForm.target_roles, ...(data.target_roles || data.inferred_target_roles || [])]));

    const incomingWorkExp = Array.isArray(ci.work_experience) && ci.work_experience.length > 0
      ? ci.work_experience
      : Array.isArray(data.work_experience) && data.work_experience.length > 0
        ? data.work_experience
        : [];

    // Merge incoming tenures with existing tenures avoiding duplicates
    const mergedWorkExp = [...dossierForm.work_experience];
    for (const inExp of incomingWorkExp) {
      const inCompNorm = (inExp.company_name || "").toLowerCase().replace(/[^a-z0-9]/g, "");
      const inTitleNorm = (inExp.job_title || "").toLowerCase().replace(/[^a-z0-9]/g, "");
      const existingIdx = mergedWorkExp.findIndex((ex) => {
        const exCompNorm = (ex.company_name || "").toLowerCase().replace(/[^a-z0-9]/g, "");
        const exTitleNorm = (ex.job_title || "").toLowerCase().replace(/[^a-z0-9]/g, "");
        const exStart = String(ex.start_date || "").slice(0, 4);
        const inStart = String(inExp.start_date || "").slice(0, 4);
        return (
          exCompNorm === inCompNorm &&
          exTitleNorm === inTitleNorm &&
          (!exStart || !inStart || exStart === inStart)
        );
      });

      if (existingIdx >= 0) {
        // Merge tenure: enrich missing location, domain, and bullets
        const exTenure = mergedWorkExp[existingIdx];
        const existingBullets = exTenure.bullets || [];
        const seenBulletTexts = new Set(
          existingBullets.map((b) => (b.raw_text || "").trim().toLowerCase())
        );
        const newBullets = (inExp.bullets || []).filter(
          (b) => !seenBulletTexts.has((b.raw_text || "").trim().toLowerCase())
        );
        mergedWorkExp[existingIdx] = {
          ...exTenure,
          location: exTenure.location || inExp.location,
          industry_domain: exTenure.industry_domain || inExp.industry_domain,
          bullets: [...existingBullets, ...newBullets],
        };
      } else {
        mergedWorkExp.push(inExp);
      }
    }

    const stagedEdu = Array.isArray(ci.education) && ci.education.length > 0
      ? ci.education
      : Array.isArray(data.education) && data.education.length > 0
        ? data.education
        : dossierForm.education;

    const stagedBlocks = Array.isArray(data.blocks) ? data.blocks : [];

    setStagedReview({
      sourceLabel,
      filename: sourceLabel,
      layoutType: ci.source_provenance?.layout_type || "standard_single_column",
      pipeline: ci.source_provenance?.recommended_pipeline || "deep_llm_structured",
      rawText: data.raw_text || "",
      newRolesCount: incomingWorkExp.length,
      newBlocksCount: stagedBlocks.length,
      newSkillsCount: newSkills.length,
      newEduCount: stagedEdu.length,
      extractedContact: {
        full_name: extractedName,
        email: extractedEmail,
        phone: extractedPhone,
      },
      stagedBlocks,
    });

    setDossierForm((prev) => ({
      ...prev,
      full_name: extractedName || prev.full_name,
      email: extractedEmail || prev.email,
      phone: extractedPhone || prev.phone,
      headline: data.headline || prev.headline,
      seniority_level: data.seniority_level || data.inferred_seniority_level || prev.seniority_level,
      years_experience: data.total_years_experience ?? data.years_experience ?? prev.years_experience,
      target_roles: combinedRoles,
      skills: combinedSkills,
      skills_matrix: data.skills_matrix || ci.skills_matrix || prev.skills_matrix,
      linkedin_url: links.linkedin_url || prev.linkedin_url,
      github_url: links.github_url || prev.github_url,
      leetcode_url: links.leetcode_url || prev.leetcode_url,
      domain_expertise: Array.isArray(data.domain_expertise) && data.domain_expertise.length > 0
        ? data.domain_expertise
        : ci.domain_expertise || prev.domain_expertise,
      work_experience: mergedWorkExp,
      education: stagedEdu,
      semantic_profile_summary: data.semantic_profile_summary || ci.semantic_profile_summary || prev.semantic_profile_summary,
      source_provenance: {
        ...(ci.source_provenance || {}),
        filename: sourceLabel,
        raw_text: data.raw_text || "",
      },
    }));
  }

  // 4. Save Dossier to Backend
  async function handleSaveDossier(e) {
    if (e) e.preventDefault();
    if (!currentPersona) return;

    setSaveLoading(true);
    setSaveSuccessMsg(null);
    setSaveErrorMsg(null);

    const careerIntelligence = {
      ...(currentPersona.career_intelligence || {}),
      education: dossierForm.education,
      work_experience: dossierForm.work_experience,
      domain_expertise: dossierForm.domain_expertise,
      projects: dossierForm.projects,
      awards_recognitions: dossierForm.awards_recognitions,
      skills_matrix: dossierForm.skills_matrix,
      semantic_profile_summary: dossierForm.semantic_profile_summary,
      external_links: {
        linkedin_url: dossierForm.linkedin_url.trim() || null,
        github_url: dossierForm.github_url.trim() || null,
        portfolio_url: dossierForm.portfolio_url.trim() || null,
        leetcode_url: dossierForm.leetcode_url.trim() || null,
        leetcode_solved: dossierForm.leetcode_solved ? Number(dossierForm.leetcode_solved) : null,
      },
      source_provenance: {
        ...(currentPersona.career_intelligence?.source_provenance || {}),
        ...dossierForm.source_provenance,
        last_updated: new Date().toISOString(),
      },
    };

    const payload = {
      name: currentPersona.is_common_persona ? currentPersona.name : dossierForm.name.trim(),
      full_name: dossierForm.full_name ? dossierForm.full_name.trim() : null,
      email: dossierForm.email ? dossierForm.email.trim() : null,
      phone: dossierForm.phone ? dossierForm.phone.trim() : null,
      headline: dossierForm.headline.trim() || null,
      seniority_level: dossierForm.seniority_level,
      years_experience: Number(dossierForm.years_experience) || 0,
      min_salary: dossierForm.min_salary ? Number(dossierForm.min_salary) : null,
      target_roles: dossierForm.target_roles,
      target_industries: dossierForm.target_industries,
      skills: dossierForm.skills,
      career_intelligence: careerIntelligence,
      visa_status: dossierForm.visa_status,
      preferred_locations: dossierForm.preferred_locations,
      remote_preference: dossierForm.remote_preference,
    };

    try {
      const updated = await updateCandidatePersona(currentPersona.id, payload);

      // Persist any unpersisted blocks and bullets into pgvector CVBlocks
      const persistedContentSet = new Set(
        persistedBlocks.map((b) => (b.content || "").trim().toLowerCase())
      );

      // 1. Process staged review blocks if present
      if (stagedReview?.stagedBlocks?.length > 0) {
        for (const block of stagedReview.stagedBlocks) {
          const bContent = (block.content || "").trim().toLowerCase();
          if (persistedContentSet.has(bContent)) {
            continue; // Skip duplicate proof point
          }
          try {
            await createCVBlock({
              category: block.category || "experience",
              title: block.title || "Career Accomplishment",
              organization: block.organization || "",
              content: block.content || "",
              metrics: block.metrics || {},
              skills: block.skills || [],
              persona_ids: [currentPersona.id],
            });
            persistedContentSet.add(bContent);
          } catch (bErr) {
            console.warn("Failed to persist staged block:", bErr);
          }
        }
      }

      // 2. Process any remaining unpersisted bullets from work_experience
      for (const exp of (dossierForm.work_experience || [])) {
        for (const bullet of (exp.bullets || [])) {
          const rawText = (bullet.raw_text || "").trim();
          if (!rawText || persistedContentSet.has(rawText.toLowerCase())) {
            continue;
          }
          try {
            await createCVBlock({
              category: "experience",
              title: `${exp.job_title || "Role"} Achievement`,
              organization: exp.company_name || "",
              content: rawText,
              metrics: bullet.metrics?.[0]
                ? { [bullet.metrics[0].metric_type || "impact"]: bullet.metrics[0].raw_metric }
                : {},
              skills: bullet.technologies_used || [],
              persona_ids: [currentPersona.id],
            });
            persistedContentSet.add(rawText.toLowerCase());
          } catch (bErr) {
            console.warn("Failed to persist tenure bullet:", bErr);
          }
        }
      }

      setStagedReview(null);
      setSaveSuccessMsg("Career dossier saved and synchronized with pgvector matching engine.");
      await loadData();
      if (onPersonaChange) onPersonaChange(updated);
    } catch (err) {
      console.error("Failed to save dossier:", err);
      setSaveErrorMsg(err.response?.data?.detail || "Failed to save profile. Please retry.");
    } finally {
      setSaveLoading(false);
    }
  }

  // 5. Create New Specialized Persona Track
  async function handleCreateTrack(e) {
    e.preventDefault();
    if (!newTrackName.trim()) return;

    try {
      setLoading(true);
      const newP = await createCandidatePersona({
        name: newTrackName.trim(),
        headline: newTrackHeadline.trim() || null,
        target_roles: dossierForm.target_roles,
        seniority_level: dossierForm.seniority_level,
        years_experience: dossierForm.years_experience,
        skills: dossierForm.skills.slice(0, 15),
      });
      setIsCreatingTrack(false);
      setNewTrackName("");
      setNewTrackHeadline("");
      await loadData();
      setSelectedPersonaId(newP.id);
      populateFormFromPersona(newP);
    } catch (err) {
      console.error("Failed to create specialized persona:", err);
      alert(err.response?.data?.detail || "Failed to create specialized track.");
    } finally {
      setLoading(false);
    }
  }

  // 6. Delete Persona Track
  async function handleDeleteTrack(p) {
    if (p.is_common_persona) return;
    if (!window.confirm(`Are you sure you want to delete the track "${p.name}"?`)) return;

    try {
      await deleteCandidatePersona(p.id);
      await loadData();
    } catch (err) {
      alert("Failed to delete persona track.");
    }
  }

  // 7. CVBlock CRUD Handlers
  async function handleSaveBlock(e) {
    e.preventDefault();
    if (!blockForm.content.trim()) return;

    const skillsArray = blockForm.skills
      ? blockForm.skills.split(",").map((s) => s.trim()).filter(Boolean)
      : [];

    try {
      if (editingBlock?.isStaged) {
        // If editing a staged bullet: persist it to CVBlock immediately and update work_experience
        const created = await createCVBlock({
          title: blockForm.title.trim() || "Achievement",
          organization: blockForm.organization.trim() || null,
          category: blockForm.category,
          content: blockForm.content.trim(),
          skills: skillsArray,
          metrics: blockForm.metrics || {},
          persona_ids: currentPersona ? [currentPersona.id] : [],
        });
        setPersistedBlocks((prev) => [created, ...prev]);

        // Update the bullet in work_experience
        setDossierForm((prev) => {
          const updatedExp = [...(prev.work_experience || [])];
          if (updatedExp[editingBlock.expIdx]) {
            const bullets = [...(updatedExp[editingBlock.expIdx].bullets || [])];
            bullets[editingBlock.bulletIdx] = {
              raw_text: blockForm.content.trim(),
              technologies_used: skillsArray,
              metrics: Object.entries(blockForm.metrics || {}).map(([k, v]) => ({
                metric_type: k,
                raw_metric: String(v),
              })),
            };
            updatedExp[editingBlock.expIdx] = { ...updatedExp[editingBlock.expIdx], bullets };
          }
          return { ...prev, work_experience: updatedExp };
        });
      } else if (editingBlock?.id) {
        // Update existing block
        const oldContent = (editingBlock.content || "").trim().toLowerCase();
        const updated = await updateCVBlock(editingBlock.id, {
          title: blockForm.title.trim() || "Achievement",
          organization: blockForm.organization.trim() || null,
          category: blockForm.category,
          content: blockForm.content.trim(),
          skills: skillsArray,
          metrics: blockForm.metrics || {},
        });
        setPersistedBlocks((prev) => prev.map((b) => (b.id === updated.id ? updated : b)));

        // Also sync updated content in work_experience
        setDossierForm((prev) => ({
          ...prev,
          work_experience: (prev.work_experience || []).map((exp) => ({
            ...exp,
            bullets: (exp.bullets || []).map((b) =>
              (b.raw_text || "").trim().toLowerCase() === oldContent
                ? {
                    ...b,
                    raw_text: blockForm.content.trim(),
                    technologies_used: skillsArray,
                  }
                : b
            ),
          })),
        }));
      } else {
        // Create new block
        const created = await createCVBlock({
          title: blockForm.title.trim() || "Achievement",
          organization: blockForm.organization.trim() || null,
          category: blockForm.category,
          content: blockForm.content.trim(),
          skills: skillsArray,
          metrics: blockForm.metrics || {},
          persona_ids: currentPersona ? [currentPersona.id] : [],
        });
        setPersistedBlocks((prev) => [created, ...prev]);

        // If target tenure specified, add bullet to it
        if (editingBlock?.expIdx !== undefined && editingBlock?.expIdx >= 0) {
          setDossierForm((prev) => {
            const updatedExp = [...(prev.work_experience || [])];
            if (updatedExp[editingBlock.expIdx]) {
              const bullets = [...(updatedExp[editingBlock.expIdx].bullets || [])];
              bullets.push({
                raw_text: blockForm.content.trim(),
                technologies_used: skillsArray,
              });
              updatedExp[editingBlock.expIdx] = { ...updatedExp[editingBlock.expIdx], bullets };
            }
            return { ...prev, work_experience: updatedExp };
          });
        }
      }
      setEditingBlock(null);
    } catch (err) {
      console.error("Failed to save CV block:", err);
      alert("Unable to save achievement block.");
    }
  }

  async function handleDeleteBlock(blockId) {
    if (!window.confirm("Delete this achievement proof point from pgvector memory?")) return;
    try {
      const blockToDelete = persistedBlocks.find((b) => b.id === blockId);
      await deleteCVBlock(blockId);
      setPersistedBlocks((prev) => prev.filter((b) => b.id !== blockId));
      if (blockToDelete) {
        const bContentNorm = (blockToDelete.content || "").trim().toLowerCase();
        setDossierForm((prev) => ({
          ...prev,
          work_experience: (prev.work_experience || []).map((exp) => ({
            ...exp,
            bullets: (exp.bullets || []).filter(
              (b) => (b.raw_text || "").trim().toLowerCase() !== bContentNorm
            ),
          })),
        }));
      }
    } catch (err) {
      alert("Failed to delete block.");
    }
  }

  function handleDeleteStagedBullet(expIdx, bulletIdx) {
    if (!window.confirm("Delete this achievement proof point?")) return;
    setDossierForm((prev) => {
      const updatedExp = [...(prev.work_experience || [])];
      if (updatedExp[expIdx]) {
        const bullets = [...(updatedExp[expIdx].bullets || [])];
        if (bulletIdx >= 0) {
          bullets.splice(bulletIdx, 1);
        }
        updatedExp[expIdx] = { ...updatedExp[expIdx], bullets };
      }
      return { ...prev, work_experience: updatedExp };
    });
  }

  function handleEditStagedBullet(exp, bullet, expIdx, bulletIdx) {
    setEditingBlock({
      isStaged: true,
      expIdx,
      bulletIdx,
      organization: exp.company_name || "",
      title: `${exp.job_title || "Role"} Achievement`,
      category: "experience",
    });
    setBlockForm({
      title: `${exp.job_title || "Role"} Achievement`,
      organization: exp.company_name || "",
      category: "experience",
      content: bullet.raw_text || "",
      skills: (bullet.technologies_used || []).join(", "),
      metrics: bullet.metrics?.[0]
        ? { [bullet.metrics[0].metric_type || "impact"]: bullet.metrics[0].raw_metric }
        : {},
    });
  }

  // Tag Pill Handlers
  function addRoleTag() {
    if (!newRoleTag.trim()) return;
    if (!dossierForm.target_roles.includes(newRoleTag.trim())) {
      setDossierForm((prev) => ({
        ...prev,
        target_roles: [...prev.target_roles, newRoleTag.trim()],
      }));
    }
    setNewRoleTag("");
  }

  function removeRoleTag(idx) {
    setDossierForm((prev) => ({
      ...prev,
      target_roles: prev.target_roles.filter((_, i) => i !== idx),
    }));
  }

  function addSkillTag(categoryKey = null) {
    if (!newSkillTag.trim()) return;
    const tag = newSkillTag.trim();
    if (!dossierForm.skills.includes(tag)) {
      setDossierForm((prev) => {
        const nextMatrix = { ...(prev.skills_matrix || {}) };
        if (categoryKey) {
          nextMatrix[categoryKey] = [...(nextMatrix[categoryKey] || []), tag];
        }
        return {
          ...prev,
          skills: [...prev.skills, tag],
          skills_matrix: nextMatrix,
        };
      });
    }
    setNewSkillTag("");
  }

  function removeSkillTag(tagToRemove) {
    setDossierForm((prev) => {
      const nextSkills = prev.skills.filter((s) => s !== tagToRemove);
      const nextMatrix = { ...(prev.skills_matrix || {}) };
      Object.keys(nextMatrix).forEach((k) => {
        if (Array.isArray(nextMatrix[k])) {
          nextMatrix[k] = nextMatrix[k].filter((s) => s !== tagToRemove);
        }
      });
      return {
        ...prev,
        skills: nextSkills,
        skills_matrix: nextMatrix,
      };
    });
  }

  // Work Experience tenure helpers
  function handleSaveRoleTenure(e) {
    e.preventDefault();
    if (!roleForm.company_name.trim() || !roleForm.job_title.trim()) return;

    setDossierForm((prev) => {
      const expList = [...(prev.work_experience || [])];
      const entry = {
        company_name: roleForm.company_name.trim(),
        job_title: roleForm.job_title.trim(),
        location: roleForm.location.trim(),
        is_remote: roleForm.is_remote,
        start_date: roleForm.start_date.trim(),
        end_date: roleForm.end_date.trim(),
        seniority_level: roleForm.seniority_level,
        industry_domain: roleForm.industry_domain,
        duration_years: 1.0,
        bullets: editingRoleIndex !== null && editingRoleIndex >= 0 ? expList[editingRoleIndex]?.bullets || [] : [],
      };

      if (editingRoleIndex !== null && editingRoleIndex >= 0) {
        expList[editingRoleIndex] = entry;
      } else {
        expList.unshift(entry);
      }
      return { ...prev, work_experience: expList };
    });

    setEditingRoleIndex(null);
  }

  function handleDeleteRoleTenure(idx) {
    if (!window.confirm("Delete this work experience tenure?")) return;
    setDossierForm((prev) => ({
      ...prev,
      work_experience: prev.work_experience.filter((_, i) => i !== idx),
    }));
  }

  // Education helpers
  function handleSaveEducation(e) {
    e.preventDefault();
    if (!eduForm.institution.trim()) return;

    setDossierForm((prev) => {
      const eduList = [...(prev.education || [])];
      const entry = {
        degree: eduForm.degree.trim(),
        major: eduForm.major.trim(),
        institution: eduForm.institution.trim(),
        institution_tier: eduForm.institution_tier,
        graduation_year: Number(eduForm.graduation_year) || null,
        gpa: eduForm.gpa?.trim() || null,
        honors: eduForm.honors?.trim() || null,
      };

      if (editingEduIndex !== null) {
        eduList[editingEduIndex] = entry;
      } else {
        eduList.push(entry);
      }
      return { ...prev, education: eduList };
    });

    setEditingEduIndex(null);
  }

  function handleDeleteEducation(idx) {
    if (!window.confirm("Delete this education credential?")) return;
    setDossierForm((prev) => ({
      ...prev,
      education: prev.education.filter((_, i) => i !== idx),
    }));
  }

  if (loading && personas.length === 0) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center p-12 text-slate-400 space-y-3">
        <Loader2 className="w-8 h-8 animate-spin text-sky-400" />
        <p className="text-sm font-medium">Loading candidate career dossier...</p>
      </div>
    );
  }

  const completenessScore = currentPersona?.completeness_score ?? 0;
  const missingSteps = currentPersona?.completeness?.missing_steps || [];

  return (
    <div
      data-testid="candidate-persona-page"
      className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 w-full space-y-6"
    >
      {/* Top Page Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pb-4 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-xs font-bold uppercase tracking-wider text-sky-400">
              Candidate Dossier & Career Architecture
            </span>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-slate-800 text-slate-300 border border-slate-700">
              pgvector Synchronized
            </span>
          </div>
          <h1 className="text-2xl font-extrabold text-white mt-1">
            Candidate Profile & Career Personas
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Verify, edit, and organize all parsed experiences, education, and skills. What you confirm here powers your 360° market matches and CV tailoring.
          </p>
        </div>

        {/* Global Save Button & Alerts */}
        <div className="flex items-center gap-3">
          {saveSuccessMsg && (
            <span className="text-xs text-emerald-400 flex items-center gap-1.5 animate-in fade-in duration-200">
              <CheckCircle2 className="w-4 h-4" /> {saveSuccessMsg}
            </span>
          )}
          {saveErrorMsg && (
            <span className="text-xs text-rose-400 flex items-center gap-1.5 animate-in fade-in duration-200">
              <AlertCircle className="w-4 h-4" /> {saveErrorMsg}
            </span>
          )}
          <button
            type="button"
            onClick={handleSaveDossier}
            data-testid="save-dossier-top-btn"
            disabled={saveLoading}
            className="px-5 py-2.5 rounded-xl bg-sky-600 hover:bg-sky-500 text-white font-semibold text-xs shadow-md shadow-sky-600/30 flex items-center gap-2 transition-all cursor-pointer disabled:opacity-50"
          >
            {saveLoading ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Check className="w-4 h-4" />
            )}
            <span>Save Dossier Changes</span>
          </button>
        </div>
      </div>

      {/* Staged Review Banner (When New CV / LinkedIn text has been uploaded/pasted) */}
      {stagedReview && (
        <div
          data-testid="staged-extraction-banner"
          className="p-4 rounded-2xl bg-gradient-to-r from-sky-950/80 via-slate-900 to-indigo-950/80 border-2 border-sky-500/50 shadow-xl space-y-3 animate-in fade-in duration-300"
        >
          <div className="flex items-center justify-between flex-wrap gap-3">
            <div className="flex items-center gap-3">
              <div className="p-2.5 rounded-xl bg-sky-500/20 text-sky-400 border border-sky-500/30">
                <Sparkles className="w-5 h-5 animate-pulse" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-white flex items-center gap-2">
                  <span>Extraction Staged from: {stagedReview.filename}</span>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded-md bg-sky-500/10 text-sky-300 border border-sky-500/20">
                    {stagedReview.layoutType}
                  </span>
                </h3>
                <p className="text-xs text-slate-300 mt-0.5">
                  Parsed: <span className="font-semibold text-white">{stagedReview.newRolesCount} Experiences</span>,{" "}
                  <span className="font-semibold text-white">{stagedReview.newBlocksCount} Proof Points</span>,{" "}
                  <span className="font-semibold text-white">{stagedReview.newSkillsCount} Skills</span>, and{" "}
                  <span className="font-semibold text-white">{stagedReview.newEduCount} Degrees</span>. Review below and commit to save.
                </p>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={() => setShowRawInspector(true)}
                className="px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 text-xs font-medium flex items-center gap-1.5 transition-colors cursor-pointer"
              >
                <Eye className="w-3.5 h-3.5 text-sky-400" />
                <span>Inspect Raw Source</span>
              </button>
              <button
                type="button"
                onClick={() => setStagedReview(null)}
                className="px-3 py-1.5 rounded-xl border border-slate-700 hover:bg-slate-800 text-slate-400 hover:text-slate-200 text-xs font-medium transition-colors cursor-pointer"
              >
                Discard
              </button>
              <button
                type="button"
                onClick={handleSaveDossier}
                disabled={saveLoading}
                className="px-4 py-1.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold shadow-md shadow-emerald-600/20 flex items-center gap-1.5 transition-all cursor-pointer"
              >
                {saveLoading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Check className="w-3.5 h-3.5" />}
                <span>Confirm & Commit to Dossier</span>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Main Two-Column Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* ========================================================================= */}
        {/* LEFT SIDEBAR (Col 4 of 12): Persona Tracks, Ingestion Hub & Completeness */}
        {/* ========================================================================= */}
        <div className="lg:col-span-4 space-y-5 sticky top-4">
          {/* Persona Track Selector */}
          <div
            data-testid="persona-track-selector"
            className="p-4 rounded-2xl bg-slate-900/90 border border-slate-800 shadow-lg space-y-3"
          >
            <div className="flex items-center justify-between">
              <h2 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
                <Layers className="w-3.5 h-3.5 text-sky-400" /> Career Tracks ({personas.length})
              </h2>
              <button
                type="button"
                onClick={() => setIsCreatingTrack(true)}
                className="text-[11px] font-semibold text-indigo-400 hover:text-indigo-300 flex items-center gap-1 cursor-pointer"
              >
                <Plus className="w-3 h-3" /> New Track
              </button>
            </div>

            {/* List of Personas */}
            <div className="space-y-2">
              {personas.map((p) => {
                const isSelected = p.id === selectedPersonaId;
                return (
                  <div
                    key={p.id}
                    onClick={() => handleSelectPersona(p)}
                    data-testid={`persona-track-card-${p.id}`}
                    className={`p-3 rounded-xl border transition-all cursor-pointer ${
                      isSelected
                        ? "bg-sky-950/60 border-sky-500/60 shadow-md"
                        : "bg-slate-850/60 border-slate-800 hover:border-slate-700 text-slate-400"
                    }`}
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div className="min-w-0">
                        <div className="flex items-center gap-1.5 flex-wrap">
                          <span className={`text-xs font-bold truncate ${isSelected ? "text-white" : "text-slate-300"}`}>
                            {p.name}
                          </span>
                          {p.is_common_persona && (
                            <span className="text-[9px] px-1.5 py-0.2 rounded bg-sky-500/20 text-sky-300 font-semibold border border-sky-500/30">
                              Universal
                            </span>
                          )}
                          {p.is_default && (
                            <span className="text-[9px] px-1.5 py-0.2 rounded bg-emerald-500/20 text-emerald-300 font-semibold border border-emerald-500/30">
                              Default
                            </span>
                          )}
                        </div>
                        <p className="text-[11px] text-slate-400 truncate mt-0.5">
                          {p.headline || "No headline configured"}
                        </p>
                      </div>

                      {!p.is_common_persona && (
                        <button
                          type="button"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleDeleteTrack(p);
                          }}
                          className="p-1 text-slate-500 hover:text-rose-400 transition-colors"
                          title="Delete track"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Create Track Form */}
            {isCreatingTrack && (
              <form onSubmit={handleCreateTrack} className="p-3 rounded-xl bg-slate-950 border border-indigo-500/30 space-y-2.5">
                <h4 className="text-xs font-bold text-white flex items-center gap-1">
                  <Sparkles className="w-3.5 h-3.5 text-indigo-400" /> Create Specialized Track
                </h4>
                <input
                  type="text"
                  required
                  placeholder="e.g. AI Platform Engineer"
                  value={newTrackName}
                  onChange={(e) => setNewTrackName(e.target.value)}
                  className="w-full px-2.5 py-1.5 bg-slate-900 border border-slate-700 rounded-lg text-xs text-white focus:outline-none focus:border-indigo-500"
                />
                <input
                  type="text"
                  placeholder="Headline: e.g. LLM Serving & Distributed Inference"
                  value={newTrackHeadline}
                  onChange={(e) => setNewTrackHeadline(e.target.value)}
                  className="w-full px-2.5 py-1.5 bg-slate-900 border border-slate-700 rounded-lg text-xs text-white focus:outline-none focus:border-indigo-500"
                />
                <div className="flex justify-end gap-2 pt-1">
                  <button
                    type="button"
                    onClick={() => setIsCreatingTrack(false)}
                    className="px-2.5 py-1 text-xs text-slate-400 hover:text-white"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="px-3 py-1 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-xs font-semibold"
                  >
                    Create
                  </button>
                </div>
              </form>
            )}
          </div>

          {/* Multi-Source Ingestion Hub */}
          <div
            data-testid="multi-source-ingestion-hub"
            className="p-4 rounded-2xl bg-slate-900/90 border border-slate-800 shadow-lg space-y-3"
          >
            <h2 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
              <Upload className="w-3.5 h-3.5 text-sky-400" /> Source Ingestion & Verification
            </h2>

            <p className="text-[11px] text-slate-400">
              Upload your documents to auto-populate experience, education, and achievements.
            </p>

            <input
              type="file"
              ref={fileInputRef}
              accept=".pdf,.docx,.txt"
              onChange={handleFileUpload}
              className="hidden"
              id="fullpage-cv-upload-input"
            />

            <div className="grid grid-cols-2 gap-2">
              <label
                htmlFor="fullpage-cv-upload-input"
                className={`flex flex-col items-center justify-center p-3 rounded-xl border border-sky-500/30 bg-sky-950/20 hover:bg-sky-950/40 text-sky-300 text-xs font-semibold cursor-pointer transition-all ${
                  parsingResume ? "opacity-50 pointer-events-none" : ""
                }`}
              >
                {parsingResume ? (
                  <Loader2 className="w-5 h-5 animate-spin mb-1 text-sky-400" />
                ) : (
                  <Upload className="w-5 h-5 mb-1 text-sky-400" />
                )}
                <span>Upload CV/Resume</span>
                <span className="text-[9px] text-slate-400 font-normal">PDF, DOCX, TXT</span>
              </label>

              <button
                type="button"
                onClick={() => setShowPasteModal(true)}
                className="flex flex-col items-center justify-center p-3 rounded-xl border border-indigo-500/30 bg-indigo-950/20 hover:bg-indigo-950/40 text-indigo-300 text-xs font-semibold cursor-pointer transition-all"
              >
                <FileText className="w-5 h-5 mb-1 text-indigo-400" />
                <span>Paste Profile Text</span>
                <span className="text-[9px] text-slate-400 font-normal">LinkedIn / Verbatim</span>
              </button>
            </div>

            {/* Source Ledger & Raw Text Inspector Trigger */}
            <div className="pt-2 border-t border-slate-800 flex items-center justify-between text-xs">
              <div className="flex items-center gap-1.5 text-slate-400">
                <FileSearch className="w-3.5 h-3.5 text-slate-500" />
                <span className="truncate max-w-[140px]">
                  {dossierForm.source_provenance?.filename || "No document loaded"}
                </span>
              </div>
              {dossierForm.source_provenance?.raw_text && (
                <button
                  type="button"
                  onClick={() => setShowRawInspector(true)}
                  className="text-[11px] font-semibold text-sky-400 hover:text-sky-300 flex items-center gap-1"
                >
                  <Eye className="w-3 h-3" /> Inspect Text
                </button>
              )}
            </div>
          </div>

          {/* 7-Dimension Completeness Radar */}
          <div
            data-testid="profile-completeness-radar"
            className="p-4 rounded-2xl bg-slate-900/90 border border-slate-800 shadow-lg space-y-3"
          >
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
                <CheckCircle2 className="w-3.5 h-3.5 text-sky-400" /> Profile Precision
              </span>
              <span
                className={`text-xs font-extrabold px-2.5 py-0.5 rounded-full border ${
                  completenessScore >= 75
                    ? "bg-emerald-500/20 text-emerald-300 border-emerald-500/40"
                    : completenessScore >= 50
                      ? "bg-sky-500/20 text-sky-300 border-sky-500/40"
                      : "bg-amber-500/20 text-amber-300 border-amber-500/40"
                }`}
              >
                {completenessScore}% Complete
              </span>
            </div>

            <div className="w-full h-2 bg-slate-950 rounded-full overflow-hidden border border-slate-800">
              <div
                className={`h-full rounded-full transition-all duration-500 ${
                  completenessScore >= 75 ? "bg-emerald-500" : completenessScore >= 50 ? "bg-sky-500" : "bg-amber-500"
                }`}
                style={{ width: `${Math.max(4, completenessScore)}%` }}
              />
            </div>

            {missingSteps.length > 0 && (
              <div className="space-y-1.5 pt-1">
                <span className="text-[11px] font-semibold text-slate-400">Actionable Precision Boosts:</span>
                <div className="space-y-1">
                  {missingSteps.slice(0, 3).map((st, idx) => (
                    <div
                      key={idx}
                      className="p-2 rounded-lg bg-slate-950/60 border border-slate-800 text-[11px] text-slate-300 flex items-start gap-1.5"
                    >
                      <span className="text-sky-400 font-bold shrink-0">+{st.potential_gain_pct}%</span>
                      <span>{st.prompt}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* ========================================================================= */}
        {/* RIGHT CANVAS (Col 8 of 12): 6 Structured Dossier Sections                */}
        {/* ========================================================================= */}
        <div className="lg:col-span-8 space-y-6">
          {/* Section 1: Executive Identity, Target Roles & Logistics */}
          <section
            data-testid="section-executive-identity"
            className="p-5 rounded-2xl bg-slate-900/90 border border-slate-800 shadow-xl space-y-4"
          >
            <div className="border-b border-slate-800 pb-3 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <User className="w-4 h-4 text-sky-400" />
                <h3 className="text-sm font-bold text-white uppercase tracking-wider">
                  1. Executive Identity, Target Roles & Logistics
                </h3>
              </div>
              {currentPersona?.is_common_persona && (
                <span className="text-[10px] text-amber-400 flex items-center gap-1 font-semibold">
                  <Lock className="w-3 h-3" /> Baseline Track Locked
                </span>
              )}
            </div>

            {/* Candidate Contact & Verified PII Card */}
            <div
              data-testid="private-contact-pii-card"
              className="p-3.5 rounded-xl bg-gradient-to-r from-sky-950/40 via-slate-950 to-indigo-950/30 border border-sky-800/40 space-y-3"
            >
              <div className="flex items-center justify-between flex-wrap gap-2">
                <div className="flex items-center gap-1.5">
                  <Shield className="w-3.5 h-3.5 text-sky-400" />
                  <span className="text-xs font-bold text-white tracking-wide">
                    Candidate Contact & Verified PII
                  </span>
                  <span className="text-[10px] px-2 py-0.5 rounded-full bg-sky-500/10 text-sky-300 border border-sky-500/20 font-medium flex items-center gap-1">
                    <Lock className="w-2.5 h-2.5" /> Private to You
                  </span>
                </div>
                <span className="text-[10px] text-slate-400 italic">
                  Encrypted & isolated from vector match queries
                </span>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <div>
                  <label className="block text-[11px] font-medium text-slate-300 mb-1">
                    Full Legal Name
                  </label>
                  <input
                    type="text"
                    data-testid="candidate-fullname-input"
                    value={dossierForm.full_name}
                    onChange={(e) => setDossierForm({ ...dossierForm, full_name: e.target.value })}
                    placeholder="e.g. John Doe"
                    className="w-full px-3 py-1.5 bg-slate-950 border border-slate-700/80 rounded-lg text-xs text-white focus:outline-none focus:border-sky-500"
                  />
                </div>

                <div>
                  <label className="block text-[11px] font-medium text-slate-300 mb-1">
                    Verified Email Address
                  </label>
                  <input
                    type="email"
                    data-testid="candidate-email-input"
                    value={dossierForm.email}
                    onChange={(e) => setDossierForm({ ...dossierForm, email: e.target.value })}
                    placeholder="e.g. candidate@example.com"
                    className="w-full px-3 py-1.5 bg-slate-950 border border-slate-700/80 rounded-lg text-xs text-white focus:outline-none focus:border-sky-500"
                  />
                </div>

                <div>
                  <label className="block text-[11px] font-medium text-slate-300 mb-1">
                    Direct Phone Number
                  </label>
                  <input
                    type="tel"
                    data-testid="candidate-phone-input"
                    value={dossierForm.phone}
                    onChange={(e) => setDossierForm({ ...dossierForm, phone: e.target.value })}
                    placeholder="e.g. +1 (555) 123-4567"
                    className="w-full px-3 py-1.5 bg-slate-950 border border-slate-700/80 rounded-lg text-xs text-white focus:outline-none focus:border-sky-500"
                  />
                </div>
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Track Name</label>
                <input
                  type="text"
                  disabled={currentPersona?.is_common_persona}
                  value={dossierForm.name}
                  onChange={(e) => setDossierForm({ ...dossierForm, name: e.target.value })}
                  className={`w-full px-3 py-2 bg-slate-950 border rounded-xl text-xs text-white ${
                    currentPersona?.is_common_persona
                      ? "border-slate-800 opacity-70 cursor-not-allowed"
                      : "border-slate-700 focus:border-sky-500"
                  }`}
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Seniority Level</label>
                <select
                  value={dossierForm.seniority_level}
                  onChange={(e) => setDossierForm({ ...dossierForm, seniority_level: e.target.value })}
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-xl text-xs text-white focus:outline-none focus:border-sky-500"
                >
                  {SENIORITY_LEVELS.map((sl) => (
                    <option key={sl.value} value={sl.value}>
                      {sl.label}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {/* Headline */}
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Professional Headline</label>
              <input
                type="text"
                value={dossierForm.headline}
                onChange={(e) => setDossierForm({ ...dossierForm, headline: e.target.value })}
                placeholder="e.g. Staff Full Stack Developer (12+ YOE) | Distributed Systems & Platform Engineering"
                className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-xl text-xs text-white focus:outline-none focus:border-sky-500"
              />
            </div>

            {/* Target Job Roles Tag Pills */}
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Target Job Roles</label>
              <div className="flex flex-wrap items-center gap-1.5 p-2 bg-slate-950 border border-slate-800 rounded-xl min-h-[42px]">
                {dossierForm.target_roles.map((role, idx) => (
                  <span
                    key={idx}
                    className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-sky-950/80 text-sky-200 border border-sky-800/60 text-xs font-medium"
                  >
                    <span>{role}</span>
                    <button
                      type="button"
                      onClick={() => removeRoleTag(idx)}
                      className="text-sky-400 hover:text-white"
                    >
                      <X className="w-3 h-3" />
                    </button>
                  </span>
                ))}
                <div className="flex items-center gap-1">
                  <input
                    type="text"
                    placeholder="+ Add Role (e.g. Platform Engineer)"
                    value={newRoleTag}
                    onChange={(e) => setNewRoleTag(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === "Enter") {
                        e.preventDefault();
                        addRoleTag();
                      }
                    }}
                    className="px-2 py-0.5 bg-transparent text-xs text-white placeholder-slate-500 focus:outline-none"
                  />
                  {newRoleTag && (
                    <button
                      type="button"
                      onClick={addRoleTag}
                      className="px-2 py-0.5 rounded bg-sky-600 text-white text-[11px]"
                    >
                      Add
                    </button>
                  )}
                </div>
              </div>
            </div>

            {/* Experience, Min Salary, Visa & Locations */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Years Experience</label>
                <input
                  type="number"
                  min={0}
                  max={50}
                  value={dossierForm.years_experience}
                  onChange={(e) => setDossierForm({ ...dossierForm, years_experience: Number(e.target.value) })}
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-xl text-xs text-white focus:outline-none focus:border-sky-500"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Min Base Salary ($ USD)</label>
                <input
                  type="number"
                  placeholder="e.g. 180000"
                  value={dossierForm.min_salary}
                  onChange={(e) => setDossierForm({ ...dossierForm, min_salary: e.target.value })}
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-xl text-xs text-white focus:outline-none focus:border-sky-500"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Work Authorization</label>
                <select
                  value={dossierForm.visa_status}
                  onChange={(e) => setDossierForm({ ...dossierForm, visa_status: e.target.value })}
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-xl text-xs text-white focus:outline-none focus:border-sky-500"
                >
                  {VISA_STATUS_OPTIONS.map((v) => (
                    <option key={v} value={v}>
                      {v}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {/* External Profile Links */}
            <div className="pt-2 border-t border-slate-800 space-y-2">
              <span className="text-xs font-semibold text-slate-400 flex items-center gap-1.5">
                <LinkIcon className="w-3.5 h-3.5 text-emerald-400" /> Verified Channel Links
              </span>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
                <input
                  type="url"
                  placeholder="LinkedIn URL (https://linkedin.com/in/...)"
                  value={dossierForm.linkedin_url}
                  onChange={(e) => setDossierForm({ ...dossierForm, linkedin_url: e.target.value })}
                  className="px-2.5 py-1.5 bg-slate-950 border border-slate-700 rounded-lg text-xs text-white placeholder-slate-500 focus:outline-none focus:border-sky-500"
                />
                <input
                  type="url"
                  placeholder="GitHub URL (https://github.com/...)"
                  value={dossierForm.github_url}
                  onChange={(e) => setDossierForm({ ...dossierForm, github_url: e.target.value })}
                  className="px-2.5 py-1.5 bg-slate-950 border border-slate-700 rounded-lg text-xs text-white placeholder-slate-500 focus:outline-none focus:border-sky-500"
                />
                <input
                  type="url"
                  placeholder="LeetCode Profile URL"
                  value={dossierForm.leetcode_url}
                  onChange={(e) => setDossierForm({ ...dossierForm, leetcode_url: e.target.value })}
                  className="px-2.5 py-1.5 bg-slate-950 border border-slate-700 rounded-lg text-xs text-white placeholder-slate-500 focus:outline-none focus:border-sky-500"
                />
              </div>
            </div>
          </section>

          {/* Section 2: Business Domain Expertise & Semantic AI Summary */}
          <section
            data-testid="section-domain-and-semantic"
            className="p-5 rounded-2xl bg-slate-900/90 border border-slate-800 shadow-xl space-y-4"
          >
            <div className="border-b border-slate-800 pb-3 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Shield className="w-4 h-4 text-indigo-400" />
                <h3 className="text-sm font-bold text-white uppercase tracking-wider">
                  2. Business Domain Expertise & Semantic AI Summary
                </h3>
              </div>
            </div>

            {/* Business Domain Cards */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-300">
                  Extracted Industry Domain Verticals ({dossierForm.domain_expertise.length})
                </span>
              </div>

              {dossierForm.domain_expertise.length > 0 ? (
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                  {dossierForm.domain_expertise.map((de, idx) => (
                    <div
                      key={idx}
                      className="p-3 rounded-xl bg-slate-950 border border-indigo-500/30 space-y-1.5"
                    >
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-bold text-white">{de.domain}</span>
                        <span className="text-[10px] px-2 py-0.5 rounded-full bg-indigo-500/20 text-indigo-300 font-semibold border border-indigo-500/30">
                          {de.years_experience}y Experience
                        </span>
                      </div>
                      {de.regulatory_frameworks?.length > 0 && (
                        <div className="flex flex-wrap items-center gap-1 pt-0.5">
                          {de.regulatory_frameworks.map((rf, rIdx) => (
                            <span
                              key={rIdx}
                              className="text-[9px] px-1.5 py-0.2 rounded bg-slate-800 text-slate-300 border border-slate-700"
                            >
                              {rf}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-xs text-slate-500 italic">
                  No specialized business domains detected yet. Upload a resume to automatically identify verticals (FinTech, HealthTech, etc.).
                </p>
              )}
            </div>

            {/* Semantic Profile Summary */}
            <div className="pt-2 border-t border-slate-800 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-300 flex items-center gap-1.5">
                  <Database className="w-3.5 h-3.5 text-sky-400" /> Grounded Semantic Matching Vector Summary
                </span>
                <span className="text-[10px] text-slate-400 font-mono">Anti-Drift Synthesis</span>
              </div>
              <textarea
                rows={3}
                value={dossierForm.semantic_profile_summary}
                onChange={(e) => setDossierForm({ ...dossierForm, semantic_profile_summary: e.target.value })}
                placeholder="Dense candidate synthesis vector summary used by pgvector two-stage ranking..."
                className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-xl text-xs text-slate-200 font-mono focus:outline-none focus:border-sky-500"
              />
            </div>
          </section>

          {/* Section 3: Chronological Work Experience Timeline & Nested pgvector Proof Points */}
          <section
            data-testid="section-work-experience"
            className="p-5 rounded-2xl bg-slate-900/90 border border-slate-800 shadow-xl space-y-4"
          >
            <div className="border-b border-slate-800 pb-3 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Briefcase className="w-4 h-4 text-emerald-400" />
                <h3 className="text-sm font-bold text-white uppercase tracking-wider">
                  3. Work Experience Timeline & Achievement Proof Points
                </h3>
              </div>
              <button
                type="button"
                onClick={() => {
                  setEditingRoleIndex(-1); // -1 indicates adding new
                  setRoleForm({
                    company_name: "",
                    job_title: "",
                    location: "Remote",
                    is_remote: true,
                    start_date: "2022",
                    end_date: "Present",
                    seniority_level: "senior",
                    industry_domain: "Cloud & Distributed Systems",
                  });
                }}
                className="text-xs font-semibold text-emerald-400 hover:text-emerald-300 flex items-center gap-1 cursor-pointer"
              >
                <Plus className="w-3.5 h-3.5" /> Add Experience Tenure
              </button>
            </div>

            {/* Role Tenure Form Modal / Inline Editor */}
            {editingRoleIndex !== null && (
              <form onSubmit={handleSaveRoleTenure} className="p-4 rounded-xl bg-slate-950 border border-emerald-500/40 space-y-3">
                <h4 className="text-xs font-bold text-white">
                  {editingRoleIndex === -1 ? "Add Work Experience Tenure" : "Edit Work Experience Tenure"}
                </h4>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <input
                    type="text"
                    required
                    placeholder="Company Name (e.g. Render)"
                    value={roleForm.company_name}
                    onChange={(e) => setRoleForm({ ...roleForm, company_name: e.target.value })}
                    className="px-2.5 py-1.5 bg-slate-900 border border-slate-700 rounded-lg text-xs text-white focus:outline-none focus:border-emerald-500"
                  />
                  <input
                    type="text"
                    required
                    placeholder="Job Title (e.g. Staff Systems Engineer)"
                    value={roleForm.job_title}
                    onChange={(e) => setRoleForm({ ...roleForm, job_title: e.target.value })}
                    className="px-2.5 py-1.5 bg-slate-900 border border-slate-700 rounded-lg text-xs text-white focus:outline-none focus:border-emerald-500"
                  />
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
                  <input
                    type="text"
                    placeholder="Location (e.g. San Francisco, CA)"
                    value={roleForm.location}
                    onChange={(e) => setRoleForm({ ...roleForm, location: e.target.value })}
                    className="px-2.5 py-1.5 bg-slate-900 border border-slate-700 rounded-lg text-xs text-white focus:outline-none"
                  />
                  <input
                    type="text"
                    placeholder="Start Date (e.g. 2021)"
                    value={roleForm.start_date}
                    onChange={(e) => setRoleForm({ ...roleForm, start_date: e.target.value })}
                    className="px-2.5 py-1.5 bg-slate-900 border border-slate-700 rounded-lg text-xs text-white focus:outline-none"
                  />
                  <input
                    type="text"
                    placeholder="End Date (e.g. Present)"
                    value={roleForm.end_date}
                    onChange={(e) => setRoleForm({ ...roleForm, end_date: e.target.value })}
                    className="px-2.5 py-1.5 bg-slate-900 border border-slate-700 rounded-lg text-xs text-white focus:outline-none"
                  />
                </div>
                <div className="flex justify-end gap-2">
                  <button
                    type="button"
                    onClick={() => setEditingRoleIndex(null)}
                    className="px-3 py-1 text-xs text-slate-400 hover:text-white"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="px-3 py-1 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-xs font-semibold"
                  >
                    Save Tenure
                  </button>
                </div>
              </form>
            )}

            {/* Work Experience Timeline */}
            <div className="space-y-4">
              {dossierForm.work_experience.map((exp, expIdx) => {
                // Find matching persisted CV blocks for this tenure:
                // 1) Blocks whose content matches any bullet in this tenure, OR
                // 2) Blocks whose title matches this tenure's title and company matches
                const tenureBulletsTextSet = new Set(
                  (exp.bullets || []).map((b) => (b.raw_text || "").trim().toLowerCase())
                );
                const relatedBlocks = persistedBlocks.filter(
                  (b) =>
                    tenureBulletsTextSet.has((b.content || "").trim().toLowerCase()) ||
                    (b.organization &&
                      exp.company_name &&
                      b.organization.toLowerCase().includes(exp.company_name.toLowerCase()) &&
                      b.title &&
                      exp.job_title &&
                      (b.title.toLowerCase().includes(exp.job_title.toLowerCase()) ||
                        exp.job_title.toLowerCase().includes(b.title.toLowerCase())))
                );

                return (
                  <div
                    key={expIdx}
                    data-testid={`experience-tenure-card-${expIdx}`}
                    className="p-4 rounded-xl bg-slate-950/80 border border-slate-800 space-y-3"
                  >
                    {/* Header of tenure */}
                    <div className="flex items-start justify-between gap-3 flex-wrap">
                      <div>
                        <div className="flex items-center gap-2 flex-wrap">
                          <h4 className="text-sm font-bold text-white">{exp.job_title}</h4>
                          <span className="text-xs font-semibold text-sky-400">@ {exp.company_name}</span>
                          <span className="text-[10px] px-2 py-0.5 rounded-full bg-slate-800 text-slate-300 border border-slate-700">
                            {exp.start_date || "2020"} — {exp.end_date || "Present"}
                          </span>
                        </div>
                        <div className="flex items-center gap-2 text-[11px] text-slate-400 mt-1">
                          <span className="flex items-center gap-1">
                            <MapPin className="w-3 h-3 text-slate-500" /> {exp.location || "Remote"}
                          </span>
                          <span>•</span>
                          <span className="capitalize">{exp.seniority_level || "senior"}</span>
                          {exp.industry_domain && (
                            <>
                              <span>•</span>
                              <span className="text-indigo-300">{exp.industry_domain}</span>
                            </>
                          )}
                        </div>
                      </div>

                      <div className="flex items-center gap-1.5">
                        <button
                          type="button"
                          onClick={() => {
                            setEditingBlock({
                              expIdx,
                              organization: exp.company_name,
                              title: `${exp.job_title} Achievement`,
                              category: "experience",
                            });
                            setBlockForm({
                              title: `${exp.job_title} Achievement`,
                              organization: exp.company_name,
                              category: "experience",
                              content: "",
                              skills: "",
                              metrics: {},
                            });
                          }}
                          className="px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-sky-300 text-[11px] font-semibold border border-slate-700 flex items-center gap-1"
                        >
                          <Plus className="w-3 h-3" /> Add Proof Point
                        </button>
                        <button
                          type="button"
                          onClick={() => {
                            setEditingRoleIndex(expIdx);
                            setRoleForm({ ...exp });
                          }}
                          className="p-1.5 text-slate-400 hover:text-white"
                          title="Edit tenure details"
                        >
                          <Edit2 className="w-3.5 h-3.5" />
                        </button>
                        <button
                          type="button"
                          onClick={() => handleDeleteRoleTenure(expIdx)}
                          className="p-1.5 text-slate-500 hover:text-rose-400"
                          title="Delete tenure"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </div>

                    {/* Bullets & Proof Points under this tenure */}
                    <div className="space-y-2 pt-2 border-t border-slate-850">
                      {(() => {
                        const persistedContentSet = new Set(
                          relatedBlocks.map((b) => (b.content || "").trim().toLowerCase())
                        );
                        const unpersistedBullets = (exp.bullets || []).filter(
                          (b) => !persistedContentSet.has((b.raw_text || "").trim().toLowerCase())
                        );

                        if (relatedBlocks.length === 0 && unpersistedBullets.length === 0) {
                          return (
                            <p className="text-xs text-slate-500 italic py-1">
                              No achievement proof points recorded for this tenure yet. Click "+ Add Proof Point" above.
                            </p>
                          );
                        }

                        return (
                          <>
                            {/* 1. Persisted pgvector CVBlocks matching this company */}
                            {relatedBlocks.map((block) => {
                              const hasMetrics = block.metrics && Object.keys(block.metrics).length > 0;
                              return (
                                <div
                                  key={block.id}
                                  data-testid={`persisted-block-${block.id}`}
                                  className="p-2.5 rounded-lg bg-slate-900/90 border border-slate-800 hover:border-slate-700 space-y-1.5 text-xs text-slate-200 transition-all"
                                >
                                  <div className="flex items-start justify-between gap-2">
                                    <p className="leading-relaxed">{block.content}</p>
                                    <div className="flex items-center gap-1 shrink-0">
                                      <button
                                        type="button"
                                        onClick={() => {
                                          setEditingBlock(block);
                                          setBlockForm({
                                            title: block.title || "",
                                            organization: block.organization || "",
                                            category: block.category || "experience",
                                            content: block.content || "",
                                            skills: (block.skills || []).join(", "),
                                            metrics: block.metrics || {},
                                          });
                                        }}
                                        className="p-1 text-slate-400 hover:text-white"
                                        title="Edit achievement proof point"
                                      >
                                        <Edit2 className="w-3 h-3" />
                                      </button>
                                      <button
                                        type="button"
                                        onClick={() => handleDeleteBlock(block.id)}
                                        className="p-1 text-slate-500 hover:text-rose-400"
                                        title="Delete proof point"
                                      >
                                        <Trash2 className="w-3 h-3" />
                                      </button>
                                    </div>
                                  </div>

                                  {/* Tags: Metrics & Skills */}
                                  <div className="flex flex-wrap items-center gap-1.5 pt-1">
                                    {hasMetrics ? (
                                      Object.entries(block.metrics).map(([k, v], mIdx) => (
                                        <span
                                          key={mIdx}
                                          className="text-[9px] font-bold px-1.5 py-0.2 rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/30"
                                        >
                                          {String(v)}
                                        </span>
                                      ))
                                    ) : (
                                      <span className="text-[9px] font-medium px-1.5 py-0.2 rounded bg-amber-500/10 text-amber-300/80 border border-amber-500/20">
                                        ⚠️ Unquantified impact
                                      </span>
                                    )}

                                    {block.skills?.map((s, sIdx) => (
                                      <span
                                        key={sIdx}
                                        className="text-[9px] px-1.5 py-0.2 rounded bg-slate-800 text-slate-300 border border-slate-700"
                                      >
                                        {s}
                                      </span>
                                    ))}

                                    <span className="text-[9px] px-1.5 py-0.2 rounded bg-indigo-950 text-indigo-300 border border-indigo-800/60 font-mono ml-auto">
                                      🟢 pgvector Embedded
                                    </span>
                                  </div>
                                </div>
                              );
                            })}

                            {/* 2. Unpersisted Staged Bullets from raw parse */}
                            {unpersistedBullets.map((b) => {
                              const origBulletIdx = (exp.bullets || []).findIndex(
                                (orig) =>
                                  (orig.raw_text || "").trim().toLowerCase() ===
                                  (b.raw_text || "").trim().toLowerCase()
                              );
                              return (
                                <div
                                  key={`staged-bullet-${origBulletIdx >= 0 ? origBulletIdx : b.raw_text}`}
                                  data-testid={`staged-bullet-${origBulletIdx >= 0 ? origBulletIdx : 0}`}
                                  className="p-2.5 rounded-lg bg-slate-900/90 border border-amber-500/30 space-y-1.5 text-xs text-slate-200"
                                >
                                  <div className="flex items-start justify-between gap-2">
                                    <p className="leading-relaxed">{b.raw_text}</p>
                                    <div className="flex items-center gap-1 shrink-0">
                                      <button
                                        type="button"
                                        onClick={() =>
                                          handleEditStagedBullet(exp, b, expIdx, origBulletIdx)
                                        }
                                        className="p-1 text-slate-400 hover:text-white"
                                        title="Edit achievement proof point"
                                      >
                                        <Edit2 className="w-3 h-3" />
                                      </button>
                                      <button
                                        type="button"
                                        onClick={() =>
                                          handleDeleteStagedBullet(expIdx, origBulletIdx)
                                        }
                                        className="p-1 text-slate-500 hover:text-rose-400"
                                        title="Delete proof point"
                                      >
                                        <Trash2 className="w-3 h-3" />
                                      </button>
                                    </div>
                                  </div>
                                  <div className="flex flex-wrap items-center gap-1 pt-1">
                                    {b.technologies_used?.map((tech, tIdx) => (
                                      <span
                                        key={tIdx}
                                        className="text-[9px] px-1.5 py-0.2 rounded bg-sky-950 text-sky-300 border border-sky-800/60 font-medium"
                                      >
                                        {tech}
                                      </span>
                                    ))}
                                    <span className="text-[9px] px-1.5 py-0.2 rounded bg-amber-500/10 text-amber-300 border border-amber-500/20 font-mono ml-auto">
                                      Staged — Click "Save Career Dossier" to Embed
                                    </span>
                                  </div>
                                </div>
                              );
                            })}
                          </>
                        );
                      })()}
                    </div>
                  </div>
                );
              })}

              {dossierForm.work_experience.length === 0 && (
                <p className="text-xs text-slate-500 italic text-center py-4">
                  No work experience recorded. Click "Add Experience Tenure" or upload a resume to populate.
                </p>
              )}
            </div>
          </section>

          {/* Section 4: Multi-Degree Education & Prestige Tier Cards */}
          <section
            data-testid="section-education"
            className="p-5 rounded-2xl bg-slate-900/90 border border-slate-800 shadow-xl space-y-4"
          >
            <div className="border-b border-slate-800 pb-3 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <GraduationCap className="w-4 h-4 text-sky-400" />
                <h3 className="text-sm font-bold text-white uppercase tracking-wider">
                  4. Multi-Degree Education & Academic Pedigree
                </h3>
              </div>
              <button
                type="button"
                onClick={() => {
                  setEditingEduIndex(-1);
                  setEduForm({
                    degree: "Master of Science",
                    major: "Management Information Systems",
                    institution: "",
                    institution_tier: "standard",
                    graduation_year: 2025,
                    gpa: "",
                    honors: "",
                  });
                }}
                className="text-xs font-semibold text-sky-400 hover:text-sky-300 flex items-center gap-1 cursor-pointer"
              >
                <Plus className="w-3.5 h-3.5" /> Add Education Credential
              </button>
            </div>

            {/* Education Form Modal / Inline Editor */}
            {editingEduIndex !== null && (
              <form onSubmit={handleSaveEducation} className="p-4 rounded-xl bg-slate-950 border border-sky-500/40 space-y-3">
                <h4 className="text-xs font-bold text-white">
                  {editingEduIndex === -1 ? "Add Academic Credential" : "Edit Academic Credential"}
                </h4>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
                  <input
                    type="text"
                    required
                    placeholder="Degree (e.g. Master of Science)"
                    value={eduForm.degree}
                    onChange={(e) => setEduForm({ ...eduForm, degree: e.target.value })}
                    className="px-2.5 py-1.5 bg-slate-900 border border-slate-700 rounded-lg text-xs text-white focus:outline-none"
                  />
                  <input
                    type="text"
                    required
                    placeholder="Major (e.g. Computer Science)"
                    value={eduForm.major}
                    onChange={(e) => setEduForm({ ...eduForm, major: e.target.value })}
                    className="px-2.5 py-1.5 bg-slate-900 border border-slate-700 rounded-lg text-xs text-white focus:outline-none"
                  />
                  <input
                    type="text"
                    required
                    placeholder="Institution (e.g. Stanford University)"
                    value={eduForm.institution}
                    onChange={(e) => setEduForm({ ...eduForm, institution: e.target.value })}
                    className="px-2.5 py-1.5 bg-slate-900 border border-slate-700 rounded-lg text-xs text-white focus:outline-none"
                  />
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
                  <input
                    type="number"
                    placeholder="Graduation Year (e.g. 2025)"
                    value={eduForm.graduation_year}
                    onChange={(e) => setEduForm({ ...eduForm, graduation_year: e.target.value })}
                    className="px-2.5 py-1.5 bg-slate-900 border border-slate-700 rounded-lg text-xs text-white focus:outline-none"
                  />
                  <select
                    value={eduForm.institution_tier}
                    onChange={(e) => setEduForm({ ...eduForm, institution_tier: e.target.value })}
                    className="px-2.5 py-1.5 bg-slate-900 border border-slate-700 rounded-lg text-xs text-white focus:outline-none"
                  >
                    <option value="standard">Standard University</option>
                    <option value="tier_2">Tier 2 Top 50 University</option>
                    <option value="tier_1">Tier 1 Target School (MIT, Stanford, CMU...)</option>
                  </select>
                  <input
                    type="text"
                    placeholder="GPA / Honors (e.g. 3.9 / Cum Laude)"
                    value={eduForm.gpa}
                    onChange={(e) => setEduForm({ ...eduForm, gpa: e.target.value })}
                    className="px-2.5 py-1.5 bg-slate-900 border border-slate-700 rounded-lg text-xs text-white focus:outline-none"
                  />
                </div>
                <div className="flex justify-end gap-2">
                  <button
                    type="button"
                    onClick={() => setEditingEduIndex(null)}
                    className="px-3 py-1 text-xs text-slate-400 hover:text-white"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="px-3 py-1 bg-sky-600 hover:bg-sky-500 text-white rounded-lg text-xs font-semibold"
                  >
                    Save Credential
                  </button>
                </div>
              </form>
            )}

            {/* Education Cards Grid */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {dossierForm.education.map((edu, eduIdx) => (
                <div
                  key={eduIdx}
                  data-testid={`education-card-${eduIdx}`}
                  className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 space-y-1.5 relative group"
                >
                  <div className="flex items-start justify-between">
                    <div>
                      <h4 className="text-xs font-bold text-white">{edu.degree}</h4>
                      <p className="text-[11px] font-semibold text-sky-300">{edu.major}</p>
                      <p className="text-[11px] text-slate-400">{edu.institution}</p>
                    </div>
                    <div className="flex items-center gap-1">
                      <button
                        type="button"
                        onClick={() => {
                          setEditingEduIndex(eduIdx);
                          setEduForm({ ...edu });
                        }}
                        className="p-1 text-slate-400 hover:text-white"
                      >
                        <Edit2 className="w-3 h-3" />
                      </button>
                      <button
                        type="button"
                        onClick={() => handleDeleteEducation(eduIdx)}
                        className="p-1 text-slate-500 hover:text-rose-400"
                      >
                        <Trash2 className="w-3 h-3" />
                      </button>
                    </div>
                  </div>
                  <div className="flex items-center gap-2 pt-1 text-[10px] text-slate-400">
                    <span>Class of {edu.graduation_year || "N/A"}</span>
                    <span>•</span>
                    <span className="capitalize">{edu.institution_tier?.replace("_", " ") || "Standard"}</span>
                    {edu.gpa && (
                      <>
                        <span>•</span>
                        <span className="text-emerald-400">{edu.gpa}</span>
                      </>
                    )}
                  </div>
                </div>
              ))}

              {dossierForm.education.length === 0 && (
                <p className="col-span-2 text-xs text-slate-500 italic text-center py-4">
                  No academic degrees listed. Add your credentials to boost pedigree matching signals.
                </p>
              )}
            </div>
          </section>

          {/* Section 5: Categorized Technical Skills Matrix */}
          <section
            data-testid="section-skills-matrix"
            className="p-5 rounded-2xl bg-slate-900/90 border border-slate-800 shadow-xl space-y-4"
          >
            <div className="border-b border-slate-800 pb-3 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Tag className="w-4 h-4 text-sky-400" />
                <h3 className="text-sm font-bold text-white uppercase tracking-wider">
                  5. Technical Skills Matrix ({dossierForm.skills.length})
                </h3>
              </div>
            </div>

            {/* Quick Add Skill Pill */}
            <div className="flex items-center gap-2">
              <input
                type="text"
                placeholder="+ Add Skill Tag (e.g. LangGraph, pgvector, PyTorch)"
                value={newSkillTag}
                onChange={(e) => setNewSkillTag(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") {
                    e.preventDefault();
                    addSkillTag();
                  }
                }}
                className="flex-1 px-3 py-1.5 bg-slate-950 border border-slate-700 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none focus:border-sky-500"
              />
              <button
                type="button"
                onClick={() => addSkillTag()}
                className="px-3.5 py-1.5 rounded-xl bg-sky-600 hover:bg-sky-500 text-white text-xs font-semibold cursor-pointer"
              >
                Add Skill
              </button>
            </div>

            {/* Categorized Matrix Pills */}
            <div className="space-y-3">
              {SKILL_CATEGORIES.map((cat) => {
                const catSkills = dossierForm.skills_matrix?.[cat.key] || [];
                return (
                  <div key={cat.key} className="space-y-1.5">
                    <span className="text-[11px] font-semibold text-slate-400">{cat.label}</span>
                    <div className="flex flex-wrap items-center gap-1.5">
                      {catSkills.length > 0 ? (
                        catSkills.map((sk, sIdx) => (
                          <span
                            key={sIdx}
                            className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-lg bg-slate-950 text-slate-200 border border-slate-800 text-xs font-medium"
                          >
                            <span>{sk}</span>
                            <button
                              type="button"
                              onClick={() => removeSkillTag(sk)}
                              className="text-slate-500 hover:text-white"
                            >
                              <X className="w-3 h-3" />
                            </button>
                          </span>
                        ))
                      ) : (
                        <span className="text-[10px] text-slate-600 italic">None specified</span>
                      )}
                    </div>
                  </div>
                );
              })}

              {/* All Other Uncategorized Skills */}
              {(() => {
                const categorizedSet = new Set(
                  Object.values(dossierForm.skills_matrix || {}).flat()
                );
                const uncategorized = dossierForm.skills.filter((s) => !categorizedSet.has(s));
                if (uncategorized.length === 0) return null;

                return (
                  <div className="space-y-1.5 pt-2 border-t border-slate-800">
                    <span className="text-[11px] font-semibold text-slate-400">All Other Domain Tools & Technologies</span>
                    <div className="flex flex-wrap items-center gap-1.5">
                      {uncategorized.map((sk, sIdx) => (
                        <span
                          key={sIdx}
                          className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-lg bg-sky-950/60 text-sky-200 border border-sky-800/60 text-xs font-medium"
                        >
                          <span>{sk}</span>
                          <button
                            type="button"
                            onClick={() => removeSkillTag(sk)}
                            className="text-sky-400 hover:text-white"
                          >
                            <X className="w-3 h-3" />
                          </button>
                        </span>
                      ))}
                    </div>
                  </div>
                );
              })()}
            </div>
          </section>

          {/* Section 6: Projects, Hackathons & Awards */}
          <section
            data-testid="section-projects-awards"
            className="p-5 rounded-2xl bg-slate-900/90 border border-slate-800 shadow-xl space-y-4"
          >
            <div className="border-b border-slate-800 pb-3 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Award className="w-4 h-4 text-amber-400" />
                <h3 className="text-sm font-bold text-white uppercase tracking-wider">
                  6. Technical Projects, Hackathons & Honors
                </h3>
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {/* Projects List */}
              <div className="space-y-2">
                <span className="text-xs font-semibold text-slate-300 flex items-center gap-1.5">
                  <FolderGit2 className="w-3.5 h-3.5 text-indigo-400" /> Open Source & Projects
                </span>
                {dossierForm.projects.length > 0 ? (
                  dossierForm.projects.map((prj, pIdx) => (
                    <div key={pIdx} className="p-3 rounded-xl bg-slate-950 border border-slate-800 space-y-1 text-xs">
                      <span className="font-bold text-white">{prj.name}</span>
                      <p className="text-[11px] text-slate-400">{prj.description}</p>
                    </div>
                  ))
                ) : (
                  <p className="text-[11px] text-slate-500 italic">No independent projects logged.</p>
                )}
              </div>

              {/* Hackathons & Awards */}
              <div className="space-y-2">
                <span className="text-xs font-semibold text-slate-300 flex items-center gap-1.5">
                  <Award className="w-3.5 h-3.5 text-amber-400" /> Competitions & Honors
                </span>
                {dossierForm.awards_recognitions.length > 0 ? (
                  dossierForm.awards_recognitions.map((aw, aIdx) => (
                    <div key={aIdx} className="p-3 rounded-xl bg-slate-950 border border-amber-500/20 space-y-1 text-xs">
                      <span className="font-bold text-amber-300">{aw.title}</span>
                      {aw.description && <p className="text-[11px] text-slate-400">{aw.description}</p>}
                    </div>
                  ))
                ) : (
                  <p className="text-[11px] text-slate-500 italic">No awards or hackathons logged.</p>
                )}
              </div>
            </div>
          </section>
        </div>
      </div>

      {/* Slide-Out Raw Source Text Inspector Drawer */}
      {showRawInspector && (
        <div
          data-testid="raw-source-inspector-drawer"
          className="fixed inset-0 z-50 flex items-center justify-end bg-slate-950/80 backdrop-blur-sm animate-in fade-in duration-200"
        >
          <div className="w-full max-w-xl h-full bg-slate-900 border-l border-slate-800 shadow-2xl flex flex-col p-6 space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <div className="flex items-center gap-2">
                <FileSearch className="w-5 h-5 text-sky-400" />
                <h3 className="text-sm font-bold text-white">Extracted Source Text Inspector</h3>
              </div>
              <button
                type="button"
                onClick={() => setShowRawInspector(false)}
                className="p-1 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="flex items-center gap-2 text-[10px] text-slate-400 flex-wrap">
              <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
                Source: {dossierForm.source_provenance?.filename || "Extracted Document"}
              </span>
              <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
                Layout: {dossierForm.source_provenance?.layout_type || "Standard"}
              </span>
              <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
                Pipeline: {dossierForm.source_provenance?.recommended_pipeline || "LLM Structured"}
              </span>
            </div>

            <p className="text-xs text-slate-400">
              Verbatim positional text extracted from your document. You can verify here whether layout columns or dates were parsed properly.
            </p>

            <div className="flex-1 overflow-y-auto p-4 bg-slate-950 border border-slate-800 rounded-xl font-mono text-[11px] text-slate-300 leading-relaxed whitespace-pre-wrap select-all">
              {dossierForm.source_provenance?.raw_text ||
                stagedReview?.rawText ||
                "No verbatim raw text available for this profile."}
            </div>

            <div className="flex justify-end gap-2 pt-2 border-t border-slate-800">
              <button
                type="button"
                onClick={() => {
                  const txt = dossierForm.source_provenance?.raw_text || stagedReview?.rawText || "";
                  navigator.clipboard.writeText(txt);
                  setCopiedRawText(true);
                  setTimeout(() => setCopiedRawText(false), 2000);
                }}
                className="px-3.5 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold flex items-center gap-1.5"
              >
                {copiedRawText ? <CheckCheck className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                <span>{copiedRawText ? "Copied!" : "Copy Raw Text"}</span>
              </button>
              <button
                type="button"
                onClick={() => setShowRawInspector(false)}
                className="px-4 py-1.5 rounded-xl bg-sky-600 hover:bg-sky-500 text-white text-xs font-bold"
              >
                Close Inspector
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Paste Profile Text Modal */}
      {showPasteModal && (
        <div
          data-testid="paste-text-modal"
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-in fade-in duration-150"
        >
          <div className="w-full max-w-xl bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl p-5 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-2.5">
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <FileText className="w-4 h-4 text-indigo-400" /> Paste Raw Resume or LinkedIn Text
              </h3>
              <button
                type="button"
                onClick={() => setShowPasteModal(false)}
                className="text-slate-400 hover:text-white"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <textarea
              rows={8}
              value={pastedText}
              onChange={(e) => setPastedText(e.target.value)}
              placeholder="Paste your raw resume text, LinkedIn profile export, or CV contents here..."
              className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-xl text-xs text-white placeholder-slate-500 font-mono focus:outline-none focus:border-indigo-500"
            />

            <div className="flex justify-end gap-2">
              <button
                type="button"
                onClick={() => setShowPasteModal(false)}
                className="px-3 py-1.5 text-xs text-slate-400 hover:text-white"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handlePasteSubmit}
                disabled={parsingResume || !pastedText.trim()}
                className="px-4 py-1.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold disabled:opacity-50 flex items-center gap-1.5"
              >
                {parsingResume ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Sparkles className="w-3.5 h-3.5" />}
                <span>Parse & Stage Extraction</span>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Inline Proof Point (CVBlock) Editor Modal */}
      {editingBlock && (
        <div
          data-testid="block-editor-modal"
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-in fade-in duration-150"
        >
          <div className="w-full max-w-lg bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl p-5 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-2.5">
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-sky-400" />
                {editingBlock.id || editingBlock.isStaged ? "Edit Achievement Proof Point" : "New Achievement Proof Point"}
              </h3>
              <button
                type="button"
                onClick={() => setEditingBlock(null)}
                className="text-slate-400 hover:text-white"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleSaveBlock} className="space-y-3">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Company / Organization</label>
                <input
                  type="text"
                  placeholder="e.g. Render"
                  value={blockForm.organization}
                  onChange={(e) => setBlockForm({ ...blockForm, organization: e.target.value })}
                  className="w-full px-2.5 py-1.5 bg-slate-950 border border-slate-700 rounded-lg text-xs text-white focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Achievement Bullet Content</label>
                <textarea
                  rows={4}
                  required
                  placeholder="e.g. Architected distributed payment processing engine scaling to 10k ops/sec with PostgreSQL and Redis."
                  value={blockForm.content}
                  onChange={(e) => setBlockForm({ ...blockForm, content: e.target.value })}
                  className="w-full px-2.5 py-1.5 bg-slate-950 border border-slate-700 rounded-lg text-xs text-white focus:outline-none focus:border-sky-500 font-sans"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Skills Used (comma-separated)</label>
                <input
                  type="text"
                  placeholder="e.g. Python, PostgreSQL, Redis, Kafka"
                  value={blockForm.skills}
                  onChange={(e) => setBlockForm({ ...blockForm, skills: e.target.value })}
                  className="w-full px-2.5 py-1.5 bg-slate-950 border border-slate-700 rounded-lg text-xs text-white focus:outline-none"
                />
              </div>

              <div className="flex justify-end gap-2 pt-2 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setEditingBlock(null)}
                  className="px-3 py-1.5 text-xs text-slate-400 hover:text-white"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-1.5 bg-sky-600 hover:bg-sky-500 text-white rounded-lg text-xs font-semibold"
                >
                  Save & Embed Block
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

export default CandidatePersonaPage;

