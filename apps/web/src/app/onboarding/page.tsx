"use client";

import React, { useState, useEffect } from "react";
import { useAuth } from "../../context/AuthContext";
import { useRouter } from "next/navigation";
import { api } from "../../lib/api/client";
import {
  Home as HomeIcon,
  Flame,
  Users,
  Car,
  Compass,
  Plane,
  Apple,
  ShoppingBag,
  Cpu,
  ArrowRight,
  ArrowLeft,
  CheckCircle,
  Loader2
} from "lucide-react";

interface QuizResponses {
  property_type: string;
  heating_type: string;
  household_size: number;
  transport_mode: string;
  weekly_mileage: string;
  flights_profile: string;
  diet_type: string;
  fashion_frequency: string;
  electronics_frequency: string;
}

export default function OnboardingPage() {
  const { user, loading: authLoading } = useAuth();
  const router = useRouter();

  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [answers, setAnswers] = useState<QuizResponses>({
    property_type: "detached",
    heating_type: "gas_oil",
    household_size: 2,
    transport_mode: "gas_car",
    weekly_mileage: "medium",
    flights_profile: "short_haul",
    diet_type: "vegetarian",
    fashion_frequency: "occasionally",
    electronics_frequency: "one"
  });

  useEffect(() => {
    if (!authLoading && !user) {
      router.push("/login");
    }
  }, [user, authLoading, router]);

  const updateAnswer = (key: keyof QuizResponses, value: any) => {
    setAnswers((prev) => ({ ...prev, [key]: value }));
  };

  const handleNext = () => {
    setStep((prev) => prev + 1);
  };

  const handleBack = () => {
    setStep((prev) => prev - 1);
  };

  const handleSubmit = async () => {
    setLoading(true);
    try {
      // Map frontend answers to backend QuizResponses schema
      const backendAnswers = {
        property_type: answers.property_type === "flat" ? "apartment" : 
                       (answers.property_type === "semi_detached" || answers.property_type === "terraced") ? "townhouse" : 
                       answers.property_type,
        
        heating_type: answers.heating_type === "electric" ? "electricity_heat_pump" :
                      answers.heating_type === "heat_pump" ? "electricity_heat_pump" :
                      answers.heating_type === "biomass" ? "renewables_solar" :
                      answers.heating_type,
                      
        household_size: answers.household_size,
        
        transport_mode: answers.transport_mode === "hybrid_ev" ? "ev" :
                        answers.transport_mode === "active" ? "pedestrian_bicycle" :
                        answers.transport_mode,
                        
        weekly_mileage: answers.weekly_mileage,
        
        flights_profile: answers.flights_profile,
        
        diet_type: answers.diet_type === "meat_heavy" ? "heavy_meat" :
                   answers.diet_type === "flexitarian" ? "omnivore" :
                   answers.diet_type,
                   
        fashion_frequency: (answers.fashion_frequency === "weekly" || answers.fashion_frequency === "monthly") ? "frequently" :
                           answers.fashion_frequency,
                           
        electronics_frequency: (answers.electronics_frequency === "high" || answers.electronics_frequency === "medium") ? "two_or_more" :
                               answers.electronics_frequency
      };

      await api.baselines.create(backendAnswers);
      router.push("/dashboard");
    } catch (error) {
      console.error("Failed to save onboarding baseline:", error);
      alert("Something went wrong saving your baseline. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  if (authLoading || !user) {
    return (
      <div className="min-h-screen bg-brand-bg flex items-center justify-center">
        <Loader2 className="w-8 h-8 text-brand-primary animate-spin" />
      </div>
    );
  }

  const renderProgress = () => {
    return (
      <div className="mb-10">
        <div className="flex justify-between items-center text-xs font-bold uppercase tracking-wider text-gray-400 mb-2">
          <span>Step {step} of 5</span>
          <span>{Math.round(((step - 1) / 4) * 100)}% Complete</span>
        </div>
        <div className="h-2 w-full bg-brand-border rounded-full overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-brand-primary to-brand-secondary transition-all duration-500 ease-out"
            style={{ width: `${((step - 1) / 4) * 100}%` }}
          ></div>
        </div>
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-brand-bg flex flex-col justify-center py-12 px-4 sm:px-6 lg:px-8 relative overflow-hidden">
      {/* Background glow animations */}
      <div className="absolute top-10 left-10 w-72 h-72 bg-brand-primary/10 rounded-full blur-3xl -z-10 animate-float"></div>
      <div className="absolute bottom-10 right-10 w-72 h-72 bg-brand-secondary/10 rounded-full blur-3xl -z-10 animate-float" style={{ animationDelay: "3s" }}></div>

      <div className="max-w-2xl w-full mx-auto glass-panel p-8 sm:p-12 rounded-3xl border border-brand-border shadow-2xl relative">
        {renderProgress()}

        {/* STEP 1: HOUSING PILLAR */}
        {step === 1 && (
          <div className="space-y-6">
            <div>
              <h2 className="text-2xl font-black text-white flex items-center gap-3">
                <HomeIcon className="text-brand-primary w-6 h-6" />
                Pillar 1: Housing & Home Energy
              </h2>
              <p className="text-sm text-gray-400 mt-1">Let's calculate your home energy emissions footprint.</p>
            </div>

            <div className="space-y-5">
              <div>
                <label className="block text-sm font-semibold text-gray-300 mb-3">Property Type</label>
                <div className="grid grid-cols-2 gap-3">
                  {[
                    { val: "detached", label: "Detached House" },
                    { val: "semi_detached", label: "Semi-Detached" },
                    { val: "terraced", label: "Terraced House" },
                    { val: "flat", label: "Flat / Apartment" }
                  ].map((p) => (
                    <button
                      key={p.val}
                      onClick={() => updateAnswer("property_type", p.val)}
                      className={`p-4 rounded-xl border text-sm font-semibold transition-all duration-300 cursor-pointer ${
                        answers.property_type === p.val
                          ? "border-brand-primary bg-brand-primary/10 text-white shadow-lg"
                          : "border-brand-border bg-brand-bg/40 text-gray-400 hover:text-gray-200"
                      }`}
                    >
                      {p.label}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="block text-sm font-semibold text-gray-300 mb-3">Home Heating Fuel</label>
                <div className="grid grid-cols-2 gap-3">
                  {[
                    { val: "gas_oil", label: "Natural Gas / Heating Oil" },
                    { val: "electric", label: "Standard Electric Heating" },
                    { val: "heat_pump", label: "Heat Pump (Eco)" },
                    { val: "biomass", label: "Biomass / Wood Pellets" }
                  ].map((h) => (
                    <button
                      key={h.val}
                      onClick={() => updateAnswer("heating_type", h.val)}
                      className={`p-4 rounded-xl border text-sm font-semibold transition-all duration-300 cursor-pointer ${
                        answers.heating_type === h.val
                          ? "border-brand-primary bg-brand-primary/10 text-white shadow-lg"
                          : "border-brand-border bg-brand-bg/40 text-gray-400 hover:text-gray-200"
                      }`}
                    >
                      {h.label}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="block text-sm font-semibold text-gray-300 mb-2">Household Size</label>
                <div className="flex items-center gap-3">
                  <Users className="w-5 h-5 text-gray-500" />
                  <input
                    type="number"
                    min="1"
                    max="20"
                    value={answers.household_size}
                    onChange={(e) => updateAnswer("household_size", Math.max(1, parseInt(e.target.value) || 1))}
                    className="w-24 py-2 px-3 rounded-lg bg-brand-bg border border-brand-border text-white text-center focus:outline-none focus:border-brand-primary"
                  />
                  <span className="text-sm text-gray-400">person(s) residing in the household</span>
                </div>
              </div>
            </div>

            <div className="pt-6 flex justify-end">
              <button
                onClick={handleNext}
                className="flex items-center gap-2 py-3 px-6 rounded-xl bg-gradient-to-r from-brand-primary to-brand-secondary text-brand-bg font-bold hover:brightness-110 shadow-lg cursor-pointer"
              >
                Next Step
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}

        {/* STEP 2: TRANSPORTATION PILLAR */}
        {step === 2 && (
          <div className="space-y-6">
            <div>
              <h2 className="text-2xl font-black text-white flex items-center gap-3">
                <Car className="text-brand-primary w-6 h-6" />
                Pillar 2: Mobility & Travel
              </h2>
              <p className="text-sm text-gray-400 mt-1">Let's estimate your transport emissions.</p>
            </div>

            <div className="space-y-5">
              <div>
                <label className="block text-sm font-semibold text-gray-300 mb-3">Primary Transport Mode</label>
                <div className="grid grid-cols-2 gap-3">
                  {[
                    { val: "gas_car", label: "Gas/Diesel Car" },
                    { val: "hybrid_ev", label: "EV / Hybrid Car" },
                    { val: "public_transit", label: "Train / Bus / Metro" },
                    { val: "active", label: "Walk / Bicycle / Active" }
                  ].map((t) => (
                    <button
                      key={t.val}
                      onClick={() => updateAnswer("transport_mode", t.val)}
                      className={`p-4 rounded-xl border text-sm font-semibold transition-all duration-300 cursor-pointer ${
                        answers.transport_mode === t.val
                          ? "border-brand-primary bg-brand-primary/10 text-white shadow-lg"
                          : "border-brand-border bg-brand-bg/40 text-gray-400 hover:text-gray-200"
                      }`}
                    >
                      {t.label}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="block text-sm font-semibold text-gray-300 mb-3">Weekly Commute Mileage</label>
                <div className="grid grid-cols-3 gap-3">
                  {[
                    { val: "low", label: "Low (<50 mi)" },
                    { val: "medium", label: "Medium (50-150 mi)" },
                    { val: "high", label: "High (>150 mi)" }
                  ].map((m) => (
                    <button
                      key={m.val}
                      onClick={() => updateAnswer("weekly_mileage", m.val)}
                      className={`p-3 rounded-xl border text-xs font-bold transition-all duration-300 cursor-pointer ${
                        answers.weekly_mileage === m.val
                          ? "border-brand-primary bg-brand-primary/10 text-white shadow-lg"
                          : "border-brand-border bg-brand-bg/40 text-gray-400 hover:text-gray-200"
                      }`}
                    >
                      {m.label}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="block text-sm font-semibold text-gray-300 mb-3">Annual Flights Profile</label>
                <div className="grid grid-cols-3 gap-3">
                  {[
                    { val: "none", label: "No Flights" },
                    { val: "short_haul", label: "Short (< 3 flights)" },
                    { val: "long_haul", label: "Frequent / Long" }
                  ].map((f) => (
                    <button
                      key={f.val}
                      onClick={() => updateAnswer("flights_profile", f.val)}
                      className={`p-3 rounded-xl border text-xs font-bold transition-all duration-300 cursor-pointer ${
                        answers.flights_profile === f.val
                          ? "border-brand-primary bg-brand-primary/10 text-white shadow-lg"
                          : "border-brand-border bg-brand-bg/40 text-gray-400 hover:text-gray-200"
                      }`}
                    >
                      {f.label}
                    </button>
                  ))}
                </div>
              </div>
            </div>

            <div className="pt-6 flex justify-between">
              <button
                onClick={handleBack}
                className="flex items-center gap-2 py-3 px-6 rounded-xl bg-brand-bg border border-brand-border text-gray-400 font-bold hover:text-gray-200 cursor-pointer"
              >
                <ArrowLeft className="w-4 h-4" />
                Back
              </button>
              <button
                onClick={handleNext}
                className="flex items-center gap-2 py-3 px-6 rounded-xl bg-gradient-to-r from-brand-primary to-brand-secondary text-brand-bg font-bold hover:brightness-110 shadow-lg cursor-pointer"
              >
                Next Step
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}

        {/* STEP 3: DIET PILLAR */}
        {step === 3 && (
          <div className="space-y-6">
            <div>
              <h2 className="text-2xl font-black text-white flex items-center gap-3">
                <Apple className="text-brand-primary w-6 h-6" />
                Pillar 3: Dietary Profile
              </h2>
              <p className="text-sm text-gray-400 mt-1">Food production accounts for up to 30% of global emissions.</p>
            </div>

            <div className="space-y-5">
              <label className="block text-sm font-semibold text-gray-300 mb-3">Which matches your primary diet?</label>
              <div className="grid grid-cols-1 gap-3">
                {[
                  { val: "vegan", label: "Vegan (Pure Plant-Based)", desc: "Lowest carbon intensity footprint" },
                  { val: "vegetarian", label: "Vegetarian (No Meat, includes dairy)", desc: "Moderate-low footprint profile" },
                  { val: "flexitarian", label: "Flexitarian (Mostly plants, occasional meat)", desc: "Moderate footprint profile" },
                  { val: "meat_heavy", label: "Standard Heavy Meat Consumer", desc: "Highest footprint intensity profile" }
                ].map((d) => (
                  <button
                    key={d.val}
                    onClick={() => updateAnswer("diet_type", d.val)}
                    className={`p-5 rounded-2xl border text-left transition-all duration-300 flex justify-between items-center cursor-pointer ${
                      answers.diet_type === d.val
                        ? "border-brand-primary bg-brand-primary/10 text-white shadow-lg"
                        : "border-brand-border bg-brand-bg/40 text-gray-400 hover:text-gray-200"
                    }`}
                  >
                    <div>
                      <div className="font-extrabold text-sm text-white">{d.label}</div>
                      <div className="text-xs text-gray-400 mt-1">{d.desc}</div>
                    </div>
                    {answers.diet_type === d.val && <CheckCircle className="w-5 h-5 text-brand-primary shrink-0" />}
                  </button>
                ))}
              </div>
            </div>

            <div className="pt-6 flex justify-between">
              <button
                onClick={handleBack}
                className="flex items-center gap-2 py-3 px-6 rounded-xl bg-brand-bg border border-brand-border text-gray-400 font-bold hover:text-gray-200 cursor-pointer"
              >
                <ArrowLeft className="w-4 h-4" />
                Back
              </button>
              <button
                onClick={handleNext}
                className="flex items-center gap-2 py-3 px-6 rounded-xl bg-gradient-to-r from-brand-primary to-brand-secondary text-brand-bg font-bold hover:brightness-110 shadow-lg cursor-pointer"
              >
                Next Step
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}

        {/* STEP 4: CONSUMPTION PILLAR */}
        {step === 4 && (
          <div className="space-y-6">
            <div>
              <h2 className="text-2xl font-black text-white flex items-center gap-3">
                <ShoppingBag className="text-brand-primary w-6 h-6" />
                Pillar 4: Consumption & Purchases
              </h2>
              <p className="text-sm text-gray-400 mt-1">Manufacturing consumer goods releases high industrial emissions.</p>
            </div>

            <div className="space-y-5">
              <div>
                <label className="block text-sm font-semibold text-gray-300 mb-3">Fashion Shopping Frequency</label>
                <div className="grid grid-cols-2 gap-3">
                  {[
                    { val: "weekly", label: "Weekly (Trend collector)" },
                    { val: "monthly", label: "Monthly (Regular buyer)" },
                    { val: "occasionally", label: "Occasionally (Need-based)" },
                    { val: "rarely", label: "Rarely (Eco-conscious)" }
                  ].map((fa) => (
                    <button
                      key={fa.val}
                      onClick={() => updateAnswer("fashion_frequency", fa.val)}
                      className={`p-4 rounded-xl border text-sm font-semibold transition-all duration-300 cursor-pointer ${
                        answers.fashion_frequency === fa.val
                          ? "border-brand-primary bg-brand-primary/10 text-white shadow-lg"
                          : "border-brand-border bg-brand-bg/40 text-gray-400 hover:text-gray-200"
                      }`}
                    >
                      {fa.label}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="block text-sm font-semibold text-gray-300 mb-3">New Electronics / Gadgets Purchased (Annual)</label>
                <div className="grid grid-cols-2 gap-3">
                  {[
                    { val: "high", label: "Frequent Upgrader (3+ items)" },
                    { val: "medium", label: "Regular Buyer (1-2 items)" },
                    { val: "one", label: "Essential Only (1 item)" },
                    { val: "none", label: "Minimal (No upgrades)" }
                  ].map((e) => (
                    <button
                      key={e.val}
                      onClick={() => updateAnswer("electronics_frequency", e.val)}
                      className={`p-4 rounded-xl border text-sm font-semibold transition-all duration-300 cursor-pointer ${
                        answers.electronics_frequency === e.val
                          ? "border-brand-primary bg-brand-primary/10 text-white shadow-lg"
                          : "border-brand-border bg-brand-bg/40 text-gray-400 hover:text-gray-200"
                      }`}
                    >
                      {e.label}
                    </button>
                  ))}
                </div>
              </div>
            </div>

            <div className="pt-6 flex justify-between">
              <button
                onClick={handleBack}
                className="flex items-center gap-2 py-3 px-6 rounded-xl bg-brand-bg border border-brand-border text-gray-400 font-bold hover:text-gray-200 cursor-pointer"
              >
                <ArrowLeft className="w-4 h-4" />
                Back
              </button>
              <button
                onClick={handleNext}
                className="flex items-center gap-2 py-3 px-6 rounded-xl bg-gradient-to-r from-brand-primary to-brand-secondary text-brand-bg font-bold hover:brightness-110 shadow-lg cursor-pointer"
              >
                Preview Summary
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}

        {/* STEP 5: PREVIEW & CALCULATION */}
        {step === 5 && (
          <div className="space-y-6">
            <div>
              <h2 className="text-2xl font-black text-white flex items-center gap-3">
                <CheckCircle className="text-brand-primary w-6 h-6 animate-bounce" />
                Ready to Calculate Baseline
              </h2>
              <p className="text-sm text-gray-400 mt-1">Review your selections below. We will compute your carbon footprint in metric tonnes.</p>
            </div>

            <div className="space-y-4 rounded-2xl bg-brand-bg/60 p-6 border border-brand-border text-sm">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <span className="text-gray-500 font-bold block uppercase tracking-wider text-[10px]">Property Type</span>
                  <span className="text-gray-200 font-semibold">{answers.property_type.replace("_", " ")}</span>
                </div>
                <div>
                  <span className="text-gray-500 font-bold block uppercase tracking-wider text-[10px]">Home Heating</span>
                  <span className="text-gray-200 font-semibold">{answers.heating_type.replace("_", " ")}</span>
                </div>
                <div>
                  <span className="text-gray-500 font-bold block uppercase tracking-wider text-[10px]">Transport Mode</span>
                  <span className="text-gray-200 font-semibold">{answers.transport_mode.replace("_", " ")}</span>
                </div>
                <div>
                  <span className="text-gray-500 font-bold block uppercase tracking-wider text-[10px]">Weekly Travel</span>
                  <span className="text-gray-200 font-semibold">{answers.weekly_mileage}</span>
                </div>
                <div>
                  <span className="text-gray-500 font-bold block uppercase tracking-wider text-[10px]">Diet Profile</span>
                  <span className="text-gray-200 font-semibold">{answers.diet_type}</span>
                </div>
                <div>
                  <span className="text-gray-500 font-bold block uppercase tracking-wider text-[10px]">Fashion Purchases</span>
                  <span className="text-gray-200 font-semibold">{answers.fashion_frequency}</span>
                </div>
              </div>
            </div>

            <div className="pt-6 flex justify-between">
              <button
                onClick={handleBack}
                disabled={loading}
                className="flex items-center gap-2 py-3 px-6 rounded-xl bg-brand-bg border border-brand-border text-gray-400 font-bold hover:text-gray-200 cursor-pointer disabled:opacity-50"
              >
                <ArrowLeft className="w-4 h-4" />
                Back
              </button>
              <button
                onClick={handleSubmit}
                disabled={loading}
                className="flex items-center justify-center gap-2 py-3 px-8 rounded-xl bg-gradient-to-r from-brand-primary to-brand-secondary text-brand-bg font-extrabold hover:brightness-110 shadow-lg cursor-pointer disabled:opacity-50"
              >
                {loading ? (
                  <>
                    <Loader2 className="w-5 h-5 animate-spin" />
                    Calculating Footprint...
                  </>
                ) : (
                  <>
                    Generate Footprint Report
                    <ArrowRight className="w-4 h-4" />
                  </>
                )}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
