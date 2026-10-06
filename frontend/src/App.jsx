import React, { useState } from "react";
import {
  Compass,
  FileText,
  MessageSquare,
  Sparkles,
  Layers,
} from "lucide-react";
import { Dashboard } from "./pages/Dashboard";
import { CVTailorView } from "./pages/CVTailorView";
import { InterviewSimulator } from "./pages/InterviewSimulator";

export function App() {
  const [activeTab, setActiveTab] = useState("dashboard"); // "dashboard" | "cv_tailor" | "interview"
  const [selectedJob, setSelectedJob] = useState(null);

  const handleSelectJobForCV = (job) => {
    setSelectedJob(job);
    setActiveTab("cv_tailor");
  };

  const handleStartInterview = (job) => {
    if (job) setSelectedJob(job);
    setActiveTab("interview");
  };

  return (
    <div className="min-h-screen bg-slate-900 text-slate-100 flex flex-col">
      {/* Top Application Navigation */}
      <header className="sticky top-0 z-50 bg-slate-900/90 backdrop-blur-md border-b border-slate-800 px-6 py-3.5">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          {/* Logo & Platform identity */}
          <div
            onClick={() => setActiveTab("dashboard")}
            className="flex items-center gap-2.5 cursor-pointer select-none"
          >
            <div className="p-2 rounded-xl bg-gradient-to-tr from-sky-500 to-indigo-600 text-white shadow-md shadow-sky-500/20">
              <Layers className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-1.5">
                <span className="font-extrabold text-base tracking-tight text-white">
                  Career<span className="text-sky-400">OS</span>
                </span>
                <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-sky-500/10 text-sky-400 border border-sky-500/20">
                  v0.1
                </span>
              </div>
              <p className="text-[10px] text-slate-400 font-medium">
                Stateful AI Multi-Agent Career Platform
              </p>
            </div>
          </div>

          {/* Navigation Tab Bar */}
          <nav className="flex items-center gap-1 bg-slate-800/80 p-1 rounded-xl border border-slate-700/60">
            <button
              onClick={() => setActiveTab("dashboard")}
              className={`px-3.5 py-1.5 rounded-lg text-xs font-medium transition-all flex items-center gap-1.5 ${
                activeTab === "dashboard"
                  ? "bg-sky-600 text-white shadow-sm"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              <Compass className="w-3.5 h-3.5" /> Discovery & Intel
            </button>

            <button
              onClick={() => setActiveTab("cv_tailor")}
              className={`px-3.5 py-1.5 rounded-lg text-xs font-medium transition-all flex items-center gap-1.5 ${
                activeTab === "cv_tailor"
                  ? "bg-sky-600 text-white shadow-sm"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              <FileText className="w-3.5 h-3.5" /> CV Tailor & ATS
            </button>

            <button
              onClick={() => setActiveTab("interview")}
              className={`px-3.5 py-1.5 rounded-lg text-xs font-medium transition-all flex items-center gap-1.5 ${
                activeTab === "interview"
                  ? "bg-sky-600 text-white shadow-sm"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              <MessageSquare className="w-3.5 h-3.5" /> Mock Coach
            </button>
          </nav>

          {/* Target Role Context Badge */}
          <div className="hidden sm:flex items-center gap-2 text-xs font-mono text-slate-400 bg-slate-800/50 px-3 py-1.5 rounded-xl border border-slate-700/50">
            <Sparkles className="w-3.5 h-3.5 text-amber-400" />
            <span>
              {selectedJob ? selectedJob.company_name : "Target Employer"}
            </span>
          </div>
        </div>
      </header>

      {/* Main View Router */}
      <main className="flex-1">
        {activeTab === "dashboard" && (
          <Dashboard
            onSelectJob={handleSelectJobForCV}
            onStartInterview={handleStartInterview}
          />
        )}

        {activeTab === "cv_tailor" && (
          <CVTailorView
            job={selectedJob}
            onBack={() => setActiveTab("dashboard")}
            onStartInterview={handleStartInterview}
          />
        )}

        {activeTab === "interview" && (
          <InterviewSimulator
            job={selectedJob}
            onBack={() => setActiveTab("dashboard")}
          />
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-800/80 py-4 px-6 text-center text-xs text-slate-500">
        <p>
          Career-OS • Decoupled Presentation Layer (React + Vite) • Multi-Agent State Machine (FastAPI + LangGraph + PostgreSQL pgvector)
        </p>
      </footer>
    </div>
  );
}

export default App;
