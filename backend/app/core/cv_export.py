"""
CV export formatting utility producing clean, ATS-compliant text and Markdown.

Produces recruiter- and ATS-readable document layouts adhering to the
strict no-table, single-column, parseable plain-text guidelines.
"""

from typing import Any


def format_cv_as_markdown(cv_draft: dict[str, Any]) -> str:
    """
    Format a tailored CV draft into a clean, single-column ATS Markdown document.
    """
    title = cv_draft.get("candidate_title", "Software Engineer")
    target_company = cv_draft.get("target_company", "Target Employer")
    summary = cv_draft.get("professional_summary", "")
    skills = cv_draft.get("skills_highlighted", [])
    experience_blocks = cv_draft.get("experience_blocks", [])

    lines: list[str] = [
        f"# {title}",
        f"**Target Company:** {target_company}",
        "",
        "## Professional Summary",
        summary,
        "",
    ]

    if skills:
        lines.extend(
            [
                "## Core Competencies & Skills",
                ", ".join(skills),
                "",
            ]
        )

    if experience_blocks:
        lines.append("## Experience & Key Achievements")
        for block in experience_blocks:
            b_title = block.get("title", "Project")
            b_org = block.get("organization", "")
            org_str = f" - {b_org}" if b_org else ""
            lines.append(f"### {b_title}{org_str}")

            b_content = block.get("content", "")
            if b_content:
                lines.append(b_content)

            metrics = block.get("metrics") or {}
            if metrics:
                metric_strs = [
                    f"{k.replace('_', ' ').capitalize()}: {v}"
                    for k, v in metrics.items()
                ]
                lines.append(f"*Key Metrics:* {', '.join(metric_strs)}")
            lines.append("")

    return "\n".join(lines).strip() + "\n"


def format_cv_as_plaintext(cv_draft: dict[str, Any]) -> str:
    """
    Format a tailored CV draft into pure plain-text suitable for ATS paste-ins.
    """
    title = cv_draft.get("candidate_title", "Software Engineer")
    target_company = cv_draft.get("target_company", "Target Employer")
    summary = cv_draft.get("professional_summary", "")
    skills = cv_draft.get("skills_highlighted", [])
    experience_blocks = cv_draft.get("experience_blocks", [])

    lines: list[str] = [
        title.upper(),
        f"Target Role at {target_company}",
        "=" * 40,
        "",
        "PROFESSIONAL SUMMARY",
        "-" * 20,
        summary,
        "",
    ]

    if skills:
        lines.extend(
            [
                "CORE SKILLS",
                "-" * 20,
                ", ".join(skills),
                "",
            ]
        )

    if experience_blocks:
        lines.extend(
            [
                "EXPERIENCE & ACCOMPLISHMENTS",
                "-" * 20,
            ]
        )
        for block in experience_blocks:
            b_title = block.get("title", "Project")
            b_org = block.get("organization", "")
            header = f"{b_title} ({b_org})" if b_org else b_title
            lines.append(f"* {header}")

            b_content = block.get("content", "")
            if b_content:
                lines.append(f"  {b_content}")

            metrics = block.get("metrics") or {}
            if metrics:
                metric_strs = [f"{k}: {v}" for k, v in metrics.items()]
                lines.append(f"  Metrics: {', '.join(metric_strs)}")
            lines.append("")

    return "\n".join(lines).strip() + "\n"
