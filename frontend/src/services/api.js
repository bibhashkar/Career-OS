import axios from "axios";

const apiBase = import.meta.env.VITE_API_URL
  ? `${import.meta.env.VITE_API_URL.replace(/\/$/, "")}/api`
  : "/api";

const apiClient = axios.create({
  baseURL: apiBase,
  timeout: 30000,
  headers: {
    "Content-Type": "application/json",
  },
});

// Attach Bearer token to outgoing requests if authenticated
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem("career_os_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Clear token on 401 Unauthorized responses
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem("career_os_token");
    }
    return Promise.reject(error);
  }
);

/**
 * Register a new candidate user account and provision Universal Persona.
 */
export async function register(payload) {
  const response = await apiClient.post("/auth/register", payload);
  if (response.data?.access_token) {
    localStorage.setItem("career_os_token", response.data.access_token);
  }
  return response.data;
}

/**
 * Authenticate candidate credentials and issue a signed JWT access token.
 */
export async function login(email, password) {
  const response = await apiClient.post("/auth/login", { email, password });
  if (response.data?.access_token) {
    localStorage.setItem("career_os_token", response.data.access_token);
  }
  return response.data;
}

/**
 * Retrieve candidate profile and personas for the current authenticated principal.
 */
export async function getCurrentUser() {
  const response = await apiClient.get("/auth/me");
  return response.data;
}

/**
 * Clear stored authentication token and end session.
 */
export function logout() {
  localStorage.removeItem("career_os_token");
}

/**
 * Search jobs with location and visa sponsorship filtering.
 */
export async function searchJobs(query = "", location = "", visaRequired = false) {
  const response = await apiClient.post("/jobs/search", {
    query,
    location,
    visa_required: visaRequired,
  });
  return response.data;
}

/**
 * Ingest a job directly by ATS URL (Greenhouse, Lever, Ashby).
 */
export async function ingestJobUrl(url) {
  const response = await apiClient.post("/jobs/ingest-url", { url });
  return response.data;
}

/**
 * Ingest a job by pasting text.
 */
export async function pasteJobText(payload) {
  const response = await apiClient.post("/jobs/paste-text", payload);
  return response.data;
}

/**
 * Force-refresh company intelligence dossier within cooldown limits.
 */
export async function refreshCompanyIntel(companyName) {
  const response = await apiClient.post(
    `/jobs/companies/${encodeURIComponent(companyName)}/refresh`
  );
  return response.data;
}

/**
 * Cross-check job listing against secondary aggregators.
 */
export async function crossCheckJob(jobId) {
  const response = await apiClient.post(`/jobs/${jobId}/cross-check`);
  return response.data;
}

/**
 * Trigger LangGraph CV tailoring and cyclic ATS evaluation.
 */
export async function generateCV(jobId, requiredSkills = [], title = "", companyName = "") {
  const response = await apiClient.post("/cv/generate", {
    job_id: jobId,
    required_skills: requiredSkills,
    title,
    company_name: companyName,
  });
  return response.data;
}

/**
 * Submit interview review feedback to Reflector agent.
 */
export async function submitFeedback(threadId, userFeedback) {
  const response = await apiClient.post("/feedback", {
    thread_id: threadId,
    user_feedback: userFeedback,
  });
  return response.data;
}

/**
 * Export tailored CV draft as Markdown or TXT blob.
 */
export async function exportCV(cvDraft, format = "markdown") {
  const response = await apiClient.post(
    `/cv/export?export_format=${format}`,
    { cv_draft: cvDraft },
    { responseType: "blob" }
  );
  return response.data;
}

/**
 * Fetch two-stage ranked job matches for a candidate persona.
 */
export async function getJobMatches(params = {}) {
  const response = await apiClient.get("/jobs/matches", { params });
  return response.data;
}

/**
 * Fetch per-job matching diagnostics and dealbreaker chip analysis.
 */
export async function getJobDiagnostics(jobId, personaId = null) {
  const params =
    personaId && personaId !== "universal" ? { persona_id: personaId } : {};
  const response = await apiClient.get(`/jobs/${jobId}/diagnostics`, { params });
  return response.data;
}

/**
 * Fetch Tier 0 360-degree holistic candidate career audit.
 */
export async function getCandidateAudit() {
  const response = await apiClient.get("/candidates/audit");
  return response.data;
}

/**
 * Fetch all candidate personas (Universal Profile + specialized personas).
 */
export async function getCandidatePersonas() {
  const response = await apiClient.get("/candidates/personas");
  return response.data;
}

/**
 * Set a persona as active default on candidate login.
 */
export async function setDefaultPersona(personaId) {
  const response = await apiClient.put(`/candidates/personas/${personaId}/default`);
  return response.data;
}

/**
 * Create a new specialized candidate persona.
 */
export async function createCandidatePersona(payload) {
  const response = await apiClient.post("/candidates/personas", payload);
  return response.data;
}

/**
 * Update or rename a candidate persona.
 */
export async function updateCandidatePersona(personaId, payload) {
  const response = await apiClient.put(`/candidates/personas/${personaId}`, payload);
  return response.data;
}

/**
 * Delete a specialized candidate persona.
 */
export async function deleteCandidatePersona(personaId) {
  const response = await apiClient.delete(`/candidates/personas/${personaId}`);
  return response.data;
}

/**
 * Parse an uploaded resume (PDF, DOCX, LinkedIn PDF) into staged blocks.
 */
export async function parseResumeDocument(file) {
  const formData = new FormData();
  formData.append("file", file);
  const response = await apiClient.post("/candidates/parse-document", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return response.data;
}

/**
 * Parse pasted resume or LinkedIn text into staged blocks.
 */
export async function parseResumeText(text) {
  const response = await apiClient.post("/candidates/parse-text", { text });
  return response.data;
}

/**
 * Submit verified candidate onboarding data with personas and blocks.
 */
export async function onboardCandidate(payload) {
  const response = await apiClient.post("/candidates/onboard", payload);
  return response.data;
}

/**
 * Fetch macro market skill requirements analyzed across target roles.
 */
export async function getPersonaBenchmark(personaId) {
  const response = await apiClient.get(`/candidates/personas/${personaId}/benchmark`);
  return response.data;
}

/**
 * Fetch candidate master CV blocks.
 */
export async function getCVBlocks(category = null) {
  const params = category ? { category } : {};
  const response = await apiClient.get("/candidates/blocks", { params });
  return response.data;
}

/**
 * Create a new master CV block.
 */
export async function createCVBlock(payload) {
  const response = await apiClient.post("/candidates/blocks", payload);
  return response.data;
}

/**
 * Delete a master CV block.
 */
export async function deleteCVBlock(blockId) {
  const response = await apiClient.delete(`/candidates/blocks/${blockId}`);
  return response.data;
}

export default apiClient;

