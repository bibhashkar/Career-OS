import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
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
  posted_at: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString(),
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

function renderDashboard(props = {}, initialEntries = ["/"]) {
  return render(
    <MemoryRouter initialEntries={initialEntries}>
      <Dashboard
        onSelectJob={vi.fn()}
        onStartInterview={vi.fn()}
        {...props}
      />
    </MemoryRouter>
  );
}

describe("Dashboard Dual-Mode: Matches and ATS Search", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
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

      renderDashboard({
        activePersona: { id: "persona-123", name: "AI Engineer Lens" },
      });

      await waitFor(() => {
        expect(api.getJobMatches).toHaveBeenCalledWith(
          expect.objectContaining({
            persona_id: "persona-123",
            min_score: 0.0,
          })
        );
      });

      expect(await screen.findByText("Senior AI Platform Engineer")).toBeInTheDocument();
      expect(screen.getByText("Anthropic")).toBeInTheDocument();
      expect(screen.getByText("88% Match")).toBeInTheDocument();
      expect(screen.getByText("Python")).toBeInTheDocument();
      expect(screen.getByText("Missing: Triton")).toBeInTheDocument();
      expect(screen.getByText("Equiv: AWS → GCP")).toBeInTheDocument();
    });

    it("renders external Apply link and posted date badge on job cards", async () => {
      api.getJobMatches.mockResolvedValueOnce({
        jobs: [mockMatchJob],
        total_count: 1,
      });

      renderDashboard();

      expect(await screen.findByText("Senior AI Platform Engineer")).toBeInTheDocument();

      // Verify concise 'Apply' button
      const applyBtn = screen.getByTestId("apply-link-match-job-001");
      expect(applyBtn).toBeInTheDocument();
      expect(applyBtn).toHaveAttribute("href", "https://jobs.lever.co/anthropic/001");
      expect(applyBtn).toHaveAttribute("target", "_blank");
      expect(applyBtn).toHaveAttribute("rel", "noopener noreferrer");
      expect(applyBtn).toHaveTextContent("Apply");

      // Verify relative posted date badge (2d ago)
      expect(screen.getByText("2d ago")).toBeInTheDocument();
    });

    it("triggers onSelectJob when clicking Tailor CV button on a match card", async () => {
      api.getJobMatches.mockResolvedValueOnce({
        jobs: [mockMatchJob],
        total_count: 1,
      });

      const handleSelectJob = vi.fn();
      renderDashboard({ onSelectJob: handleSelectJob });

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

      renderDashboard();

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

    it("filters matches by text search keyword query", async () => {
      api.getJobMatches.mockResolvedValue({
        jobs: [mockMatchJob],
        total_count: 1,
      });

      renderDashboard();

      const searchInput = screen.getByTestId("matches-search-input");
      fireEvent.change(searchInput, { target: { value: "Anthropic" } });

      await waitFor(() => {
        expect(api.getJobMatches).toHaveBeenCalledWith(
          expect.objectContaining({
            q: "Anthropic",
          })
        );
      });
    });

    it("filters matches by location query supporting city, state, country, or region", async () => {
      api.getJobMatches.mockResolvedValue({
        jobs: [mockMatchJob],
        total_count: 1,
      });

      renderDashboard();

      const locationInput = screen.getByTestId("matches-location-input");
      fireEvent.change(locationInput, { target: { value: "San Francisco, CA" } });

      await waitFor(() => {
        expect(api.getJobMatches).toHaveBeenCalledWith(
          expect.objectContaining({
            location: "San Francisco, CA",
          })
        );
      });
    });

    it("changes sort order between best match and most recent", async () => {
      api.getJobMatches.mockResolvedValue({
        jobs: [mockMatchJob],
        total_count: 1,
      });

      renderDashboard();

      const sortSelect = screen.getByLabelText("Sort match opportunities");
      fireEvent.change(sortSelect, { target: { value: "date" } });

      await waitFor(() => {
        expect(api.getJobMatches).toHaveBeenCalledWith(
          expect.objectContaining({
            sort_by: "date",
          })
        );
      });
    });

    it("filters matches by posted date range", async () => {
      api.getJobMatches.mockResolvedValue({
        jobs: [mockMatchJob],
        total_count: 1,
      });

      renderDashboard();

      const postedSelect = screen.getByLabelText("Filter by date posted");
      fireEvent.change(postedSelect, { target: { value: "7" } });

      await waitFor(() => {
        expect(api.getJobMatches).toHaveBeenCalledWith(
          expect.objectContaining({
            posted_within: 7,
          })
        );
      });
    });

    it("clears all active filters when clicking Clear All", async () => {
      api.getJobMatches.mockResolvedValue({
        jobs: [mockMatchJob],
        total_count: 1,
      });

      renderDashboard();

      const searchInput = screen.getByTestId("matches-search-input");
      fireEvent.change(searchInput, { target: { value: "Anthropic" } });

      const clearBtn = await screen.findByRole("button", { name: /Clear All/i });
      fireEvent.click(clearBtn);

      await waitFor(() => {
        expect(searchInput.value).toBe("");
      });
    });

    it("initializes filters from URL search parameters", async () => {
      api.getJobMatches.mockResolvedValue({
        jobs: [mockMatchJob],
        total_count: 1,
      });

      renderDashboard({}, ["/?q=Platform&loc=Seattle&sort=date&posted=14"]);

      await waitFor(() => {
        expect(api.getJobMatches).toHaveBeenCalledWith(
          expect.objectContaining({
            q: "Platform",
            location: "Seattle",
            sort_by: "date",
            posted_within: 14,
          })
        );
      });

      const searchInput = screen.getByTestId("matches-search-input");
      expect(searchInput.value).toBe("Platform");

      const locationInput = screen.getByTestId("matches-location-input");
      expect(locationInput.value).toBe("Seattle");
    });
  });

  describe("Direct ATS Search & Ingest Tab", () => {
    it("renders empty state with sample keywords and does not call searchJobs on initial load", () => {
      api.getJobMatches.mockResolvedValueOnce({ jobs: [], total_count: 0 });

      renderDashboard({ defaultTab: "search" });

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

      renderDashboard({ defaultTab: "search" });

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

      renderDashboard({ defaultTab: "search" });

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

      renderDashboard();

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
