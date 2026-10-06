import React from "react";
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { CVPreview } from "../components/CVPreview";

describe("CVPreview Component", () => {
  it("renders candidate title, target company, summary, and experience blocks", () => {
    const draft = {
      candidate_title: "Staff AI Engineer",
      target_company: "NexusAI Labs",
      professional_summary: "Experienced engineer specializing in LangGraph and distributed systems.",
      skills_highlighted: ["Python", "FastAPI", "PostgreSQL", "LangGraph"],
      experience_blocks: [
        {
          title: "Senior Backend Engineer",
          organization: "DataCorp",
          content: "Architected low-latency microservices with FastAPI handling 5k req/s.",
          metrics: { throughput: "5k req/s" },
        },
      ],
    };

    render(<CVPreview draft={draft} />);

    expect(screen.getByText("Staff AI Engineer")).toBeInTheDocument();
    expect(screen.getByText(/Targeted for NexusAI Labs/i)).toBeInTheDocument();
    expect(screen.getByText(/Experienced engineer specializing in LangGraph/i)).toBeInTheDocument();
    expect(screen.getByText("Python")).toBeInTheDocument();
    expect(screen.getByText("Senior Backend Engineer")).toBeInTheDocument();
    expect(screen.getByText(/Architected low-latency microservices/i)).toBeInTheDocument();
  });
});
