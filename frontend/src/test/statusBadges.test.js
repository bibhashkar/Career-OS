import { describe, it, expect } from "vitest";
import { getStatusBadgeClass } from "../utils/statusBadges";

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
});
