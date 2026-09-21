import axios from "axios";

const apiClient = axios.create({
  baseURL: "/api",
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
 * Query backend health status.
 */
export async function checkHealth() {
  const response = await axios.get("/health");
  return response.data;
}

export default apiClient;
