"use client";

import React, { useState, useEffect } from "react";
import { useAuth } from "../../context/AuthContext";
import { useRouter } from "next/navigation";
import { api } from "../../lib/api/client";
import Navbar from "../../components/Navbar";
import {
  Car,
  Home,
  Utensils,
  ShoppingBag,
  Plus,
  Loader2,
  Trash2,
  Calendar,
  AlertCircle
} from "lucide-react";

export default function LogPage() {
  const { user, loading: authLoading } = useAuth();
  const router = useRouter();

  const [logDate, setLogDate] = useState<string>("");
  const [activeTab, setActiveTab] = useState<string>("transport");
  const [logs, setLogs] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);

  // Form Fields
  const [quantity, setQuantity] = useState<number>(10);
  const [activityType, setActivityType] = useState<string>("gas_car");
  
  // Options mapping based on database seed
  const activityOptions: Record<string, { label: string; unit: string; options: { val: string; label: string }[] }> = {
    transport: {
      label: "Transportation",
      unit: "miles traveled",
      options: [
        { val: "gas_car", label: "Gasoline/Diesel Vehicle" },
        { val: "electric_car", label: "Electric/Hybrid Vehicle" },
        { val: "public_bus", label: "Public Bus Commute" },
        { val: "train_metro", label: "Rail / Train / Subway" },
      ]
    },
    diet: {
      label: "Dietary Consumption",
      unit: "meals consumed",
      options: [
        { val: "meal_meat_heavy", label: "Heavy Red Meat Meal" },
        { val: "meal_flexitarian", label: "Chicken / Fish / Pork Meal" },
        { val: "meal_vegetarian", label: "Vegetarian Meal" },
        { val: "meal_vegan", label: "Vegan / Plant-based Meal" },
      ]
    },
    housing: {
      label: "Housing & Utilities",
      unit: "units consumed (kWh / therms)",
      options: [
        { val: "electricity_kwh", label: "Electricity Usage (kWh)" },
        { val: "natural_gas_therms", label: "Natural Gas (therms)" },
        { val: "heating_oil_gallons", label: "Heating Oil (gallons)" },
      ]
    },
    consumption: {
      label: "Shopping & Consumption",
      unit: "dollars spent ($)",
      options: [
        { val: "fashion_purchases", label: "Clothing / Fashion Items" },
        { val: "electronics_purchases", label: "Electronics & Upgrades" },
        { val: "general_consumption", label: "General Consumer Goods" },
      ]
    }
  };

  useEffect(() => {
    // Default to today
    setLogDate(new Date().toISOString().split("T")[0]);
  }, []);

  const loadLogs = async (dateStr: string) => {
    if (!dateStr) return;
    setLoading(true);
    try {
      const data = await api.logs.get(dateStr);
      setLogs(data);
    } catch (err) {
      console.error("Failed to load logs:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!authLoading) {
      if (!user) {
        router.push("/login");
      } else if (logDate) {
        loadLogs(logDate);
      }
    }
  }, [user, authLoading, logDate, router]);

  // Set default activity when tab changes
  useEffect(() => {
    setActivityType(activityOptions[activeTab].options[0].val);
    setQuantity(activeTab === "diet" ? 1 : 10);
  }, [activeTab]);

  const handleAddLog = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    try {
      await api.logs.create({
        log_date: logDate,
        category: activeTab,
        activity_type: activityType,
        quantity: quantity,
        metadata: {}
      });
      await loadLogs(logDate);
    } catch (err) {
      console.error("Failed to add log:", err);
      alert("Error adding log. Check that database seeds are running.");
    } finally {
      setSaving(false);
    }
  };

  if (authLoading || !user) {
    return (
      <div className="min-h-screen bg-brand-bg flex items-center justify-center">
        <Loader2 className="w-8 h-8 text-brand-primary animate-spin" />
      </div>
    );
  }

  const dailyTotalCo2e = logs.reduce((sum, log) => sum + (parseFloat(log.total_co2e) || 0), 0);

  return (
    <div className="min-h-screen bg-brand-bg flex flex-col">
      <Navbar />

      <main className="flex-grow max-w-5xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-3xl font-black text-white">Daily Footprint Logging</h1>
            <p className="text-sm text-gray-400 mt-1">Input your metrics to calculate actual daily emissions in kilograms.</p>
          </div>

          {/* Date Picker */}
          <div className="flex items-center gap-2 bg-brand-card p-2.5 rounded-xl border border-brand-border">
            <Calendar className="w-4 h-4 text-brand-primary" />
            <input
              type="date"
              value={logDate}
              onChange={(e) => setLogDate(e.target.value)}
              className="bg-transparent text-sm font-semibold text-white focus:outline-none border-none cursor-pointer"
            />
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* LOGGING INPUT FORM */}
          <div className="lg:col-span-2 glass-panel p-6 sm:p-8 rounded-3xl border border-brand-border space-y-6">
            {/* Tabs Row */}
            <div className="flex border-b border-brand-border/60 gap-1 pb-1 overflow-x-auto">
              {[
                { key: "transport", label: "Transport", icon: Car },
                { key: "diet", label: "Diet", icon: Utensils },
                { key: "housing", label: "Energy", icon: Home },
                { key: "consumption", label: "Consumption", icon: ShoppingBag }
              ].map((tab) => {
                const TabIcon = tab.icon;
                const isSelected = activeTab === tab.key;
                return (
                  <button
                    key={tab.key}
                    onClick={() => setActiveTab(tab.key)}
                    className={`flex items-center gap-2 px-4 py-3 text-xs font-bold uppercase tracking-wider border-b-2 transition-all duration-300 cursor-pointer ${
                      isSelected
                        ? "border-brand-primary text-brand-primary"
                        : "border-transparent text-gray-400 hover:text-gray-200"
                    }`}
                  >
                    <TabIcon className="w-4 h-4" />
                    {tab.label}
                  </button>
                );
              })}
            </div>

            <form onSubmit={handleAddLog} className="space-y-6">
              <div>
                <label className="block text-xs font-bold uppercase tracking-wider text-gray-400 mb-2">
                  Activity Subtype
                </label>
                <select
                  value={activityType}
                  onChange={(e) => setActivityType(e.target.value)}
                  className="w-full py-3 px-4 rounded-xl bg-brand-bg border border-brand-border text-white focus:outline-none focus:border-brand-primary transition-all duration-300"
                >
                  {activityOptions[activeTab].options.map((opt) => (
                    <option key={opt.val} value={opt.val} className="bg-brand-card">
                      {opt.label}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-bold uppercase tracking-wider text-gray-400 mb-2">
                  Quantity ({activityOptions[activeTab].unit})
                </label>
                <input
                  type="number"
                  min="0.1"
                  step="any"
                  required
                  value={quantity}
                  onChange={(e) => setQuantity(parseFloat(e.target.value) || 0)}
                  className="w-full py-3 px-4 rounded-xl bg-brand-bg border border-brand-border text-white focus:outline-none focus:border-brand-primary transition-all duration-300"
                />
              </div>

              <button
                type="submit"
                disabled={saving}
                className="w-full flex items-center justify-center gap-2 py-3.5 px-6 rounded-xl bg-gradient-to-r from-brand-primary to-brand-secondary text-brand-bg font-extrabold hover:brightness-110 shadow-lg shadow-brand-primary/20 cursor-pointer disabled:opacity-50"
              >
                {saving ? (
                  <>
                    <Loader2 className="w-5 h-5 animate-spin" />
                    Recording Log Entry...
                  </>
                ) : (
                  <>
                    <Plus className="w-5 h-5" />
                    Submit Log Entry
                  </>
                )}
              </button>
            </form>
          </div>

          {/* TODAY'S EMISSIONS SUMMARY */}
          <div className="space-y-6">
            <div className="glass-panel p-6 sm:p-8 rounded-3xl border border-brand-border text-center">
              <span className="text-xs font-bold text-gray-500 uppercase tracking-wider">Total CO₂e for this date</span>
              <div className="flex items-baseline justify-center gap-2 mt-2">
                <span className="text-5xl font-black text-white">{dailyTotalCo2e.toFixed(2)}</span>
                <span className="text-sm font-semibold text-gray-400">kg</span>
              </div>
              <p className="text-xs text-gray-400 mt-4 leading-relaxed">
                Equivalent to avoiding driving <span className="font-bold text-brand-secondary">{(dailyTotalCo2e * 2.5).toFixed(1)} miles</span> in a conventional gasoline vehicle.
              </p>
            </div>

            <div className="glass-panel p-6 sm:p-8 rounded-3xl border border-brand-border space-y-4">
              <span className="text-xs font-bold text-gray-300 uppercase tracking-wider block">Submitted Entries</span>
              
              {loading ? (
                <div className="flex justify-center py-6">
                  <Loader2 className="w-6 h-6 text-brand-primary animate-spin" />
                </div>
              ) : logs.length > 0 ? (
                <div className="space-y-3 max-h-72 overflow-y-auto pr-1">
                  {logs.map((log) => (
                    <div key={log.id} className="p-3 rounded-xl bg-brand-bg/60 border border-brand-border flex justify-between items-center text-xs">
                      <div>
                        <span className="font-bold text-gray-200 capitalize block">
                          {log.activity_type.replace(/_/g, " ")}
                        </span>
                        <span className="text-gray-500">Qty: {log.quantity}</span>
                      </div>
                      <div className="text-right">
                        <span className="font-black text-brand-primary block">{log.total_co2e} kg</span>
                        <span className="text-[10px] text-gray-500">CO₂e</span>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-6">
                  <AlertCircle className="w-6 h-6 text-gray-500 mx-auto mb-2" />
                  <p className="text-[11px] text-gray-500">No logs exist for this date.</p>
                </div>
              )}
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
