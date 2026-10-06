import React from "react";
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { ATSCard } from "../components/ATSCard";

describe("ATSCard Component", () => {
  it("renders passing ATS score with green status", () => {
    const feedback = {
      matched_keywords: ["Python", "FastAPI"],
      missing_keywords: [],
      keyword_density: 0.9,
      recommendations: ["Great keyword alignment."],
    };

    render(
      <ATSCard
        score={85.5}
        feedback={feedback}
        revisionCount={1}
        onRetry={() => {}}
      />
    );

    expect(screen.getByText(/ATS Match Score:\s*85\.5%/i)).toBeInTheDocument();
    expect(screen.getByText("PASSED (≥75%)")).toBeInTheDocument();
    expect(screen.getByText("Revision #1")).toBeInTheDocument();
    expect(screen.getByText("Python")).toBeInTheDocument();
    expect(screen.getByText("FastAPI")).toBeInTheDocument();
  });

  it("renders failing score and flags missing keywords", () => {
    const feedback = {
      matched_keywords: [],
      missing_keywords: ["Kubernetes", "PostgreSQL"],
      keyword_density: 0.5,
      recommendations: ["Incorporate missing system architecture skills."],
    };

    render(
      <ATSCard
        score={62.0}
        feedback={feedback}
        revisionCount={2}
        onRetry={() => {}}
      />
    );

    expect(screen.getByText(/ATS Match Score:\s*62%/i)).toBeInTheDocument();
    expect(screen.getByText("NEEDS REVISION (<75%)")).toBeInTheDocument();
    expect(screen.getByText("Revision #2")).toBeInTheDocument();
    expect(screen.getByText("Kubernetes")).toBeInTheDocument();
    expect(screen.getByText("PostgreSQL")).toBeInTheDocument();
  });
});
