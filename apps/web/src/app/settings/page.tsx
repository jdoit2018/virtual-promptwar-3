"use client";

import React, { useState } from "react";
import { useAuth } from "../../context/AuthContext";
import { useRouter } from "next/navigation";
import Navbar from "../../components/Navbar";
import { ShieldAlert, Download, Trash2, Loader2, ArrowRight } from "lucide-react";
import { api } from "../../lib/api/client";

export default function SettingsPage() {
  const { user, logout, loading: authLoading } = useAuth();
  const router = useRouter();

  const [exporting, setExporting] = useState(false);
  const [deleting, setDeleting] = useState(false);

  const handleExport = async () => {
    setExporting(true);
    try {
      const data = await api.users.exportData();
      const jsonStr = JSON.stringify(data, null, 2);
      const blob = new Blob([jsonStr], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `auracarbon-data-export-${new Date().toISOString().split("T")[0]}.json`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
    } catch (err) {
      console.error("Failed to export data:", err);
      alert("Error generating GDPR export package.");
    } finally {
      setExporting(false);
    }
  };

  const handleDelete = async () => {
    if (confirm("WARNING: Are you absolutely sure you want to delete your account? This action is permanent and all logged data will be deleted immediately.")) {
      setDeleting(true);
      try {
        await api.users.deleteAccount();
        logout();
        router.push("/login");
      } catch (err) {
        console.error("Failed to delete account:", err);
        alert("Error deleting account.");
      } finally {
        setDeleting(false);
      }
    }
  };

  if (authLoading || !user) {
    return (
      <div className="min-h-screen bg-brand-bg flex items-center justify-center">
        <Loader2 className="w-8 h-8 text-brand-primary animate-spin" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-brand-bg flex flex-col">
      <Navbar />

      <main className="flex-grow max-w-3xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        <div>
          <h1 className="text-3xl font-black text-white">System Settings</h1>
          <p className="text-sm text-gray-400 mt-1">Manage data privacy policies, exports, and account status.</p>
        </div>

        <div className="glass-panel p-6 sm:p-8 rounded-3xl border border-brand-border space-y-6">
          <div className="flex items-start gap-4">
            <div className="p-3 bg-brand-primary/10 text-brand-primary rounded-xl">
              <Download className="w-6 h-6" />
            </div>
            <div className="flex-grow space-y-1">
              <h3 className="font-extrabold text-white text-base">Export Personal Data (GDPR Compliance)</h3>
              <p className="text-xs text-gray-400">
                Download a machine-readable JSON archive containing all baseline answers, daily footprint entries, and challenges.
              </p>
              <button
                onClick={handleExport}
                disabled={exporting}
                className="mt-3 inline-flex items-center gap-2 py-2 px-4 rounded-xl bg-brand-primary/10 hover:bg-brand-primary/20 border border-brand-primary/20 text-brand-primary text-xs font-extrabold cursor-pointer transition-all"
              >
                {exporting ? (
                  <>
                    <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    Packaging...
                  </>
                ) : (
                  <>
                    Request Archive Package
                  </>
                )}
              </button>
            </div>
          </div>

          <div className="border-t border-brand-border/60 pt-6 flex items-start gap-4">
            <div className="p-3 bg-red-500/10 text-red-400 rounded-xl">
              <Trash2 className="w-6 h-6" />
            </div>
            <div className="flex-grow space-y-1">
              <h3 className="font-extrabold text-white text-base">Terminate & Delete Account</h3>
              <p className="text-xs text-gray-400">
                Immediately delete your profile, current streak history, and all logged CO₂e entries. This is irreversible.
              </p>
              <button
                onClick={handleDelete}
                disabled={deleting}
                className="mt-3 inline-flex items-center gap-2 py-2 px-4 rounded-xl bg-red-500/10 hover:bg-red-500/20 border border-red-500/20 text-red-400 text-xs font-extrabold cursor-pointer transition-all"
              >
                {deleting ? (
                  <>
                    <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    Terminating...
                  </>
                ) : (
                  <>
                    Delete Account Permanently
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
