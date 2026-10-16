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

  it("submits registration details and calls onSuccess", async () => {
    const mockUser = {
      id: "u-new",
      email: "newcand@example.com",
      full_name: "New Candidate",
    };
    api.register.mockResolvedValueOnce({
      access_token: "mock-reg-token",
      user: mockUser,
      default_persona_id: "p-new",
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

    fireEvent.click(screen.getByTestId("tab-register"));

    fireEvent.change(screen.getByPlaceholderText("e.g. Alex Smith"), {
      target: { value: "New Candidate" },
    });
    fireEvent.change(screen.getByPlaceholderText("name@example.com"), {
      target: { value: "newcand@example.com" },
    });
    fireEvent.change(screen.getByPlaceholderText("••••••••"), {
      target: { value: "SecurePass123!" },
    });

    fireEvent.click(screen.getByTestId("auth-submit-btn"));

    await waitFor(() => {
      expect(api.register).toHaveBeenCalledWith({
        email: "newcand@example.com",
        password: "SecurePass123!",
        full_name: "New Candidate",
        visa_status: "Citizen",
        remote_preference: "Remote",
        preferred_locations: ["Remote", "San Francisco, CA"],
      });
      expect(handleSuccess).toHaveBeenCalledWith(mockUser);
      expect(handleClose).toHaveBeenCalled();
    });
  });

  it("displays error message on authentication failure", async () => {
    api.login.mockRejectedValueOnce({
      response: { data: { detail: "Invalid email or password." } },
    });

    render(
      <AuthModal
        isOpen={true}
        onClose={vi.fn()}
        onSuccess={vi.fn()}
      />
    );

    fireEvent.change(screen.getByPlaceholderText("name@example.com"), {
      target: { value: "wrong@example.com" },
    });
    fireEvent.change(screen.getByPlaceholderText("••••••••"), {
      target: { value: "WrongPass" },
    });

    fireEvent.click(screen.getByTestId("auth-submit-btn"));

    await waitFor(() => {
      expect(screen.getByText("Invalid email or password.")).toBeInTheDocument();
    });
  });
});

