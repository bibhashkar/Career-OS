import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { CandidatePersonaPage } from "../pages/CandidatePersonaPage";
import * as api from "../services/api";

vi.mock("../services/api", () => ({
  getCandidatePersonas: vi.fn(),
  updateCandidatePersona: vi.fn(),
  deleteCandidatePersona: vi.fn(),
  setDefaultPersona: vi.fn(),
  createCandidatePersona: vi.fn(),
  parseResumeDocument: vi.fn(),
  parseResumeText: vi.fn(),
  getCVBlocks: vi.fn(),
  createCVBlock: vi.fn(),
  updateCVBlock: vi.fn(),
  deleteCVBlock: vi.fn(),
}));

describe("CandidatePersonaPage Full-Screen Dossier Workspace", () => {
  const mockPersonas = [
    {
      id: "p-universal",
      name: "Universal Profile",
      is_common_persona: true,
      headline: "Staff Full Stack Developer (12+ YOE) | Distributed Systems & Platform Engineering",
      seniority_level: "staff",
      years_experience: 12,
      min_salary: 195000,
      target_roles: ["Full Stack Developer", "Senior Software Engineer"],
      target_industries: ["FinTech", "HealthTech"],
      is_default: true,
      skill_count: 8,
      block_count: 2,
      skills: ["Python", "FastAPI", "React", "PostgreSQL", "Docker", "Kubernetes", "Kafka", "TypeScript"],
      visa_status: "Citizen",
      preferred_locations: ["Remote", "San Francisco, CA"],
      remote_preference: "Remote",
      completeness_score: 85,
      completeness: {
        missing_steps: [{ prompt: "Add LeetCode handle", potential_gain_pct: 15 }],
      },
      career_intelligence: {
        domain_expertise: [
          { domain: "HealthTech / HIPAA", years_experience: 5.0, regulatory_frameworks: ["HIPAA", "DICOM"] },
          { domain: "FinTech / Transactions", years_experience: 4.0, regulatory_frameworks: ["EDI/X12"] },
        ],
        education: [
          {
            degree: "Master of Science",
            major: "Management Information Systems",
            institution: "University of Nevada, Las Vegas",
            institution_tier: "tier_2",
            graduation_year: 2025,
            gpa: "3.9",
          },
          {
            degree: "Bachelor of Science",
            major: "Computer Science",
            institution: "San Jose State University",
            institution_tier: "standard",
            graduation_year: 2018,
            gpa: "3.8",
          },
        ],
        work_experience: [
          {
            company_name: "Render",
            job_title: "Staff Distributed Systems Engineer",
            location: "Remote",
            is_remote: true,
            start_date: "2021",
            end_date: "Present",
            seniority_level: "staff",
            industry_domain: "Cloud & Distributed Systems",
            bullets: [
              {
                raw_text: "Architected high-throughput payment ledgers processing $7B volume.",
                technologies_used: ["Python", "PostgreSQL"],
                metrics: [{ metric_type: "financial_volume", raw_metric: "$7B" }],
              },
            ],
          },
        ],
        skills_matrix: {
          backend_and_frameworks: ["Python", "FastAPI"],
          databases_and_caching: ["PostgreSQL"],
          cloud_and_devops: ["Docker", "Kubernetes"],
        },
        semantic_profile_summary: "Staff Engineer with 12+ YOE in distributed ledgers and cloud platform architecture.",
        external_links: {
          linkedin_url: "https://linkedin.com/in/test-candidate",
          github_url: "https://github.com/test-candidate",
        },
        source_provenance: {
          filename: "B_Kar_Resume.pdf",
          layout_type: "standard_single_column",
          recommended_pipeline: "deep_llm_structured",
          raw_text: "Full verbatim resume text of B Kar with experience at Render and degrees from UNLV.",
        },
      },
    },
  ];

  const mockBlocks = [
    {
      id: "block-1",
      title: "Payment Ledger Architecture",
      organization: "Render",
      category: "experience",
      content: "Scaled distributed payment ledger pipeline to 10k ops/sec with zero downtime.",
      metrics: { throughput: "10k ops/sec" },
      skills: ["Python", "PostgreSQL", "Kafka"],
      has_embedding: true,
    },
  ];

  beforeEach(() => {
    vi.clearAllMocks();
    api.getCandidatePersonas.mockResolvedValue(mockPersonas);
    api.getCVBlocks.mockResolvedValue(mockBlocks);
    api.updateCandidatePersona.mockResolvedValue(mockPersonas[0]);
    api.createCVBlock.mockResolvedValue(mockBlocks[0]);
    api.updateCVBlock.mockResolvedValue({
      ...mockBlocks[0],
      content: "Updated payment ledger scaling to 25k ops/sec.",
    });
    api.deleteCVBlock.mockResolvedValue({ status: "deleted" });
  });

  it("renders CandidatePersonaPage with 2-column layout, sidebar tracks, and all 6 dossier sections", async () => {
    render(<CandidatePersonaPage />);

    expect(await screen.findByTestId("candidate-persona-page")).toBeInTheDocument();

    // 1. Sidebar components
    expect(screen.getByTestId("persona-track-selector")).toBeInTheDocument();
    expect(screen.getByTestId("multi-source-ingestion-hub")).toBeInTheDocument();
    expect(screen.getByTestId("profile-completeness-radar")).toBeInTheDocument();
    expect(screen.getByText("85% Complete")).toBeInTheDocument();

    // 2. Main Canvas sections
    expect(screen.getByTestId("section-executive-identity")).toBeInTheDocument();
    expect(screen.getByTestId("section-domain-and-semantic")).toBeInTheDocument();
    expect(screen.getByTestId("section-work-experience")).toBeInTheDocument();
    expect(screen.getByTestId("section-education")).toBeInTheDocument();
    expect(screen.getByTestId("section-skills-matrix")).toBeInTheDocument();
    expect(screen.getByTestId("section-projects-awards")).toBeInTheDocument();

    // 3. Verify data binding
    expect(screen.getByDisplayValue(/Staff Full Stack Developer \(12\+ YOE\)/i)).toBeInTheDocument();
    expect(screen.getByText("Full Stack Developer")).toBeInTheDocument();
    expect(screen.getByText("HealthTech / HIPAA")).toBeInTheDocument();
    expect(screen.getByText("Staff Distributed Systems Engineer")).toBeInTheDocument();
    expect(screen.getByText("University of Nevada, Las Vegas")).toBeInTheDocument();
    expect(screen.getByText("San Jose State University")).toBeInTheDocument();
  });

  it("displays nested pgvector proof point cards under role tenure with quantified metrics", async () => {
    render(<CandidatePersonaPage />);

    expect(await screen.findByTestId("candidate-persona-page")).toBeInTheDocument();

    // Find persisted block matching company "Render"
    const blockCard = await screen.findByTestId("persisted-block-block-1");
    expect(blockCard).toBeInTheDocument();
    expect(screen.getByText(/Scaled distributed payment ledger pipeline to 10k ops\/sec/i)).toBeInTheDocument();
    expect(screen.getByText("10k ops/sec")).toBeInTheDocument();
    expect(screen.getByText("🟢 pgvector Embedded")).toBeInTheDocument();
  });

  it("allows adding and removing role tags", async () => {
    render(<CandidatePersonaPage />);

    expect(await screen.findByTestId("candidate-persona-page")).toBeInTheDocument();

    const roleInput = screen.getByPlaceholderText(/\+ Add Role/i);
    fireEvent.change(roleInput, { target: { value: "Principal Platform Architect" } });
    fireEvent.keyDown(roleInput, { key: "Enter", code: "Enter" });

    expect(screen.getByText("Principal Platform Architect")).toBeInTheDocument();

    // Remove existing role
    const removeBtn = screen.getAllByRole("button").find((btn) => btn.querySelector("svg") && btn.closest("span")?.textContent.includes("Full Stack Developer"));
    if (removeBtn) {
      fireEvent.click(removeBtn);
      expect(screen.queryByText("Full Stack Developer")).not.toBeInTheDocument();
    }
  });

  it("opens Raw Source Text Inspector drawer and displays verbatim text", async () => {
    render(<CandidatePersonaPage />);

    expect(await screen.findByTestId("candidate-persona-page")).toBeInTheDocument();

    const inspectBtn = screen.getByRole("button", { name: /Inspect Text/i });
    fireEvent.click(inspectBtn);

    const drawer = await screen.findByTestId("raw-source-inspector-drawer");
    expect(drawer).toBeInTheDocument();
    expect(screen.getByText(/Full verbatim resume text of B Kar with experience at Render/i)).toBeInTheDocument();
    expect(screen.getByText(/Source: B_Kar_Resume.pdf/i)).toBeInTheDocument();

    // Close drawer
    const closeBtn = screen.getByRole("button", { name: /Close Inspector/i });
    fireEvent.click(closeBtn);
    expect(screen.queryByTestId("raw-source-inspector-drawer")).not.toBeInTheDocument();
  });

  it("parses resume document, stages review banner, and commits to dossier", async () => {
    api.parseResumeDocument.mockResolvedValue({
      full_name: "B Kar",
      headline: "AI & Distributed Systems Architect",
      seniority_level: "staff",
      total_years_experience: 12,
      target_roles: ["Distributed Systems Architect"],
      all_skills_flat: ["Python", "Rust", "vLLM"],
      work_experience: [
        {
          company_name: "NexusAI",
          job_title: "Lead AI Engineer",
          start_date: "2023",
          end_date: "Present",
          bullets: [{ raw_text: "Built LLM inference engine serving 50k req/s." }],
        },
      ],
      education: [
        {
          degree: "Ph.D.",
          major: "Computer Science",
          institution: "MIT",
          graduation_year: 2026,
        },
      ],
      blocks: [
        {
          title: "LLM Inference Engine",
          organization: "NexusAI",
          category: "experience",
          content: "Built LLM inference engine serving 50k req/s.",
          metrics: { throughput: "50k req/s" },
          skills: ["Rust", "vLLM"],
        },
      ],
      career_intelligence: {
        source_provenance: {
          filename: "NexusAI_CV.pdf",
          layout_type: "standard_single_column",
          recommended_pipeline: "deep_llm_structured",
        },
      },
    });

    render(<CandidatePersonaPage />);

    expect(await screen.findByTestId("candidate-persona-page")).toBeInTheDocument();

    // Trigger upload
    const file = new File(["dummy pdf bytes"], "NexusAI_CV.pdf", { type: "application/pdf" });
    const input = document.getElementById("fullpage-cv-upload-input");
    Object.defineProperty(input, "files", { value: [file] });
    fireEvent.change(input);

    // Staged banner appears
    expect(await screen.findByTestId("staged-extraction-banner")).toBeInTheDocument();
    expect(screen.getByText(/Extraction Staged from: NexusAI_CV.pdf/i)).toBeInTheDocument();

    // Click Confirm & Commit
    const commitBtn = screen.getByRole("button", { name: /Confirm & Commit to Dossier/i });
    fireEvent.click(commitBtn);

    await waitFor(() => {
      expect(api.updateCandidatePersona).toHaveBeenCalled();
      expect(api.createCVBlock).toHaveBeenCalledWith(
        expect.objectContaining({
          title: "LLM Inference Engine",
          organization: "NexusAI",
        })
      );
    });
  });

  it("saves dossier changes via top save button", async () => {
    render(<CandidatePersonaPage />);

    expect(await screen.findByTestId("candidate-persona-page")).toBeInTheDocument();

    const saveBtn = screen.getByTestId("save-dossier-top-btn");
    fireEvent.click(saveBtn);

    await waitFor(() => {
      expect(api.updateCandidatePersona).toHaveBeenCalledWith(
        "p-universal",
        expect.objectContaining({
          name: "Universal Profile",
          headline: expect.stringContaining("Staff Full Stack Developer"),
        })
      );
    });
  });
});
