import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { Dashboard, generatePaginationPages } from "../pages/Dashboard";
import * as api from "../services/api";

vi.mock("../services/api", () => ({
  searchJobs: vi.fn(),
  crossCheckJob: vi.fn(),
  getJobMatches: vi.fn(),
  getJobDiagnostics: vi.fn(),
  parseSearchQuery: vi.fn().mockResolvedValue({}),
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
  raw_description:
    "Build low-latency inference cluster orchestration in Python and Rust.",
  match_score: 0.88,
  hard_gate_pass: true,
  probability_band: "high",
  breakdown: {
    g_prob: 1.0,
    skill_score: 0.9,
    semantic_score: 0.85,
    seniority_score: 1.0,
    prestige_booster: 0.1,
    achievement_booster: 0.05,
    freshness_booster: 0.08,
    context_score: 0.8,
    comp_score: 1.0,
  },
  matched_skills: ["Python", "PyTorch", "Kubernetes"],
  missing_dealbreakers: ["Triton"],
  phrasing_equivalents: [{ candidate_has: "AWS", job_requested: "GCP" }],
  gate_notes: ["Hard gates verified"],
};

const secondMatchJob = {
  job_id: "match-job-002",
  title: "Staff Distributed Systems Engineer",
  company_name: "Stripe",
  location: "Remote",
  workplace_type: "remote",
  salary_range: "$210,000 - $260,000",
  visa_sponsorship: "yes",
  apply_url: "https://stripe.com/jobs/002",
  posted_at: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000).toISOString(),
  raw_description:
    "Architect global payment ledger pipelines with high availability.",
  match_score: 0.79,
  hard_gate_pass: true,
  probability_band: "high",
  breakdown: {
    g_prob: 1.0,
    skill_score: 0.85,
    semantic_score: 0.8,
    seniority_score: 0.9,
  },
  matched_skills: ["Python", "Kafka"],
  missing_dealbreakers: [],
  phrasing_equivalents: [],
  gate_notes: ["Remote modality aligned"],
};

function renderDashboard(props = {}, initialEntries = ["/"]) {
  return render(
    <MemoryRouter initialEntries={initialEntries}>
      <Dashboard onSelectJob={vi.fn()} onStartInterview={vi.fn()} {...props} />
    </MemoryRouter>,
  );
}

describe("Jobs Dashboard & Split-Pane Master-Detail View", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
  });

  describe("Jobs Feed & Split-Pane Master-Detail View", () => {
    it("renders the Jobs header and no dual tab buttons or database corpus count badge", async () => {
      api.getJobMatches.mockResolvedValueOnce({
        total_count: 2,
        page: 1,
        page_size: 15,
        jobs: [mockMatchJob],
      });

      renderDashboard();

      expect(
        screen.getByRole("heading", { name: /^Jobs$/i }),
      ).toBeInTheDocument();
      expect(
        screen.queryByText(/High-Probability Matches/i),
      ).not.toBeInTheDocument();
      expect(
        screen.queryByRole("button", { name: /Direct ATS Search & Ingest/i }),
      ).not.toBeInTheDocument();
      expect(
        screen.queryByRole("button", { name: /Import Job/i }),
      ).not.toBeInTheDocument();

      await waitFor(() => {
        expect(api.getJobMatches).toHaveBeenCalled();
      });
    });

    it("calls getJobMatches with page_size=15 and renders split-pane list and detail panel", async () => {
      api.getJobMatches.mockResolvedValueOnce({
        persona_id: "persona-123",
        persona_name: "AI Engineer Lens",
        total_count: 2,
        page: 1,
        page_size: 15,
        jobs: [mockMatchJob, secondMatchJob],
      });

      renderDashboard({
        activePersona: { id: "persona-123", name: "AI Engineer Lens" },
      });

      await waitFor(() => {
        expect(api.getJobMatches).toHaveBeenCalledWith(
          expect.objectContaining({
            persona_id: "persona-123",
            page: 1,
            page_size: 15,
            min_score: 0.0,
          }),
        );
      });

      expect(
        await screen.findByTestId("matches-split-pane"),
      ).toBeInTheDocument();
      expect(screen.getByTestId("job-detail-panel")).toBeInTheDocument();
      expect(
        screen.getAllByText("Senior AI Platform Engineer").length,
      ).toBeGreaterThanOrEqual(1);
      expect(screen.getAllByText("Anthropic").length).toBeGreaterThanOrEqual(1);
      expect(screen.getAllByText("88% Match").length).toBeGreaterThanOrEqual(1);
      expect(screen.getAllByText("Python").length).toBeGreaterThanOrEqual(1);
      expect(screen.getByText("Missing: Triton")).toBeInTheDocument();
      expect(screen.getByText("Equiv: AWS → GCP")).toBeInTheDocument();
      expect(
        screen.getByText(/Build low-latency inference cluster orchestration/i),
      ).toBeInTheDocument();

      // Clicking the second card updates the right-hand detail panel
      const secondCard = screen.getByTestId("match-card-match-job-002");
      fireEvent.click(secondCard);
      expect(
        await screen.findByText(/Architect global payment ledger pipelines/i),
      ).toBeInTheDocument();
    });

    it("navigates match list via ArrowDown and ArrowUp keyboard shortcuts", async () => {
      api.getJobMatches.mockResolvedValueOnce({
        total_count: 2,
        page: 1,
        page_size: 15,
        jobs: [mockMatchJob, secondMatchJob],
      });

      renderDashboard();

      expect(
        await screen.findByTestId("matches-split-pane"),
      ).toBeInTheDocument();
      expect(
        screen.getByText(/Build low-latency inference cluster orchestration/i),
      ).toBeInTheDocument();

      // Press ArrowDown to navigate to second job
      fireEvent.keyDown(window, { key: "ArrowDown" });
      expect(
        await screen.findByText(/Architect global payment ledger pipelines/i),
      ).toBeInTheDocument();

      // Press ArrowUp to navigate back to first job
      fireEvent.keyDown(window, { key: "ArrowUp" });
      expect(
        await screen.findByText(
          /Build low-latency inference cluster orchestration/i,
        ),
      ).toBeInTheDocument();
    });

    it("enforces equal-height split container and single continuous scroll body without nested scrollbars", async () => {
      api.getJobMatches.mockResolvedValueOnce({
        total_count: 2,
        page: 1,
        page_size: 15,
        jobs: [mockMatchJob, secondMatchJob],
      });

      renderDashboard();

      const splitPane = await screen.findByTestId("matches-split-pane");
      expect(splitPane.className).toContain("items-stretch");

      const leftList = screen.getByTestId("matches-left-list");
      expect(leftList.className).toContain("h-full");
      expect(leftList.className).toContain("flex-col");

      const detailPanel = screen.getByTestId("job-detail-panel");
      expect(detailPanel.className).toContain("h-full");
      expect(detailPanel.className).toContain("flex-col");

      const detailBody = screen.getByTestId("job-detail-scroll-body");
      expect(detailBody.className).toContain("overflow-y-auto");
      expect(detailBody.className).toContain("flex-1");

      const descBox = screen.getByTestId("job-detail-raw-description");
      expect(descBox.className).not.toContain("overflow-y-auto");
    });

    it("hides % Match badge in Explorer (unbiased) mode", async () => {
      api.getJobMatches.mockResolvedValue({
        jobs: [
          {
            ...mockMatchJob,
            match_score: null,
            probability_band: "unranked",
            breakdown: null,
          },
        ],
        total_count: 1,
      });

      renderDashboard({}, ["/?mode=unbiased"]);

      expect(
        (await screen.findAllByText("Senior AI Platform Engineer")).length,
      ).toBeGreaterThanOrEqual(1);
      expect(screen.queryByText(/% Match/i)).not.toBeInTheDocument();
    });

    it("renders pagination controls when total_count exceeds 15", async () => {
      api.getJobMatches.mockResolvedValue({
        jobs: [mockMatchJob],
        total_count: 32,
        page: 1,
        page_size: 15,
      });

      renderDashboard();

      expect(
        await screen.findByTestId("matches-pagination"),
      ).toBeInTheDocument();
      expect(screen.getByTestId("pagination-summary")).toHaveTextContent(
        "Showing 1–15 of 32 (max 15 per page)",
      );

      const nextBtn = screen.getByRole("button", { name: /Next/i });
      fireEvent.click(nextBtn);

      await waitFor(() => {
        expect(api.getJobMatches).toHaveBeenCalledWith(
          expect.objectContaining({
            page: 2,
            page_size: 15,
          }),
        );
      });
    });

    it("renders interactive numbered pagination and retains selected job context across page change", async () => {
      const page1Job = {
        ...mockMatchJob,
        job_id: "job-page-1",
        title: "Page 1 Selected Role",
      };
      const page2Job = {
        ...mockMatchJob,
        job_id: "job-page-2",
        title: "Page 2 Unselected Role",
      };

      api.getJobMatches
        .mockResolvedValueOnce({
          jobs: [page1Job],
          total_count: 45,
          page: 1,
          page_size: 15,
        })
        .mockResolvedValueOnce({
          jobs: [page2Job],
          total_count: 45,
          page: 2,
          page_size: 15,
        });

      renderDashboard();

      // Page 1 is active, page buttons 1, 2, 3 should exist
      expect(
        await screen.findByRole("button", { name: "Page 1" }),
      ).toBeInTheDocument();
      expect(screen.getByRole("button", { name: "Page 2" })).toBeInTheDocument();
      expect(screen.getByRole("button", { name: "Page 3" })).toBeInTheDocument();

      // Initially Page 1 Selected Role is displayed in detail panel
      expect(
        screen.getAllByText("Page 1 Selected Role").length,
      ).toBeGreaterThanOrEqual(1);

      // Click directly on Page 2 button
      const page2Btn = screen.getByRole("button", { name: "Page 2" });
      fireEvent.click(page2Btn);

      await waitFor(() => {
        expect(api.getJobMatches).toHaveBeenCalledWith(
          expect.objectContaining({ page: 2 }),
        );
      });

      // Crucial UX check: Page 1 Selected Role is STILL displayed in detail panel!
      expect(screen.getByText("Page 1 Selected Role")).toBeInTheDocument();
      // And Page 2 job is present in the opportunity list
      expect(
        await screen.findByText("Page 2 Unselected Role"),
      ).toBeInTheDocument();
    });

    it("correctly generates pagination ranges with ellipses for various page counts", () => {
      expect(generatePaginationPages(1, 1)).toEqual([1]);
      expect(generatePaginationPages(1, 3)).toEqual([1, 2, 3]);
      expect(generatePaginationPages(1, 7)).toEqual([1, 2, 3, 4, 5, 6, 7]);
      expect(generatePaginationPages(2, 10)).toEqual([
        1,
        2,
        3,
        4,
        5,
        "...",
        10,
      ]);
      expect(generatePaginationPages(5, 10)).toEqual([
        1,
        "...",
        4,
        5,
        6,
        "...",
        10,
      ]);
      expect(generatePaginationPages(9, 10)).toEqual([
        1,
        "...",
        6,
        7,
        8,
        9,
        10,
      ]);
    });

    it("renders external Apply link and posted date badge on job detail panel", async () => {
      api.getJobMatches.mockResolvedValueOnce({
        jobs: [mockMatchJob],
        total_count: 1,
      });

      renderDashboard();

      await screen.findAllByText("Senior AI Platform Engineer");

      const applyBtn = screen.getByTestId("apply-link-match-job-001");
      expect(applyBtn).toBeInTheDocument();
      expect(applyBtn).toHaveAttribute(
        "href",
        "https://jobs.lever.co/anthropic/001",
      );
      expect(applyBtn).toHaveAttribute("target", "_blank");
      expect(applyBtn).toHaveAttribute("rel", "noopener noreferrer");
      expect(applyBtn).toHaveTextContent("Apply");

      expect(screen.getAllByText("2d ago").length).toBeGreaterThanOrEqual(1);
    });

    it("triggers onSelectJob when clicking Tailor CV button on detail panel", async () => {
      api.getJobMatches.mockResolvedValueOnce({
        jobs: [mockMatchJob],
        total_count: 1,
      });

      const handleSelectJob = vi.fn();
      renderDashboard({ onSelectJob: handleSelectJob });

      const tailorBtn = await screen.findByRole("button", {
        name: /Tailor CV/i,
      });
      fireEvent.click(tailorBtn);

      expect(handleSelectJob).toHaveBeenCalledTimes(1);
      expect(handleSelectJob).toHaveBeenCalledWith(
        expect.objectContaining({
          id: "match-job-001",
          title: "Senior AI Platform Engineer",
          company_name: "Anthropic",
        }),
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

      const diagBtn = await screen.findByRole("button", {
        name: /Why this match\?/i,
      });
      fireEvent.click(diagBtn);

      expect(
        await screen.findByText(/Tier 1 Match Diagnostics/i),
      ).toBeInTheDocument();
      expect(api.getJobDiagnostics).toHaveBeenCalledWith(
        "match-job-001",
        undefined,
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
          }),
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
      fireEvent.change(locationInput, {
        target: { value: "San Francisco, CA" },
      });

      await waitFor(() => {
        expect(api.getJobMatches).toHaveBeenCalledWith(
          expect.objectContaining({
            location: "San Francisco, CA",
          }),
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
          }),
        );
      });
    });

    it("opens SearchFilterModal when clicking All Filters and filters by date posted & work auth", async () => {
      api.getJobMatches.mockResolvedValue({
        jobs: [mockMatchJob],
        total_count: 1,
      });

      renderDashboard();

      const openModalBtn = screen.getByTestId("open-filter-modal-btn");
      fireEvent.click(openModalBtn);

      expect(
        await screen.findByTestId("search-filter-modal"),
      ).toBeInTheDocument();

      const postedSelect = screen.getByLabelText("Filter by date posted");
      fireEvent.change(postedSelect, { target: { value: "7" } });

      const workAuthSelect = screen.getByLabelText(
        "Filter by work authorization",
      );
      fireEvent.change(workAuthSelect, { target: { value: "f1_opt_cpt" } });

      await waitFor(() => {
        expect(api.getJobMatches).toHaveBeenCalledWith(
          expect.objectContaining({
            posted_within: 7,
            work_auth_tier: "f1_opt_cpt",
          }),
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

      const clearBtn = await screen.findByRole("button", {
        name: /Clear All/i,
      });
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
          }),
        );
      });

      const searchInput = screen.getByTestId("matches-search-input");
      expect(searchInput.value).toBe("Platform");

      const locationInput = screen.getByTestId("matches-location-input");
      expect(locationInput.value).toBe("Seattle");
    });

    it("renders brief daily filter row and separate sorting row with All Filters modal trigger", async () => {
      api.getJobMatches.mockResolvedValue({
        jobs: [mockMatchJob],
        total_count: 1,
      });

      renderDashboard();

      const filterRow = screen.getByTestId("search-filters-row");
      const sortRow = screen.getByTestId("sorting-controls-row");
      expect(filterRow).toBeInTheDocument();
      expect(sortRow).toBeInTheDocument();
      expect(filterRow).not.toContainElement(sortRow);

      expect(screen.getByTestId("open-filter-modal-btn")).toBeInTheDocument();
      expect(screen.getAllByLabelText("Sort match opportunities")).toHaveLength(
        1,
      );
    });

    it("renders chips under the omnibar without 'Vertical:' prefix and clears only text when clicking omnibar clear", async () => {
      api.getJobMatches.mockResolvedValue({
        jobs: [mockMatchJob],
        total_count: 1,
      });

      const initialChips = encodeURIComponent(
        JSON.stringify([
          {
            id: "ind-1",
            type: "industry",
            value: "healthtech",
            label: "Vertical: Healthtech",
          },
        ]),
      );

      renderDashboard({}, [`/?q=distributed&loc=Boston&chips=${initialChips}`]);

      const searchInput = screen.getByTestId("matches-search-input");
      const chipsRow = await screen.findByTestId("omnibar-chips-row");

      expect(chipsRow).toHaveTextContent("HealthTech");
      expect(chipsRow).not.toHaveTextContent("Vertical:");

      const clearOmnibarBtn = screen.getByLabelText("Clear omnibar");
      fireEvent.click(clearOmnibarBtn);

      expect(searchInput.value).toBe("");
      expect(screen.getByTestId("matches-location-input").value).toBe("Boston");
      expect(screen.getByTestId("omnibar-chips-row")).toHaveTextContent(
        "HealthTech",
      );
    });
  });
});
