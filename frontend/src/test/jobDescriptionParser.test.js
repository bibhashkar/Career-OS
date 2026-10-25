import { describe, it, expect } from "vitest";
import {
  parseJobDescription,
  tokenizeHighlightedText,
} from "../utils/jobDescriptionParser";

const sampleJobText = `
About Render:
At Render, we're building the modern cloud platform for developers. Our mission is to eliminate tradeoffs.
Our platform is trusted by over 7 million developers worldwide.

About the Role:
Billing is mission-critical to Render's success. We are seeking a Senior Distributed Systems Engineer.

What You'll Do:
• Architect high-throughput distributed payment ledger pipelines in Python and Go.
• Build low-latency database queries with PostgreSQL and Redis.
• Collaborate with product teams to design billing metering services.

Requirements:
- 5+ years of experience building distributed systems.
- Strong proficiency in Python, PostgreSQL, and Kubernetes.
- Experience with high-availability systems.

Bonus Points:
• Experience with Kafka or message brokers.
• Familiarity with H-1B compliance standards.

Benefits:
• 100% employer-covered health insurance.
• Unlimited PTO and home office stipend.

APPLYING TO RENDER:
We're seeking candidates who possess high integrity, humility, and an insatiable drive to learn.
Equal Opportunity Employer: We celebrate diversity and are committed to creating an inclusive environment.
`;

describe("jobDescriptionParser utility", () => {
  it("parses headings and categorizes sections accurately", () => {
    const parsed = parseJobDescription(sampleJobText);

    expect(parsed.summary).toContain("At Render");
    expect(parsed.responsibilities.length).toBeGreaterThanOrEqual(2);
    expect(parsed.responsibilities[0]).toContain(
      "Architect high-throughput distributed payment ledger",
    );

    expect(parsed.requirements.length).toBeGreaterThanOrEqual(2);
    expect(parsed.requirements[0]).toContain("5+ years of experience");

    expect(parsed.niceToHave.length).toBeGreaterThanOrEqual(1);
    expect(parsed.niceToHave[0]).toContain("Kafka");

    expect(parsed.benefits.length).toBeGreaterThanOrEqual(1);
    expect(parsed.yearsExperience).toBe("5+ years of experience");

    expect(parsed.boilerplates.length).toBeGreaterThanOrEqual(1);
    expect(parsed.boilerplates[0].title).toMatch(/APPLYING TO RENDER/i);
  });

  it("handles empty or malformed inputs without throwing errors", () => {
    const emptyResult = parseJobDescription("");
    expect(emptyResult.summary).toBe("");
    expect(emptyResult.responsibilities).toEqual([]);
    expect(emptyResult.requirements).toEqual([]);
    expect(emptyResult.sections).toEqual([]);

    const nullResult = parseJobDescription(null);
    expect(nullResult.summary).toBe("");
    expect(nullResult.sections).toEqual([]);
  });

  it("tokenizes text with matched skills, missing skills, and years of experience", () => {
    const text =
      "We require 5+ years of experience with Python, Kubernetes, and Triton.";
    const matched = ["Python", "Kubernetes"];
    const missing = ["Triton"];

    const segments = tokenizeHighlightedText(text, matched, missing);

    const pythonSeg = segments.find((s) => s.text === "Python");
    expect(pythonSeg).toBeDefined();
    expect(pythonSeg.type).toBe("matched");

    const tritonSeg = segments.find((s) => s.text === "Triton");
    expect(tritonSeg).toBeDefined();
    expect(tritonSeg.type).toBe("missing");

    const yoeSeg = segments.find((s) => s.type === "yoe");
    expect(yoeSeg).toBeDefined();
    expect(yoeSeg.text).toMatch(/5\+\s*years/i);
  });
});
