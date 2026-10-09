import React, { useState } from "react";
import { X, Link as LinkIcon, FileText, Loader2, AlertCircle, CheckCircle } from "lucide-react";
import { ingestJobUrl, pasteJobText } from "../services/api";

export function AddJobModal({ isOpen, onClose, onJobAdded }) {
  const [tab, setTab] = useState("url"); // "url" | "paste"
  const [url, setUrl] = useState("");
  const [title, setTitle] = useState("");
  const [companyName, setCompanyName] = useState("");
  const [location, setLocation] = useState("Remote");
  const [salaryRange, setSalaryRange] = useState("");
  const [rawDescription, setRawDescription] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  if (!isOpen) return null;

  const handleUrlSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setSuccess(null);
    try {
      const res = await ingestJobUrl(url);
      setSuccess(res.message);
      if (onJobAdded && res.job) {
        onJobAdded(res.job);
      }
      setTimeout(() => {
        onClose();
        setUrl("");
        setSuccess(null);
      }, 1200);
    } catch (err) {
      setError(
        err.response?.data?.detail || "Failed to import job by URL. Ensure it is a valid ATS posting."
      );
    } finally {
      setLoading(false);
    }
  };

  const handlePasteSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setSuccess(null);
    try {
      const res = await pasteJobText({
        title,
        company_name: companyName,
        location,
        salary_range: salaryRange || null,
        raw_description: rawDescription,
      });
      setSuccess("Job parsed and imported successfully!");
      if (onJobAdded && res.job) {
        onJobAdded(res.job);
      }
      setTimeout(() => {
        onClose();
        setTitle("");
        setCompanyName("");
        setRawDescription("");
        setSalaryRange("");
        setSuccess(null);
      }, 1200);
    } catch (err) {
      setError(
        err.response?.data?.detail || "Failed to process job description. Please check your inputs."
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 backdrop-blur-sm p-4">
      <div className="bg-slate-900 border border-slate-800 w-full max-w-lg rounded-2xl p-6 shadow-2xl space-y-5 animate-scaleIn">
        {/* Modal Header */}
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <h3 className="text-lg font-bold text-white flex items-center gap-2">
            Import Job Posting
          </h3>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-white p-1 rounded-lg hover:bg-slate-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Tab Switcher */}
        <div className="flex bg-slate-800/80 p-1 rounded-xl">
          <button
            type="button"
            onClick={() => {
              setTab("url");
              setError(null);
            }}
            className={`flex-1 py-1.5 text-xs font-semibold rounded-lg flex items-center justify-center gap-1.5 transition-all ${
              tab === "url"
                ? "bg-sky-600 text-white shadow-sm"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            <LinkIcon className="w-3.5 h-3.5" /> Direct ATS URL
          </button>
          <button
            type="button"
            onClick={() => {
              setTab("paste");
              setError(null);
            }}
            className={`flex-1 py-1.5 text-xs font-semibold rounded-lg flex items-center justify-center gap-1.5 transition-all ${
              tab === "paste"
                ? "bg-sky-600 text-white shadow-sm"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            <FileText className="w-3.5 h-3.5" /> Paste Description
          </button>
        </div>

        {error && (
          <div className="p-3 bg-rose-500/10 border border-rose-500/30 rounded-xl text-rose-300 text-xs flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-rose-400 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {success && (
          <div className="p-3 bg-emerald-500/10 border border-emerald-500/30 rounded-xl text-emerald-300 text-xs flex items-center gap-2">
            <CheckCircle className="w-4 h-4 text-emerald-400 flex-shrink-0" />
            <span>{success}</span>
          </div>
        )}

        {/* Form: By URL */}
        {tab === "url" && (
          <form onSubmit={handleUrlSubmit} className="space-y-4">
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-slate-300">
                Careers URL (Greenhouse, Lever, or Ashby)
              </label>
              <input
                type="url"
                required
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                placeholder="https://boards.greenhouse.io/company/jobs/12345"
                className="w-full px-3.5 py-2 bg-slate-950 border border-slate-700 rounded-xl text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-sky-500"
              />
              <p className="text-[11px] text-slate-500">
                Official API endpoint queried directly with anti-SSRF protections.
              </p>
            </div>

            <button
              type="submit"
              disabled={loading || !url.trim()}
              className="w-full py-2.5 bg-sky-600 hover:bg-sky-500 disabled:bg-slate-800 text-white font-medium rounded-xl text-sm transition-all shadow-md shadow-sky-600/20 flex items-center justify-center gap-2"
            >
              {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : "Import & Sync Board"}
            </button>
          </form>
        )}

        {/* Form: Paste Text */}
        {tab === "paste" && (
          <form onSubmit={handlePasteSubmit} className="space-y-3">
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1">
                <label className="text-xs font-medium text-slate-300">Role Title</label>
                <input
                  type="text"
                  required
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="e.g. Senior Backend Engineer"
                  className="w-full px-3 py-1.5 bg-slate-950 border border-slate-700 rounded-lg text-xs text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-sky-500"
                />
              </div>
              <div className="space-y-1">
                <label className="text-xs font-medium text-slate-300">Company Name</label>
                <input
                  type="text"
                  required
                  value={companyName}
                  onChange={(e) => setCompanyName(e.target.value)}
                  placeholder="e.g. Acme Corp"
                  className="w-full px-3 py-1.5 bg-slate-950 border border-slate-700 rounded-lg text-xs text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-sky-500"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1">
                <label className="text-xs font-medium text-slate-300">Location</label>
                <input
                  type="text"
                  value={location}
                  onChange={(e) => setLocation(e.target.value)}
                  placeholder="Remote"
                  className="w-full px-3 py-1.5 bg-slate-950 border border-slate-700 rounded-lg text-xs text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-sky-500"
                />
              </div>
              <div className="space-y-1">
                <label className="text-xs font-medium text-slate-300">Salary Range (optional)</label>
                <input
                  type="text"
                  value={salaryRange}
                  onChange={(e) => setSalaryRange(e.target.value)}
                  placeholder="e.g. $150k - $180k"
                  className="w-full px-3 py-1.5 bg-slate-950 border border-slate-700 rounded-lg text-xs text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-sky-500"
                />
              </div>
            </div>

            <div className="space-y-1">
              <label className="text-xs font-medium text-slate-300">Job Description</label>
              <textarea
                required
                rows={5}
                value={rawDescription}
                onChange={(e) => setRawDescription(e.target.value)}
                placeholder="Paste the full job description text here..."
                className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-lg text-xs text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-sky-500 resize-none font-mono"
              />
            </div>

            <button
              type="submit"
              disabled={loading || !title || !companyName || !rawDescription}
              className="w-full py-2.5 bg-sky-600 hover:bg-sky-500 disabled:bg-slate-800 text-white font-medium rounded-xl text-sm transition-all shadow-md shadow-sky-600/20 flex items-center justify-center gap-2"
            >
              {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : "Extract Skills & Save"}
            </button>
          </form>
        )}
      </div>
    </div>
  );
}
