"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "../context/AuthContext";
import { Leaf } from "lucide-react";

export default function Home() {
  const { user, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading) {
      if (user) {
        router.push("/dashboard");
      } else {
        router.push("/login");
      }
    }
  }, [user, loading, router]);

  return (
    <div className="min-h-screen bg-brand-bg flex items-center justify-center">
      <div className="text-center flex flex-col items-center gap-4">
        <div className="bg-gradient-to-tr from-brand-primary to-brand-secondary p-4 rounded-3xl text-brand-bg shadow-xl animate-bounce">
          <Leaf className="w-10 h-10" />
        </div>
        <div className="text-gray-400 text-sm font-semibold tracking-wider uppercase animate-pulse">
          Loading AuraCarbon...
        </div>
      </div>
    </div>
  );
}
