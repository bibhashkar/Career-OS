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
  Award,
  Layers,
  LogIn,
  LogOut,
} from "lucide-react";
import { Dashboard } from "./pages/Dashboard";
import { CVTailorView } from "./pages/CVTailorView";
import { InterviewSimulator } from "./pages/InterviewSimulator";
import { CandidateAuditView } from "./pages/CandidateAuditView";
import { OnboardingWizard } from "./pages/OnboardingWizard";
import { PersonaSwitcher } from "./components/PersonaSwitcher";
import { PersonaManagementModal } from "./components/PersonaManagementModal";
import { AuthModal } from "./components/AuthModal";
import { getCurrentUser, logout } from "./services/api";

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
  const [activePersona, setActivePersona] = useState(null);
  const [currentUser, setCurrentUser] = useState(null);
  const [isAuthModalOpen, setIsAuthModalOpen] = useState(false);
  const [isPersonaModalOpen, setIsPersonaModalOpen] = useState(false);
  const navigate = useNavigate();

  React.useEffect(() => {
    const token = localStorage.getItem("career_os_token");
    if (token) {
      getCurrentUser()
        .then((user) => setCurrentUser(user))
        .catch(() => {
          logout();
          setCurrentUser(null);
        });
    }
  }, []);

  const handleAuthSuccess = (user) => {
    setCurrentUser(user);
    if (user?.personas?.length > 0) {
      const defaultP = user.personas.find((p) => p.is_default) || user.personas[0];
      setActivePersona(defaultP);
    }
  };

  const handleLogout = () => {
    logout();
    setCurrentUser(null);
  };

  const handleSelectJobForCV = (job) => {
    setSelectedJob(job);
    navigate("/cv-tailor");
  };

  const handleStartInterview = (job) => {
    if (job) setSelectedJob(job);
    navigate("/interview");
  };

  const handlePersonaChange = (persona) => {
    setActivePersona(persona);
  };

  return (
    <div className="min-h-screen bg-slate-900 text-slate-100 flex flex-col">
      {/* Top Application Navigation */}
      <header className="sticky top-0 z-50 bg-slate-900/90 backdrop-blur-md border-b border-slate-800 px-6 py-3.5">
        <div className="max-w-7xl mx-auto flex items-center justify-between gap-4">
          {/* Logo & Platform identity */}
          <div
            onClick={() => navigate("/")}
            className="flex items-center gap-2.5 cursor-pointer select-none shrink-0"
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
                  v0.2
                </span>
              </div>
              <p className="text-[10px] text-slate-400 font-medium hidden sm:block">
                Multi-Persona Intelligence & Matching
              </p>
            </div>
          </div>

          {/* Navigation Tab Bar */}
          <nav className="flex items-center gap-1 bg-slate-800/80 p-1 rounded-xl border border-slate-700/60 overflow-x-auto">
            <NavLink
              to="/"
              end
              className={({ isActive }) =>
                `px-3 py-1.5 rounded-lg text-xs font-medium transition-all flex items-center gap-1.5 whitespace-nowrap ${
                  isActive
                    ? "bg-sky-600 text-white shadow-sm"
                    : "text-slate-400 hover:text-slate-200"
                }`
              }
            >
              <Compass className="w-3.5 h-3.5" /> Matches & Intel
            </NavLink>

            <NavLink
              to="/cv-tailor"
              className={({ isActive }) =>
                `px-3 py-1.5 rounded-lg text-xs font-medium transition-all flex items-center gap-1.5 whitespace-nowrap ${
                  isActive
                    ? "bg-sky-600 text-white shadow-sm"
                    : "text-slate-400 hover:text-slate-200"
                }`
              }
            >
              <FileText className="w-3.5 h-3.5" /> CV Tailor
            </NavLink>

            <NavLink
              to="/interview"
              className={({ isActive }) =>
                `px-3 py-1.5 rounded-lg text-xs font-medium transition-all flex items-center gap-1.5 whitespace-nowrap ${
                  isActive
                    ? "bg-sky-600 text-white shadow-sm"
                    : "text-slate-400 hover:text-slate-200"
                }`
              }
            >
              <MessageSquare className="w-3.5 h-3.5" /> Mock Coach
            </NavLink>

            <NavLink
              to="/audit"
              className={({ isActive }) =>
                `px-3 py-1.5 rounded-lg text-xs font-medium transition-all flex items-center gap-1.5 whitespace-nowrap ${
                  isActive
                    ? "bg-sky-600 text-white shadow-sm"
                    : "text-slate-400 hover:text-slate-200"
                }`
              }
            >
              <Award className="w-3.5 h-3.5" /> 360° Audit
            </NavLink>
          </nav>

          {/* Right Controls: Persona Switcher and Account */}
          <div className="flex items-center gap-2.5 shrink-0">
            <PersonaSwitcher
              key={currentUser?.id || "default"}
              activePersonaId={activePersona?.id}
              onPersonaChange={handlePersonaChange}
              onOpenAudit={() => navigate("/audit")}
              onManagePersonas={() => setIsPersonaModalOpen(true)}
            />

            {currentUser ? (
              <div className="flex items-center gap-2 bg-slate-800/80 border border-slate-700/60 rounded-xl px-2.5 py-1.5 text-xs text-slate-300">
                <div className="w-5 h-5 rounded-full bg-gradient-to-tr from-sky-400 to-indigo-500 text-white flex items-center justify-center font-bold text-[10px]">
                  {currentUser.full_name?.charAt(0).toUpperCase() || "U"}
                </div>
                <span className="font-medium hidden sm:inline max-w-[110px] truncate">
                  {currentUser.full_name}
                </span>
                <button
                  onClick={handleLogout}
                  title="Sign Out"
                  className="p-1 hover:text-rose-400 text-slate-400 rounded transition-colors ml-0.5 cursor-pointer"
                >
                  <LogOut className="w-3.5 h-3.5" />
                </button>
              </div>
            ) : (
              <button
                onClick={() => setIsAuthModalOpen(true)}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-sky-600 hover:bg-sky-500 text-white font-medium text-xs shadow-sm shadow-sky-500/20 transition-all cursor-pointer"
              >
                <LogIn className="w-3.5 h-3.5" />
                <span>Sign In</span>
              </button>
            )}
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
                activePersona={activePersona}
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
          <Route
            path="/audit"
            element={<CandidateAuditView onNavigateBack={() => navigate("/")} />}
          />
          <Route
            path="/onboarding"
            element={<OnboardingWizard />}
          />
        </Routes>

        <AuthModal
          isOpen={isAuthModalOpen}
          onClose={() => setIsAuthModalOpen(false)}
          onSuccess={handleAuthSuccess}
        />

        <PersonaManagementModal
          isOpen={isPersonaModalOpen}
          onClose={() => setIsPersonaModalOpen(false)}
          activePersonaId={activePersona?.id}
          onPersonaSelect={(persona) => {
            setActivePersona(persona);
          }}
          onPersonasChanged={(personas) => {
            if (
              personas.length > 0 &&
              (!activePersona || !personas.some((p) => p.id === activePersona.id))
            ) {
              const def = personas.find((p) => p.is_default) || personas[0];
              setActivePersona(def);
            }
          }}
        />
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-800/80 py-4 px-6 text-center text-xs text-slate-500">
        <p>
          Career-OS • Multi-Persona Candidate Intelligence • Two-Stage Retrieval (ADR-008) • FastAPI + PostgreSQL pgvector
        </p>
      </footer>
    </div>
  );
}

export default App;
