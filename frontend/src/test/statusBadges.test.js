import { describe, it, expect } from "vitest";
import {
  getStatusBadgeClass,
  formatWorkplaceType,
} from "../utils/statusBadges";

describe("statusBadges utility", () => {
  it("returns emerald badge styling for successful/completed/healthy/active statuses", () => {
    expect(getStatusBadgeClass("success")).toContain("emerald");
    expect(getStatusBadgeClass("completed")).toContain("emerald");
    expect(getStatusBadgeClass("active")).toContain("emerald");
    expect(getStatusBadgeClass("healthy")).toContain("emerald");
    expect(getStatusBadgeClass("COMPLETED")).toContain("emerald");
  });

  it("returns sky badge styling for in-progress/running/pending statuses", () => {
    expect(getStatusBadgeClass("running")).toContain("sky");
    expect(getStatusBadgeClass("in_progress")).toContain("sky");
    expect(getStatusBadgeClass("pending")).toContain("sky");
    expect(getStatusBadgeClass("syncing")).toContain("sky");
  });

  it("returns amber badge styling for warning/degraded/caution statuses", () => {
    expect(getStatusBadgeClass("warning")).toContain("amber");
    expect(getStatusBadgeClass("degraded")).toContain("amber");
    expect(getStatusBadgeClass("tripped")).toContain("amber");
    expect(getStatusBadgeClass("discrepancy")).toContain("amber");
  });

  it("returns rose badge styling for failure/error/crashed/dead statuses", () => {
    expect(getStatusBadgeClass("failed")).toContain("rose");
    expect(getStatusBadgeClass("error")).toContain("rose");
    expect(getStatusBadgeClass("crashed")).toContain("rose");
    expect(getStatusBadgeClass("dead")).toContain("rose");
  });

  it("returns slate badge styling for unknown/idle/cancelled statuses", () => {
    expect(getStatusBadgeClass("unknown")).toContain("slate");
    expect(getStatusBadgeClass("idle")).toContain("slate");
    expect(getStatusBadgeClass(null)).toContain("slate");
  });

  describe("formatWorkplaceType helper", () => {
    it("formats ON_SITE and variations to On-Site", () => {
      expect(formatWorkplaceType("ON_SITE")).toBe("On-Site");
      expect(formatWorkplaceType("on_site")).toBe("On-Site");
      expect(formatWorkplaceType("onsite")).toBe("On-Site");
      expect(formatWorkplaceType("on-site")).toBe("On-Site");
    });

    it("formats HYBRID to Hybrid and REMOTE to Remote", () => {
      expect(formatWorkplaceType("HYBRID")).toBe("Hybrid");
      expect(formatWorkplaceType("hybrid")).toBe("Hybrid");
      expect(formatWorkplaceType("REMOTE")).toBe("Remote");
      expect(formatWorkplaceType("remote")).toBe("Remote");
    });

    it("handles falsy and custom workplace types gracefully", () => {
      expect(formatWorkplaceType("")).toBe("");
      expect(formatWorkplaceType(null)).toBe("");
      expect(formatWorkplaceType(undefined)).toBe("");
      expect(formatWorkplaceType("in_office")).toBe("In-Office");
    });
  });
});
