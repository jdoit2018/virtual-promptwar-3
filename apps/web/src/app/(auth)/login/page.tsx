"use client";

import React, { useState, useEffect } from "react";
import { useAuth } from "../../../context/AuthContext";
import { useRouter } from "next/navigation";
import { Leaf, Lock, Mail, User, Info, ArrowRight } from "lucide-react";

export default function LoginPage() {
  const { user, loginWithEmail, signUpWithEmail, loginWithGoogle, isMock } = useAuth();
  const router = useRouter();

  const [isRegister, setIsRegister] = useState(false);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (user) {
      router.push("/dashboard");
    }
  }, [user, router]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      if (isRegister) {
        if (!name.trim()) throw new Error("Full name is required");
        await signUpWithEmail(email, password, name);
      } else {
        await loginWithEmail(email, password);
      }
      router.push("/dashboard");
    } catch (err: any) {
      setError(err.message || "Authentication failed. Please check your credentials.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-brand-bg flex flex-col justify-center py-12 sm:px-6 lg:px-8 relative overflow-hidden">
      {/* Dynamic Glowing backgrounds */}
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-brand-primary/10 rounded-full blur-3xl -z-10 animate-float"></div>
      <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-brand-secondary/10 rounded-full blur-3xl -z-10 animate-float" style={{ animationDelay: "2s" }}></div>

      <div className="sm:mx-auto sm:w-full sm:max-w-md text-center">
        <div className="inline-flex bg-gradient-to-tr from-brand-primary to-brand-secondary p-3 rounded-2xl text-brand-bg shadow-xl mb-4">
          <Leaf className="w-8 h-8" />
        </div>
        <h2 className="text-3xl font-extrabold tracking-tight text-white bg-gradient-to-r from-brand-primary via-brand-secondary to-brand-accent bg-clip-text text-transparent">
          Welcome to AuraCarbon
        </h2>
        <p className="mt-2 text-sm text-gray-400">
          Empowering you to calculate, track, and reduce daily carbon emissions.
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md px-4">
        <div className="glass-panel py-8 px-6 sm:px-10 rounded-3xl shadow-2xl border border-brand-border">
          {isMock && (
            <div className="mb-6 p-4 rounded-xl bg-blue-500/10 border border-blue-500/25 flex items-start gap-3">
              <Info className="w-5 h-5 text-blue-400 shrink-0 mt-0.5" />
              <div className="text-xs text-blue-300">
                <span className="font-bold">Mock Mode Active:</span> Client-side mock auth fallback is active. Enter any email/password to sign in instantly.
              </div>
            </div>
          )}

          {error && (
            <div className="mb-6 p-4 rounded-xl bg-red-500/10 border border-red-500/25 text-sm text-red-400">
              {error}
            </div>
          )}

          <form className="space-y-5" onSubmit={handleSubmit}>
            {isRegister && (
              <div>
                <label className="block text-xs font-bold uppercase tracking-wider text-gray-400 mb-2">
                  Full Name
                </label>
                <div className="relative">
                  <span className="absolute inset-y-0 left-0 pl-3 flex items-center text-gray-500">
                    <User className="w-5 h-5" />
                  </span>
                  <input
                    type="text"
                    required
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    placeholder="Jane Doe"
                    className="w-full pl-10 pr-4 py-3 rounded-xl bg-brand-bg/50 border border-brand-border text-white placeholder-gray-500 focus:outline-none focus:border-brand-primary transition-all duration-300"
                  />
                </div>
              </div>
            )}

            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-gray-400 mb-2">
                Email Address
              </label>
              <div className="relative">
                <span className="absolute inset-y-0 left-0 pl-3 flex items-center text-gray-500">
                  <Mail className="w-5 h-5" />
                </span>
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="jane.doe@example.com"
                  className="w-full pl-10 pr-4 py-3 rounded-xl bg-brand-bg/50 border border-brand-border text-white placeholder-gray-500 focus:outline-none focus:border-brand-primary transition-all duration-300"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-gray-400 mb-2">
                Password
              </label>
              <div className="relative">
                <span className="absolute inset-y-0 left-0 pl-3 flex items-center text-gray-500">
                  <Lock className="w-5 h-5" />
                </span>
                <input
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="w-full pl-10 pr-4 py-3 rounded-xl bg-brand-bg/50 border border-brand-border text-white placeholder-gray-500 focus:outline-none focus:border-brand-primary transition-all duration-300"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full flex items-center justify-center gap-2 py-3 px-4 rounded-xl bg-gradient-to-r from-brand-primary to-brand-secondary text-brand-bg font-extrabold transition-all duration-300 hover:brightness-110 shadow-lg shadow-brand-primary/20 cursor-pointer disabled:opacity-50"
            >
              {loading ? "Authenticating..." : isRegister ? "Create Account" : "Sign In"}
              <ArrowRight className="w-4 h-4" />
            </button>
          </form>

          <div className="mt-6 flex flex-col gap-4">
            <div className="relative flex py-2 items-center">
              <div className="flex-grow border-t border-brand-border"></div>
              <span className="flex-shrink mx-4 text-gray-500 text-xs uppercase tracking-wider">Or continue with</span>
              <div className="flex-grow border-t border-brand-border"></div>
            </div>

            <button
              onClick={loginWithGoogle}
              className="w-full py-3 px-4 rounded-xl bg-brand-bg hover:bg-brand-border/40 border border-brand-border text-gray-200 text-sm font-semibold transition-all duration-300 flex items-center justify-center gap-3 cursor-pointer"
            >
              {/* Google Icon SVG */}
              <svg className="w-5 h-5" viewBox="0 0 24 24">
                <path
                  fill="#EA4335"
                  d="M12 5.04c1.62 0 3.08.56 4.22 1.64l3.15-3.15C17.45 1.84 14.97 1 12 1 7.24 1 3.2 3.74 1.25 7.75l3.83 2.97C6.01 7.69 8.78 5.04 12 5.04z"
                />
                <path
                  fill="#4285F4"
                  d="M23.49 12.27c0-.81-.07-1.59-.2-2.35H12v4.51h6.44c-.28 1.47-1.11 2.71-2.36 3.55l3.66 2.84c2.14-1.97 3.39-4.88 3.39-8.55z"
                />
                <path
                  fill="#FBBC05"
                  d="M5.08 14.78c-.24-.75-.38-1.55-.38-2.38s.14-1.63.38-2.38L1.25 7.05C.45 8.65 0 10.45 0 12.35s.45 3.7 1.25 5.3l3.83-2.97c-.24-.65-.38-1.4-.38-2.15z"
                />
                <path
                  fill="#34A853"
                  d="M12 23c3.24 0 5.97-1.07 7.96-2.91l-3.66-2.84c-1.01.68-2.31 1.09-3.9 1.09-3.22 0-5.99-2.65-6.92-5.68l-3.83 2.97C3.2 19.61 7.24 23 12 23z"
                />
              </svg>
              Google
            </button>
          </div>

          <div className="mt-8 text-center text-sm text-gray-400">
            {isRegister ? "Already have an account?" : "New to AuraCarbon?"}{" "}
            <button
              onClick={() => setIsRegister(!isRegister)}
              className="text-brand-primary font-bold hover:underline"
            >
              {isRegister ? "Sign In" : "Register Now"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
