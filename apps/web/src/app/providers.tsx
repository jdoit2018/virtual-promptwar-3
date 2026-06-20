"use client";

import React, { useEffect } from "react";
import { AuthProvider } from "../context/AuthContext";
import { useRouter } from "next/navigation";

export function Providers({ children }: { children: React.ReactNode }) {
  const router = useRouter();

  useEffect(() => {
    const handleUnauthorized = () => {
      router.push("/login");
    };

    window.addEventListener("unauthorized-event", handleUnauthorized);
    return () => {
      window.removeEventListener("unauthorized-event", handleUnauthorized);
    };
  }, [router]);

  return <AuthProvider>{children}</AuthProvider>;
}
