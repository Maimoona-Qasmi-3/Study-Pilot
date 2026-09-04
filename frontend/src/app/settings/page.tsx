"use client";

import React, { useState, useEffect } from "react";
import {
  Globe,
  Key,
  ShieldCheck,
  AlertCircle,
  Clock,
  Terminal,
  Save,
  CheckCircle2,
  ExternalLink,
  Laptop,
} from "lucide-react";
import { fetchSettings, updateSettings, launchMoodleLogin, verifyMoodleSession } from "@/lib/api";

export default function SettingsPage() {
  const [moodleUrl, setMoodleUrl] = useState("");
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [saveStatus, setSaveStatus] = useState<string | null>(null);
  const [loginStatus, setLoginStatus] = useState<string | null>(null);
  const [verifyStatus, setVerifyStatus] = useState<{ valid: boolean; message: string } | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchSettings()
      .then((data) => {
        if (data.settings.moodle_url) setMoodleUrl(data.settings.moodle_url);
        setIsAuthenticated(data.is_authenticated);
      })
      .catch((err) => console.error("Failed to load settings:", err))
      .finally(() => setLoading(false));
  }, []);

  const handleSaveSettings = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaveStatus("Saving...");
    try {
      await updateSettings({ moodle_url: moodleUrl });
      setSaveStatus("Saved successfully!");
      setTimeout(() => setSaveStatus(null), 3000);
    } catch (err: any) {
      setSaveStatus(`Failed to save: ${err.message}`);
    }
  };

  const handleLaunchLogin = async () => {
    setLoginStatus("Launching browser login window...");
    setVerifyStatus(null);
    try {
      const res = await launchMoodleLogin();
      setLoginStatus(res.message);
    } catch (err: any) {
      setLoginStatus(`Error: ${err.message}`);
    }
  };

  const handleVerifySession = async () => {
    setVerifyStatus({ valid: false, message: "Testing headless session..." });
    try {
      const res = await verifyMoodleSession();
      setVerifyStatus(res);
      setIsAuthenticated(res.valid);
    } catch (err: any) {
      setVerifyStatus({ valid: false, message: err.message || "Failed to verify session" });
    }
  };

  return (
    <div className="space-y-8 max-w-4xl">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-white">System Settings & Connection</h1>
        <p className="text-sm text-slate-400 mt-1">
          Configure your university Moodle connection, session credentials, and local scheduler.
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

      {/* Authentication & Session Management Card */}
      <div className="p-6 rounded-xl bg-slate-900/60 border border-slate-800 space-y-6">
        <div className="flex items-center space-x-3 pb-4 border-b border-slate-800">
          <Key className="w-5 h-5 text-indigo-400" />
          <div>
            <h2 className="text-base font-semibold text-white">Moodle Authentication Session</h2>
            <p className="text-xs text-slate-400">Zero-credential-leak interactive login capture</p>
          </div>
        </div>

        <div className="space-y-4 text-sm text-slate-300">
          <p className="text-xs text-slate-400 leading-relaxed">
            Study Pilot does not store your password. Instead, clicking <strong>&quot;Open Login Browser&quot;</strong>{" "}
            launches a dedicated real browser window where you can log in through whatever method your university uses
            (including Microsoft 365, Google Workspace, Duo, or 2FA).
            Once you log in, session cookies are securely stored in your local <code className="text-blue-400">data/moodle_auth/storage_state.json</code>.
          </p>

          <div className="flex items-center space-x-3 pt-2">
            <div className="flex items-center space-x-2 px-3 py-1.5 rounded-md bg-slate-950 border border-slate-800 text-xs">
              <span className="text-slate-400">Session Status:</span>
              {isAuthenticated ? (
                <span className="text-emerald-400 font-semibold flex items-center gap-1">
                  <ShieldCheck className="w-3.5 h-3.5" /> Active
                </span>
              ) : (
                <span className="text-amber-400 font-semibold flex items-center gap-1">
                  <AlertCircle className="w-3.5 h-3.5" /> Not Connected / Expired
                </span>
              )}
            </div>

            <button
              type="button"
              onClick={handleLaunchLogin}
              disabled={!moodleUrl}
              className={`px-4 py-2 rounded-lg text-xs font-semibold transition flex items-center space-x-2 ${
                !moodleUrl
                  ? "bg-slate-800 text-slate-500 cursor-not-allowed"
                  : "bg-indigo-600 hover:bg-indigo-500 text-white"
              }`}
            >
              <Laptop className="w-3.5 h-3.5" />
              <span>Open Login Browser</span>
            </button>

            <button
              type="button"
              onClick={handleVerifySession}
              disabled={!moodleUrl}
              className="px-3 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium transition"
            >
              Verify Session
            </button>
          </div>

          {loginStatus && (
            <div className="p-3 rounded-lg bg-blue-500/10 border border-blue-500/20 text-xs text-blue-300">
              {loginStatus}
            </div>
          )}

          {verifyStatus && (
            <div
              className={`p-3 rounded-lg text-xs border ${
                verifyStatus.valid
                  ? "bg-emerald-500/10 border-emerald-500/20 text-emerald-300"
                  : "bg-rose-500/10 border-rose-500/20 text-rose-300"
              }`}
            >
              {verifyStatus.message}
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
            As designed, the primary mechanism for the automatic daily Moodle check runs via Windows Task Scheduler.
            It operates independently even when the web application or browser is closed.
          </p>

          <div className="space-y-1.5">
            <span className="font-semibold text-slate-300">Windows Task Scheduler Command:</span>
            <pre className="p-3 bg-slate-950 border border-slate-800 rounded-lg font-mono text-emerald-400 text-xs select-all overflow-x-auto">
              {`python -m backend.app.cli sync --trigger scheduled`}
            </pre>
          </div>

          <p className="text-[11px] text-slate-500">
            A setup script (<code className="text-blue-400">setup_windows_scheduler.ps1</code>) is provided in your repository root to register this task automatically in Windows with a single click.
          </p>
        </div>
      </div>
    </div>
  );
}
