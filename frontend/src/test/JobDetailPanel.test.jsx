import React from "react";
import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { JobDetailPanel } from "../components/JobDetailPanel";

const mockJob = {
  job_id: "job-render-001",
  title: "Staff Distributed Systems Engineer",
  company_name: "Render",
  location: "Remote: United States",
  workplace_type: "remote",
  salary_range: "$210,000 - $260,000",
  apply_url: "https://render.com/jobs/001",
  posted_at: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000).toISOString(),
  match_score: 0.85,
  probability_band: "high",
  raw_description: `
About Render:
At Render, we're building the modern cloud platform for developers. Our mission is to eliminate tradeoffs.

About the Role:
Billing is mission-critical to Render's success. We need a Staff Engineer to architect payment ledgers.

What You'll Do:
• Architect high-throughput distributed payment ledger pipelines in Python and Go.
• Build low-latency database queries with PostgreSQL.

Requirements:
• 5+ years of experience building distributed systems.
• Deep proficiency in Python and Kubernetes.

APPLYING TO RENDER:
We're seeking candidates who possess high integrity, humility, and an insatiable drive to learn.
Equal Opportunity Employer: We celebrate diversity and are committed to creating an inclusive environment.
`,
  matched_skills: ["Python", "Kubernetes"],
  missing_dealbreakers: ["Kafka"],
  phrasing_equivalents: [{ candidate_has: "AWS", job_requested: "GCP" }],
  gate_notes: ["Remote modality aligned"],
};

describe("JobDetailPanel Dual-Mode Presentation", () => {
  it("renders Smart Brief view by default with 30s Snapshot and skill analysis", () => {
    render(
      <JobDetailPanel
        match={mockJob}
        onTailorCV={vi.fn()}
        onStartInterview={vi.fn()}
      />,
    );

    expect(screen.getByTestId("job-smart-brief")).toBeInTheDocument();
    expect(screen.getByText(/30-Second Role Snapshot/i)).toBeInTheDocument();
    expect(
      screen.getByText(/At Render, we're building the modern cloud platform/i),
    ).toBeInTheDocument();
    expect(screen.getByText(/Core Responsibilities/i)).toBeInTheDocument();
    expect(screen.getByText(/Skill Match & Gap Analysis/i)).toBeInTheDocument();

    // Verify matched skill badge
    expect(screen.getAllByText("Python").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText("Kafka").length).toBeGreaterThanOrEqual(1);
  });

  it("switches to Full Formatted view with in-text highlights and collapsible boilerplate accordion", () => {
    render(
      <JobDetailPanel
        match={mockJob}
        onTailorCV={vi.fn()}
        onStartInterview={vi.fn()}
      />,
    );

    // Switch to Full Formatted
    const formattedBtn = screen.getByTestId("view-mode-formatted-btn");
    fireEvent.click(formattedBtn);

    expect(screen.getByTestId("job-full-formatted")).toBeInTheDocument();
    expect(screen.queryByTestId("job-smart-brief")).not.toBeInTheDocument();

    // Boilerplate accordion is collapsed initially
    expect(screen.getByText(/APPLYING TO RENDER/i)).toBeInTheDocument();
    expect(screen.getByText(/Expand statement/i)).toBeInTheDocument();

    // Click to expand accordion
    const accordionBtn = screen.getByText(/Expand statement/i);
    fireEvent.click(accordionBtn);

    expect(screen.getByText(/Collapse/i)).toBeInTheDocument();
    expect(
      screen.getByText(/We're seeking candidates who possess high integrity/i),
    ).toBeInTheDocument();
  });

  it("switches to Raw ATS view when clicking Raw ATS button", () => {
    render(
      <JobDetailPanel
        match={mockJob}
        onTailorCV={vi.fn()}
        onStartInterview={vi.fn()}
      />,
    );

    const rawBtn = screen.getByTestId("view-mode-raw-btn");
    fireEvent.click(rawBtn);

    expect(screen.getByTestId("job-raw-ats")).toBeInTheDocument();
    expect(screen.getByText(/Verbatim ATS Listing Text/i)).toBeInTheDocument();
    expect(screen.getByText(/Copy Raw Text/i)).toBeInTheDocument();
  });

  it("renders role title at the top, formats workplace label as On-Site, and nests match probability & why-match in Match Breakdown", () => {
    const onOpenDiag = vi.fn();
    const onSiteJob = {
      ...mockJob,
      title: "Principal Infrastructure Architect",
      workplace_type: "ON_SITE",
      posted_at: new Date(Date.now() - 60 * 1000).toISOString(), // 1m ago
    };

    render(
      <JobDetailPanel
        match={onSiteJob}
        onTailorCV={vi.fn()}
        onStartInterview={vi.fn()}
        onOpenDiagnostics={onOpenDiag}
      />,
    );

    // 1. Role title at the top
    const heading = screen.getByRole("heading", { level: 2 });
    expect(heading).toHaveTextContent("Principal Infrastructure Architect");

    // 2. Workplace type formatted as "On-Site"
    expect(screen.getAllByText("On-Site").length).toBeGreaterThanOrEqual(1);

    // 3. Match Probability & Why this match are in Match Breakdown section
    const breakdownHeader = screen.getByText(/Match Breakdown & Skill Alignment/i);
    expect(breakdownHeader).toBeInTheDocument();
    expect(screen.getByText(/85% Probability of Match/i)).toBeInTheDocument();

    const whyMatchBtn = screen.getByRole("button", {
      name: /Why this match\?/i,
    });
    expect(whyMatchBtn).toBeInTheDocument();
    fireEvent.click(whyMatchBtn);
    expect(onOpenDiag).toHaveBeenCalledWith(onSiteJob);
  });
});
