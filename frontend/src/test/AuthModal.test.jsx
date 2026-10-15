import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { AuthModal } from "../components/AuthModal";
import * as api from "../services/api";

vi.mock("../services/api", () => ({
  login: vi.fn(),
  register: vi.fn(),
}));

describe("AuthModal Component", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("does not render when isOpen is false", () => {
    render(<AuthModal isOpen={false} onClose={vi.fn()} onSuccess={vi.fn()} />);
    expect(screen.queryByText(/Sign In to Career-OS/i)).not.toBeInTheDocument();
  });

  it("renders Sign In form when isOpen is true", () => {
    render(<AuthModal isOpen={true} onClose={vi.fn()} onSuccess={vi.fn()} />);
    expect(screen.getByText(/Sign In to Career-OS/i)).toBeInTheDocument();
    expect(screen.getByPlaceholderText("name@example.com")).toBeInTheDocument();
    expect(screen.getByPlaceholderText("••••••••")).toBeInTheDocument();
  });

  it("switches to Create Account tab and shows registration inputs", () => {
    render(<AuthModal isOpen={true} onClose={vi.fn()} onSuccess={vi.fn()} />);

    const createTab = screen.getByTestId("tab-register");
    fireEvent.click(createTab);

    expect(screen.getByText(/Create Candidate Account/i)).toBeInTheDocument();
    expect(screen.getByPlaceholderText("e.g. Alex Smith")).toBeInTheDocument();
    expect(screen.getByText("Visa / Authorization")).toBeInTheDocument();
  });

  it("submits login credentials and calls onSuccess", async () => {
    const mockUser = {
      id: "u-123",
      email: "test@example.com",
      full_name: "Test Candidate",
    };
    api.login.mockResolvedValueOnce({
      access_token: "mock-jwt-token",
      user: mockUser,
      default_persona_id: "p-123",
    });

    const handleSuccess = vi.fn();
    const handleClose = vi.fn();

    render(
      <AuthModal
        isOpen={true}
        onClose={handleClose}
        onSuccess={handleSuccess}
      />
    );

    fireEvent.change(screen.getByPlaceholderText("name@example.com"), {
      target: { value: "test@example.com" },
    });
    fireEvent.change(screen.getByPlaceholderText("••••••••"), {
      target: { value: "Password123!" },
    });

    fireEvent.click(screen.getByTestId("auth-submit-btn"));

    await waitFor(() => {
      expect(api.login).toHaveBeenCalledWith("test@example.com", "Password123!");
      expect(handleSuccess).toHaveBeenCalledWith(mockUser);
      expect(handleClose).toHaveBeenCalled();
    });
  });

  it("triggers One-Click Demo Candidate login", async () => {
    const mockUser = {
      id: "demo-user",
      email: "demo@career-os.local",
      full_name: "Alex Smith (Demo)",
    };
    api.login.mockResolvedValueOnce({
      access_token: "demo-jwt-token",
      user: mockUser,
      default_persona_id: "demo-persona",
    });

    const handleSuccess = vi.fn();
    const handleClose = vi.fn();

    render(
      <AuthModal
        isOpen={true}
        onClose={handleClose}
        onSuccess={handleSuccess}
      />
    );

    const demoBtn = screen.getByTestId("demo-login-btn");
    fireEvent.click(demoBtn);

    await waitFor(() => {
      expect(api.login).toHaveBeenCalledWith(
        "demo@career-os.local",
        "DemoPassword123!"
      );
      expect(handleSuccess).toHaveBeenCalledWith(mockUser);
      expect(handleClose).toHaveBeenCalled();
    });
  });
});

