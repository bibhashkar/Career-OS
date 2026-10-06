import React from "react";
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { CompanyDossierCard } from "../components/CompanyDossierCard";

describe("CompanyDossierCard Component", () => {
  it("renders company dossier tech stack, business model, and news", () => {
    const dossier = {
      company_name: "NexusAI Labs",
      industry: "Artificial Intelligence",
      domain: "nexusai.com",
      business_model: "Enterprise AI workflow orchestration platforms.",
      tech_stack: ["Python", "FastAPI", "PostgreSQL", "LangGraph"],
      recent_news: [
        {
          title: "NexusAI Labs announces Series B for agentic infrastructure",
          source: "TechCrunch",
        },
      ],
    };

    render(<CompanyDossierCard dossier={dossier} />);

    expect(screen.getByText("NexusAI Labs")).toBeInTheDocument();
    expect(screen.getByText(/Artificial Intelligence • nexusai\.com/i)).toBeInTheDocument();
    expect(screen.getByText("Python")).toBeInTheDocument();
    expect(screen.getByText("FastAPI")).toBeInTheDocument();
    expect(screen.getByText("Enterprise AI workflow orchestration platforms.")).toBeInTheDocument();
    expect(screen.getByText(/NexusAI Labs announces Series B/i)).toBeInTheDocument();
  });
});
