import React, { useState } from "react";
import { Tag, Plus, X, Layers, Sparkles } from "lucide-react";

export const ARCHETYPE_SKILL_CATEGORIES = {
  technology_engineering: [
    { key: "system_architecture", label: "System Architecture & Patterns" },
    { key: "backend_and_frameworks", label: "Backend & Distributed Frameworks" },
    { key: "ai_and_infrastructure", label: "AI, RAG & Vector Infrastructure" },
    { key: "databases_and_caching", label: "Databases, Storage & Caching" },
    { key: "cloud_and_devops", label: "Cloud, DevOps & CI/CD" },
    { key: "frontend_and_ui", label: "Frontend & Web Architecture" },
    { key: "security_and_compliance", label: "Security, Governance & Compliance" },
    { key: "testing_and_qa", label: "Testing, Observability & QA" },
  ],
  executive_leadership: [
    { key: "executive_pnl", label: "Executive & P&L Leadership" },
    { key: "corp_strategy_mna", label: "Corporate Strategy, M&A & Due Diligence" },
    { key: "gtm_revenue", label: "Go-To-Market & Revenue Growth" },
    { key: "org_scale_talent", label: "Talent Scaling & Organizational Design" },
    { key: "board_investor_rel", label: "Board Governance & Investor Relations" },
    { key: "ops_supply_chain", label: "Operations, Execution & Supply Chain" },
    { key: "risk_legal_gov", label: "Risk, Legal, ESG & Corporate Governance" },
    { key: "digital_transformation", label: "Digital Transformation & Technology" },
  ],
  marketing_growth: [
    { key: "growth_performance", label: "Growth & Performance Marketing" },
    { key: "brand_product_pos", label: "Brand Strategy & Product Positioning" },
    { key: "demand_gen_abm", label: "Demand Generation & ABM Pipelines" },
    { key: "content_pr_comms", label: "Content, PR & Executive Communications" },
    { key: "martech_crm_analytics", label: "MarTech, CRM & Attribution Analytics" },
    { key: "lifecycle_retention", label: "Customer Lifecycle, Retention & LTV" },
    { key: "market_research_pricing", label: "Market Research, ICP & Pricing Models" },
    { key: "agency_leadership", label: "Agency & Cross-Functional Team Leadership" },
  ],
  product_strategy: [
    { key: "product_vision_strategy", label: "Product Vision, Strategy & Roadmaps" },
    { key: "customer_discovery_ux", label: "User Discovery, Design & Personas" },
    { key: "roadmap_delivery", label: "Agile Execution & Delivery Velocity" },
    { key: "data_experimentation", label: "Data Analytics, Metrics & A/B Testing" },
    { key: "product_led_growth", label: "Product-Led Growth (PLG) & Adoption" },
    { key: "bizops_process", label: "Business Operations & Scale (BizOps)" },
    { key: "monetization_packaging", label: "Monetization, Packaging & Tiers" },
    { key: "stakeholder_alignment", label: "Executive & Stakeholder Alignment" },
  ],
  finance_fintech: [
    { key: "fpa_modeling", label: "Financial Modeling, Forecasting & FP&A" },
    { key: "payments_clearing", label: "Payments, Billing & Transaction Clearing" },
    { key: "risk_underwriting", label: "Risk Management, Underwriting & Fraud" },
    { key: "capital_markets_treasury", label: "Capital Markets, Debt/Equity & Treasury" },
    { key: "regulatory_compliance", label: "Regulatory Compliance (SOX, SEC, PCI)" },
    { key: "mna_valuation", label: "Strategic Transactions, Valuation & M&A" },
    { key: "quant_data_analytics", label: "Quantitative Data & Business Intelligence" },
    { key: "audit_internal_controls", label: "Audit, Controls & Enterprise Accounting" },
  ],
  healthcare_lifesciences: [
    { key: "clinical_ops_quality", label: "Clinical Operations, Care Quality & Safety" },
    { key: "health_it_interop", label: "Health IT, EHR & Interoperability (FHIR/HL7)" },
    { key: "regulatory_hipaa_fda", label: "Regulatory & Compliance (HIPAA, FDA, CLIA)" },
    { key: "population_health", label: "Population Health & Patient Outcomes" },
    { key: "revenue_cycle_billing", label: "Payer / Provider Revenue Cycle & Claims" },
    { key: "clinical_trials_rd", label: "Clinical Trials, Protocols & Biotech R&D" },
    { key: "medical_affairs", label: "Medical Affairs, Evidence & Strategy" },
    { key: "interprofessional_lead", label: "Clinical & Cross-Functional Leadership" },
  ],
  custom_hybrid: [
    { key: "core_domain_strategy", label: "Core Strategic Competencies" },
    { key: "execution_delivery", label: "Operations, Execution & Delivery" },
    { key: "tools_platforms", label: "Domain Tools, Systems & Platforms" },
    { key: "leadership_governance", label: "Leadership, People & Governance" },
  ],
};

export function CompetencyMatrixSection({
  skills = [],
  skillsMatrix = {},
  archetype = "technology_engineering",
  onAddSkill,
  onRemoveSkill,
}) {
  const [newSkillTag, setNewSkillTag] = useState("");
  const [selectedCategoryKey, setSelectedCategoryKey] = useState("");
  const [isAddingCustomCategory, setIsAddingCustomCategory] = useState(false);
  const [customCatName, setCustomCatName] = useState("");
  const [customCategories, setCustomCategories] = useState([]);

  const baseCategories =
    ARCHETYPE_SKILL_CATEGORIES[archetype] ||
    ARCHETYPE_SKILL_CATEGORIES.technology_engineering;

  const allCategories = [...baseCategories, ...customCategories];

  function handleAdd() {
    const clean = newSkillTag.trim();
    if (!clean) return;

    // Case-insensitive check
    if (skills.some((s) => s.toLowerCase() === clean.toLowerCase())) {
      setNewSkillTag("");
      return;
    }

    const catKey = selectedCategoryKey || allCategories[0]?.key || null;
    onAddSkill(clean, catKey);
    setNewSkillTag("");
  }

  function handleAddInline(catKey) {
    const inputVal = window.prompt(`Add new skill/competency to "${allCategories.find((c) => c.key === catKey)?.label}":`);
    if (inputVal && inputVal.trim()) {
      const clean = inputVal.trim();
      if (!skills.some((s) => s.toLowerCase() === clean.toLowerCase())) {
        onAddSkill(clean, catKey);
      }
    }
  }

  function handleCreateCustomCategory(e) {
    e.preventDefault();
    const clean = customCatName.trim();
    if (!clean) return;
    const key = clean.toLowerCase().replace(/[^a-z0-9]/g, "_");
    if (!allCategories.some((c) => c.key === key)) {
      setCustomCategories([...customCategories, { key, label: clean }]);
      setSelectedCategoryKey(key);
    }
    setCustomCatName("");
    setIsAddingCustomCategory(false);
  }

  return (
    <section
      data-testid="section-skills"
      id="section-skills"
      className="p-5 rounded-2xl bg-slate-900/90 border border-slate-800 shadow-xl space-y-4"
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Tag className="w-4 h-4 text-sky-400" />
          <h3 className="text-sm font-bold text-white uppercase tracking-wider">
            5. Competency & Skills Matrix ({skills.length})
          </h3>
        </div>
        <button
          type="button"
          onClick={() => setIsAddingCustomCategory(true)}
          className="text-[11px] text-sky-400 hover:text-sky-300 font-semibold inline-flex items-center gap-1 cursor-pointer"
        >
          <Plus className="w-3.5 h-3.5" />
          <span>Add Custom Category</span>
        </button>
      </div>

      {/* Add Custom Category Drawer */}
      {isAddingCustomCategory && (
        <form
          onSubmit={handleCreateCustomCategory}
          className="p-3 rounded-xl bg-slate-950 border border-sky-800/80 flex items-center gap-2"
        >
          <input
            type="text"
            placeholder="Custom Category Name (e.g. Developer Relations or Hospital Ops)"
            value={customCatName}
            onChange={(e) => setCustomCatName(e.target.value)}
            className="flex-1 px-3 py-1.5 bg-slate-900 border border-slate-700 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none focus:border-sky-500"
            autoFocus
          />
          <button
            type="submit"
            className="px-3 py-1.5 rounded-xl bg-sky-600 hover:bg-sky-500 text-white text-xs font-semibold cursor-pointer"
          >
            Create
          </button>
          <button
            type="button"
            onClick={() => setIsAddingCustomCategory(false)}
            className="px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold cursor-pointer"
          >
            Cancel
          </button>
        </form>
      )}

      {/* Add Skill Tag Bar with Category Dropdown */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-2">
        <input
          type="text"
          placeholder="+ Add Skill or Competency Tag (e.g. P&L, LangGraph, M&A, HIPAA, FHIR)"
          value={newSkillTag}
          onChange={(e) => setNewSkillTag(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") {
              e.preventDefault();
              handleAdd();
            }
          }}
          className="flex-1 px-3 py-1.5 bg-slate-950 border border-slate-700 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none focus:border-sky-500"
        />

        <select
          value={selectedCategoryKey}
          onChange={(e) => setSelectedCategoryKey(e.target.value)}
          className="px-3 py-1.5 bg-slate-950 border border-slate-700 rounded-xl text-xs text-slate-300 focus:outline-none focus:border-sky-500 cursor-pointer"
        >
          <option value="">Auto / First Category</option>
          {allCategories.map((cat) => (
            <option key={cat.key} value={cat.key}>
              {cat.label}
            </option>
          ))}
        </select>

        <button
          type="button"
          onClick={handleAdd}
          className="px-4 py-1.5 rounded-xl bg-sky-600 hover:bg-sky-500 text-white text-xs font-semibold cursor-pointer shrink-0"
        >
          Add Tag
        </button>
      </div>

      {/* Categorized Matrix Pills */}
      <div className="space-y-3 pt-1">
        {allCategories.map((cat) => {
          const catSkills = skillsMatrix?.[cat.key] || [];
          return (
            <div key={cat.key} className="space-y-1.5">
              <div className="flex items-center justify-between">
                <span className="text-[11px] font-semibold text-slate-400">
                  {cat.label} ({catSkills.length})
                </span>
                <button
                  type="button"
                  onClick={() => handleAddInline(cat.key)}
                  className="text-[10px] text-slate-500 hover:text-sky-400 inline-flex items-center gap-0.5 cursor-pointer"
                  title={`Add tag directly to ${cat.label}`}
                >
                  <Plus className="w-2.5 h-2.5" />
                  <span>Add</span>
                </button>
              </div>

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
                        onClick={() => onRemoveSkill(sk)}
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

        {/* Uncategorized Skills */}
        {(() => {
          const categorizedSet = new Set(
            Object.values(skillsMatrix || {}).flat().map((s) => s.toLowerCase())
          );
          const uncategorized = skills.filter((s) => !categorizedSet.has(s.toLowerCase()));
          if (uncategorized.length === 0) return null;

          return (
            <div className="space-y-1.5 pt-2 border-t border-slate-850">
              <span className="text-[11px] font-semibold text-slate-400">
                All Other Competencies & Tools ({uncategorized.length})
              </span>
              <div className="flex flex-wrap items-center gap-1.5">
                {uncategorized.map((sk, sIdx) => (
                  <span
                    key={sIdx}
                    className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-lg bg-sky-950/60 text-sky-200 border border-sky-800/60 text-xs font-medium"
                  >
                    <span>{sk}</span>
                    <button
                      type="button"
                      onClick={() => onRemoveSkill(sk)}
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
  );
}

