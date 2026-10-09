import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { JobProvenanceBadge } from "../components/JobProvenanceBadge";
import { AddJobModal } from "../components/AddJobModal";

describe("JobProvenanceBadge component", () => {
  it("renders verified career site badge for high confidence direct ATS jobs", () => {
    const job = {
      data_origin: "live",
      source_confidence: "high",
    };
    render(<JobProvenanceBadge job={job} />);
    expect(screen.getByTestId("badge-verified-ats")).toHaveTextContent("Verified Careers Site");
  });

  it("renders manual import badge for user pasted or manual roles", () => {
    const job = {
      data_origin: "manual",
      source_confidence: "high",
    };
    render(<JobProvenanceBadge job={job} />);
    expect(screen.getByTestId("badge-manual")).toHaveTextContent("Manual Import");
  });

  it("renders demo role badge for fixture jobs", () => {
    const job = {
      data_origin: "demo",
    };
    render(<JobProvenanceBadge job={job} />);
    expect(screen.getByTestId("badge-demo")).toHaveTextContent("Demo Role");
  });

  it("renders aggregator unverified badge for legacy or scraped jobs", () => {
    const job = {
      data_origin: "legacy",
      source_confidence: "low",
    };
    render(<JobProvenanceBadge job={job} />);
    expect(screen.getByTestId("badge-aggregator")).toHaveTextContent("Aggregator / Unverified");
  });

  it("renders cross-checked badge when secondary verification is verified", () => {
    const job = {
      data_origin: "live",
      source_confidence: "high",
      verification: {
        status: "verified",
      },
    };
    render(<JobProvenanceBadge job={job} />);
    expect(screen.getByTestId("badge-cross-checked-verified")).toHaveTextContent("Cross-Checked");
  });

  it("renders discrepancy badge when cross-check detects salary/status mismatch", () => {
    const job = {
      data_origin: "live",
      source_confidence: "high",
      verification: {
        status: "discrepancy",
      },
    };
    render(<JobProvenanceBadge job={job} />);
    expect(screen.getByTestId("badge-cross-checked-discrepancy")).toHaveTextContent("Discrepancy Found");
  });
});

describe("AddJobModal component", () => {
  it("renders modal when open and switches between URL and Paste tabs", () => {
    const handleClose = vi.fn();
    render(<AddJobModal isOpen={true} onClose={handleClose} onJobAdded={vi.fn()} />);

    expect(screen.getByText("Import Job Posting")).toBeInTheDocument();
    expect(screen.getByText("Direct ATS URL")).toBeInTheDocument();
    expect(screen.getByText("Paste Description")).toBeInTheDocument();

    // Switch to paste tab
    fireEvent.click(screen.getByText("Paste Description"));
    expect(screen.getByText("Job Description")).toBeInTheDocument();
    expect(screen.getByText("Role Title")).toBeInTheDocument();
  });

  it("does not render when isOpen is false", () => {
    const { container } = render(
      <AddJobModal isOpen={false} onClose={vi.fn()} onJobAdded={vi.fn()} />
    );
    expect(container).toBeEmptyDOMElement();
  });
});
