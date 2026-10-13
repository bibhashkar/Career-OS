import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { Dashboard } from "../pages/Dashboard";
import * as api from "../services/api";

vi.mock("../services/api", () => ({
  searchJobs: vi.fn(),
  crossCheckJob: vi.fn(),
}));

describe("Dashboard Search and Empty State Experience", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders empty state with sample keywords and does not call searchJobs on initial load", () => {
    render(<Dashboard onSelectJob={vi.fn()} onStartInterview={vi.fn()} />);

    expect(
      screen.getByText(/Ready to explore open positions\?/i)
    ).toBeInTheDocument();
    expect(
      screen.getByText(/Suggested Search Keywords/i)
    ).toBeInTheDocument();
    expect(screen.getByText("Software Developer")).toBeInTheDocument();
    expect(screen.getByText("Stripe")).toBeInTheDocument();
    expect(screen.getByText("OpenAI")).toBeInTheDocument();

    // searchJobs should NOT have been invoked on initial mount with empty inputs
    expect(api.searchJobs).not.toHaveBeenCalled();
  });

  it("submitting empty search does not trigger searchJobs and maintains clean empty state", () => {
    render(<Dashboard onSelectJob={vi.fn()} onStartInterview={vi.fn()} />);

    const searchButton = screen.getByRole("button", { name: /Search jobs/i });
    fireEvent.click(searchButton);

    expect(api.searchJobs).not.toHaveBeenCalled();
    expect(
      screen.getByText(/Ready to explore open positions\?/i)
    ).toBeInTheDocument();
    expect(screen.queryByText(/validation failed/i)).not.toBeInTheDocument();
  });

  it("clicking a sample keyword populates query and executes search", async () => {
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

    render(<Dashboard onSelectJob={vi.fn()} onStartInterview={vi.fn()} />);

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
});
