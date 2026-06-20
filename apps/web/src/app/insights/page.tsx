"use client";

import React, { useState, useEffect } from "react";
import { useAuth } from "../../context/AuthContext";
import { useRouter } from "next/navigation";
import { api } from "../../lib/api/client";
import Navbar from "../../components/Navbar";
import {
  Award,
  Loader2,
  Trophy,
  Activity,
  Flame,
  CheckCircle,
  Plus,
  Play,
  RotateCcw
} from "lucide-react";

export default function InsightsPage() {
  const { user, loading: authLoading } = useAuth();
  const router = useRouter();

  const [challenges, setChallenges] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [updating, setUpdating] = useState<string | null>(null);
  const [progressInputs, setProgressInputs] = useState<Record<string, number>>({});

  const loadChallenges = async () => {
    setLoading(true);
    try {
      const data = await api.challenges.list();
      setChallenges(data);
      
      // Initialize progress input values
      const inputs: Record<string, number> = {};
      data.forEach((c) => {
        if (c.user_challenge) {
          inputs[c.id] = c.user_challenge.progress || 0;
        } else {
          inputs[c.id] = 0;
        }
      });
      setProgressInputs(inputs);
    } catch (err) {
      console.error("Failed to load challenges:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!authLoading) {
      if (!user) {
        router.push("/login");
      } else {
        loadChallenges();
      }
    }
  }, [user, authLoading, router]);

  const handleStartChallenge = async (id: string) => {
    setUpdating(id);
    try {
      await api.challenges.start(id);
      await loadChallenges();
    } catch (err) {
      console.error("Failed to start challenge:", err);
      alert("Error enrolling in challenge.");
    } finally {
      setUpdating(null);
    }
  };

  const handleUpdateProgress = async (id: string, targetValue: number) => {
    setUpdating(id);
    const progressVal = progressInputs[id] || 0;
    try {
      await api.challenges.updateProgress(id, progressVal);
      await loadChallenges();
    } catch (err) {
      console.error("Failed to update progress:", err);
      alert("Error updating challenge progress.");
    } finally {
      setUpdating(null);
    }
  };

  if (authLoading || loading) {
    return (
      <div className="min-h-screen bg-brand-bg flex items-center justify-center">
        <Loader2 className="w-8 h-8 text-brand-primary animate-spin" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-brand-bg flex flex-col">
      <Navbar />

      <main className="flex-grow max-w-6xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h1 className="text-3xl font-black text-white">Eco-Challenges Portal</h1>
            <p className="text-sm text-gray-400 mt-1">Enroll in weekly reduction challenges and earn CO₂e reduction rewards.</p>
          </div>
        </div>

        {/* Catalog grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {challenges.map((c) => {
            const isEnrolled = !!c.user_challenge;
            const isCompleted = c.user_challenge?.status === "completed";
            const progress = c.user_challenge?.progress || 0;
            const targetVal = c.target_value || 100;
            const pct = Math.min(100, Math.round((progress / targetVal) * 100));

            return (
              <div
                key={c.id}
                className={`glass-panel p-6 rounded-3xl border transition-all duration-300 flex flex-col justify-between ${
                  isCompleted
                    ? "border-brand-primary/40 bg-brand-primary/5 shadow-brand-primary/5"
                    : isEnrolled
                    ? "border-brand-secondary/30"
                    : "border-brand-border"
                }`}
              >
                {/* Header info */}
                <div>
                  <div className="flex justify-between items-start gap-2 mb-4">
                    <span className="text-[10px] font-extrabold uppercase tracking-wider text-gray-500 bg-brand-bg/60 border border-brand-border px-2.5 py-1 rounded-md">
                      {c.category}
                    </span>
                    <span className="text-[10px] font-black uppercase tracking-wider text-brand-secondary">
                      {c.difficulty}
                    </span>
                  </div>

                  <h3 className="text-lg font-black text-white leading-snug">{c.title}</h3>
                  <p className="text-xs text-gray-400 mt-2 leading-relaxed">{c.description}</p>
                </div>

                {/* Progress / Enrollment CTA footer */}
                <div className="mt-6 pt-6 border-t border-brand-border/40 space-y-4">
                  {/* Reward Badge */}
                  <div className="flex justify-between text-xs font-semibold">
                    <span className="text-gray-500">Eco Reward:</span>
                    <span className="text-brand-primary font-bold">-{c.co2e_reward} kg CO₂e</span>
                  </div>

                  {isCompleted ? (
                    <div className="p-3 rounded-xl bg-brand-primary/10 border border-brand-primary/20 flex items-center justify-center gap-2 text-xs font-bold text-brand-primary">
                      <CheckCircle className="w-4 h-4 shrink-0" />
                      Challenge Completed!
                    </div>
                  ) : isEnrolled ? (
                    <div className="space-y-4">
                      {/* Progress Bar */}
                      <div>
                        <div className="flex justify-between text-[10px] font-bold text-gray-500 uppercase tracking-wider mb-1.5">
                          <span>Progress ({progress} / {targetVal})</span>
                          <span>{pct}%</span>
                        </div>
                        <div className="h-2 w-full bg-brand-border rounded-full overflow-hidden">
                          <div
                            className="h-full bg-brand-secondary rounded-full"
                            style={{ width: `${pct}%` }}
                          ></div>
                        </div>
                      </div>

                      {/* Progress update inputs */}
                      <div className="flex gap-2">
                        <input
                          type="number"
                          min="0"
                          max={targetVal}
                          value={progressInputs[c.id] || 0}
                          onChange={(e) =>
                            setProgressInputs((prev) => ({
                              ...prev,
                              [c.id]: Math.min(targetVal, Math.max(0, parseInt(e.target.value) || 0))
                            }))
                          }
                          className="w-20 text-center py-2 px-1 rounded-xl bg-brand-bg border border-brand-border text-white text-xs focus:outline-none"
                        />
                        <button
                          onClick={() => handleUpdateProgress(c.id, targetVal)}
                          disabled={updating === c.id}
                          className="flex-grow py-2 px-3 rounded-xl bg-brand-secondary/20 hover:bg-brand-secondary/35 border border-brand-secondary/30 text-brand-secondary text-xs font-extrabold cursor-pointer flex items-center justify-center gap-1.5"
                        >
                          {updating === c.id ? (
                            <Loader2 className="w-3.5 h-3.5 animate-spin" />
                          ) : (
                            "Update"
                          )}
                        </button>
                      </div>
                    </div>
                  ) : (
                    <button
                      onClick={() => handleStartChallenge(c.id)}
                      disabled={updating === c.id}
                      className="w-full py-2.5 px-4 rounded-xl bg-brand-bg hover:bg-brand-border/40 border border-brand-border text-gray-200 text-xs font-extrabold transition-all duration-300 flex items-center justify-center gap-2 cursor-pointer"
                    >
                      {updating === c.id ? (
                        <Loader2 className="w-4 h-4 animate-spin" />
                      ) : (
                        <>
                          <Play className="w-3.5 h-3.5 fill-gray-200" />
                          Start Challenge
                        </>
                      )}
                    </button>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </main>
    </div>
  );
}
