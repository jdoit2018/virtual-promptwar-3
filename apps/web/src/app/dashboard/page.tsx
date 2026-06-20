"use client";

import React, { useState, useEffect } from "react";
import { useAuth } from "../../context/AuthContext";
import { useRouter } from "next/navigation";
import { api } from "../../lib/api/client";
import Navbar from "../../components/Navbar";
import Link from "next/link";
import {
  TrendingDown,
  Flame,
  Award,
  ArrowRight,
  TrendingUp,
  AlertCircle,
  Home,
  Car,
  Utensils,
  ShoppingBag,
  Sparkles,
  Calendar
} from "lucide-react";

export default function DashboardPage() {
  const { user, loading: authLoading } = useAuth();
  const router = useRouter();

  const [baseline, setBaseline] = useState<any>(null);
  const [profile, setProfile] = useState<any>(null);
  const [goalData, setGoalData] = useState<any>(null);
  const [recentLogs, setRecentLogs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [noBaseline, setNoBaseline] = useState(false);

  const fetchDashboardData = async () => {
    try {
      // 1. Fetch Profile
      const profileData = await api.users.me();
      setProfile(profileData);

      // 2. Fetch Active Goal
      try {
        const activeGoal = await api.goals.getActive();
        setGoalData(activeGoal);
      } catch (err) {
        console.log("No active goal yet:", err);
      }

      // 3. Fetch Current Baseline
      try {
        const baselineData = await api.baselines.getCurrent();
        setBaseline(baselineData);
      } catch (err: any) {
        if (err.status === 404) {
          setNoBaseline(true);
        } else {
          console.error("Error fetching baseline:", err);
        }
      }

      // 4. Fetch Today's Logs
      try {
        const todayStr = new Date().toISOString().split("T")[0];
        const logs = await api.logs.get(todayStr);
        setRecentLogs(logs);
      } catch (err) {
        console.error("Error fetching logs:", err);
      }

    } catch (error) {
      console.error("Error fetching dashboard data:", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!authLoading) {
      if (!user) {
        router.push("/login");
      } else {
        fetchDashboardData();
      }
    }
  }, [user, authLoading, router]);

  if (authLoading || loading) {
    return (
      <div className="min-h-screen bg-brand-bg flex items-center justify-center">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-brand-primary border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <span className="text-gray-400 font-semibold text-sm">Assembling your eco-dashboard...</span>
        </div>
      </div>
    );
  }

  if (noBaseline) {
    return (
      <div className="min-h-screen bg-brand-bg flex flex-col">
        <Navbar />
        <main className="flex-grow flex items-center justify-center p-6 relative">
          <div className="absolute top-10 left-10 w-72 h-72 bg-brand-primary/10 rounded-full blur-3xl -z-10 animate-float"></div>
          <div className="absolute bottom-10 right-10 w-72 h-72 bg-brand-secondary/10 rounded-full blur-3xl -z-10 animate-float"></div>
          
          <div className="max-w-md w-full glass-panel p-8 sm:p-10 rounded-3xl border border-brand-border text-center shadow-2xl">
            <div className="bg-brand-primary/10 w-16 h-16 rounded-2xl flex items-center justify-center text-brand-primary mx-auto mb-6">
              <Sparkles className="w-8 h-8" />
            </div>
            <h2 className="text-2xl font-black text-white">Start Your Eco Journey</h2>
            <p className="text-sm text-gray-400 mt-3 mb-8 leading-relaxed">
              Complete our quick 4-step onboarding quiz to compute your baseline carbon footprint. It takes less than 2 minutes.
            </p>
            <Link
              href="/onboarding"
              className="w-full inline-flex items-center justify-center gap-2 py-3.5 px-6 rounded-xl bg-gradient-to-r from-brand-primary to-brand-secondary text-brand-bg font-extrabold transition-all duration-300 hover:brightness-110 shadow-lg shadow-brand-primary/20 cursor-pointer"
            >
              Take Onboarding Quiz
              <ArrowRight className="w-5 h-5" />
            </Link>
          </div>
        </main>
      </div>
    );
  }

  const baselineValue = baseline ? parseFloat(baseline.total_co2e) : 0;
  // Trees needed to offset baseline: 1 tonne of CO2 requires roughly 50 trees to absorb in a year
  const treesOffset = Math.round(baselineValue * 50);

  return (
    <div className="min-h-screen bg-brand-bg flex flex-col">
      <Navbar />
      
      <main className="flex-grow max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        {/* Dynamic header / Welcome */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h1 className="text-3xl font-black tracking-tight text-white">
              Hello, <span className="bg-gradient-to-r from-brand-primary to-brand-secondary bg-clip-text text-transparent">{profile?.first_name || "Eco Citizen"}</span>
            </h1>
            <p className="text-sm text-gray-400 mt-1">Here is your carbon footprint breakdown and reduction progress.</p>
          </div>
          <div className="flex gap-3">
            <Link
              href="/log"
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-brand-primary text-brand-bg font-bold hover:brightness-110 shadow-md cursor-pointer transition-all duration-300"
            >
              <Calendar className="w-4 h-4" />
              Log Daily Activity
            </Link>
          </div>
        </div>

        {/* Core KPIs Row */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Baseline Summary */}
          <div className="glass-card p-6 rounded-3xl border border-brand-border">
            <span className="text-xs font-bold text-gray-500 uppercase tracking-wider">Annual Baseline Footprint</span>
            <div className="flex items-baseline gap-2 mt-2">
              <span className="text-4xl font-black text-white">{baselineValue}</span>
              <span className="text-sm font-semibold text-gray-400">MT CO₂e / yr</span>
            </div>
            <p className="text-xs text-gray-500 mt-3 border-t border-brand-border/40 pt-3">
              Calculated on {new Date(baseline?.created_at).toLocaleDateString()}
            </p>
          </div>

          {/* Goal Summary */}
          <div className="glass-card p-6 rounded-3xl border border-brand-border">
            <span className="text-xs font-bold text-gray-500 uppercase tracking-wider">Annual Reduction Target</span>
            {goalData?.goal ? (
              <>
                <div className="flex items-baseline gap-2 mt-2">
                  <span className="text-4xl font-black text-brand-secondary">{goalData.goal.target_co2e}</span>
                  <span className="text-sm font-semibold text-gray-400">MT (-{goalData.goal.reduction_pct}%)</span>
                </div>
                <div className="mt-3 flex items-center gap-2">
                  <span className={`px-2 py-0.5 rounded text-[10px] font-extrabold uppercase ${
                    goalData.pace?.on_track ? "bg-brand-primary/10 text-brand-primary border border-brand-primary/20" : "bg-red-500/10 text-red-400 border border-red-500/25"
                  }`}>
                    {goalData.pace?.on_track ? "On Track" : "Off Track"}
                  </span>
                  <span className="text-xs text-gray-500">
                    Projected YTD: {goalData.pace?.projected_annual_co2e_mt} MT
                  </span>
                </div>
              </>
            ) : (
              <div className="h-full flex flex-col justify-between mt-2">
                <span className="text-sm text-gray-400">No active reduction goal set.</span>
                <Link href="/goals" className="text-xs font-bold text-brand-primary hover:underline flex items-center gap-1 mt-2">
                  Set annual target <ArrowRight className="w-3 h-3" />
                </Link>
              </div>
            )}
          </div>

          {/* Impact Equivalency */}
          <div className="glass-card p-6 rounded-3xl border border-brand-border bg-gradient-to-tr from-brand-primary/5 to-transparent">
            <span className="text-xs font-bold text-brand-primary uppercase tracking-wider flex items-center gap-1.5">
              <Sparkles className="w-3.5 h-3.5 animate-pulse" />
              Equivalency Metric
            </span>
            <div className="mt-2 text-2xl font-black text-white">
              {treesOffset} trees
            </div>
            <p className="text-xs text-gray-400 mt-2">
              needed to absorb your annual emissions output. Reduce emissions to decrease this count!
            </p>
          </div>
        </div>

        {/* Details & Logs Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Pillar breakdowns */}
          <div className="lg:col-span-2 glass-panel p-8 rounded-3xl border border-brand-border space-y-6">
            <h2 className="text-xl font-extrabold text-white">Footprint Breakdown by Pillar</h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {[
                { title: "Housing Energy", val: baseline?.housing_co2e, icon: Home, color: "text-blue-400", bg: "bg-blue-500/10" },
                { title: "Transportation", val: baseline?.transport_co2e, icon: Car, color: "text-emerald-400", bg: "bg-emerald-500/10" },
                { title: "Dietary", val: baseline?.diet_co2e, icon: Utensils, color: "text-orange-400", bg: "bg-orange-500/10" },
                { title: "Consumption", val: baseline?.consumption_co2e, icon: ShoppingBag, color: "text-purple-400", bg: "bg-purple-500/10" }
              ].map((p) => {
                const percentage = Math.round((parseFloat(p.val) / baselineValue) * 100) || 0;
                const Icon = p.icon;
                return (
                  <div key={p.title} className="p-5 rounded-2xl bg-brand-bg/40 border border-brand-border flex items-center gap-4">
                    <div className={`${p.bg} ${p.color} p-3 rounded-xl`}>
                      <Icon className="w-5 h-5" />
                    </div>
                    <div className="flex-grow">
                      <span className="text-xs font-bold text-gray-400 block">{p.title}</span>
                      <div className="flex items-baseline gap-2 mt-1">
                        <span className="text-lg font-black text-white">{p.val}</span>
                        <span className="text-xs text-gray-500">MT ({percentage}%)</span>
                      </div>
                      <div className="h-1.5 w-full bg-brand-border rounded-full mt-2 overflow-hidden">
                        <div className="h-full bg-brand-secondary rounded-full" style={{ width: `${percentage}%` }}></div>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Activity Logs sidebar */}
          <div className="glass-panel p-8 rounded-3xl border border-brand-border space-y-6">
            <div className="flex justify-between items-center">
              <h2 className="text-xl font-extrabold text-white">Today's Logs</h2>
              <Link href="/log" className="text-xs font-bold text-brand-primary hover:underline">
                View all
              </Link>
            </div>

            <div className="space-y-3">
              {recentLogs.length > 0 ? (
                recentLogs.map((log) => (
                  <div key={log.id} className="p-4 rounded-2xl bg-brand-bg/40 border border-brand-border flex justify-between items-center text-sm">
                    <div>
                      <span className="font-semibold text-gray-200 capitalize">{log.activity_type.replace(/_/g, " ")}</span>
                      <span className="text-xs text-gray-500 block">Qty: {log.quantity}</span>
                    </div>
                    <div className="text-right">
                      <span className="font-extrabold text-brand-primary">{log.total_co2e} kg</span>
                      <span className="text-[10px] text-gray-500 block">CO₂e</span>
                    </div>
                  </div>
                ))
              ) : (
                <div className="text-center py-8 border border-dashed border-brand-border rounded-2xl">
                  <AlertCircle className="w-8 h-8 text-gray-500 mx-auto mb-2" />
                  <p className="text-xs text-gray-500 font-semibold">No logs submitted today yet.</p>
                  <Link
                    href="/log"
                    className="text-xs text-brand-primary font-bold hover:underline block mt-2"
                  >
                    Log activities now
                  </Link>
                </div>
              )}
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
