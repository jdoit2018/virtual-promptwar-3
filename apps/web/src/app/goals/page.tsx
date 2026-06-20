"use client";

import React, { useState, useEffect } from "react";
import { useAuth } from "../../context/AuthContext";
import { useRouter } from "next/navigation";
import { api } from "../../lib/api/client";
import Navbar from "../../components/Navbar";
import { Target, Loader2, Award, Sparkles, TrendingDown, Check } from "lucide-react";

export default function GoalsPage() {
  const { user, loading: authLoading } = useAuth();
  const router = useRouter();

  const [activeGoal, setActiveGoal] = useState<any>(null);
  const [baseline, setBaseline] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  // Form states
  const [reductionPct, setReductionPct] = useState<number>(20);
  const [targetYear, setTargetYear] = useState<number>(new Date().getFullYear());

  const loadGoalData = async () => {
    setLoading(true);
    try {
      // Load baseline
      try {
        const bl = await api.baselines.getCurrent();
        setBaseline(bl);
      } catch (err) {
        console.error("Baseline not found during goals load:", err);
      }

      // Load active goal
      try {
        const data = await api.goals.getActive();
        setActiveGoal(data);
        if (data?.goal) {
          setReductionPct(data.goal.reduction_pct);
          setTargetYear(data.goal.target_year);
        }
      } catch (err) {
        console.log("No active goal found.");
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!authLoading) {
      if (!user) {
        router.push("/login");
      } else {
        loadGoalData();
      }
    }
  }, [user, authLoading, router]);

  const handleSetGoal = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!baseline) {
      alert("You need to take the onboarding baseline quiz before setting a goal.");
      return;
    }
    setSaving(true);
    try {
      const baselineVal = parseFloat(baseline.total_co2e) || 0;
      // Target is baseline reduced by percentage
      const targetVal = parseFloat((baselineVal * (1 - reductionPct / 100)).toFixed(2));
      
      await api.goals.create({
        target_co2e: targetVal,
        target_year: targetYear,
      });

      await loadGoalData();
    } catch (err) {
      console.error("Failed to create goal:", err);
      alert("Error setting reduction goal.");
    } finally {
      setSaving(false);
    }
  };

  if (authLoading || loading) {
    return (
      <div className="min-h-screen bg-brand-bg flex items-center justify-center">
        <Loader2 className="w-8 h-8 text-brand-primary animate-spin" />
      </div>
    );
  }

  const baselineValue = baseline ? parseFloat(baseline.total_co2e) : 0;
  const targetCo2e = parseFloat((baselineValue * (1 - reductionPct / 100)).toFixed(2));

  return (
    <div className="min-h-screen bg-brand-bg flex flex-col">
      <Navbar />

      <main className="flex-grow max-w-4xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        <div>
          <h1 className="text-3xl font-black text-white">Annual Reduction Goals</h1>
          <p className="text-sm text-gray-400 mt-1">Establish annual targets and monitor your reduction trajectory.</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {/* GOAL SETTING FORM */}
          <div className="md:col-span-2 glass-panel p-6 sm:p-8 rounded-3xl border border-brand-border space-y-6">
            <h2 className="text-xl font-extrabold text-white flex items-center gap-2">
              <Target className="text-brand-primary w-5 h-5" />
              Establish New Target
            </h2>

            {!baseline ? (
              <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/25 text-sm text-red-400">
                You must complete onboarding before configuring goals.
              </div>
            ) : (
              <form onSubmit={handleSetGoal} className="space-y-6">
                <div>
                  <div className="flex justify-between text-xs font-bold text-gray-400 uppercase tracking-wider mb-2">
                    <span>Reduction Percentage</span>
                    <span className="text-brand-primary font-black text-sm">{reductionPct}% Reduction</span>
                  </div>
                  <input
                    type="range"
                    min="5"
                    max="60"
                    step="5"
                    value={reductionPct}
                    onChange={(e) => setReductionPct(parseInt(e.target.value))}
                    className="w-full h-2 bg-brand-border rounded-lg appearance-none cursor-pointer accent-brand-primary"
                  />
                  <div className="flex justify-between text-[10px] text-gray-500 mt-1">
                    <span>5% (Conservative)</span>
                    <span>30% (Ambitious)</span>
                    <span>60% (Carbon Neutral Path)</span>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-bold uppercase tracking-wider text-gray-400 mb-2">
                      Target Year
                    </label>
                    <input
                      type="number"
                      min={new Date().getFullYear()}
                      max={new Date().getFullYear() + 5}
                      value={targetYear}
                      onChange={(e) => setTargetYear(parseInt(e.target.value))}
                      className="w-full py-2.5 px-4 rounded-xl bg-brand-bg border border-brand-border text-white focus:outline-none focus:border-brand-primary"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-bold uppercase tracking-wider text-gray-400 mb-2">
                      Computed Target CO₂e
                    </label>
                    <div className="py-2.5 px-4 rounded-xl bg-brand-bg/50 border border-brand-border text-gray-300 font-bold">
                      {targetCo2e} MT / yr
                    </div>
                  </div>
                </div>

                <button
                  type="submit"
                  disabled={saving}
                  className="w-full flex items-center justify-center gap-2 py-3.5 px-6 rounded-xl bg-gradient-to-r from-brand-primary to-brand-secondary text-brand-bg font-extrabold hover:brightness-110 shadow-lg cursor-pointer"
                >
                  {saving ? (
                    <>
                      <Loader2 className="w-5 h-5 animate-spin" />
                      Saving Target...
                    </>
                  ) : (
                    <>
                      <Check className="w-5 h-5" />
                      Set Annual Goal
                    </>
                  )}
                </button>
              </form>
            )}
          </div>

          {/* ACTIVE GOAL VIEW */}
          <div className="glass-panel p-6 sm:p-8 rounded-3xl border border-brand-border space-y-6">
            <h2 className="text-xl font-extrabold text-white flex items-center gap-2">
              <Award className="text-brand-secondary w-5 h-5" />
              Active Goal
            </h2>

            {activeGoal?.goal ? (
              <div className="space-y-6">
                <div>
                  <span className="text-xs font-bold text-gray-500 uppercase tracking-wider">Annual Target</span>
                  <div className="text-3xl font-black text-white mt-1">
                    {activeGoal.goal.target_co2e} <span className="text-xs text-gray-400">MT</span>
                  </div>
                  <div className="text-xs text-brand-primary font-bold mt-1">
                    -{activeGoal.goal.reduction_pct}% relative to baseline ({baselineValue} MT)
                  </div>
                </div>

                <div className="border-t border-brand-border/60 pt-4 space-y-3">
                  <div className="flex justify-between items-center text-xs font-bold">
                    <span className="text-gray-400 uppercase tracking-wider">YTD Trajectory</span>
                    <span className={`px-2 py-0.5 rounded text-[10px] font-extrabold uppercase ${
                      activeGoal.pace?.on_track ? "bg-brand-primary/10 text-brand-primary" : "bg-red-500/10 text-red-400"
                    }`}>
                      {activeGoal.pace?.on_track ? "On Track" : "Off Track"}
                    </span>
                  </div>
                  <div className="flex justify-between text-xs">
                    <span className="text-gray-500">Projected Run Rate:</span>
                    <span className="text-gray-200 font-semibold">{activeGoal.pace?.projected_annual_co2e_mt} MT</span>
                  </div>
                </div>

                <div className="border-t border-brand-border/60 pt-4 text-center">
                  <Sparkles className="w-5 h-5 text-brand-secondary mx-auto mb-2 animate-pulse" />
                  <p className="text-xs text-gray-400 leading-relaxed">
                    Set small daily habits to stay below your trajectory run rate. Make sure to log every commute and meal!
                  </p>
                </div>
              </div>
            ) : (
              <div className="text-center py-8">
                <Target className="w-10 h-10 text-gray-600 mx-auto mb-3" />
                <p className="text-sm text-gray-400 font-bold">No active goal set</p>
                <p className="text-xs text-gray-500 mt-1">Set a target on the left to start tracking reduction metrics.</p>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
