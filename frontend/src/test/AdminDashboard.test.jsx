import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { AdminDashboard } from "../pages/AdminDashboard";
import * as api from "../services/api";

vi.mock("../services/api", () => ({
  getAdminOverview: vi.fn(),
  syncBoard: vi.fn(),
  syncAllBoards: vi.fn(),
  retryFailedTasks: vi.fn(),
  purgeFailedTasks: vi.fn(),
  resetCircuitBreaker: vi.fn(),
  flushMatchCache: vi.fn(),
  updateUserStatus: vi.fn(),
  registerATSBoard: vi.fn(),
  searchJobs: vi.fn(),
  crossCheckJob: vi.fn(),
  addCustomJob: vi.fn(),
}));

const mockOverviewData = {
  current_operator: {
    email: "admin@career-os.dev",
    role: "admin",
    id: "usr-admin-1",
  },
  system_health: {
    status: "healthy",
    db_connected: true,
    redis_connected: true,
    active_circuit_breakers: [],
  },
  crawler_pipeline: {
    boards: [],
    sync_jobs_in_flight: 0,
    dead_letter_count: 0,
  },
  catalog_breakdown: {
    total_jobs: 120,
    by_provider: {},
  },
  ai_cost_and_quotas: {
    total_tokens_24h: 1500,
    estimated_cost_usd: 0.04,
  },
  users: [
    {
      id: "usr-1",
      email: "candidate@career-os.dev",
      full_name: "Jane Candidate",
      role: "candidate",
      is_active: true,
      personas_count: 1,
      cv_blocks_count: 5,
      last_login_at: new Date().toISOString(),
    },
  ],
};

describe("AdminDashboard Component", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    api.getAdminOverview.mockResolvedValue(mockOverviewData);
  });

  it("renders Admin Console and displays the Job Ingestion & ATS Search tab", async () => {
    render(<AdminDashboard />);

    expect(
      await screen.findByText(/Admin Control Plane & Observability/i),
    ).toBeInTheDocument();

    const ingestTabBtn = screen.getByRole("button", {
      name: /Job Ingestion & ATS Search/i,
    });
    expect(ingestTabBtn).toBeInTheDocument();
  });

  it("switches to Job Ingestion tab and displays search controls and import action", async () => {
    render(<AdminDashboard />);

    const ingestTabBtn = await screen.findByRole("button", {
      name: /Job Ingestion & ATS Search/i,
    });
    fireEvent.click(ingestTabBtn);

    expect(
      screen.getByText(/Direct ATS Hunting & Job Ingestion/i),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /Import Job \(URL \/ Text\)/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByPlaceholderText(/Job title, keywords, or company\.\.\./i),
    ).toBeInTheDocument();
  });

  it("opens AddJobModal when clicking Import Job button", async () => {
    render(<AdminDashboard />);

    const ingestTabBtn = await screen.findByRole("button", {
      name: /Job Ingestion & ATS Search/i,
    });
    fireEvent.click(ingestTabBtn);

    const importJobBtn = screen.getByRole("button", {
      name: /Import Job \(URL \/ Text\)/i,
    });
    fireEvent.click(importJobBtn);

    expect(
      await screen.findByText(/Import Job Posting/i),
    ).toBeInTheDocument();
  });

  it("executes external ATS search and renders job cards with cross-check action", async () => {
    api.searchJobs.mockResolvedValueOnce({
      jobs: [
        {
          id: "job-ats-999",
          title: "Staff Infrastructure Engineer",
          company_name: "Cloudflare",
          location: "San Francisco, CA",
          salary_min: 190000,
          salary_max: 240000,
          salary_currency: "$",
          provenance: {
            source_aggregator: "jsearch",
            is_cross_checked: false,
          },
          ats_requirements: {
            required_skills: ["Go", "Kubernetes", "BGP"],
          },
          apply_url: "https://boards.greenhouse.io/cloudflare/jobs/999",
        },
      ],
    });

    render(<AdminDashboard />);

    const ingestTabBtn = await screen.findByRole("button", {
      name: /Job Ingestion & ATS Search/i,
    });
    fireEvent.click(ingestTabBtn);

    const queryInput = screen.getByPlaceholderText(
      /Job title, keywords, or company\.\.\./i,
    );
    fireEvent.change(queryInput, { target: { value: "Cloudflare" } });

    const searchBtn = screen.getByRole("button", { name: /Search ATS/i });
    fireEvent.click(searchBtn);

    await waitFor(() => {
      expect(api.searchJobs).toHaveBeenCalledWith("Cloudflare", "", false);
    });

    expect(
      await screen.findByText("Staff Infrastructure Engineer"),
    ).toBeInTheDocument();
    expect(screen.getAllByText("Cloudflare").length).toBeGreaterThanOrEqual(2);
    expect(screen.getByText("Go")).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /Cross-Check/i }),
    ).toBeInTheDocument();
  });
});
