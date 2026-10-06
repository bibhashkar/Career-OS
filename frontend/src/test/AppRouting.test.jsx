import React from "react";
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { App } from "../App";

describe("App Routing and Navigation", () => {
  it("renders the Dashboard view on default '/' route", () => {
    render(
      <MemoryRouter initialEntries={["/"]}>
        <App />
      </MemoryRouter>
    );

    expect(
      screen.getByText(/Career Intelligence & Hunter/i)
    ).toBeInTheDocument();
    expect(
      screen.getByPlaceholderText(/Target role or skills/i)
    ).toBeInTheDocument();
  });

  it("renders CVTailorView empty state on '/cv-tailor' route without selected job", () => {
    render(
      <MemoryRouter initialEntries={["/cv-tailor"]}>
        <App />
      </MemoryRouter>
    );

    expect(screen.getByText("No Target Job Selected")).toBeInTheDocument();
    expect(screen.getByText("Go to Job Discovery")).toBeInTheDocument();
  });

  it("renders InterviewSimulator on '/interview' route", () => {
    render(
      <MemoryRouter initialEntries={["/interview"]}>
        <App />
      </MemoryRouter>
    );

    expect(screen.getByText("Technical Mock Interview")).toBeInTheDocument();
    expect(screen.getByText(/Thread Checkpoint:/i)).toBeInTheDocument();
  });

  it("renders InterviewSimulator with specific threadId on '/interview/:threadId'", () => {
    render(
      <MemoryRouter initialEntries={["/interview/thread_custom_123"]}>
        <App />
      </MemoryRouter>
    );

    expect(screen.getByText(/Thread Checkpoint: thread_custom_123/i)).toBeInTheDocument();
  });
});
