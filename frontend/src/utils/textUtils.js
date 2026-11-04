/**
 * Text processing and normalization utilities.
 */

/**
 * Strips all non-alphanumeric characters and converts text to lowercase.
 * Useful for deterministic equality checks, deduplication, and loose string comparisons.
 *
 * @param {string|null|undefined} text
 * @returns {string}
 */
export function normalizeAlphanumeric(text) {
  return (text || "").toLowerCase().replace(/[^a-z0-9]/g, "");
}

/**
 * Converts arbitrary text into a safe alphanumeric slug with custom delimiters (default "_").
 *
 * @param {string|null|undefined} text
 * @param {string} [separator="_"]
 * @returns {string}
 */
export function slugify(text, separator = "_") {
  if (!text) return "";
  return text
    .toString()
    .toLowerCase()
    .trim()
    .replace(/[^a-z0-9]+/g, separator)
    .replace(new RegExp(`^\\${separator}+|\\${separator}+$`, "g"), "");
}

