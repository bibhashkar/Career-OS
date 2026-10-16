import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { JobDiagnosticModal } from "../components/JobDiagnosticModal";
import * as api from "../services/api";

vi.mock("../services/api", () => ({
  getJobDiagnostics: vi.fn(),
}));

const mockDiagnosticData = {
  job_id: "job-100",
  title: "Principal ML Engineer",
  company_name: "OpenAI",
  match_score: 0.91,
  probability_band: "high",
  hard_gate_pass: true,
  visa_status_message: "Visa sponsorship explicitly confirmed by OpenAI.",
  next_step_action: "Outstanding fit: prioritize direct referral or tailored submission.",
  matched_skills: ["Python", "PyTorch", "Distributed Systems"],
  missing_dealbreakers: ["CUDA Kernel Optimization"],
  phrasing_equivalents: [
    { candidate_has: "GCP Vertex AI", job_term: "AWS SageMaker" },
  ],
  breakdown: {
    g_prob: 1.0,
    skill_score: 0.92,
    semantic_score: 0.88,
    seniority_score: 1.0,
    prestige_booster: 0.10,
    achievement_booster: 0.05,
    freshness_booster: 0.10,
  },
};

describe("JobDiagnosticModal Component", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("fetches and renders Tier 1 diagnostic breakdown for given job", async () => {
    api.getJobDiagnostics.mockResolvedValueOnce(mockDiagnosticData);

    render(
      <JobDiagnosticModal
        jobId="job-100"
        jobTitle="Principal ML Engineer"
        companyName="OpenAI"
        personaId="persona-123"
        onClose={vi.fn()}
      />
    );

    expect(api.getJobDiagnostics).toHaveBeenCalledWith("job-100", "persona-123");

    expect(await screen.findByText("91%")).toBeInTheDocument();
    expect(screen.getByText("high probability")).toBeInTheDocument();
    expect(
      screen.getByText(/Work Authorization & Modality Passed/i)
    ).toBeInTheDocument();
    expect(
      screen.getByText(/Visa sponsorship explicitly confirmed/i)
    ).toBeInTheDocument();

    // Matched competencies
    expect(screen.getByText("Python")).toBeInTheDocument();
    expect(screen.getByText("Distributed Systems")).toBeInTheDocument();

    // Missing dealbreakers
    expect(screen.getByText("Missing: CUDA Kernel Optimization")).toBeInTheDocument();

    // Phrasing equivalents
    expect(screen.getByText(/You have GCP Vertex AI/i)).toBeInTheDocument();
  });

  it("triggers onTailorCV and closes modal when clicking Tailor CV Now", async () => {
    api.getJobDiagnostics.mockResolvedValueOnce(mockDiagnosticData);

    const handleClose = vi.fn();
    const handleTailor = vi.fn();

    render(
      <JobDiagnosticModal
        jobId="job-100"
        jobTitle="Principal ML Engineer"
        companyName="OpenAI"
        personaId="persona-123"
        onClose={handleClose}
        onTailorCV={handleTailor}
      />
    );

    const tailorBtn = await screen.findByRole("button", { name: /Tailor CV Now/i });
    fireEvent.click(tailorBtn);

    expect(handleClose).toHaveBeenCalledTimes(1);
    expect(handleTailor).toHaveBeenCalledTimes(1);
  });

  it("triggers onStartInterview and closes modal when clicking Mock Interview", async () => {
    api.getJobDiagnostics.mockResolvedValueOnce(mockDiagnosticData);

    const handleClose = vi.fn();
    const handleInterview = vi.fn();

    render(
      <JobDiagnosticModal
        jobId="job-100"
        jobTitle="Principal ML Engineer"
        companyName="OpenAI"
        onClose={handleClose}
        onStartInterview={handleInterview}
      />
    );

    const interviewBtn = await screen.findByRole("button", { name: /Mock Interview/i });
    fireEvent.click(interviewBtn);

    expect(handleClose).toHaveBeenCalledTimes(1);
    expect(handleInterview).toHaveBeenCalledTimes(1);
  });

  it("renders external Apply link when applyUrl is provided", async () => {
    api.getJobDiagnostics.mockResolvedValueOnce(mockDiagnosticData);

    render(
      <JobDiagnosticModal
        jobId="job-100"
        jobTitle="Principal ML Engineer"
        companyName="OpenAI"
        applyUrl="https://careers.openai.com/jobs/100"
        onClose={vi.fn()}
      />
    );

    const applyLink = await screen.findByTestId("diagnostic-apply-btn");
    expect(applyLink).toBeInTheDocument();
    expect(applyLink).toHaveAttribute("href", "https://careers.openai.com/jobs/100");
    expect(applyLink).toHaveAttribute("target", "_blank");
  });
});

