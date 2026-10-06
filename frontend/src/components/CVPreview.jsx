import React, { useState } from "react";
import { Check, Copy, UserCheck, Layers, TrendingUp, Sparkles } from "lucide-react";

export function CVPreview({ draft }) {
  const [copied, setCopied] = useState(false);

  if (!draft) return null;

  const handleCopy = () => {
    const textContent = `
${draft.candidate_title || "Software Engineer"}
Target Company: ${draft.target_company || ""}

PROFESSIONAL SUMMARY:
${draft.professional_summary || ""}

HIGHLIGHTED SKILLS:
${draft.skills_highlighted?.join(", ") || ""}

EXPERIENCE & ACHIEVEMENTS:
${draft.experience_blocks
  ?.map(
    (b) => `
• ${b.title} (${b.organization || ""})
  ${b.content}
  Metrics: ${JSON.stringify(b.metrics || {})}
`
  )
  .join("\n")}
    `.trim();

    navigator.clipboard.writeText(textContent);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownload = (format) => {
    const filename = `tailored_cv_${(draft.target_company || "draft").toLowerCase().replace(/[^a-z0-9]/g, "_")}.${format === "txt" ? "txt" : "md"}`;
    const textContent = format === "txt"
      ? `
${(draft.candidate_title || "Software Engineer").toUpperCase()}
Target Role at ${draft.target_company || "Target Company"}
========================================

PROFESSIONAL SUMMARY
--------------------
${draft.professional_summary || ""}

CORE SKILLS
-----------
${draft.skills_highlighted?.join(", ") || ""}

EXPERIENCE & ACCOMPLISHMENTS
----------------------------
${draft.experience_blocks?.map((b) => `* ${b.title} (${b.organization || ""})\n  ${b.content}`).join("\n\n") || ""}
`.trim()
      : `
# ${draft.candidate_title || "Software Engineer"}
**Target Company:** ${draft.target_company || ""}

## Professional Summary
${draft.professional_summary || ""}

## Core Competencies & Skills
${draft.skills_highlighted?.join(", ") || ""}

## Experience & Key Achievements
${draft.experience_blocks?.map((b) => `### ${b.title}${b.organization ? ` - ${b.organization}` : ""}\n${b.content}`).join("\n\n") || ""}
`.trim();

    const blob = new Blob([textContent], { type: format === "txt" ? "text/plain" : "text/markdown" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="bg-slate-800/90 border border-slate-700/80 rounded-2xl p-6 shadow-xl space-y-6">
      {/* Top action bar */}
      <div className="flex items-center justify-between border-b border-slate-700/60 pb-4 flex-wrap gap-2">
        <div className="flex items-center gap-2">
          <div className="p-2 bg-sky-500/10 text-sky-400 rounded-lg">
            <UserCheck className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-base font-bold text-white">
              {draft.candidate_title || "Tailored CV Draft"}
            </h3>
            <span className="text-xs text-slate-400">
              Targeted for {draft.target_company || "Target Role"}
            </span>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => handleDownload("md")}
            className="px-3 py-1.5 bg-sky-600 hover:bg-sky-500 text-white font-medium rounded-lg text-xs transition-colors flex items-center gap-1.5 focus:outline-none focus:ring-2 focus:ring-sky-400"
            title="Download ATS-compliant Markdown"
          >
            Export .md
          </button>
          <button
            onClick={() => handleDownload("txt")}
            className="px-3 py-1.5 bg-slate-700 hover:bg-slate-600 text-slate-200 font-medium rounded-lg text-xs transition-colors flex items-center gap-1.5 focus:outline-none focus:ring-2 focus:ring-sky-400"
            title="Download ATS Plaintext"
          >
            Export .txt
          </button>
          <button
            onClick={handleCopy}
            className="px-3 py-1.5 bg-slate-700 hover:bg-slate-600 text-slate-200 font-medium rounded-lg text-xs transition-colors flex items-center gap-1.5 focus:outline-none focus:ring-2 focus:ring-sky-400"
          >
            {copied ? (
              <>
                <Check className="w-3.5 h-3.5 text-emerald-400" /> Copied
              </>
            ) : (
              <>
                <Copy className="w-3.5 h-3.5" /> Copy Text
              </>
            )}
          </button>
        </div>
      </div>

      {/* Professional Summary */}
      <div className="space-y-1.5">
        <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
          <Sparkles className="w-3.5 h-3.5 text-amber-400" /> Executive Summary
        </div>
        <p className="text-xs leading-relaxed text-slate-300 bg-slate-900/60 p-3.5 rounded-xl border border-slate-700/50">
          {draft.professional_summary}
        </p>
      </div>

      {/* Skills Badges */}
      {draft.skills_highlighted?.length > 0 && (
        <div className="space-y-1.5">
          <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
            <Layers className="w-3.5 h-3.5 text-sky-400" /> Tailored Skill Alignment
          </div>
          <div className="flex flex-wrap gap-1.5">
            {draft.skills_highlighted.map((skill, idx) => (
              <span
                key={idx}
                className="text-xs px-2.5 py-1 rounded-md bg-slate-900 text-sky-300 border border-slate-700 font-mono"
              >
                {skill}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Semantic Experience Blocks (pgvector matches) */}
      <div className="space-y-3">
        <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
          <TrendingUp className="w-3.5 h-3.5 text-emerald-400" /> Semantic Experience Blocks (pgvector)
        </div>
        <div className="space-y-3">
          {draft.experience_blocks?.map((block, idx) => (
            <div
              key={idx}
              className="bg-slate-900/70 border border-slate-700/60 rounded-xl p-4 space-y-2"
            >
              <div className="flex items-center justify-between">
                <h4 className="text-xs font-bold text-white">{block.title}</h4>
                {block.organization && (
                  <span className="text-[11px] text-slate-400 font-medium">
                    {block.organization}
                  </span>
                )}
              </div>
              <p className="text-xs text-slate-300 leading-relaxed">{block.content}</p>

              {/* Quantifiable metrics badges */}
              {block.metrics && Object.keys(block.metrics).length > 0 && (
                <div className="flex flex-wrap gap-2 pt-1 border-t border-slate-800/80">
                  {Object.entries(block.metrics).map(([key, val], mIdx) => (
                    <span
                      key={mIdx}
                      className="text-[10px] px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-300 font-mono border border-emerald-500/20"
                    >
                      {key.replace(/_/g, " ")}: {val}
                    </span>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
