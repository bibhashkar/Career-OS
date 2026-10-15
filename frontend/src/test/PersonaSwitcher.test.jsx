import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { PersonaSwitcher } from "../components/PersonaSwitcher";
import * as api from "../services/api";

vi.mock("../services/api", () => ({
  getCandidatePersonas: vi.fn(),
  setDefaultPersona: vi.fn(),
}));

const mockPersonas = [
  {
    id: "persona-001",
    name: "Universal Profile",
    is_common_persona: true,
    is_default: true,
    target_roles: ["Senior Software Engineer"],
  },
  {
    id: "persona-002",
    name: "AI Platform Engineer",
    is_common_persona: false,
    is_default: false,
    target_roles: ["AI Infrastructure Engineer"],
  },
];

describe("PersonaSwitcher Component", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("loads personas on mount and displays default persona name", async () => {
    api.getCandidatePersonas.mockResolvedValueOnce(mockPersonas);

    render(<PersonaSwitcher onPersonaChange={vi.fn()} onOpenAudit={vi.fn()} />);

    expect(api.getCandidatePersonas).toHaveBeenCalledTimes(1);
    expect(await screen.findByText("Universal Profile")).toBeInTheDocument();
  });

  it("opens dropdown and displays available personas on button click", async () => {
    api.getCandidatePersonas.mockResolvedValueOnce(mockPersonas);

    render(<PersonaSwitcher onPersonaChange={vi.fn()} onOpenAudit={vi.fn()} />);

    const switcherBtn = await screen.findByTitle(/Switch active career persona lens/i);
    fireEvent.click(switcherBtn);

    expect(await screen.findByText("Target Career Personas")).toBeInTheDocument();
    expect(screen.getByText("AI Platform Engineer")).toBeInTheDocument();
  });

  it("calls setDefaultPersona and onPersonaChange when a persona is selected", async () => {
    api.getCandidatePersonas.mockResolvedValue(mockPersonas);
    api.setDefaultPersona.mockResolvedValueOnce({ status: "success" });

    const handlePersonaChange = vi.fn();
    render(
      <PersonaSwitcher
        onPersonaChange={handlePersonaChange}
        onOpenAudit={vi.fn()}
      />
    );

    const switcherBtn = await screen.findByTitle(/Switch active career persona lens/i);
    fireEvent.click(switcherBtn);

    const aiPersonaBtn = await screen.findByText("AI Platform Engineer");
    fireEvent.click(aiPersonaBtn);

    await waitFor(() => {
      expect(api.setDefaultPersona).toHaveBeenCalledWith("persona-002");
    });
    expect(handlePersonaChange).toHaveBeenCalledWith(
      expect.objectContaining({ id: "persona-002", name: "AI Platform Engineer" })
    );
  });

  it("triggers onOpenAudit when clicking the 360 Audit button in dropdown", async () => {
    api.getCandidatePersonas.mockResolvedValueOnce(mockPersonas);

    const handleOpenAudit = vi.fn();
    render(
      <PersonaSwitcher
        onPersonaChange={vi.fn()}
        onOpenAudit={handleOpenAudit}
      />
    );

    const switcherBtn = await screen.findByTitle(/Switch active career persona lens/i);
    fireEvent.click(switcherBtn);

    const auditBtn = await screen.findByRole("button", { name: /360° Audit/i });
    fireEvent.click(auditBtn);

    expect(handleOpenAudit).toHaveBeenCalledTimes(1);
  });
});
