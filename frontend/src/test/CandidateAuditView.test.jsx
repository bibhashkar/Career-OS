import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { CandidateAuditView } from "../pages/CandidateAuditView";
import * as api from "../services/api";

vi.mock("../services/api", () => ({
  getCandidateAudit: vi.fn(),
}));

const mockAuditData = {
  candidate_name: "Jane Doe",
  market_percentile: 88,
  overall_health_score: 85,
  quantified_impact_ratio: 0.75,
  quantified_blocks_count: 6,
  total_blocks_count: 8,
  distinction_badges: [
    {
      code: "hackathon_winner",
      title: "Hackathon Champion",
      description: "1st Place at Global AI Hackathon",
      verified: true,
    },
    {
      code: "tier1_pedigree",
      title: "Tier-1 Pedigree",
      description: "Former Google Software Engineer",
      verified: true,
    },
  ],
  career_ceiling_diagnosis: {
    current_tier: "Senior",
    next_target_tier: "Staff",
    primary_barrier: "Leadership Visibility",
    recommended_action: "Highlight cross-functional architectural leadership in CV blocks.",
  },
  t_shaped_radar: [
    {
      category: "Distributed Systems",
      score: 90,
      skill_count: 5,
      depth_label: "Specialist",
      top_skills: ["Kafka", "Kubernetes"],
    },
    {
      category: "Machine Learning",
      score: 75,
      skill_count: 4,
      depth_label: "Proficient",
      top_skills: ["PyTorch", "vLLM"],
    },
  ],
  personas: [
    {
      id: "p-1",
      name: "Universal Profile",
      is_default: true,
      target_roles: ["Senior Backend Engineer"],
      skills_count: 12,
    },
  ],
};

describe("CandidateAuditView Component", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("fetches and renders 360 Candidate Health and Market Standing", async () => {
    api.getCandidateAudit.mockResolvedValueOnce(mockAuditData);

    render(<CandidateAuditView onNavigateBack={vi.fn()} />);

    expect(api.getCandidateAudit).toHaveBeenCalledTimes(1);

    expect(
      await screen.findByText(/Candidate Career Health & Market Standing/i)
    ).toBeInTheDocument();
    expect(screen.getByText("(88th percentile)")).toBeInTheDocument();
    expect(screen.getByText("85")).toBeInTheDocument();
    expect(screen.getByText("75%")).toBeInTheDocument();
    expect(screen.getByText("Leadership Visibility")).toBeInTheDocument();
    expect(
      screen.getByText(/Highlight cross-functional architectural leadership/i)
    ).toBeInTheDocument();

    // Badges
    expect(screen.getByText("Hackathon Champion")).toBeInTheDocument();
    expect(screen.getByText("Tier-1 Pedigree")).toBeInTheDocument();

    // Radar categories
    expect(screen.getByText("Distributed Systems")).toBeInTheDocument();
    expect(screen.getByText("Machine Learning")).toBeInTheDocument();
  });

  it("handles recalculation on button click", async () => {
    api.getCandidateAudit.mockResolvedValue(mockAuditData);

    render(<CandidateAuditView onNavigateBack={vi.fn()} />);

    expect(
      await screen.findByText(/Candidate Career Health & Market Standing/i)
    ).toBeInTheDocument();

    const recalcBtn = screen.getByRole("button", { name: /Recalculate Audit/i });
    fireEvent.click(recalcBtn);

    await waitFor(() => {
      expect(api.getCandidateAudit).toHaveBeenCalledTimes(2);
    });
  });
});
