import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  Upload,
  FileText,
  Sparkles,
  Trophy,
  CheckCircle2,
  Trash2,
  ArrowRight,
  ArrowLeft,
  Plus,
  ShieldCheck,
  Briefcase,
  Layers,
} from "lucide-react";
import {
  parseResumeDocument,
  parseResumeText,
  onboardCandidate,
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

const SENIORITY_LEVELS = ["intern", "junior", "mid", "senior", "lead", "staff"];

const POPULAR_SKILLS = [
  "Python",
  "Go",
  "FastAPI",
  "Django",
  "Kafka",
  "PostgreSQL",
  "Redis",
  "Docker",
  "Kubernetes",
  "AWS",
  "GCP",
  "LangGraph",
  "LangChain",
  "TypeScript",
  "React",
];

export function OnboardingWizard() {
  const navigate = useNavigate();

  // Mode: 'choose', 'upload', 'paste', 'guided', 'verify'
  const [mode, setMode] = useState("choose");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Form State
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [visaStatus, setVisaStatus] = useState("Citizen");
  const [locations, setLocations] = useState(["Remote"]);
  const [remotePref, setRemotePref] = useState("Remote");
  const [targetRoles, setTargetRoles] = useState(["Senior Software Engineer"]);
  const [yearsExperience, setYearsExperience] = useState(4);
  const [seniorityLevel, setSeniorityLevel] = useState("mid");
  const [skills, setSkills] = useState(["Python", "PostgreSQL", "Docker"]);
  const [skillInput, setSkillInput] = useState("");
  const [roleInput, setRoleInput] = useState("");
  const [blocks, setBlocks] = useState([]);

  // Paste Text state
  const [pastedText, setPastedText] = useState("");

  // Guided Wizard Step (1 to 5)
  const [guidedStep, setGuidedStep] = useState(1);
  const [guidedExpTitle, setGuidedExpTitle] = useState("");
  const [guidedExpOrg, setGuidedExpOrg] = useState("");
  const [guidedExpAction, setGuidedExpAction] = useState("");
  const [guidedExpResult, setGuidedExpResult] = useState("");

  const [guidedHackName, setGuidedHackName] = useState("");
  const [guidedHackPlacement, setGuidedHackPlacement] = useState("1st Place");
  const [guidedHackDesc, setGuidedHackDesc] = useState("");

  // Specialized Persona state in verification
  const [createAiPersona, setCreateAiPersona] = useState(true);

  // 1. Handle Document Upload
  async function handleFileUpload(e) {
    const file = e.target.files?.[0];
    if (!file) return;

    try {
      setLoading(true);
      setError(null);
      const data = await parseResumeDocument(file);
      applyParsedData(data);
      setMode("verify");
    } catch (err) {
      console.error("Upload parse error:", err);
      setError("Failed to parse resume document. Please try pasting text instead.");
    } finally {
      setLoading(false);
    }
  }

  // 2. Handle Text Paste
  async function handleTextPasteSubmit() {
    if (!pastedText || pastedText.length < 20) {
      setError("Please paste at least 20 characters of resume or LinkedIn text.");
      return;
    }

    try {
      setLoading(true);
      setError(null);
      const data = await parseResumeText(pastedText);
      applyParsedData(data);
      setMode("verify");
    } catch (err) {
      console.error("Paste parse error:", err);
      setError("Failed to parse text. Please check format and retry.");
    } finally {
      setLoading(false);
    }
  }

  function applyParsedData(data) {
    if (data.full_name && data.full_name !== "Candidate") {
      setFullName(data.full_name);
    }
    if (data.email) setEmail(data.email);
    if (data.skills && data.skills.length > 0) {
      setSkills(Array.from(new Set([...skills, ...data.skills])));
    }
    if (data.blocks && data.blocks.length > 0) {
      setBlocks(data.blocks);
    }
  }

  // 3. Guided Wizard Handlers
  function addGuidedExperienceBlock() {
    if (!guidedExpTitle || !guidedExpOrg) return;
    const content = `${guidedExpTitle} at ${guidedExpOrg}. Action: ${guidedExpAction}. Result: ${guidedExpResult}`;
    const newBlock = {
      category: "work_experience",
      title: guidedExpTitle,
      organization: guidedExpOrg,
      content,
      metrics: guidedExpResult ? { percentage_impact: guidedExpResult } : {},
      skills: skills.slice(0, 3),
    };
    setBlocks([...blocks, newBlock]);
    setGuidedExpTitle("");
    setGuidedExpOrg("");
    setGuidedExpAction("");
    setGuidedExpResult("");
  }

  function addGuidedHackathonBlock() {
    if (!guidedHackName) return;
    const content = `${guidedHackPlacement} at ${guidedHackName}. ${guidedHackDesc}`;
    const newBlock = {
      category: "hackathon_achievement",
      title: `${guidedHackPlacement} - ${guidedHackName}`,
      organization: guidedHackName,
      content,
      metrics: {
        placement: guidedHackPlacement,
        honor_placement: guidedHackPlacement,
      },
      skills: skills.slice(0, 3),
    };
    setBlocks([...blocks, newBlock]);
    setGuidedHackName("");
    setGuidedHackDesc("");
  }

  function toggleSkill(skill) {
    if (skills.includes(skill)) {
      setSkills(skills.filter((s) => s !== skill));
    } else {
      setSkills([...skills, skill]);
    }
  }

  function addCustomSkill() {
    if (skillInput.trim() && !skills.includes(skillInput.trim())) {
      setSkills([...skills, skillInput.trim()]);
      setSkillInput("");
    }
  }

  function addTargetRole() {
    if (roleInput.trim() && !targetRoles.includes(roleInput.trim())) {
      setTargetRoles([...targetRoles, roleInput.trim()]);
      setRoleInput("");
    }
  }

  function removeBlock(index) {
    setBlocks(blocks.filter((_, idx) => idx !== index));
  }

  // 4. Final Submission
  async function handleFinalSubmit() {
    try {
      setLoading(true);
      setError(null);

      const specializedPersonas = [];
      if (createAiPersona) {
        specializedPersonas.push({
          name: "AI & Distributed Systems Specialist",
          headline: `${fullName || "Candidate"} — AI & Distributed Systems Specialist`,
          target_roles: ["AI Platform Engineer", "Machine Learning Systems Engineer"],
          target_industries: ["technology_software", "ai_ml_infra"],
          seniority_level: seniorityLevel,
          years_experience: yearsExperience,
          skills: skills.filter((s) =>
            ["Python", "Kafka", "Docker", "LangGraph", "FastAPI", "Go", "AWS"].includes(s)
          ),
        });
      }

      const payload = {
        full_name: fullName || "Candidate",
        visa_status: visaStatus,
        citizenship_country_code: "US",
        preferred_locations: locations,
        remote_preference: remotePref,
        target_roles: targetRoles,
        target_industries: ["technology_software"],
        years_experience: Number(yearsExperience),
        seniority_level: seniorityLevel,
        skills,
        blocks,
        specialized_personas: specializedPersonas,
      };

      await onboardCandidate(payload);
      navigate("/");
    } catch (err) {
      console.error("Onboarding failed:", err);
      setError("Onboarding submission failed. Please verify inputs and retry.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="max-w-4xl mx-auto px-4 py-8 space-y-8">
      {/* Step Header */}
      <div className="text-center space-y-2">
        <span className="text-xs font-bold uppercase tracking-wider text-sky-400">
          Career-OS Onboarding
        </span>
        <h1 className="text-3xl font-extrabold text-white">
          Build Your Multi-Persona Candidate Profile
        </h1>
        <p className="text-sm text-slate-400 max-w-lg mx-auto">
          We extract your atomic career blocks, quantified STAR proof points, and achievements to calculate true hiring match probabilities.
        </p>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-400 text-sm">
          {error}
        </div>
      )}

      {/* Mode Selection */}
      {mode === "choose" && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-5 pt-4">
          {/* Card 1: Resume Upload */}
          <div
            onClick={() => setMode("upload")}
            className="p-6 rounded-2xl bg-slate-850 hover:bg-slate-800 border border-slate-750 hover:border-sky-500/50 cursor-pointer transition-all shadow-lg group flex flex-col justify-between"
          >
            <div>
              <div className="p-3 rounded-xl bg-sky-500/10 text-sky-400 w-fit mb-4 group-hover:scale-110 transition-transform">
                <Upload className="w-6 h-6" />
              </div>
              <h3 className="text-base font-bold text-white">Upload Resume / CV</h3>
              <p className="text-xs text-slate-400 mt-2 leading-relaxed">
                PDF or Word DOCX. Position-aware text parsing preserves column layouts without merging errors.
              </p>
            </div>
            <span className="mt-6 text-xs font-semibold text-sky-400 flex items-center gap-1">
              Upload file <ArrowRight className="w-3.5 h-3.5" />
            </span>
          </div>

          {/* Card 2: LinkedIn PDF / Paste */}
          <div
            onClick={() => setMode("paste")}
            className="p-6 rounded-2xl bg-slate-850 hover:bg-slate-800 border border-slate-750 hover:border-indigo-500/50 cursor-pointer transition-all shadow-lg group flex flex-col justify-between"
          >
            <div>
              <div className="p-3 rounded-xl bg-indigo-500/10 text-indigo-400 w-fit mb-4 group-hover:scale-110 transition-transform">
                <FileText className="w-6 h-6" />
              </div>
              <h3 className="text-base font-bold text-white">Paste Text / LinkedIn</h3>
              <p className="text-xs text-slate-400 mt-2 leading-relaxed">
                Paste your LinkedIn "Save to PDF" text or profile summary directly into our layout normalizer.
              </p>
            </div>
            <span className="mt-6 text-xs font-semibold text-indigo-400 flex items-center gap-1">
              Paste profile <ArrowRight className="w-3.5 h-3.5" />
            </span>
          </div>

          {/* Card 3: Interactive Guided Form */}
          <div
            onClick={() => setMode("guided")}
            className="p-6 rounded-2xl bg-slate-850 hover:bg-slate-800 border border-slate-750 hover:border-amber-500/50 cursor-pointer transition-all shadow-lg group flex flex-col justify-between"
          >
            <div>
              <div className="p-3 rounded-xl bg-amber-500/10 text-amber-400 w-fit mb-4 group-hover:scale-110 transition-transform">
                <Sparkles className="w-6 h-6" />
              </div>
              <h3 className="text-base font-bold text-white">Guided 5-Step Wizard</h3>
              <p className="text-xs text-slate-400 mt-2 leading-relaxed">
                No existing resume? Our step-by-step STAR prompt captures projects, hackathons, and skills cleanly.
              </p>
            </div>
            <span className="mt-6 text-xs font-semibold text-amber-400 flex items-center gap-1">
              Start wizard <ArrowRight className="w-3.5 h-3.5" />
            </span>
          </div>
        </div>
      )}

      {/* Mode: Upload */}
      {mode === "upload" && (
        <div className="p-8 rounded-2xl bg-slate-850 border border-slate-800 text-center space-y-6">
          <div className="w-16 h-16 rounded-2xl bg-sky-500/10 text-sky-400 flex items-center justify-center mx-auto">
            <Upload className="w-8 h-8" />
          </div>
          <div>
            <h3 className="text-lg font-bold text-white">Upload Your Resume</h3>
            <p className="text-xs text-slate-400 mt-1">
              Supports .pdf and .docx. Extracted blocks will be staged for your review.
            </p>
          </div>

          <label className="inline-block px-6 py-3 rounded-xl bg-sky-500 hover:bg-sky-400 text-white font-semibold text-xs cursor-pointer shadow-lg shadow-sky-500/20 transition-all">
            Choose Resume File
            <input
              type="file"
              accept=".pdf,.docx"
              onChange={handleFileUpload}
              className="hidden"
            />
          </label>

          <div className="pt-4 border-t border-slate-800">
            <button
              onClick={() => setMode("choose")}
              className="text-xs text-slate-400 hover:text-white"
            >
              ← Back to options
            </button>
          </div>
        </div>
      )}

      {/* Mode: Paste Text */}
      {mode === "paste" && (
        <div className="p-6 rounded-2xl bg-slate-850 border border-slate-800 space-y-4">
          <div>
            <h3 className="text-base font-bold text-white">Paste Profile or Resume Text</h3>
            <p className="text-xs text-slate-400 mt-1">
              Paste your resume or LinkedIn "Save to PDF" contents below.
            </p>
          </div>

          <textarea
            rows={10}
            value={pastedText}
            onChange={(e) => setPastedText(e.target.value)}
            placeholder="Jane Doe&#10;Software Engineer&#10;Experience: Senior Engineer at CloudCo..."
            className="w-full p-4 rounded-xl bg-slate-900 border border-slate-800 text-slate-200 font-mono text-xs focus:outline-none focus:border-sky-500 transition-colors"
          />

          <div className="flex items-center justify-between pt-2">
            <button
              onClick={() => setMode("choose")}
              className="text-xs text-slate-400 hover:text-white"
            >
              ← Back to options
            </button>
            <button
              onClick={handleTextPasteSubmit}
              disabled={loading}
              className="px-5 py-2.5 rounded-xl bg-sky-500 hover:bg-sky-400 text-white font-semibold text-xs shadow-md transition-all flex items-center gap-1.5"
            >
              {loading ? "Analyzing..." : "Parse & Verify Blocks"}
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      )}

      {/* Mode: Guided Wizard (5 steps) */}
      {mode === "guided" && (
        <div className="p-6 rounded-2xl bg-slate-850 border border-slate-800 space-y-6">
          {/* Step indicator */}
          <div className="flex items-center justify-between pb-4 border-b border-slate-800 text-xs">
            <span className="font-bold text-sky-400">Step {guidedStep} of 5</span>
            <span className="text-slate-500">
              {guidedStep === 1 && "Work Authorization & Basics"}
              {guidedStep === 2 && "Target Career Roles"}
              {guidedStep === 3 && "Key Experience (STAR)"}
              {guidedStep === 4 && "Hackathons & Achievements"}
              {guidedStep === 5 && "Technical Skills"}
            </span>
          </div>

          {/* Step 1: Work Auth */}
          {guidedStep === 1 && (
            <div className="space-y-4">
              <div>
                <label className="text-xs font-bold text-slate-300 block mb-1">
                  Full Name
                </label>
                <input
                  type="text"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  placeholder="e.g. Alex Chen"
                  className="w-full p-2.5 rounded-xl bg-slate-900 border border-slate-800 text-sm text-white"
                />
              </div>

              <div>
                <label className="text-xs font-bold text-slate-300 block mb-1">
                  Visa / Work Authorization Status
                </label>
                <select
                  value={visaStatus}
                  onChange={(e) => setVisaStatus(e.target.value)}
                  className="w-full p-2.5 rounded-xl bg-slate-900 border border-slate-800 text-sm text-white"
                >
                  {VISA_STATUS_OPTIONS.map((opt) => (
                    <option key={opt} value={opt}>
                      {opt}
                    </option>
                  ))}
                </select>
                <p className="text-[11px] text-slate-500 mt-1">
                  Used for Bayesian uncertainty matching (never blindly blacklists unconfirmed roles).
                </p>
              </div>

              <div>
                <label className="text-xs font-bold text-slate-300 block mb-1">
                  Workplace Preference
                </label>
                <div className="flex gap-2">
                  {["Remote", "Hybrid", "On-site"].map((p) => (
                    <button
                      key={p}
                      onClick={() => setRemotePref(p)}
                      className={`px-4 py-2 rounded-xl text-xs font-semibold border ${
                        remotePref === p
                          ? "bg-sky-500/20 border-sky-500 text-sky-300"
                          : "bg-slate-900 border-slate-800 text-slate-400"
                      }`}
                    >
                      {p}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Step 2: Target Roles */}
          {guidedStep === 2 && (
            <div className="space-y-4">
              <div>
                <label className="text-xs font-bold text-slate-300 block mb-1">
                  Target Job Titles
                </label>
                <div className="flex gap-2 mb-2">
                  <input
                    type="text"
                    value={roleInput}
                    onChange={(e) => setRoleInput(e.target.value)}
                    placeholder="e.g. Distributed Systems Engineer"
                    className="flex-1 p-2.5 rounded-xl bg-slate-900 border border-slate-800 text-sm text-white"
                  />
                  <button
                    onClick={addTargetRole}
                    className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white rounded-xl text-xs font-semibold"
                  >
                    Add
                  </button>
                </div>
                <div className="flex flex-wrap gap-1.5">
                  {targetRoles.map((r, i) => (
                    <span
                      key={i}
                      className="px-2.5 py-1 rounded-lg bg-sky-500/15 text-sky-300 border border-sky-500/30 text-xs font-medium"
                    >
                      {r}
                    </span>
                  ))}
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-xs font-bold text-slate-300 block mb-1">
                    Years of Relevant Experience
                  </label>
                  <input
                    type="number"
                    min="0"
                    max="30"
                    value={yearsExperience}
                    onChange={(e) => setYearsExperience(e.target.value)}
                    className="w-full p-2.5 rounded-xl bg-slate-900 border border-slate-800 text-sm text-white"
                  />
                </div>
                <div>
                  <label className="text-xs font-bold text-slate-300 block mb-1">
                    Calibrated Seniority Tier
                  </label>
                  <select
                    value={seniorityLevel}
                    onChange={(e) => setSeniorityLevel(e.target.value)}
                    className="w-full p-2.5 rounded-xl bg-slate-900 border border-slate-800 text-sm text-white"
                  >
                    {SENIORITY_LEVELS.map((lvl) => (
                      <option key={lvl} value={lvl}>
                        {lvl.toUpperCase()}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
            </div>
          )}

          {/* Step 3: Experience (STAR) */}
          {guidedStep === 3 && (
            <div className="space-y-4">
              <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider">
                Add Key Work Experience / Project
              </h4>
              <div className="grid grid-cols-2 gap-3">
                <input
                  type="text"
                  placeholder="Role / Title (e.g. Backend Lead)"
                  value={guidedExpTitle}
                  onChange={(e) => setGuidedExpTitle(e.target.value)}
                  className="p-2.5 rounded-xl bg-slate-900 border border-slate-800 text-xs text-white"
                />
                <input
                  type="text"
                  placeholder="Organization / Company"
                  value={guidedExpOrg}
                  onChange={(e) => setGuidedExpOrg(e.target.value)}
                  className="p-2.5 rounded-xl bg-slate-900 border border-slate-800 text-xs text-white"
                />
              </div>
              <textarea
                rows={2}
                placeholder="Action: What did you build or architect?"
                value={guidedExpAction}
                onChange={(e) => setGuidedExpAction(e.target.value)}
                className="w-full p-2.5 rounded-xl bg-slate-900 border border-slate-800 text-xs text-white"
              />
              <input
                type="text"
                placeholder="Quantified Result: e.g. Reduced query latency by 45% at 50k req/s"
                value={guidedExpResult}
                onChange={(e) => setGuidedExpResult(e.target.value)}
                className="w-full p-2.5 rounded-xl bg-slate-900 border border-slate-800 text-xs text-white"
              />
              <button
                onClick={addGuidedExperienceBlock}
                className="px-4 py-2 bg-sky-600 hover:bg-sky-500 text-white rounded-xl text-xs font-semibold flex items-center gap-1.5"
              >
                <Plus className="w-3.5 h-3.5" /> Save Experience Block
              </button>

              {blocks.length > 0 && (
                <div className="mt-3 space-y-2">
                  <span className="text-xs font-bold text-slate-400">Added Blocks:</span>
                  {blocks.map((b, idx) => (
                    <div
                      key={idx}
                      className="p-2.5 rounded-xl bg-slate-900 border border-slate-800 text-xs flex justify-between items-center"
                    >
                      <span className="font-semibold text-white">
                        {b.title} • {b.organization}
                      </span>
                      <button
                        onClick={() => removeBlock(idx)}
                        className="text-slate-500 hover:text-rose-400"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Step 4: Hackathons & Honors */}
          {guidedStep === 4 && (
            <div className="space-y-4">
              <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center gap-1.5">
                <Trophy className="w-4 h-4 text-amber-400" />
                Hackathon Wins & Distinctive Honors
              </h4>
              <p className="text-xs text-slate-400">
                Major competitions (ETHGlobal, MLH, HackMIT) grant high-signal merit boosts in the matching reranker.
              </p>

              <div className="grid grid-cols-2 gap-3">
                <input
                  type="text"
                  placeholder="Hackathon Name (e.g. ETHGlobal)"
                  value={guidedHackName}
                  onChange={(e) => setGuidedHackName(e.target.value)}
                  className="p-2.5 rounded-xl bg-slate-900 border border-slate-800 text-xs text-white"
                />
                <select
                  value={guidedHackPlacement}
                  onChange={(e) => setGuidedHackPlacement(e.target.value)}
                  className="p-2.5 rounded-xl bg-slate-900 border border-slate-800 text-xs text-white"
                >
                  <option value="1st Place Winner">1st Place Winner</option>
                  <option value="2nd Place Winner">2nd Place Winner</option>
                  <option value="3rd Place Winner">3rd Place Winner</option>
                  <option value="Finalist">Finalist</option>
                  <option value="Participant">Participant</option>
                </select>
              </div>
              <textarea
                rows={2}
                placeholder="What did you build? e.g. Autonomous agent scheduler in Python & Kafka."
                value={guidedHackDesc}
                onChange={(e) => setGuidedHackDesc(e.target.value)}
                className="w-full p-2.5 rounded-xl bg-slate-900 border border-slate-800 text-xs text-white"
              />
              <button
                onClick={addGuidedHackathonBlock}
                className="px-4 py-2 bg-amber-600 hover:bg-amber-500 text-white rounded-xl text-xs font-semibold flex items-center gap-1.5"
              >
                <Plus className="w-3.5 h-3.5" /> Add Hackathon Honor
              </button>
            </div>
          )}

          {/* Step 5: Skills */}
          {guidedStep === 5 && (
            <div className="space-y-4">
              <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider">
                Select Your Core Technical Stack
              </h4>
              <div className="flex flex-wrap gap-2">
                {POPULAR_SKILLS.map((sk) => {
                  const isSel = skills.includes(sk);
                  return (
                    <button
                      key={sk}
                      onClick={() => toggleSkill(sk)}
                      className={`px-3 py-1.5 rounded-xl text-xs font-medium border transition-all ${
                        isSel
                          ? "bg-sky-500/20 border-sky-500 text-sky-300 font-semibold"
                          : "bg-slate-900 border-slate-800 text-slate-400 hover:text-white"
                      }`}
                    >
                      {sk}
                    </button>
                  );
                })}
              </div>

              <div className="flex gap-2 pt-2">
                <input
                  type="text"
                  placeholder="Add custom skill (e.g. vLLM, GraphQL)"
                  value={skillInput}
                  onChange={(e) => setSkillInput(e.target.value)}
                  className="flex-1 p-2.5 rounded-xl bg-slate-900 border border-slate-800 text-xs text-white"
                />
                <button
                  onClick={addCustomSkill}
                  className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white rounded-xl text-xs font-semibold"
                >
                  Add
                </button>
              </div>
            </div>
          )}

          {/* Wizard Navigation Footer */}
          <div className="flex items-center justify-between pt-4 border-t border-slate-800">
            {guidedStep > 1 ? (
              <button
                onClick={() => setGuidedStep(guidedStep - 1)}
                className="text-xs font-medium text-slate-400 hover:text-white flex items-center gap-1"
              >
                <ArrowLeft className="w-3.5 h-3.5" /> Previous
              </button>
            ) : (
              <button
                onClick={() => setMode("choose")}
                className="text-xs text-slate-400 hover:text-white"
              >
                Cancel
              </button>
            )}

            {guidedStep < 5 ? (
              <button
                onClick={() => setGuidedStep(guidedStep + 1)}
                className="px-4 py-2 bg-sky-500 hover:bg-sky-400 text-white rounded-xl text-xs font-semibold flex items-center gap-1"
              >
                Next <ArrowRight className="w-3.5 h-3.5" />
              </button>
            ) : (
              <button
                onClick={() => setMode("verify")}
                className="px-5 py-2 bg-emerald-500 hover:bg-emerald-400 text-white rounded-xl text-xs font-semibold flex items-center gap-1.5 shadow-md shadow-emerald-500/20"
              >
                Review & Activate <CheckCircle2 className="w-3.5 h-3.5" />
              </button>
            )}
          </div>
        </div>
      )}

      {/* Mode: Staging & Verification Screen */}
      {mode === "verify" && (
        <div className="p-6 rounded-2xl bg-slate-850 border border-slate-800 space-y-6">
          <div className="flex items-center justify-between pb-4 border-b border-slate-800">
            <div>
              <h3 className="text-base font-bold text-white">Staging & Profile Verification</h3>
              <p className="text-xs text-slate-400 mt-0.5">
                Review parsed atomic blocks and configure candidate career personas.
              </p>
            </div>
            <button
              onClick={() => setMode("choose")}
              className="text-xs text-slate-400 hover:text-white"
            >
              Start over
            </button>
          </div>

          {/* Basic Info Verification */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="text-xs font-bold text-slate-400 block mb-1">
                Candidate Name
              </label>
              <input
                type="text"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                className="w-full p-2.5 rounded-xl bg-slate-900 border border-slate-800 text-xs text-white"
              />
            </div>
            <div>
              <label className="text-xs font-bold text-slate-400 block mb-1">
                Work Authorization / Visa
              </label>
              <select
                value={visaStatus}
                onChange={(e) => setVisaStatus(e.target.value)}
                className="w-full p-2.5 rounded-xl bg-slate-900 border border-slate-800 text-xs text-white"
              >
                {VISA_STATUS_OPTIONS.map((opt) => (
                  <option key={opt} value={opt}>
                    {opt}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Staged CV Blocks */}
          <div>
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-3 flex items-center gap-1.5">
              <Briefcase className="w-3.5 h-3.5 text-sky-400" />
              Atomic Career Blocks ({blocks.length})
            </h4>
            <div className="space-y-3 max-h-72 overflow-y-auto">
              {blocks.map((b, idx) => (
                <div
                  key={idx}
                  className="p-3.5 rounded-xl bg-slate-900/80 border border-slate-800 text-xs space-y-1.5"
                >
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-white">
                      {b.title} • {b.organization || "Independent Project"}
                    </span>
                    <button
                      onClick={() => removeBlock(idx)}
                      className="text-slate-500 hover:text-rose-400"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                  <p className="text-slate-300 leading-relaxed">{b.content}</p>
                </div>
              ))}
              {blocks.length === 0 && (
                <div className="p-4 rounded-xl bg-slate-900 text-center text-xs text-slate-500 italic">
                  No career blocks added yet.
                </div>
              )}
            </div>
          </div>

          {/* Specialized Persona Toggle */}
          <div className="p-4 rounded-xl bg-slate-850 border border-slate-750 flex items-start gap-3">
            <input
              type="checkbox"
              id="aiPersonaToggle"
              checked={createAiPersona}
              onChange={(e) => setCreateAiPersona(e.target.checked)}
              className="mt-1 rounded bg-slate-900 border-slate-750 text-sky-500 focus:ring-0"
            />
            <label htmlFor="aiPersonaToggle" className="text-xs cursor-pointer">
              <span className="font-bold text-slate-200 block">
                Provision "AI & Distributed Systems Specialist" Persona
              </span>
              <span className="text-slate-400 block mt-0.5">
                In addition to your Universal Profile, create a dedicated persona targeting high-performance machine learning infra roles.
              </span>
            </label>
          </div>

          {/* Action Footer */}
          <div className="flex items-center justify-between pt-4 border-t border-slate-800">
            <button
              onClick={() => setMode("choose")}
              className="text-xs text-slate-400 hover:text-white"
            >
              Cancel
            </button>
            <button
              onClick={handleFinalSubmit}
              disabled={loading}
              className="px-6 py-2.5 rounded-xl bg-gradient-to-r from-sky-500 to-indigo-600 hover:from-sky-400 hover:to-indigo-500 text-white font-bold text-xs shadow-lg shadow-sky-500/25 transition-all flex items-center gap-2"
            >
              {loading ? "Activating Profile..." : "Activate & View Matching Opportunities"}
              <CheckCircle2 className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default OnboardingWizard;

