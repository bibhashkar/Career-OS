import React from "react";
import {
  Briefcase,
  Cpu,
  TrendingUp,
  Award,
  DollarSign,
  HeartPulse,
  Layers,
  Sparkles,
} from "lucide-react";

export const ARCHETYPES = [
  {
    id: "technology_engineering",
    label: "Technology & Engineering",
    subtitle: "SWE, AI, Platform, Cloud & Security",
    icon: Cpu,
    color: "sky",
    domainPresets: [
      "Enterprise SaaS / Distributed Systems",
      "Cloud & DevOps Infrastructure",
      "AI / Machine Learning Infrastructure",
      "Cybersecurity & Compliance (SOC2 / ISO)",
    ],
  },
  {
    id: "executive_leadership",
    label: "Executive & C-Suite",
    subtitle: "CEO, COO, Founder, VP, Managing Director",
    icon: Award,
    color: "amber",
    domainPresets: [
      "Executive Leadership & Corporate Strategy",
      "P&L Ownership & Turnaround",
      "M&A, Due Diligence & Deal Structuring",
      "Board Governance & Investor Relations",
    ],
  },
  {
    id: "marketing_growth",
    label: "Marketing & Growth",
    subtitle: "CMO, Product Marketing, Brand, GTM",
    icon: TrendingUp,
    color: "emerald",
    domainPresets: [
      "Marketing, Brand & Revenue Growth",
      "Product Marketing & GTM Positioning",
      "Performance Marketing & Paid Acquisition",
      "Customer Lifecycle, Retention & CRM",
    ],
  },
  {
    id: "product_strategy",
    label: "Product & Operations",
    subtitle: "CPO, VP Product, BizOps, Chief of Staff",
    icon: Briefcase,
    color: "purple",
    domainPresets: [
      "Product Strategy & Roadmap Execution",
      "Business Operations & Scaling (BizOps)",
      "Cross-Functional Program Management",
      "Revenue Operations & Monetization",
    ],
  },
  {
    id: "finance_fintech",
    label: "Finance & FinTech",
    subtitle: "CFO, FinTech, Risk, Capital Markets, FP&A",
    icon: DollarSign,
    color: "teal",
    domainPresets: [
      "FinTech / High-Throughput Transactions",
      "Payments, Billing & Multi-State Clearing",
      "Financial Planning & Analysis (FP&A)",
      "Risk, Fraud Detection & Regulatory Compliance",
    ],
  },
  {
    id: "healthcare_lifesciences",
    label: "Healthcare & Biotech",
    subtitle: "HealthTech, Clinical Ops, Medical Affairs",
    icon: HeartPulse,
    color: "rose",
    domainPresets: [
      "HealthTech / HIPAA & EHR Interoperability",
      "Clinical Trial Operations & Compliance",
      "Biotechnology R&D & Bioinformatics",
      "Healthcare Administration & Quality Care",
    ],
  },
  {
    id: "custom_hybrid",
    label: "Cross-Functional Hybrid",
    subtitle: "Custom focus tailored to your unique career path",
    icon: Layers,
    color: "indigo",
    domainPresets: [
      "Strategic Advisory & Consulting",
      "Operations & Program Management",
      "Technical Product Management",
    ],
  },
];

export function ArchetypeCustomizationBar({
  currentArchetype = "technology_engineering",
  onSelectArchetype,
  onAddDomainPreset,
}) {
  const activeObj =
    ARCHETYPES.find((a) => a.id === currentArchetype) || ARCHETYPES[0];

  return (
    <div
      data-testid="archetype-customization-bar"
      className="p-4 rounded-2xl bg-slate-900/90 border border-slate-800 shadow-xl space-y-3"
    >
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <Sparkles className="w-4 h-4 text-amber-400" />
          <h3 className="text-xs font-bold text-white uppercase tracking-wider">
            Career Archetype & Domain Focus Lens
          </h3>
        </div>
        <span className="text-[11px] text-slate-400">
          Adapts skills taxonomy, proof-point prompts, and channel fields
        </span>
      </div>

      {/* Archetype Selector Chips */}
      <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-1.5">
        {ARCHETYPES.map((arch) => {
          const Icon = arch.icon;
          const isSelected = arch.id === currentArchetype;
          return (
            <button
              key={arch.id}
              type="button"
              onClick={() => onSelectArchetype(arch.id)}
              className={`flex flex-col items-start p-2 rounded-xl border text-left transition-all cursor-pointer ${
                isSelected
                  ? "bg-slate-800 border-sky-500 shadow-md shadow-sky-950/40"
                  : "bg-slate-950/60 border-slate-800/80 hover:border-slate-700 hover:bg-slate-900/60"
              }`}
            >
              <div className="flex items-center gap-1.5 w-full">
                <Icon
                  className={`w-3.5 h-3.5 shrink-0 ${
                    isSelected ? "text-sky-400" : "text-slate-400"
                  }`}
                />
                <span
                  className={`text-[11px] font-semibold truncate ${
                    isSelected ? "text-white" : "text-slate-300"
                  }`}
                >
                  {arch.label}
                </span>
              </div>
              <span className="text-[9px] text-slate-500 line-clamp-1 mt-0.5">
                {arch.subtitle}
              </span>
            </button>
          );
        })}
      </div>

      {/* Recommended Domain Verticals for this Archetype */}
      {activeObj.domainPresets && activeObj.domainPresets.length > 0 && (
        <div className="pt-2 border-t border-slate-850 flex flex-wrap items-center gap-1.5 text-xs">
          <span className="text-[10px] uppercase font-bold text-slate-500 tracking-wider mr-1">
            Recommended Domain Verticals:
          </span>
          {activeObj.domainPresets.map((preset, idx) => (
            <button
              key={idx}
              type="button"
              onClick={() => onAddDomainPreset && onAddDomainPreset(preset)}
              className="px-2.5 py-1 rounded-lg bg-slate-950 border border-slate-800 hover:border-sky-500/60 text-[11px] text-slate-300 hover:text-sky-300 transition-colors cursor-pointer"
              title="Click to add to your Domain Verticals"
            >
              + {preset}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
