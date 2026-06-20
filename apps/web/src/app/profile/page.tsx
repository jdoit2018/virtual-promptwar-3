"use client";

import React, { useState, useEffect } from "react";
import { useAuth } from "../../context/AuthContext";
import { useRouter } from "next/navigation";
import { api } from "../../lib/api/client";
import Navbar from "../../components/Navbar";
import { User, Globe, Bell, Shield, Loader2, Award, Flame, Check } from "lucide-react";

export default function ProfilePage() {
  const { user, loading: authLoading } = useAuth();
  const router = useRouter();

  const [profile, setProfile] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [regionCode, setRegionCode] = useState("UK");
  const [fcmRegistered, setFcmRegistered] = useState(false);

  useEffect(() => {
    if (!authLoading) {
      if (!user) {
        router.push("/login");
      } else {
        api.users.me()
          .then((data) => {
            setProfile(data);
            setRegionCode(data.region_code || "UK");
          })
          .catch((err) => console.error("Error loading user me:", err))
          .finally(() => setLoading(false));
      }
    }
  }, [user, authLoading, router]);

  const handleRegisterToken = async () => {
    try {
      // Simulate registering a mock FCM token
      await api.notifications.registerToken("mock-fcm-device-token");
      setFcmRegistered(true);
      setTimeout(() => setFcmRegistered(false), 3000);
    } catch (err) {
      console.error("Token registration failed:", err);
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

      <main className="flex-grow max-w-4xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        <div>
          <h1 className="text-3xl font-black text-white">Account Profile</h1>
          <p className="text-sm text-gray-400 mt-1">Manage credentials, region settings, and device notification tokens.</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {/* PROFILE STATS SIDEBAR */}
          <div className="glass-panel p-6 sm:p-8 rounded-3xl border border-brand-border text-center space-y-6">
            <div className="w-20 h-20 rounded-3xl bg-brand-primary/10 border border-brand-primary/20 text-brand-primary flex items-center justify-center text-3xl font-black mx-auto">
              {user?.displayName ? user.displayName[0].toUpperCase() : "U"}
            </div>
            <div>
              <h3 className="text-lg font-black text-white">{user?.displayName || "User"}</h3>
              <p className="text-xs text-gray-500 mt-1">{user?.email}</p>
            </div>

            <div className="border-t border-brand-border/60 pt-6 grid grid-cols-2 gap-4">
              <div className="p-3 rounded-2xl bg-brand-bg/40 border border-brand-border">
                <Flame className="w-5 h-5 text-orange-400 mx-auto mb-1" />
                <span className="text-[10px] text-gray-500 font-bold block uppercase tracking-wider">Current Streak</span>
                <span className="text-lg font-black text-white">{profile?.current_streak || 0}</span>
              </div>
              <div className="p-3 rounded-2xl bg-brand-bg/40 border border-brand-border">
                <Award className="w-5 h-5 text-brand-secondary mx-auto mb-1" />
                <span className="text-[10px] text-gray-500 font-bold block uppercase tracking-wider">Highest Streak</span>
                <span className="text-lg font-black text-white">{profile?.highest_streak || 0}</span>
              </div>
            </div>
          </div>

          {/* PREFERENCES SETTINGS */}
          <div className="md:col-span-2 glass-panel p-6 sm:p-8 rounded-3xl border border-brand-border space-y-6">
            <div className="space-y-4">
              <h2 className="text-xl font-extrabold text-white flex items-center gap-2">
                <Globe className="text-brand-primary w-5 h-5" />
                Region & Emission Factors
              </h2>
              <p className="text-xs text-gray-400">
                Carbon factor intensities vary across regions depending on their clean energy grids.
              </p>
              <div>
                <select
                  disabled
                  value={regionCode}
                  onChange={(e) => setRegionCode(e.target.value)}
                  className="w-full py-2.5 px-4 rounded-xl bg-brand-bg border border-brand-border text-gray-400 focus:outline-none focus:border-brand-primary"
                >
                  <option value="UK">United Kingdom (DEFRA 2024)</option>
                  <option value="US">United States (EPA eGRID)</option>
                  <option value="EU">European Union (EEA Factors)</option>
                  <option value="GLOBAL">Global Fallback Average</option>
                </select>
                <span className="text-[10px] text-gray-500 mt-1 block">UK and Global fallback grids are currently loaded in the database.</span>
              </div>
            </div>

            <div className="border-t border-brand-border/60 pt-6 space-y-4">
              <h2 className="text-xl font-extrabold text-white flex items-center gap-2">
                <Bell className="text-brand-secondary w-5 h-5" />
                FCM Push Notifications
              </h2>
              <p className="text-xs text-gray-400">
                Register this device to receive weekly reduction summaries and challenge streaks reminders.
              </p>
              <button
                onClick={handleRegisterToken}
                className="inline-flex items-center gap-2 py-2 px-5 rounded-xl bg-brand-secondary text-brand-bg font-extrabold hover:brightness-110 shadow-md cursor-pointer transition-all duration-300 text-xs"
              >
                {fcmRegistered ? (
                  <>
                    <Check className="w-4 h-4" />
                    Device Token Registered!
                  </>
                ) : (
                  <>
                    Register FCM Device Token
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
