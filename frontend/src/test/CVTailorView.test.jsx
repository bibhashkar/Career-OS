import React from "react";
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { CVTailorView } from "../pages/CVTailorView";

describe("CVTailorView Component", () => {
  it("renders empty state when no job is selected", () => {
    render(
      <CVTailorView
        job={null}
        onBack={() => {}}
        onStartInterview={() => {}}
      />
    );

    expect(screen.getByText("No Target Job Selected")).toBeInTheDocument();
    expect(
      screen.getByText(/Select a target position from the Discovery dashboard/i)
    ).toBeInTheDocument();
    expect(screen.getByText("Go to Job Discovery")).toBeInTheDocument();
  });
});
