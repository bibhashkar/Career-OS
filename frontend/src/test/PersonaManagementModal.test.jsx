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
      expect(screen.getByText("Default Lens")).toBeInTheDocument();
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
});
