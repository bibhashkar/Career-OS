import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { Dashboard } from "../pages/Dashboard";
import * as api from "../services/api";

vi.mock("../services/api", () => ({
  searchJobs: vi.fn(),
  crossCheckJob: vi.fn(),
  getJobMatches: vi.fn(),
  getJobDiagnostics: vi.fn(),
}));

const mockMatchJob = {
  job_id: "match-job-001",
  title: "Senior AI Platform Engineer",
  company_name: "Anthropic",
  location: "San Francisco, CA",
  workplace_type: "hybrid",
  salary_range: "$220,000 - $280,000",
  visa_sponsorship: "yes",
  apply_url: "https://jobs.lever.co/anthropic/001",
  match_score: 0.88,
  hard_gate_pass: true,
  probability_band: "high",
  breakdown: {
    g_prob: 1.0,
    skill_score: 0.90,
    semantic_score: 0.85,
    seniority_score: 1.0,
    prestige_booster: 0.10,
    achievement_booster: 0.05,
    freshness_booster: 0.08,
  },
  matched_skills: ["Python", "PyTorch", "Kubernetes"],
  missing_dealbreakers: ["Triton"],
  phrasing_equivalents: [
    { candidate_has: "AWS", job_requested: "GCP" },
  ],
  gate_notes: ["Hard gates verified"],
};

describe("Dashboard Dual-Mode: Matches and ATS Search", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe("High-Probability Matches Tab", () => {
    it("calls getJobMatches on mount and renders ranked job matches", async () => {
      api.getJobMatches.mockResolvedValueOnce({
        persona_id: "persona-123",
        persona_name: "AI Engineer Lens",
        total_count: 1,
        page: 1,
        page_size: 25,
        jobs: [mockMatchJob],
      });

      render(
        <Dashboard
          onSelectJob={vi.fn()}
          onStartInterview={vi.fn()}
          activePersona={{ id: "persona-123", name: "AI Engineer Lens" }}
        />
      );

      expect(api.getJobMatches).toHaveBeenCalledWith(
        expect.objectContaining({
          persona_id: "persona-123",
          min_score: 0.0,
        })
      );

      expect(await screen.findByText("Senior AI Platform Engineer")).toBeInTheDocument();
      expect(screen.getByText("Anthropic")).toBeInTheDocument();
      expect(screen.getByText("88% Match")).toBeInTheDocument();
      expect(screen.getByText("Python")).toBeInTheDocument();
      expect(screen.getByText("Missing: Triton")).toBeInTheDocument();
      expect(screen.getByText("Equiv: AWS → GCP")).toBeInTheDocument();
    });

    it("triggers onSelectJob when clicking Tailor CV button on a match card", async () => {
      api.getJobMatches.mockResolvedValueOnce({
        jobs: [mockMatchJob],
        total_count: 1,
      });

      const handleSelectJob = vi.fn();
      render(
        <Dashboard
          onSelectJob={handleSelectJob}
          onStartInterview={vi.fn()}
        />
      );

      const tailorBtn = await screen.findByRole("button", { name: /Tailor CV/i });
      fireEvent.click(tailorBtn);

      expect(handleSelectJob).toHaveBeenCalledTimes(1);
      expect(handleSelectJob).toHaveBeenCalledWith(
        expect.objectContaining({
          id: "match-job-001",
          title: "Senior AI Platform Engineer",
          company_name: "Anthropic",
        })
      );
    });

    it("opens JobDiagnosticModal when clicking 'Why this match?' button", async () => {
      api.getJobMatches.mockResolvedValueOnce({
        jobs: [mockMatchJob],
        total_count: 1,
      });
      api.getJobDiagnostics.mockResolvedValueOnce({
        job_id: "match-job-001",
        title: "Senior AI Platform Engineer",
        company_name: "Anthropic",
        match_score: 0.88,
        probability_band: "high",
        hard_gate_pass: true,
        gate_notes: ["Visa verified"],
        breakdown: mockMatchJob.breakdown,
        matched_skills: mockMatchJob.matched_skills,
        missing_dealbreakers: mockMatchJob.missing_dealbreakers,
        phrasing_equivalents: mockMatchJob.phrasing_equivalents,
        ceiling_diagnosis: {
          primary_ceiling: "N/A",
          recommendation: "Strong profile alignment.",
        },
      });

      render(
        <Dashboard
          onSelectJob={vi.fn()}
          onStartInterview={vi.fn()}
        />
      );

      const diagBtn = await screen.findByRole("button", { name: /Why this match\?/i });
      fireEvent.click(diagBtn);

      expect(
        await screen.findByText(/Tier 1 Match Diagnostics/i)
      ).toBeInTheDocument();
      expect(api.getJobDiagnostics).toHaveBeenCalledWith(
        "match-job-001",
        undefined
      );
    });
  });

  describe("Direct ATS Search & Ingest Tab", () => {
    it("renders empty state with sample keywords and does not call searchJobs on initial load", () => {
      api.getJobMatches.mockResolvedValueOnce({ jobs: [], total_count: 0 });

      render(
        <Dashboard
          defaultTab="search"
          onSelectJob={vi.fn()}
          onStartInterview={vi.fn()}
        />
      );

      expect(
        screen.getByText(/Ready to explore open positions\?/i)
      ).toBeInTheDocument();
      expect(
        screen.getByText(/Suggested Search Keywords/i)
      ).toBeInTheDocument();
      expect(screen.getByText("Software Developer")).toBeInTheDocument();
      expect(screen.getByText("Stripe")).toBeInTheDocument();
      expect(screen.getByText("OpenAI")).toBeInTheDocument();

      expect(api.searchJobs).not.toHaveBeenCalled();
    });

    it("submitting empty search does not trigger searchJobs and maintains clean empty state", () => {
      api.getJobMatches.mockResolvedValueOnce({ jobs: [], total_count: 0 });

      render(
        <Dashboard
          defaultTab="search"
          onSelectJob={vi.fn()}
          onStartInterview={vi.fn()}
        />
      );

      const searchButton = screen.getByRole("button", { name: /Search jobs/i });
      fireEvent.click(searchButton);

      expect(api.searchJobs).not.toHaveBeenCalled();
      expect(
        screen.getByText(/Ready to explore open positions\?/i)
      ).toBeInTheDocument();
    });

    it("clicking a sample keyword populates query and executes search", async () => {
      api.getJobMatches.mockResolvedValueOnce({ jobs: [], total_count: 0 });
      api.searchJobs.mockResolvedValueOnce({
        jobs: [
          {
            id: "job-stripe-101",
            title: "Software Engineer - Payments",
            company_name: "Stripe",
            location: "San Francisco, CA",
            salary_range: "$170,000 - $210,000",
            data_origin: "live",
            source_confidence: "high",
            ats_requirements: { required_skills: ["Python", "Go"] },
          },
        ],
      });

      render(
        <Dashboard
          defaultTab="search"
          onSelectJob={vi.fn()}
          onStartInterview={vi.fn()}
        />
      );

      const stripeKeywordBtn = screen.getByRole("button", { name: "Stripe" });
      fireEvent.click(stripeKeywordBtn);

      await waitFor(() => {
        expect(api.searchJobs).toHaveBeenCalledWith("Stripe", "", false);
      });

      expect(
        await screen.findByText("Software Engineer - Payments")
      ).toBeInTheDocument();
      expect(screen.getByText("Stripe")).toBeInTheDocument();
    });

    it("can switch between Matches and ATS Search tabs via tab buttons", async () => {
      api.getJobMatches.mockResolvedValueOnce({ jobs: [], total_count: 0 });

      render(
        <Dashboard
          onSelectJob={vi.fn()}
          onStartInterview={vi.fn()}
        />
      );

      // Initially on High-Probability Matches tab
      expect(screen.getByText(/High-Probability Matches/i)).toBeInTheDocument();

      // Click Direct ATS Search tab
      const searchTabBtn = screen.getByRole("button", {
        name: /Direct ATS Search & Ingest/i,
      });
      fireEvent.click(searchTabBtn);

      // Now on ATS search tab
      expect(
        await screen.findByText(/Suggested Search Keywords/i)
      ).toBeInTheDocument();
    });
  });
});
