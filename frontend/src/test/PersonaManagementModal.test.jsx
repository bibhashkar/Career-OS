import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { PersonaManagementModal } from "../components/PersonaManagementModal";
import * as api from "../services/api";

vi.mock("../services/api", () => ({
  getCandidatePersonas: vi.fn(),
  updateCandidatePersona: vi.fn(),
  deleteCandidatePersona: vi.fn(),
  setDefaultPersona: vi.fn(),
  createCandidatePersona: vi.fn(),
  parseResumeDocument: vi.fn(),
  parseResumeText: vi.fn(),
  createCVBlock: vi.fn(),
}));

describe("PersonaManagementModal Component", () => {
  const mockPersonas = [
    {
      id: "p-universal",
      name: "Universal Profile",
      is_common_persona: true,
      headline: "Master Profile",
      seniority_level: "senior",
      years_experience: 6,
      target_roles: ["Staff Engineer"],
      is_default: true,
      skill_count: 12,
      block_count: 5,
    },
    {
      id: "p-specialized-1",
      name: "AI Platform Engineer",
      is_common_persona: false,
      headline: "Specializing in Large-Scale AI Orchestration",
      seniority_level: "senior",
      years_experience: 4,
      target_roles: ["AI Platform Engineer"],
      is_default: false,
      skill_count: 8,
      block_count: 3,
    },
  ];

  beforeEach(() => {
    vi.clearAllMocks();
    api.getCandidatePersonas.mockResolvedValue(mockPersonas);
  });

  it("does not render when isOpen is false", () => {
    render(
      <PersonaManagementModal
        isOpen={false}
        onClose={vi.fn()}
        activePersonaId="p-universal"
      />
    );
    expect(screen.queryByTestId("persona-management-modal")).not.toBeInTheDocument();
  });

  it("renders list of personas with badges and details when isOpen is true", async () => {
    render(
      <PersonaManagementModal
        isOpen={true}
        onClose={vi.fn()}
        activePersonaId="p-universal"
      />
    );

    expect(screen.getByTestId("persona-management-modal")).toBeInTheDocument();
    expect(screen.getByText("Candidate Career Personas")).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText("Universal Profile")).toBeInTheDocument();
      expect(screen.getAllByText("AI Platform Engineer").length).toBeGreaterThan(0);
      expect(screen.getByText("Universal Baseline")).toBeInTheDocument();
      expect(screen.getByText("Default Profile")).toBeInTheDocument();
    });
  });

  it("disables name input when editing Universal Persona", async () => {
    render(
      <PersonaManagementModal
        isOpen={true}
        onClose={vi.fn()}
        activePersonaId="p-universal"
      />
    );

    await waitFor(() => {
      expect(screen.getByTestId("edit-persona-btn-p-universal")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByTestId("edit-persona-btn-p-universal"));

    expect(screen.getByTestId("edit-persona-form")).toBeInTheDocument();
    expect(screen.getByText(/System Locked Name/i)).toBeInTheDocument();

    const nameInput = screen.getByTestId("edit-persona-name-input");
    expect(nameInput).toBeDisabled();
    expect(nameInput).toHaveValue("Universal Profile");
  });

  it("allows editing and renaming a specialized persona", async () => {
    api.updateCandidatePersona.mockResolvedValueOnce({
      ...mockPersonas[1],
      name: "Distributed Systems Architect",
    });

    render(
      <PersonaManagementModal
        isOpen={true}
        onClose={vi.fn()}
        activePersonaId="p-universal"
      />
    );

    await waitFor(() => {
      expect(screen.getByTestId("edit-persona-btn-p-specialized-1")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByTestId("edit-persona-btn-p-specialized-1"));

    const nameInput = screen.getByTestId("edit-persona-name-input");
    expect(nameInput).not.toBeDisabled();
    fireEvent.change(nameInput, {
      target: { value: "Distributed Systems Architect" },
    });

    const headlineInput = screen.getByTestId("edit-persona-headline-input");
    fireEvent.change(headlineInput, {
      target: { value: "High-Throughput Systems" },
    });

    fireEvent.click(screen.getByTestId("save-persona-btn"));

    await waitFor(() => {
      expect(api.updateCandidatePersona).toHaveBeenCalledWith(
        "p-specialized-1",
        expect.objectContaining({
          name: "Distributed Systems Architect",
          headline: "High-Throughput Systems",
        })
      );
    });
  });

  it("displays duplicate name error message when updating fails", async () => {
    api.updateCandidatePersona.mockRejectedValueOnce({
      response: {
        data: {
          detail: "A persona with the name 'AI Platform Engineer' already exists for this account.",
        },
      },
    });

    render(
      <PersonaManagementModal
        isOpen={true}
        onClose={vi.fn()}
        activePersonaId="p-universal"
      />
    );

    await waitFor(() => {
      expect(screen.getByTestId("edit-persona-btn-p-specialized-1")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByTestId("edit-persona-btn-p-specialized-1"));

    fireEvent.click(screen.getByTestId("save-persona-btn"));

    await waitFor(() => {
      expect(
        screen.getByText(/A persona with the name 'AI Platform Engineer' already exists/i)
      ).toBeInTheDocument();
    });
  });

  it("sets a persona as login default", async () => {
    api.setDefaultPersona.mockResolvedValueOnce({ status: "success" });

    render(
      <PersonaManagementModal
        isOpen={true}
        onClose={vi.fn()}
        activePersonaId="p-universal"
      />
    );

    await waitFor(() => {
      expect(screen.getByTestId("set-default-btn-p-specialized-1")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByTestId("set-default-btn-p-specialized-1"));

    await waitFor(() => {
      expect(api.setDefaultPersona).toHaveBeenCalledWith("p-specialized-1");
    });
  });

  it("creates a new specialized persona", async () => {
    api.createCandidatePersona.mockResolvedValueOnce({
      id: "p-new",
      name: "MLOps Engineer",
      is_common_persona: false,
      headline: "Model Pipelines & Registry",
      seniority_level: "mid",
      years_experience: 3,
      target_roles: ["MLOps Engineer"],
      is_default: false,
      skill_count: 3,
      block_count: 0,
    });

    render(
      <PersonaManagementModal
        isOpen={true}
        onClose={vi.fn()}
        activePersonaId="p-universal"
      />
    );

    fireEvent.click(screen.getByTestId("add-persona-btn"));

    expect(screen.getByTestId("create-persona-form")).toBeInTheDocument();

    fireEvent.change(screen.getByTestId("create-persona-name-input"), {
      target: { value: "MLOps Engineer" },
    });

    fireEvent.click(screen.getByTestId("submit-create-persona-btn"));

    await waitFor(() => {
      expect(api.createCandidatePersona).toHaveBeenCalledWith(
        expect.objectContaining({
          name: "MLOps Engineer",
        })
      );
    });
  });

  it("hides persona list and footer actions when editing, and returns to list via bottom-left back button", async () => {
    render(
      <PersonaManagementModal
        isOpen={true}
        onClose={vi.fn()}
        activePersonaId="p-universal"
      />
    );

    await waitFor(() => {
      expect(screen.getByTestId("edit-persona-btn-p-specialized-1")).toBeInTheDocument();
      expect(screen.getByTestId("persona-list")).toBeInTheDocument();
      expect(screen.getByTestId("add-persona-btn")).toBeInTheDocument();
      expect(screen.getByRole("button", { name: "Done" })).toBeInTheDocument();
    });

    // Enter edit mode
    fireEvent.click(screen.getByTestId("edit-persona-btn-p-specialized-1"));

    // In edit mode: edit form is shown, persona list is HIDDEN, and Add/Done footer buttons are REMOVED
    expect(screen.getByTestId("edit-persona-form")).toBeInTheDocument();
    expect(screen.queryByTestId("persona-list")).not.toBeInTheDocument();
    expect(screen.queryByTestId("add-persona-btn")).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Done" })).not.toBeInTheDocument();

    // Bottom-left Back to Persona List button is rendered
    const backBtn = screen.getByTestId("back-to-persona-list-btn");
    expect(backBtn).toBeInTheDocument();
    expect(backBtn).toHaveTextContent("Back to Persona List");

    // Click Back to Persona List
    fireEvent.click(backBtn);

    // Edit form unmounted and Persona list restored
    expect(screen.queryByTestId("edit-persona-form")).not.toBeInTheDocument();
    expect(screen.getByTestId("persona-list")).toBeInTheDocument();
    expect(screen.getByTestId("add-persona-btn")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Done" })).toBeInTheDocument();
  });

  it("hides persona list and footer actions when creating, and returns to list via bottom-left back button", async () => {
    render(
      <PersonaManagementModal
        isOpen={true}
        onClose={vi.fn()}
        activePersonaId="p-universal"
      />
    );

    await waitFor(() => {
      expect(screen.getByTestId("persona-list")).toBeInTheDocument();
    });

    // Enter create mode
    fireEvent.click(screen.getByTestId("add-persona-btn"));

    // In create mode: create form is shown, persona list is HIDDEN, and Add/Done footer buttons are REMOVED
    expect(screen.getByTestId("create-persona-form")).toBeInTheDocument();
    expect(screen.queryByTestId("persona-list")).not.toBeInTheDocument();
    expect(screen.queryByTestId("add-persona-btn")).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Done" })).not.toBeInTheDocument();

    // Bottom-left Back to Persona List button is rendered
    const backBtn = screen.getByTestId("back-to-persona-list-btn");
    expect(backBtn).toBeInTheDocument();
    expect(backBtn).toHaveTextContent("Back to Persona List");

    // Click Back to Persona List
    fireEvent.click(backBtn);

    // Create form unmounted and Persona list restored
    expect(screen.queryByTestId("create-persona-form")).not.toBeInTheDocument();
    expect(screen.getByTestId("persona-list")).toBeInTheDocument();
    expect(screen.getByTestId("add-persona-btn")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Done" })).toBeInTheDocument();
  });

  it("renders 7-dimension profile completeness overview and missing checklist items", async () => {
    const personasWithCompleteness = [
      {
        ...mockPersonas[0],
        completeness_score: 75,
        completeness: {
          completeness_score: 75,
          status: "grounded_ready",
          missing_steps: [
            {
              pillar: "hackathons_competitions",
              potential_gain_pct: 10,
              prompt: "Add Hackathons, Awards, or LeetCode achievements to stand out.",
            },
          ],
        },
      },
    ];
    api.getCandidatePersonas.mockResolvedValueOnce(personasWithCompleteness);

    render(
      <PersonaManagementModal
        isOpen={true}
        onClose={vi.fn()}
        activePersonaId="p-universal"
      />
    );

    await waitFor(() => {
      expect(screen.getByTestId("profile-completeness-overview")).toBeInTheDocument();
      expect(screen.getByText("75% Complete")).toBeInTheDocument();
      expect(
        screen.getByText(/Add Hackathons, Awards, or LeetCode achievements/i)
      ).toBeInTheDocument();
    });
  });

  it("renders zero-state experience as '0y experience' and pre-fills 0 into edit form for uncalibrated personas", async () => {
    const zeroStatePersona = [
      {
        id: "p-zero",
        name: "Admin Profile",
        is_common_persona: true,
        headline: "",
        seniority_level: "entry",
        years_experience: 0,
        target_roles: [],
        is_default: true,
        skill_count: 0,
        block_count: 0,
        skills: [],
      },
    ];
    api.getCandidatePersonas.mockResolvedValueOnce(zeroStatePersona);

    render(
      <PersonaManagementModal
        isOpen={true}
        onClose={vi.fn()}
        activePersonaId="p-zero"
      />
    );

    await waitFor(() => {
      expect(screen.getByText("0y experience")).toBeInTheDocument();
      expect(screen.queryByText("10y experience")).not.toBeInTheDocument();
      expect(screen.getByTestId("upload-cv-card-btn-p-zero")).toBeInTheDocument();
    });

    // Enter edit mode
    fireEvent.click(screen.getByTestId("edit-persona-btn-p-zero"));

    // Check that years experience input is 0, NOT 10 or 3
    const yearsInput = screen.getByDisplayValue("0");
    expect(yearsInput).toBeInTheDocument();
    expect(yearsInput.getAttribute("type")).toBe("number");
  });

  it("handles resume document file upload and auto-fills persona edit fields", async () => {
    const zeroStatePersona = [
      {
        id: "p-zero",
        name: "Admin Profile",
        is_common_persona: true,
        headline: "",
        seniority_level: "entry",
        years_experience: 0,
        target_roles: [],
        is_default: true,
        skill_count: 0,
        block_count: 0,
      },
    ];
    api.getCandidatePersonas.mockResolvedValueOnce(zeroStatePersona);
    api.parseResumeDocument.mockResolvedValueOnce({
      full_name: "Alex Mercer",
      headline: "Distributed Systems & Machine Learning Engineer",
      seniority_level: "senior",
      years_experience: 5,
      target_roles: ["Backend Architect", "MLOps Engineer"],
      skills: ["Python", "FastAPI", "PostgreSQL", "PyTorch"],
      education: [
        {
          degree: "B.S. Computer Science",
          major: "Computer Systems",
          institution: "Stanford University",
          graduation_year: 2021,
          institution_tier: "tier_1",
        },
      ],
      blocks: [
        {
          category: "work_experience",
          title: "Senior Engineer",
          organization: "Tech Corp",
          content: "Built real-time streaming pipeline processing 10k eps.",
          metrics: { speedup: "4x" },
          skills: ["Python", "Kafka"],
        },
      ],
    });

    render(
      <PersonaManagementModal
        isOpen={true}
        onClose={vi.fn()}
        activePersonaId="p-zero"
      />
    );

    await waitFor(() => {
      expect(screen.getByTestId("edit-persona-btn-p-zero")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByTestId("edit-persona-btn-p-zero"));

    const fileInput = screen.getByTestId("persona-cv-file-input");
    const fakeFile = new File(["dummy resume content"], "resume.pdf", {
      type: "application/pdf",
    });

    fireEvent.change(fileInput, { target: { files: [fakeFile] } });

    await waitFor(() => {
      expect(api.parseResumeDocument).toHaveBeenCalledWith(fakeFile);
      expect(screen.getByTestId("cv-parse-success")).toBeInTheDocument();
      expect(screen.getByText(/1 career block staged/i)).toBeInTheDocument();
    });

    // Check that form inputs were auto-filled
    expect(screen.getByTestId("edit-persona-headline-input")).toHaveValue(
      "Distributed Systems & Machine Learning Engineer"
    );
    expect(screen.getByDisplayValue("5")).toBeInTheDocument(); // Years of experience
    expect(
      screen.getByDisplayValue("Backend Architect, MLOps Engineer")
    ).toBeInTheDocument();
    expect(
      screen.getByDisplayValue("Python, FastAPI, PostgreSQL, PyTorch")
    ).toBeInTheDocument();
  });

  it("handles resume text paste and auto-fills persona edit fields", async () => {
    const zeroStatePersona = [
      {
        id: "p-zero",
        name: "Admin Profile",
        is_common_persona: true,
        headline: "",
        seniority_level: "entry",
        years_experience: 0,
        target_roles: [],
        is_default: true,
        skill_count: 0,
        block_count: 0,
      },
    ];
    api.getCandidatePersonas.mockResolvedValueOnce(zeroStatePersona);
    api.parseResumeText.mockResolvedValueOnce({
      headline: "Senior Cloud Architect",
      seniority_level: "lead",
      years_experience: 8,
      target_roles: ["Staff Infrastructure Engineer"],
      skills: ["Kubernetes", "Terraform", "Go"],
      blocks: [],
    });

    render(
      <PersonaManagementModal
        isOpen={true}
        onClose={vi.fn()}
        activePersonaId="p-zero"
      />
    );

    await waitFor(() => {
      expect(screen.getByTestId("edit-persona-btn-p-zero")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByTestId("edit-persona-btn-p-zero"));

    // Open paste text section
    fireEvent.click(screen.getByRole("button", { name: /Paste Text/i }));

    const textarea = screen.getByTestId("paste-resume-textarea");
    expect(textarea).toBeInTheDocument();

    fireEvent.change(textarea, {
      target: {
        value: "Senior Cloud Architect with 8 years building Kubernetes platforms.",
      },
    });

    fireEvent.click(screen.getByTestId("submit-resume-text-btn"));

    await waitFor(() => {
      expect(api.parseResumeText).toHaveBeenCalledWith(
        "Senior Cloud Architect with 8 years building Kubernetes platforms."
      );
      expect(screen.getByTestId("cv-parse-success")).toBeInTheDocument();
    });

    expect(screen.getByTestId("edit-persona-headline-input")).toHaveValue(
      "Senior Cloud Architect"
    );
    expect(screen.getByDisplayValue("8")).toBeInTheDocument();
    expect(
      screen.getByDisplayValue("Staff Infrastructure Engineer")
    ).toBeInTheDocument();
    expect(
      screen.getByDisplayValue("Kubernetes, Terraform, Go")
    ).toBeInTheDocument();
  });

  it("persists staged CV blocks via createCVBlock when saving an auto-filled persona", async () => {
    const zeroStatePersona = [
      {
        id: "p-zero",
        name: "Admin Profile",
        is_common_persona: true,
        headline: "",
        seniority_level: "entry",
        years_experience: 0,
        target_roles: [],
        is_default: true,
        skill_count: 0,
        block_count: 0,
      },
    ];
    api.getCandidatePersonas.mockResolvedValue(zeroStatePersona);
    api.updateCandidatePersona.mockResolvedValueOnce({
      ...zeroStatePersona[0],
      years_experience: 4,
    });
    api.createCVBlock.mockResolvedValue({ id: "block-1", title: "Core Platform" });

    api.parseResumeDocument.mockResolvedValueOnce({
      headline: "Platform Engineer",
      seniority_level: "mid",
      years_experience: 4,
      target_roles: ["Platform Engineer"],
      skills: ["Docker", "Kubernetes"],
      blocks: [
        {
          category: "work_experience",
          title: "Core Platform",
          organization: "Acme",
          content: "Maintained Kubernetes clusters",
          metrics: {},
          skills: ["Kubernetes"],
        },
      ],
    });

    render(
      <PersonaManagementModal
        isOpen={true}
        onClose={vi.fn()}
        activePersonaId="p-zero"
      />
    );

    await waitFor(() => {
      expect(screen.getByTestId("edit-persona-btn-p-zero")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByTestId("edit-persona-btn-p-zero"));

    const fileInput = screen.getByTestId("persona-cv-file-input");
    const fakeFile = new File(["dummy cv"], "cv.pdf", { type: "application/pdf" });
    fireEvent.change(fileInput, { target: { files: [fakeFile] } });

    await waitFor(() => {
      expect(screen.getByTestId("cv-parse-success")).toBeInTheDocument();
    });

    // Save the persona
    fireEvent.click(screen.getByTestId("save-persona-btn"));

    await waitFor(() => {
      expect(api.updateCandidatePersona).toHaveBeenCalled();
      expect(api.createCVBlock).toHaveBeenCalledWith(
        expect.objectContaining({
          title: "Core Platform",
          organization: "Acme",
          persona_ids: ["p-zero"],
        })
      );
    });
  });
});
