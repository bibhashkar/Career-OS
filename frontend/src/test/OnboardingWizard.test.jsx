import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { OnboardingWizard } from "../pages/OnboardingWizard";
import * as api from "../services/api";

vi.mock("../services/api", () => ({
  parseResumeDocument: vi.fn(),
  parseResumeText: vi.fn(),
  onboardCandidate: vi.fn(),
}));

const mockParsedResult = {
  full_name: "Alex Rivera",
  email: "alex@example.com",
  target_roles: ["AI Infrastructure Engineer"],
  years_experience: 5,
  seniority_level: "senior",
  skills: ["Python", "Kubernetes", "PyTorch"],
  blocks: [
    {
      block_type: "experience",
      title: "Senior AI Engineer",
      organization: "Meta",
      content: "Optimized LLM serving latency by 35% using vLLM.",
    },
  ],
};

const sampleLongResumeText =
  "Alex Rivera, Senior AI Engineer at Meta with 5 years experience building distributed LLM systems.";

describe("OnboardingWizard Component", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders onboarding modality selector on mount", () => {
    render(
      <MemoryRouter>
        <OnboardingWizard />
      </MemoryRouter>
    );

    expect(
      screen.getByText(/Build Your Multi-Persona Candidate Profile/i)
    ).toBeInTheDocument();
    expect(screen.getByText("Upload Resume / CV")).toBeInTheDocument();
    expect(screen.getByText("Paste Text / LinkedIn")).toBeInTheDocument();
    expect(screen.getByText("Guided 5-Step Wizard")).toBeInTheDocument();
  });

  it("navigates to paste text mode and parses candidate profile", async () => {
    api.parseResumeText.mockResolvedValueOnce(mockParsedResult);

    render(
      <MemoryRouter>
        <OnboardingWizard />
      </MemoryRouter>
    );

    const pasteCard = screen.getByText("Paste Text / LinkedIn");
    fireEvent.click(pasteCard);

    expect(
      await screen.findByText(/Paste Profile or Resume Text/i)
    ).toBeInTheDocument();

    const textarea = await screen.findByRole("textbox");
    fireEvent.change(textarea, {
      target: {
        value: sampleLongResumeText,
      },
    });

    await waitFor(() => {
      expect(textarea.value).toBe(sampleLongResumeText);
    });

    const parseBtn = await screen.findByRole("button", {
      name: /Parse & Verify Blocks/i,
    });
    fireEvent.click(parseBtn);

    await waitFor(() => {
      expect(api.parseResumeText).toHaveBeenCalledWith(sampleLongResumeText);
    });

    // Should transition to verify screen
    expect(
      await screen.findByText(/Staging & Profile Verification/i)
    ).toBeInTheDocument();
    expect(screen.getByDisplayValue("Alex Rivera")).toBeInTheDocument();
  });

  it("completes full onboarding submission on verify step", async () => {
    api.parseResumeText.mockResolvedValueOnce(mockParsedResult);
    api.onboardCandidate.mockResolvedValueOnce({
      account: { id: "acc-101", full_name: "Alex Rivera" },
      default_persona: { id: "p-101", name: "Universal Profile" },
      additional_personas: [],
      cv_blocks_created: 1,
    });

    render(
      <MemoryRouter>
        <OnboardingWizard />
      </MemoryRouter>
    );

    // Switch to paste mode
    fireEvent.click(screen.getByText("Paste Text / LinkedIn"));
    const textarea = await screen.findByRole("textbox");
    fireEvent.change(textarea, { target: { value: sampleLongResumeText } });

    await waitFor(() => {
      expect(textarea.value).toBe(sampleLongResumeText);
    });

    const parseBtn = await screen.findByRole("button", {
      name: /Parse & Verify Blocks/i,
    });
    fireEvent.click(parseBtn);

    // Verify screen loaded
    const completeBtn = await screen.findByRole("button", {
      name: /Activate & View Matching Opportunities/i,
    });
    fireEvent.click(completeBtn);

    await waitFor(() => {
      expect(api.onboardCandidate).toHaveBeenCalledWith(
        expect.objectContaining({
          full_name: "Alex Rivera",
          visa_status: "Citizen",
        })
      );
    });
  });
});
