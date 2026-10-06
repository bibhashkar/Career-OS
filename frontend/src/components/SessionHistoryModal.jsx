import React from "react";
import { History, Play, Trash2, Clock, Building2, Briefcase } from "lucide-react";

export function SessionHistoryModal({
  isOpen,
  onClose,
  sessions,
  activeThreadId,
  onResumeSession,
  onDeleteSession,
  onClearAllSessions,
}) {
  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 backdrop-blur-sm p-4 animate-fadeIn"
      role="dialog"
      aria-modal="true"
      aria-labelledby="session-history-title"
    >
      <div className="bg-slate-900 border border-slate-700 rounded-2xl w-full max-w-lg shadow-2xl flex flex-col max-h-[80vh]">
        {/* Modal Header */}
        <div className="p-4 border-b border-slate-800 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="p-2 rounded-xl bg-sky-500/10 text-sky-400 border border-sky-500/20">
              <History className="w-4 h-4" />
            </div>
            <div>
              <h3 id="session-history-title" className="text-sm font-bold text-white">
                Interview Sessions History
              </h3>
              <p className="text-[11px] text-slate-400">
                Resumable PostgreSQL checkpoints
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-white text-xs px-2 py-1 rounded-lg hover:bg-slate-800 transition-colors"
          >
            Close
          </button>
        </div>

        {/* Modal Body / Session List */}
        <div className="p-4 overflow-y-auto space-y-2.5 flex-1">
          {sessions.length === 0 ? (
            <div className="text-center py-8 text-slate-500 space-y-1">
              <Clock className="w-8 h-8 mx-auto text-slate-600 mb-2" />
              <p className="text-xs font-medium text-slate-400">No saved sessions found.</p>
              <p className="text-[11px]">Start a mock interview to record checkpoint history.</p>
            </div>
          ) : (
            sessions.map((s) => {
              const isActive = s.threadId === activeThreadId;
              const formattedTime = new Date(s.timestamp).toLocaleString(undefined, {
                month: "short",
                day: "numeric",
                hour: "2-digit",
                minute: "2-digit",
              });

              return (
                <div
                  key={s.threadId}
                  className={`p-3 rounded-xl border transition-all flex items-center justify-between gap-3 ${
                    isActive
                      ? "bg-sky-950/40 border-sky-600/60 shadow-sm"
                      : "bg-slate-800/80 border-slate-700/70 hover:border-slate-600"
                  }`}
                >
                  <div className="space-y-1 min-w-0 flex-1">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="text-xs font-bold text-white truncate flex items-center gap-1">
                        <Building2 className="w-3 h-3 text-slate-400 shrink-0" />
                        {s.companyName || "Employer Session"}
                      </span>
                      {isActive && (
                        <span className="text-[9px] uppercase font-bold px-1.5 py-0.2 rounded bg-sky-500/20 text-sky-300 border border-sky-500/40">
                          Active
                        </span>
                      )}
                    </div>
                    {s.title && (
                      <p className="text-[11px] text-slate-300 truncate flex items-center gap-1">
                        <Briefcase className="w-3 h-3 text-slate-500 shrink-0" />
                        {s.title}
                      </p>
                    )}
                    <div className="flex items-center gap-2 text-[10px] text-slate-400 font-mono">
                      <span>{formattedTime}</span>
                      <span>•</span>
                      <span className="truncate max-w-[120px]">{s.threadId}</span>
                    </div>
                  </div>

                  <div className="flex items-center gap-1.5 shrink-0">
                    <button
                      onClick={() => onResumeSession(s.threadId)}
                      disabled={isActive}
                      className="px-2.5 py-1.5 rounded-lg text-xs font-medium transition-colors flex items-center gap-1 bg-sky-600 hover:bg-sky-500 disabled:bg-slate-800 disabled:text-slate-500 text-white"
                      title={isActive ? "Currently Active" : "Resume Session"}
                    >
                      <Play className="w-3 h-3" /> Resume
                    </button>
                    <button
                      onClick={() => onDeleteSession(s.threadId)}
                      className="p-1.5 rounded-lg text-slate-400 hover:text-rose-400 hover:bg-rose-500/10 transition-colors"
                      title="Delete Session"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
              );
            })
          )}
        </div>

        {/* Modal Footer */}
        {sessions.length > 0 && (
          <div className="p-3 border-t border-slate-800 flex items-center justify-between text-xs">
            <span className="text-[11px] text-slate-400">
              {sessions.length} saved session{sessions.length > 1 ? "s" : ""}
            </span>
            <button
              onClick={onClearAllSessions}
              className="text-rose-400 hover:text-rose-300 text-[11px] font-medium transition-colors"
            >
              Clear All History
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
