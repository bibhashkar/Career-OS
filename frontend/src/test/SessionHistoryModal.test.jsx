import React from "react";
import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { SessionHistoryModal } from "../components/SessionHistoryModal";

describe("SessionHistoryModal Component", () => {
  const mockSessions = [
    {
      threadId: "thread_123",
      companyName: "Google",
      title: "Senior AI Engineer",
      timestamp: 1717200000000,
    },
    {
      threadId: "thread_456",
      companyName: "Meta",
      title: "ML Infra Engineer",
      timestamp: 1717100000000,
    },
  ];

  it("does not render when isOpen is false", () => {
    const { container } = render(
      <SessionHistoryModal
        isOpen={false}
        onClose={() => {}}
        sessions={mockSessions}
        activeThreadId="thread_123"
        onResumeSession={() => {}}
        onDeleteSession={() => {}}
        onClearAllSessions={() => {}}
      />
    );
    expect(container.firstChild).toBeNull();
  });

  it("renders list of sessions and active session badge", () => {
    render(
      <SessionHistoryModal
        isOpen={true}
        onClose={() => {}}
        sessions={mockSessions}
        activeThreadId="thread_123"
        onResumeSession={() => {}}
        onDeleteSession={() => {}}
        onClearAllSessions={() => {}}
      />
    );

    expect(screen.getByText("Interview Sessions History")).toBeInTheDocument();
    expect(screen.getByText("Google")).toBeInTheDocument();
    expect(screen.getByText("Meta")).toBeInTheDocument();
    expect(screen.getByText("Active")).toBeInTheDocument();
  });

  it("triggers onResumeSession callback when clicking Resume button", () => {
    const onResume = vi.fn();
    render(
      <SessionHistoryModal
        isOpen={true}
        onClose={() => {}}
        sessions={mockSessions}
        activeThreadId="thread_123"
        onResumeSession={onResume}
        onDeleteSession={() => {}}
        onClearAllSessions={() => {}}
      />
    );

    // Click resume on the non-active session
    const resumeButtons = screen.getAllByRole("button", { name: /Resume/i });
    expect(resumeButtons[0]).toBeDisabled(); // thread_123 is active
    expect(resumeButtons[1]).not.toBeDisabled(); // thread_456

    fireEvent.click(resumeButtons[1]);
    expect(onResume).toHaveBeenCalledWith("thread_456");
  });

  it("triggers onDeleteSession callback when clicking trash button", () => {
    const onDelete = vi.fn();
    render(
      <SessionHistoryModal
        isOpen={true}
        onClose={() => {}}
        sessions={mockSessions}
        activeThreadId="thread_123"
        onResumeSession={() => {}}
        onDeleteSession={onDelete}
        onClearAllSessions={() => {}}
      />
    );

    const deleteButtons = screen.getAllByTitle("Delete Session");
    fireEvent.click(deleteButtons[0]);
    expect(onDelete).toHaveBeenCalledWith("thread_123");
  });
});
