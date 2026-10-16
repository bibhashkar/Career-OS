import React, { useState } from "react";
import {
  X,
  LogIn,
  UserPlus,
  Mail,
  Lock,
  User,
  AlertCircle,
  Loader2,
} from "lucide-react";
import { login, register } from "../services/api";

export function AuthModal({ isOpen, onClose, onSuccess }) {
  const [mode, setMode] = useState("login"); // 'login' | 'register'
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Form fields
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [visaStatus, setVisaStatus] = useState("Citizen");
  const [remotePreference, setRemotePreference] = useState("Remote");

  if (!isOpen) return null;

  async function handleSubmit(e) {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      if (mode === "login") {
        const res = await login(email, password);
        if (onSuccess) onSuccess(res.user);
        onClose();
      } else {
        const payload = {
          email,
          password,
          full_name: fullName,
          visa_status: visaStatus,
          remote_preference: remotePreference,
          preferred_locations: ["Remote", "San Francisco, CA"],
        };
        const res = await register(payload);
        if (onSuccess) onSuccess(res.user);
        onClose();
      }
    } catch (err) {
      console.error("Authentication error:", err);
      const msg =
        err.response?.data?.detail ||
        (mode === "login"
          ? "Invalid email or password. Please try again."
          : "Failed to create account. Please check your details.");
      setError(msg);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-in fade-in duration-150">
      <div className="relative w-full max-w-md bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl overflow-hidden">
        {/* Modal Header */}
        <div className="flex items-center justify-between p-5 border-b border-slate-800 bg-slate-900/50">
          <div className="flex items-center gap-2">
            <div className="p-2 rounded-xl bg-sky-500/10 text-sky-400 border border-sky-500/20">
              {mode === "login" ? (
                <LogIn className="w-5 h-5" />
              ) : (
                <UserPlus className="w-5 h-5" />
              )}
            </div>
            <div>
              <h2 className="text-base font-bold text-white">
                {mode === "login" ? "Sign In to Career-OS" : "Create Candidate Account"}
              </h2>
              <p className="text-xs text-slate-400">
                {mode === "login"
                  ? "Access your personas, matched feeds, and mock history"
                  : "Start tailored multi-persona job discovery"}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800 transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Tab Switcher */}
        <div className="flex border-b border-slate-800 bg-slate-950/40 p-1 m-4 rounded-xl">
          <button
            type="button"
            data-testid="tab-login"
            onClick={() => {
              setMode("login");
              setError(null);
            }}
            className={`flex-1 py-1.5 text-xs font-medium rounded-lg transition-all ${
              mode === "login"
                ? "bg-slate-800 text-white shadow-sm"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            Sign In
          </button>
          <button
            type="button"
            data-testid="tab-register"
            onClick={() => {
              setMode("register");
              setError(null);
            }}
            className={`flex-1 py-1.5 text-xs font-medium rounded-lg transition-all ${
              mode === "register"
                ? "bg-slate-800 text-white shadow-sm"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            Create Account
          </button>
        </div>

        {/* Form Body */}
        <form onSubmit={handleSubmit} className="px-5 pb-5 space-y-3.5">
          {error && (
            <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs flex items-start gap-2">
              <AlertCircle className="w-4 h-4 shrink-0 mt-0.5 text-rose-400" />
              <span>{error}</span>
            </div>
          )}

          {mode === "register" && (
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">
                Full Name
              </label>
              <div className="relative">
                <User className="absolute left-3 top-2.5 w-4 h-4 text-slate-500" />
                <input
                  type="text"
                  required
                  placeholder="e.g. Alex Smith"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  className="w-full pl-9 pr-3 py-2 bg-slate-950 border border-slate-700 rounded-xl text-sm text-white placeholder-slate-500 focus:outline-none focus:border-sky-500 focus:ring-1 focus:ring-sky-500"
                />
              </div>
            </div>
          )}

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">
              Email Address
            </label>
            <div className="relative">
              <Mail className="absolute left-3 top-2.5 w-4 h-4 text-slate-500" />
              <input
                type="email"
                required
                placeholder="name@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full pl-9 pr-3 py-2 bg-slate-950 border border-slate-700 rounded-xl text-sm text-white placeholder-slate-500 focus:outline-none focus:border-sky-500 focus:ring-1 focus:ring-sky-500"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">
              Password
            </label>
            <div className="relative">
              <Lock className="absolute left-3 top-2.5 w-4 h-4 text-slate-500" />
              <input
                type="password"
                required
                minLength={8}
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full pl-9 pr-3 py-2 bg-slate-950 border border-slate-700 rounded-xl text-sm text-white placeholder-slate-500 focus:outline-none focus:border-sky-500 focus:ring-1 focus:ring-sky-500"
              />
            </div>
          </div>

          {mode === "register" && (
            <div className="grid grid-cols-2 gap-3 pt-1">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">
                  Visa / Authorization
                </label>
                <select
                  value={visaStatus}
                  onChange={(e) => setVisaStatus(e.target.value)}
                  className="w-full px-2.5 py-2 bg-slate-950 border border-slate-700 rounded-xl text-xs text-white focus:outline-none focus:border-sky-500"
                >
                  <option value="Citizen">Citizen / PR</option>
                  <option value="H-1B">H-1B</option>
                  <option value="F-1 OPT">F-1 OPT</option>
                  <option value="Requires Sponsorship">Needs Sponsorship</option>
                  <option value="None">None / Other</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">
                  Modality
                </label>
                <select
                  value={remotePreference}
                  onChange={(e) => setRemotePreference(e.target.value)}
                  className="w-full px-2.5 py-2 bg-slate-950 border border-slate-700 rounded-xl text-xs text-white focus:outline-none focus:border-sky-500"
                >
                  <option value="Remote">Remote</option>
                  <option value="Hybrid">Hybrid</option>
                  <option value="On-site">On-site</option>
                </select>
              </div>
            </div>
          )}

          <div className="pt-2">
            <button
              type="submit"
              data-testid="auth-submit-btn"
              disabled={loading}
              className="w-full py-2.5 px-4 bg-sky-600 hover:bg-sky-500 disabled:opacity-50 text-white font-medium text-xs rounded-xl shadow-lg shadow-sky-500/20 transition-all flex items-center justify-center gap-2 cursor-pointer"
            >
              {loading && <Loader2 className="w-4 h-4 animate-spin" />}
              <span>
                {loading
                  ? "Processing..."
                  : mode === "login"
                  ? "Sign In"
                  : "Create Account"}
              </span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
