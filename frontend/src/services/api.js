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

/**
 * Search jobs with location and visa sponsorship filtering.
 */
export async function searchJobs(query, location = "Remote", visaRequired = false) {
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

export default apiClient;
