"use client";

import React, { useState, useEffect } from "react";
import {
  Globe,
  Key,
  ShieldCheck,
  AlertCircle,
  Clock,
  Save,
  CheckCircle2,
  Laptop,
  RefreshCw,
  Sparkles,
} from "lucide-react";
import { fetchSettings, updateSettings, launchMoodleLogin, verifyMoodleSession, fetchLoginProgress } from "@/lib/api";

export default function SettingsPage() {
  const [moodleUrl, setMoodleUrl] = useState("");
  const [sessionState, setSessionState] = useState<{
    isAuthenticated: boolean;
    isExpired: boolean;
    message: string;
  }>({
    isAuthenticated: false,
    isExpired: false,
    message: "Checking session...",
  });
  const [saveStatus, setSaveStatus] = useState<string | null>(null);
  const [isLoggingIn, setIsLoggingIn] = useState(false);
  const [loginProgressMsg, setLoginProgressMsg] = useState<string | null>(null);
  const [verifyStatus, setVerifyStatus] = useState<{ valid: boolean; expired?: boolean; message: string } | null>(null);
  const [isVerifying, setIsVerifying] = useState(false);
  const [loading, setLoading] = useState(true);

  const checkSession = async () => {
    try {
      const data = await fetchSettings();
      if (data.settings.moodle_url) setMoodleUrl(data.settings.moodle_url);
      if (data.settings.moodle_url && data.is_authenticated) {
        const v = await verifyMoodleSession();
        setSessionState({
          isAuthenticated: v.valid,
          isExpired: v.expired,
          message: v.message,
        });
      } else {
        setSessionState({
          isAuthenticated: false,
          isExpired: false,
          message: data.is_authenticated ? "Session saved" : "Not connected",
        });
      }
    } catch (err) {
      console.error("Failed to load settings:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    checkSession();
  }, []);

  // Poll interactive login progress while browser is open
  useEffect(() => {
    let timer: NodeJS.Timeout;
    if (isLoggingIn) {
      timer = setInterval(async () => {
        try {
          const prog = await fetchLoginProgress();
          setLoginProgressMsg(prog.message);
          if (!prog.is_logging_in) {
            setIsLoggingIn(false);
            clearInterval(timer);
            checkSession();
          }
        } catch (err) {
          console.error("Error polling login progress:", err);
        }
      }, 1200);
    }
    return () => clearInterval(timer);
  }, [isLoggingIn]);

  const handleSaveSettings = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaveStatus("Saving...");
    try {
      await updateSettings({ moodle_url: moodleUrl.trim() });
      setSaveStatus("URL saved successfully!");
      setTimeout(() => setSaveStatus(null), 3000);
    } catch (err: any) {
      setSaveStatus(`Failed to save: ${err.message}`);
    }
  };

  const handleLaunchMicrosoftSSO = async () => {
    setIsLoggingIn(true);
    setLoginProgressMsg("Opening browser window for Microsoft SSO...");
    setVerifyStatus(null);
    try {
      const res = await launchMoodleLogin();
      setLoginProgressMsg(res.message);
    } catch (err: any) {
      setIsLoggingIn(false);
      setLoginProgressMsg(`Error: ${err.message}`);
    }
  };

  const handleVerifySession = async () => {
    setIsVerifying(true);
    setVerifyStatus(null);
    try {
      const res = await verifyMoodleSession();
      setVerifyStatus(res);
      setSessionState({
        isAuthenticated: res.valid,
        isExpired: res.expired,
        message: res.message,
      });
    } catch (err: any) {
      setVerifyStatus({ valid: false, expired: true, message: err.message || "Failed to verify session" });
    } finally {
      setIsVerifying(false);
    }
  };

  return (
    <div className="space-y-8 max-w-4xl">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-white">System Settings & Connection</h1>
        <p className="text-sm text-slate-400 mt-1">
          Configure your university Moodle connection, Microsoft SSO credentials, and local scheduler.
        </p>
      </div>

      {/* Moodle Connection Configuration Card */}
      <div className="p-6 rounded-xl bg-slate-900/60 border border-slate-800 space-y-6">
        <div className="flex items-center space-x-3 pb-4 border-b border-slate-800">
          <Globe className="w-5 h-5 text-blue-400" />
          <div>
            <h2 className="text-base font-semibold text-white">University Moodle Portal</h2>
            <p className="text-xs text-slate-400">Specify the base URL of your institution&apos;s Moodle instance</p>
          </div>
        </div>

        <form onSubmit={handleSaveSettings} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-1.5">
              Moodle Base URL
            </label>
            <input
              type="url"
              required
              placeholder="https://moodle.your-university.edu"
              value={moodleUrl}
              onChange={(e) => setMoodleUrl(e.target.value)}
              className="w-full px-4 py-2 bg-slate-950 border border-slate-800 rounded-lg text-sm text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
            />
            <p className="text-[11px] text-slate-500 mt-1">
              Example: https://moodle.example.edu or https://lms.university.edu
            </p>
          </div>

          <div className="flex items-center space-x-3">
            <button
              type="submit"
              className="flex items-center space-x-2 px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-medium text-xs transition"
            >
              <Save className="w-3.5 h-3.5" />
              <span>Save URL</span>
            </button>
            {saveStatus && <span className="text-xs text-emerald-400 font-medium">{saveStatus}</span>}
          </div>
        </form>
      </div>

      {/* Microsoft SSO Authentication Card */}
      <div className="p-6 rounded-xl bg-slate-900/60 border border-slate-800 space-y-6">
        <div className="flex items-center justify-between pb-4 border-b border-slate-800">
          <div className="flex items-center space-x-3">
            <Key className="w-5 h-5 text-indigo-400" />
            <div>
              <h2 className="text-base font-semibold text-white">Microsoft Single Sign-On (SSO)</h2>
              <p className="text-xs text-slate-400">Real browser session capture for university Microsoft authentication & MFA</p>
            </div>
          </div>

          {/* Live Status Pill */}
          <div>
            {sessionState.isExpired ? (
              <span className="px-3 py-1 rounded-full text-xs font-semibold bg-rose-500/15 border border-rose-500/30 text-rose-300 flex items-center gap-1.5 animate-pulse">
                <AlertCircle className="w-3.5 h-3.5 text-rose-400" />
                Moodle session expired — Sign in again
              </span>
            ) : sessionState.isAuthenticated ? (
              <span className="px-3 py-1 rounded-full text-xs font-semibold bg-emerald-500/15 border border-emerald-500/30 text-emerald-300 flex items-center gap-1.5">
                <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
                Moodle Connected
              </span>
            ) : (
              <span className="px-3 py-1 rounded-full text-xs font-semibold bg-amber-500/15 border border-amber-500/30 text-amber-300 flex items-center gap-1.5">
                <AlertCircle className="w-3.5 h-3.5 text-amber-400" />
                Not Connected
              </span>
            )}
          </div>
        </div>

        <div className="space-y-4 text-sm text-slate-300">
          <div className="bg-slate-950/60 p-4 rounded-lg border border-slate-800/80 space-y-2 text-xs text-slate-400 leading-relaxed">
            <p className="font-semibold text-slate-200">How Microsoft SSO works with Study Pilot:</p>
            <ol className="list-decimal list-inside space-y-1 text-slate-300">
              <li>Click <strong>&quot;Sign in with Microsoft SSO&quot;</strong> to open a real browser window.</li>
              <li>The browser navigates to Moodle and clicks <strong>&quot;Sign in with Microsoft&quot;</strong>.</li>
              <li>Microsoft will automatically authenticate you if a session is cached, or display the Microsoft login and MFA prompt.</li>
              <li>Complete your Microsoft login and MFA manually in the browser.</li>
              <li>Once Microsoft redirects back to Moodle, Study Pilot detects successful authentication and saves the session locally to <code className="text-blue-400">data/moodle_auth/storage_state.json</code>.</li>
            </ol>
            <p className="text-slate-500 text-[11px] pt-1">
              Zero-credential leak: Study Pilot never handles, logs, or stores your password or MFA codes.
            </p>
          </div>

          <div className="flex items-center space-x-3 pt-2">
            <button
              type="button"
              onClick={handleLaunchMicrosoftSSO}
              disabled={!moodleUrl || isLoggingIn}
              className={`px-4 py-2.5 rounded-lg text-xs font-semibold transition flex items-center space-x-2 shadow-sm ${
                !moodleUrl || isLoggingIn
                  ? "bg-slate-800 text-slate-500 cursor-not-allowed border border-slate-700"
                  : "bg-indigo-600 hover:bg-indigo-500 text-white shadow-indigo-500/20"
              }`}
            >
              <Laptop className="w-4 h-4" />
              <span>{isLoggingIn ? "Browser Window Open..." : "Sign in with Microsoft SSO"}</span>
            </button>

            <button
              type="button"
              onClick={handleVerifySession}
              disabled={!moodleUrl || isVerifying || isLoggingIn}
              className="px-4 py-2.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium transition flex items-center space-x-1.5"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${isVerifying ? "animate-spin" : ""}`} />
              <span>{isVerifying ? "Verifying..." : "Verify Session"}</span>
            </button>
          </div>

          {/* Live Interactive Login Progress Box */}
          {loginProgressMsg && (
            <div className={`p-3.5 rounded-lg text-xs border flex items-center space-x-2.5 ${
              isLoggingIn
                ? "bg-blue-500/10 border-blue-500/20 text-blue-300 animate-pulse"
                : sessionState.isAuthenticated
                ? "bg-emerald-500/10 border-emerald-500/20 text-emerald-300"
                : "bg-slate-950 border-slate-800 text-slate-300"
            }`}>
              {isLoggingIn && <RefreshCw className="w-3.5 h-3.5 animate-spin shrink-0" />}
              <span>{loginProgressMsg}</span>
            </div>
          )}

          {verifyStatus && (
            <div
              className={`p-3.5 rounded-lg text-xs border flex items-center space-x-2 ${
                verifyStatus.valid
                  ? "bg-emerald-500/10 border-emerald-500/20 text-emerald-300"
                  : "bg-rose-500/10 border-rose-500/20 text-rose-300"
              }`}
            >
              {verifyStatus.valid ? (
                <CheckCircle2 className="w-4 h-4 shrink-0 text-emerald-400" />
              ) : (
                <AlertCircle className="w-4 h-4 shrink-0 text-rose-400" />
              )}
              <span>{verifyStatus.message}</span>
            </div>
          )}
        </div>
      </div>

      {/* Windows Task Scheduler Automatic Daily Sync Card */}
      <div className="p-6 rounded-xl bg-slate-900/60 border border-slate-800 space-y-6">
        <div className="flex items-center space-x-3 pb-4 border-b border-slate-800">
          <Clock className="w-5 h-5 text-emerald-400" />
          <div>
            <h2 className="text-base font-semibold text-white">Daily Automatic Synchronization</h2>
            <p className="text-xs text-slate-400">Windows Task Scheduler primary execution mechanism</p>
          </div>
        </div>

        <div className="space-y-3 text-xs text-slate-400 leading-relaxed">
          <p>
            The automatic daily Moodle check runs via Windows Task Scheduler.
            It operates independently using the saved Microsoft SSO session even when the web application or browser is closed.
          </p>

          <div className="space-y-1.5">
            <span className="font-semibold text-slate-300">Windows Task Scheduler Command:</span>
            <pre className="p-3 bg-slate-950 border border-slate-800 rounded-lg font-mono text-emerald-400 text-xs select-all overflow-x-auto">
              {`python -m backend.app.cli sync --trigger scheduled`}
            </pre>
          </div>

          <p className="text-[11px] text-slate-500">
            Run <code className="text-blue-400">setup_windows_scheduler.ps1</code> in your repository root to register this task automatically in Windows with a single click.
          </p>
        </div>
      </div>
    </div>
  );
}
