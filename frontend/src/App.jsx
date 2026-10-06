import React, { useState } from "react";
import {
  Routes,
  Route,
  NavLink,
  useNavigate,
  useParams,
} from "react-router-dom";
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

function InterviewRouteWrapper({ job, onBack }) {
  const { threadId } = useParams();
  return (
    <InterviewSimulator
      job={job}
      initialThreadId={threadId}
      onBack={onBack}
    />
  );
}

export function App() {
  const [selectedJob, setSelectedJob] = useState(null);
  const navigate = useNavigate();

  const handleSelectJobForCV = (job) => {
    setSelectedJob(job);
    navigate("/cv-tailor");
  };

  const handleStartInterview = (job) => {
    if (job) setSelectedJob(job);
    navigate("/interview");
  };

  return (
    <div className="min-h-screen bg-slate-900 text-slate-100 flex flex-col">
      {/* Top Application Navigation */}
      <header className="sticky top-0 z-50 bg-slate-900/90 backdrop-blur-md border-b border-slate-800 px-6 py-3.5">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          {/* Logo & Platform identity */}
          <div
            onClick={() => navigate("/")}
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
            <NavLink
              to="/"
              end
              className={({ isActive }) =>
                `px-3.5 py-1.5 rounded-lg text-xs font-medium transition-all flex items-center gap-1.5 ${
                  isActive
                    ? "bg-sky-600 text-white shadow-sm"
                    : "text-slate-400 hover:text-slate-200"
                }`
              }
            >
              <Compass className="w-3.5 h-3.5" /> Discovery & Intel
            </NavLink>

            <NavLink
              to="/cv-tailor"
              className={({ isActive }) =>
                `px-3.5 py-1.5 rounded-lg text-xs font-medium transition-all flex items-center gap-1.5 ${
                  isActive
                    ? "bg-sky-600 text-white shadow-sm"
                    : "text-slate-400 hover:text-slate-200"
                }`
              }
            >
              <FileText className="w-3.5 h-3.5" /> CV Tailor & ATS
            </NavLink>

            <NavLink
              to="/interview"
              className={({ isActive }) =>
                `px-3.5 py-1.5 rounded-lg text-xs font-medium transition-all flex items-center gap-1.5 ${
                  isActive
                    ? "bg-sky-600 text-white shadow-sm"
                    : "text-slate-400 hover:text-slate-200"
                }`
              }
            >
              <MessageSquare className="w-3.5 h-3.5" /> Mock Coach
            </NavLink>
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
        <Routes>
          <Route
            path="/"
            element={
              <Dashboard
                onSelectJob={handleSelectJobForCV}
                onStartInterview={handleStartInterview}
              />
            }
          />
          <Route
            path="/cv-tailor"
            element={
              <CVTailorView
                job={selectedJob}
                onBack={() => navigate("/")}
                onStartInterview={handleStartInterview}
              />
            }
          />
          <Route
            path="/interview"
            element={
              <InterviewSimulator
                job={selectedJob}
                onBack={() => navigate("/")}
              />
            }
          />
          <Route
            path="/interview/:threadId"
            element={
              <InterviewRouteWrapper
                job={selectedJob}
                onBack={() => navigate("/")}
              />
            }
          />
        </Routes>
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
