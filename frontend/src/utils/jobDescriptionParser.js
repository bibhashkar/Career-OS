/**
 * Job Description Smart Parser & Keyword Highlighter Utility.
 *
 * Transforms raw, unstructured ATS job posting descriptions into clean,
 * scannable, and modular sections with keyword & dealbreaker highlights.
 */

// Section category classifiers
const SECTION_PATTERNS = [
  {
    category: "company",
    title: "About the Company",
    regex:
      /^(?:about\s+(?:the\s+company|us|render|anthropic|stripe|google|openai|meta|amazon|[a-z0-9\s-]+)|who\s+we\s+are|company\s+overview|our\s+mission)\b/i,
  },
  {
    category: "role_overview",
    title: "About the Role",
    regex:
      /^(?:about\s+the\s+role|role\s+overview|position\s+overview|the\s+opportunity|role\s+summary|position\s+summary|overview)\b/i,
  },
  {
    category: "responsibilities",
    title: "Core Responsibilities",
    regex:
      /^(?:what\s+you(?:'ll|\swill)\s+do|responsibilities|key\s+duties|core\s+responsibilities|what\s+you\s+will\s+work\s+on|in\s+this\s+role(?:\s+you\s+will)?|what\s+you(?:'ll|\swill)\s+be\s+doing)\b/i,
  },
  {
    category: "requirements",
    title: "Requirements & Qualifications",
    regex:
      /^(?:what\s+you(?:'ll|\swill)\s+need|requirements|qualifications|minimum\s+qualifications|basic\s+qualifications|must\s+haves?|what\s+you\s+bring|what\s+we(?:'re|\sare)\s+looking\s+for|who\s+you\s+are)\b/i,
  },
  {
    category: "nice_to_have",
    title: "Bonus / Preferred Qualifications",
    regex:
      /^(?:preferred\s+qualifications|nice\s+to\s+haves?|bonus\s+points?|bonus\s+qualifications|what\s+will\s+set\s+you\s+apart|desired\s+skills?)\b/i,
  },
  {
    category: "tech_stack",
    title: "Tech Stack & Tools",
    regex:
      /^(?:tech\s+stack|technologies|tools\s+we\s+use|technology\s+stack)\b/i,
  },
  {
    category: "benefits",
    title: "Compensation & Benefits",
    regex:
      /^(?:benefits(?:\s+&\s+perks)?|perks|compensation(?:\s+&\s+benefits)?|what\s+we\s+offer|salary\s+&\s+benefits|why\s+join\s+us)\b/i,
  },
  {
    category: "boilerplate",
    title: "Equal Opportunity & Legal Notice",
    regex:
      /^(?:applying\s+to\s+[a-z0-9\s-]+|equal\s+opportunity(?:\s+employer)?|eeo(?:\s+statement)?|diversity,\s+equity|reasonable\s+accommodations?|notice\s+to\s+applicants|privacy\s+notice)\b/i,
  },
];

// Regex for extracting years of experience
const YOE_REGEX =
  /\b(\d+)\s*\+?\s*years?(?:\s+(?:of|in))?(?:\s+[\w-]+)*\s+experience\b|\b(\d+)\s*-\s*\d+\s*years?(?:\s+experience)?\b|\bat\s+least\s+(\d+)\s*years?\b|\bminimum\s+(?:of\s+)?(\d+)\s*years?\b|\b(\d+\+?)\s*years?\b/i;

/**
 * Parses raw job description into structured sections.
 */
export function parseJobDescription(rawText = "") {
  if (!rawText || !rawText.trim()) {
    return {
      summary: "",
      responsibilities: [],
      requirements: [],
      niceToHave: [],
      benefits: [],
      techStack: [],
      yearsExperience: null,
      boilerplates: [],
      sections: [],
    };
  }

  // Normalize line breaks
  const normalized = rawText.replace(/\r\n/g, "\n").replace(/\r/g, "\n").trim();

  // Split into raw blocks by double line breaks or heading-like lines
  const lines = normalized.split("\n");
  const rawSections = [];
  let currentTitle = "Overview";
  let currentCategory = "role_overview";
  let currentLines = [];

  const flushSection = () => {
    if (currentLines.length > 0) {
      const content = currentLines.join("\n").trim();
      if (content) {
        rawSections.push({
          title: currentTitle,
          category: currentCategory,
          content,
          bullets: extractBullets(content),
          isBoilerplate: currentCategory === "boilerplate",
        });
      }
    }
    currentLines = [];
  };

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i].trim();
    if (!line) {
      if (currentLines.length > 0) currentLines.push("");
      continue;
    }

    // Check if this line looks like a section header (short line or ends with colon or all-caps)
    const isHeadingShape =
      line.length < 80 &&
      (line.endsWith(":") ||
        line === line.toUpperCase() ||
        /^[A-Z][A-Za-z0-9\s,&/'-]+$/.test(line));

    let matchedHeading = null;
    if (isHeadingShape) {
      const cleanLine = line.replace(/[:#*_-]/g, "").trim();
      matchedHeading = SECTION_PATTERNS.find((p) => p.regex.test(cleanLine));
    }

    if (matchedHeading) {
      flushSection();
      currentTitle = line.replace(/[:#*_-]/g, "").trim();
      currentCategory = matchedHeading.category;
    } else {
      currentLines.push(lines[i]);
    }
  }
  flushSection();

  // Extract years of experience
  const yoeMatch = normalized.match(YOE_REGEX);
  const yearsExperience = yoeMatch ? yoeMatch[0] : null;

  // Extract structured parts
  const responsibilitiesSec = rawSections.find(
    (s) => s.category === "responsibilities",
  );
  const requirementsSec = rawSections.find(
    (s) => s.category === "requirements",
  );
  const niceToHaveSec = rawSections.find((s) => s.category === "nice_to_have");
  const benefitsSec = rawSections.find((s) => s.category === "benefits");
  const boilerplates = rawSections.filter((s) => s.category === "boilerplate");

  // Summary: First non-boilerplate section paragraph or first 2 sentences
  const overviewSec =
    rawSections.find(
      (s) => s.category === "role_overview" || s.category === "company",
    ) || rawSections[0];
  let summary = "";
  if (overviewSec) {
    const firstPara =
      overviewSec.content.split("\n\n")[0] || overviewSec.content;
    const sentences = firstPara.split(/(?<=[.!?])\s+/);
    summary = sentences.slice(0, 3).join(" ").trim();
  }

  return {
    summary,
    responsibilities: responsibilitiesSec ? responsibilitiesSec.bullets : [],
    requirements: requirementsSec ? requirementsSec.bullets : [],
    niceToHave: niceToHaveSec ? niceToHaveSec.bullets : [],
    benefits: benefitsSec ? benefitsSec.bullets : [],
    yearsExperience,
    boilerplates,
    sections: rawSections,
  };
}

/**
 * Extracts bullet points from a block of text.
 */
function extractBullets(text = "") {
  const lines = text.split("\n");
  const bullets = [];
  let currentBullet = "";

  for (const line of lines) {
    const trimmed = line.trim();
    if (!trimmed) continue;

    // Matches bullet starters like •, -, *, or numbered 1.
    const isBulletStart = /^([•\-*▪▫►–—]|\d+\.)\s+/.test(trimmed);

    if (isBulletStart) {
      if (currentBullet) bullets.push(currentBullet.trim());
      currentBullet = trimmed.replace(/^([•\-*▪▫►–—]|\d+\.)\s+/, "");
    } else if (currentBullet) {
      // Continuation of current bullet point
      currentBullet += " " + trimmed;
    } else {
      // Standalone sentence or line
      if (trimmed.length > 15) {
        bullets.push(trimmed);
      }
    }
  }
  if (currentBullet) bullets.push(currentBullet.trim());

  return bullets.filter((b) => b.length > 5);
}

/**
 * Safely escapes regex special characters.
 */
function escapeRegex(str) {
  return str.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

/**
 * Tokenizes text and injects keyword highlights:
 * - matched_skills: emerald highlight
 * - missing_dealbreakers: amber highlight
 * - years of experience: sky highlight
 *
 * Returns an array of segment objects: [{ text, type: "plain" | "matched" | "missing" | "yoe" }]
 */
export function tokenizeHighlightedText(
  text = "",
  matchedSkills = [],
  missingSkills = [],
) {
  if (!text) return [];

  // Build sorted list of keyword patterns to match (longest first to avoid partial overlap)
  const terms = [];

  for (const skill of matchedSkills) {
    if (skill && skill.trim().length >= 2) {
      terms.push({ term: skill.trim(), type: "matched" });
    }
  }

  for (const miss of missingSkills) {
    if (miss && miss.trim().length >= 2) {
      // Don't duplicate if already in matched
      if (
        !terms.some((t) => t.term.toLowerCase() === miss.trim().toLowerCase())
      ) {
        terms.push({ term: miss.trim(), type: "missing" });
      }
    }
  }

  // Sort by length descending
  terms.sort((a, b) => b.term.length - a.term.length);

  // If no terms, check for YOE only
  const termPatterns = terms
    .map((t) => `\\b${escapeRegex(t.term)}\\b`)
    .concat(["\\b\\d+\\+?\\s*years?(?:\\s+experience)?\\b"]);

  if (termPatterns.length === 0) {
    return [{ text, type: "plain" }];
  }

  const combinedRegex = new RegExp(`(${termPatterns.join("|")})`, "gi");
  const parts = text.split(combinedRegex);
  const segments = [];

  for (const part of parts) {
    if (!part) continue;

    const lowerPart = part.toLowerCase();
    const matchedTerm = terms.find((t) => t.term.toLowerCase() === lowerPart);

    if (matchedTerm) {
      segments.push({ text: part, type: matchedTerm.type });
    } else if (/\b\d+\+?\s*years?/i.test(part)) {
      segments.push({ text: part, type: "yoe" });
    } else {
      segments.push({ text: part, type: "plain" });
    }
  }

  return segments;
}
