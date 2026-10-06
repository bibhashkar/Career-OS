import React, { useState, useEffect, useRef } from "react";
import {
  ArrowLeft,
  Send,
  Pause,
  Play,
  RotateCcw,
  Sparkles,
  Bot,
  User,
  ShieldCheck,
  Building2,
  Cpu,
  ThumbsUp,
  Loader2,
  History,
} from "lucide-react";
import { InterviewWebSocket } from "../services/websocket";
import { submitFeedback } from "../services/api";
import { SessionHistoryModal } from "../components/SessionHistoryModal";

const SESSIONS_STORAGE_KEY = "career_os_interview_sessions";

function getStoredSessions() {
  try {
    const raw = localStorage.getItem(SESSIONS_STORAGE_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}

function saveStoredSessions(sessions) {
  try {
    localStorage.setItem(SESSIONS_STORAGE_KEY, JSON.stringify(sessions));
  } catch (err) {
    console.error("Failed to save sessions to localStorage:", err);
  }
}

export function InterviewSimulator({ job, initialThreadId, onBack }) {
  // Retrieve passed initialThreadId, saved thread_id, or initialize fresh session
  const [threadId, setThreadId] = useState(() => {
    return (
      initialThreadId ||
      localStorage.getItem("active_interview_thread_id") ||
      `thread_${Date.now()}_${Math.random().toString(36).substring(2, 7)}`
    );
  });

  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState("");
  const [connectionStatus, setConnectionStatus] = useState("disconnected");
  const [showPrepSheet, setShowPrepSheet] = useState(true);
  const [showHistoryModal, setShowHistoryModal] = useState(false);
  const [savedSessions, setSavedSessions] = useState(getStoredSessions);
  const [feedbackText, setFeedbackText] = useState("");
  const [feedbackSent, setFeedbackSent] = useState(false);
  const [feedbackLoading, setFeedbackLoading] = useState(false);
  const [feedbackError, setFeedbackError] = useState(null);

  const wsRef = useRef(null);
  const messagesEndRef = useRef(null);

  // Sync thread_id if initialThreadId changes from route param
  useEffect(() => {
    if (initialThreadId && initialThreadId !== threadId) {
      setThreadId(initialThreadId);
    }
  }, [initialThreadId]);

  // Sync thread_id with localStorage and update sessions history
  useEffect(() => {
    localStorage.setItem("active_interview_thread_id", threadId);

    // Record or update session in history
    setSavedSessions((prev) => {
      const existingIdx = prev.findIndex((s) => s.threadId === threadId);
      const sessionEntry = {
        threadId,
        companyName: job?.company_name || (existingIdx >= 0 ? prev[existingIdx].companyName : "Target Employer"),
        title: job?.title || (existingIdx >= 0 ? prev[existingIdx].title : "Technical Interview"),
        timestamp: Date.now(),
      };

      let updated;
      if (existingIdx >= 0) {
        updated = [...prev];
        updated[existingIdx] = { ...updated[existingIdx], ...sessionEntry };
      } else {
        updated = [sessionEntry, ...prev].slice(0, 20); // Retain latest 20 sessions
      }
      saveStoredSessions(updated);
      return updated;
    });
  }, [threadId, job]);

  // Connect WebSocket on mount or when threadId changes
  useEffect(() => {
    const ws = new InterviewWebSocket(
      threadId,
      (data) => {
        if (data.type === "message") {
          setMessages((prev) => [
            ...prev,
            {
              role: data.sender || "coach",
              content: data.content,
              turn: data.turn,
            },
          ]);
        }
      },
      (status) => {
        setConnectionStatus(status);
      },
      {
        jobId: job?.id,
        companyName: job?.company_name,
        title: job?.title,
      }
    );

    ws.connect();
    wsRef.current = ws;

    return () => {
      ws.disconnect();
    };
  }, [threadId]);

  // Auto-scroll chat to latest message
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSendMessage = (e) => {
    e?.preventDefault();
    const text = inputValue.trim();
    if (!text || connectionStatus !== "connected") return;

    // Append local candidate message immediately
    setMessages((prev) => [...prev, { role: "user", content: text }]);
    wsRef.current?.sendMessage(text);
    setInputValue("");
  };

  const handleTogglePause = () => {
    if (connectionStatus === "connected") {
      wsRef.current?.disconnect();
    } else {
      wsRef.current?.connect();
    }
  };

  const handleNewSession = () => {
    wsRef.current?.disconnect();
    const newId = `thread_${Date.now()}_${Math.random().toString(36).substring(2, 7)}`;
    setMessages([]);
    setThreadId(newId);
  };

  const handleSubmitFeedback = async (e) => {
    e?.preventDefault();
    if (!feedbackText.trim()) return;
    setFeedbackLoading(true);
    setFeedbackError(null);
    try {
      await submitFeedback(threadId, feedbackText);
      setFeedbackSent(true);
      setFeedbackText("");
      setTimeout(() => setFeedbackSent(false), 3000);
    } catch (err) {
      console.error("Failed to submit feedback:", err);
      setFeedbackError(
        err.response?.data?.detail ||
          "Failed to submit feedback to Reflector agent. Please try again."
      );
    } finally {
      setFeedbackLoading(false);
    }
  };

  const handleResumeSession = (targetThreadId) => {
    wsRef.current?.disconnect();
    setMessages([]);
    setThreadId(targetThreadId);
    setShowHistoryModal(false);
  };

  const handleDeleteSession = (targetThreadId) => {
    const updated = savedSessions.filter((s) => s.threadId !== targetThreadId);
    setSavedSessions(updated);
    saveStoredSessions(updated);
  };

  const handleClearAllSessions = () => {
    setSavedSessions([]);
    saveStoredSessions([]);
    setShowHistoryModal(false);
  };

  const dossier = job?.company_dossier || {
    company_name: job?.company_name || "Target Employer",
    tech_stack: ["Python", "FastAPI", "PostgreSQL", "LangGraph"],
    business_model: "Software engineering and AI services.",
  };

  return (
    <div className="max-w-7xl mx-auto px-4 py-6 space-y-6">
      {/* Session History Modal */}
      <SessionHistoryModal
        isOpen={showHistoryModal}
        onClose={() => setShowHistoryModal(false)}
        sessions={savedSessions}
        activeThreadId={threadId}
        onResumeSession={handleResumeSession}
        onDeleteSession={handleDeleteSession}
        onClearAllSessions={handleClearAllSessions}
      />

      {/* Navigation & Controls Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-4">
        <div className="flex items-center gap-3">
          <button
            onClick={onBack}
            className="p-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
          </button>
          <div>
            <h2 className="text-base font-bold text-white flex items-center gap-2">
              <span>Technical Mock Interview</span>
              <span
                className={`text-[10px] uppercase font-bold px-2 py-0.5 rounded-full border ${
                  connectionStatus === "connected"
                    ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/30"
                    : connectionStatus === "paused"
                    ? "bg-amber-500/10 text-amber-400 border-amber-500/30"
                    : "bg-slate-700 text-slate-400 border-slate-600"
                }`}
              >
                {connectionStatus === "connected"
                  ? "Live Streaming"
                  : connectionStatus === "paused"
                  ? "Paused (Resumable)"
                  : connectionStatus}
              </span>
            </h2>
            <p className="text-xs text-slate-400 font-mono">
              Thread Checkpoint: {threadId}
            </p>
          </div>
        </div>

        {/* Action Controls */}
        <div className="flex items-center gap-2 flex-wrap">
          <button
            onClick={() => setShowHistoryModal(true)}
            className="px-3 py-1.5 rounded-xl border border-slate-700 hover:bg-slate-800 text-xs font-medium text-slate-300 transition-colors flex items-center gap-1.5"
            title="View Past Sessions"
          >
            <History className="w-3.5 h-3.5 text-sky-400" /> Past Sessions ({savedSessions.length})
          </button>

          <button
            onClick={handleTogglePause}
            className="px-3 py-1.5 rounded-xl border border-slate-700 hover:bg-slate-800 text-xs font-medium text-slate-300 transition-colors flex items-center gap-1.5"
          >
            {connectionStatus === "connected" ? (
              <>
                <Pause className="w-3.5 h-3.5 text-amber-400" /> Pause Session
              </>
            ) : (
              <>
                <Play className="w-3.5 h-3.5 text-emerald-400" /> Resume Session
              </>
            )}
          </button>

          <button
            onClick={handleNewSession}
            className="px-3 py-1.5 rounded-xl border border-slate-700 hover:bg-slate-800 text-xs font-medium text-slate-300 transition-colors flex items-center gap-1.5"
          >
            <RotateCcw className="w-3.5 h-3.5" /> Reset Thread
          </button>

          <button
            onClick={() => setShowPrepSheet(!showPrepSheet)}
            className="px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 border border-slate-700 text-xs font-medium text-slate-200 transition-colors flex items-center gap-1.5"
          >
            <Cpu className="w-3.5 h-3.5 text-sky-400" />
            {showPrepSheet ? "Hide Prep Sheet" : "Show Prep Sheet"}
          </button>
        </div>
      </div>

      {/* Main Split Grid: Chat Window + Strategist Prep Sheet */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 items-start">
        {/* Chat Window Column */}
        <div className="lg:col-span-2 bg-slate-800/90 border border-slate-700/80 rounded-2xl p-4 shadow-xl flex flex-col h-[650px]">
          {/* Scrollable Message History */}
          <div className="flex-1 overflow-y-auto space-y-4 pr-2">
            {messages.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-full text-slate-500 space-y-2">
                <Bot className="w-8 h-8 text-sky-400 animate-pulse" />
                <p className="text-sm font-medium">Connecting to Coach Agent...</p>
                <p className="text-xs">
                  Restoring session checkpoint from PostgreSQL memory.
                </p>
              </div>
            ) : (
              messages.map((msg, idx) => {
                const isCoach = msg.role === "coach" || msg.role === "assistant";
                return (
                  <div
                    key={idx}
                    className={`flex items-start gap-3 ${
                      isCoach ? "justify-start" : "justify-end"
                    }`}
                  >
                    {isCoach && (
                      <div className="p-2 rounded-xl bg-sky-500/10 text-sky-400 border border-sky-500/20 shrink-0">
                        <Bot className="w-4 h-4" />
                      </div>
                    )}
                    <div
                      className={`max-w-xl rounded-2xl p-4 text-xs leading-relaxed space-y-1 shadow-sm ${
                        isCoach
                          ? "bg-slate-900/90 text-slate-200 border border-slate-700/60"
                          : "bg-sky-600 text-white font-medium"
                      }`}
                    >
                      <div className="flex items-center justify-between text-[10px] text-slate-400 font-mono mb-1">
                        <span>{isCoach ? "Coach Agent" : "You (Candidate)"}</span>
                        {msg.turn && <span>Turn #{msg.turn}</span>}
                      </div>
                      <p className="whitespace-pre-wrap">{msg.content}</p>
                    </div>
                    {!isCoach && (
                      <div className="p-2 rounded-xl bg-slate-700 text-slate-200 shrink-0">
                        <User className="w-4 h-4" />
                      </div>
                    )}
                  </div>
                );
              })
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Chat Input Bar */}
          <form
            onSubmit={handleSendMessage}
            className="pt-3 border-t border-slate-700/60 flex items-center gap-2"
          >
            <input
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              disabled={connectionStatus !== "connected"}
              placeholder={
                connectionStatus === "connected"
                  ? "Type your technical response..."
                  : "Session is paused. Click 'Resume Session' to continue."
              }
              className="flex-1 px-4 py-2.5 bg-slate-900 border border-slate-700 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-sky-500 disabled:opacity-50"
            />
            <button
              type="submit"
              disabled={!inputValue.trim() || connectionStatus !== "connected"}
              className="px-4 py-2.5 bg-sky-600 hover:bg-sky-500 disabled:bg-slate-700 text-white font-semibold rounded-xl text-xs transition-all shadow-md shadow-sky-600/20 flex items-center gap-1.5"
            >
              <Send className="w-3.5 h-3.5" /> Send
            </button>
          </form>
        </div>

        {/* Strategist Technical Prep Sheet Column */}
        {showPrepSheet && (
          <div className="space-y-4 animate-fadeIn">
            <div className="bg-slate-800/90 border border-slate-700/80 rounded-2xl p-5 shadow-xl space-y-4">
              <div className="flex items-center gap-2 border-b border-slate-700/60 pb-3">
                <Sparkles className="w-4 h-4 text-sky-400" />
                <h3 className="text-sm font-bold text-white">
                  Strategist Technical Prep Sheet
                </h3>
              </div>

              {/* Target Role & Company */}
              <div className="space-y-1">
                <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
                  Employer
                </div>
                <div className="text-xs font-bold text-white flex items-center gap-1.5">
                  <Building2 className="w-3.5 h-3.5 text-slate-400" />
                  {dossier.company_name}
                </div>
              </div>

              {/* Architecture & Tech Stack */}
              <div className="space-y-2">
                <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-1">
                  <Cpu className="w-3.5 h-3.5 text-sky-400" /> Likely Interview Topics
                </div>
                <div className="flex flex-wrap gap-1">
                  {dossier.tech_stack?.map((tech, idx) => (
                    <span
                      key={idx}
                      className="text-[10px] px-2 py-0.5 rounded bg-slate-900 text-sky-300 border border-slate-700 font-mono"
                    >
                      {tech}
                    </span>
                  ))}
                </div>
              </div>

              {/* Key Prep Tips */}
              <div className="space-y-1.5 pt-2 border-t border-slate-700/50">
                <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
                  Interview Directives
                </div>
                <ul className="text-xs text-slate-300 space-y-1.5 list-disc list-inside">
                  <li>Quantify past impacts (e.g. latency, throughput).</li>
                  <li>Highlight stateful recovery and database failovers.</li>
                  <li>Address concurrency limits and connection pooling.</li>
                </ul>
              </div>
            </div>

            {/* Candidate Feedback & Reflector Input */}
            <div className="bg-slate-800/90 border border-slate-700/80 rounded-2xl p-5 shadow-xl space-y-3">
              <div className="flex items-center gap-2 text-xs font-bold text-white">
                <ShieldCheck className="w-4 h-4 text-emerald-400" />
                <span>Coach Feedback & Weight Tuner</span>
              </div>
              <p className="text-xs text-slate-400">
                Tell the Reflector agent how to adjust its technical depth or style:
              </p>
              <form onSubmit={handleSubmitFeedback} className="space-y-2">
                <textarea
                  rows={2}
                  value={feedbackText}
                  onChange={(e) => setFeedbackText(e.target.value)}
                  placeholder="e.g. 'Ask harder questions on concurrency and PostgreSQL replication.'"
                  className="w-full p-2.5 bg-slate-900 border border-slate-700 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-sky-500"
                />
                {feedbackError && (
                  <div className="p-2.5 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs flex items-center justify-between gap-2">
                    <span className="truncate">{feedbackError}</span>
                    <button
                      type="button"
                      onClick={handleSubmitFeedback}
                      className="underline text-rose-200 hover:text-white font-medium shrink-0"
                    >
                      Retry
                    </button>
                  </div>
                )}
                <button
                  type="submit"
                  disabled={!feedbackText.trim() || feedbackLoading}
                  className="w-full py-2 bg-slate-700 hover:bg-slate-600 disabled:bg-slate-800 text-white font-medium rounded-xl text-xs transition-colors flex items-center justify-center gap-1.5"
                >
                  {feedbackLoading ? (
                    <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  ) : feedbackSent ? (
                    <>
                      <ThumbsUp className="w-3.5 h-3.5 text-emerald-400" /> Weights Updated!
                    </>
                  ) : (
                    "Apply to Reflector Agent"
                  )}
                </button>
              </form>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
