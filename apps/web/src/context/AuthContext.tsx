"use client";

import React, { createContext, useContext, useEffect, useState } from "react";
import { auth, isFirebaseConfigured } from "../lib/firebase/config";
import {
  signInWithEmailAndPassword,
  createUserWithEmailAndPassword,
  signInWithPopup,
  GoogleAuthProvider,
  signOut as fbSignOut,
  onAuthStateChanged,
  updateProfile,
} from "firebase/auth";

export interface UserProfile {
  uid: string;
  email: string | null;
  displayName: string | null;
  token: string | null;
}

interface AuthContextType {
  user: UserProfile | null;
  loading: boolean;
  isMock: boolean;
  loginWithEmail: (email: string, pass: string) => Promise<void>;
  signUpWithEmail: (email: string, pass: string, name: string) => Promise<void>;
  loginWithGoogle: () => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(true);

  // Sync token to API calls or sync state
  const syncUserSession = async (profile: UserProfile | null) => {
    if (!profile) {
      setUser(null);
      if (typeof window !== "undefined") {
        localStorage.removeItem("auth_token");
        localStorage.removeItem("user_profile");
      }
      return;
    }

    setUser(profile);
    if (typeof window !== "undefined" && profile.token) {
      localStorage.setItem("auth_token", profile.token);
      localStorage.setItem("user_profile", JSON.stringify(profile));
    }

    // Call backend sync endpoint
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const res = await fetch(`${apiUrl}/api/auth/sync`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${profile.token}`,
        },
      });
      if (!res.ok) {
        console.error("Backend identity sync failed", await res.text());
      }
    } catch (e) {
      console.error("Failed to connect to backend api during sync", e);
    }
  };

  useEffect(() => {
    if (!isFirebaseConfigured) {
      // Run in Mock Auth Mode
      if (typeof window !== "undefined") {
        const storedProfile = localStorage.getItem("user_profile");
        if (storedProfile) {
          try {
            setUser(JSON.parse(storedProfile));
          } catch (e) {
            localStorage.removeItem("user_profile");
          }
        }
      }
      setLoading(false);
      return;
    }

    const unsubscribe = onAuthStateChanged(auth, async (fbUser) => {
      setLoading(true);
      if (fbUser) {
        const token = await fbUser.getIdToken();
        const profile: UserProfile = {
          uid: fbUser.uid,
          email: fbUser.email,
          displayName: fbUser.displayName || "Firebase User",
          token,
        };
        await syncUserSession(profile);
      } else {
        await syncUserSession(null);
      }
      setLoading(false);
    });

    return () => unsubscribe();
  }, []);

  const loginWithEmail = async (email: string, pass: string) => {
    setLoading(true);
    try {
      if (isFirebaseConfigured) {
        const credential = await signInWithEmailAndPassword(auth, email, pass);
        const token = await credential.user.getIdToken();
        await syncUserSession({
          uid: credential.user.uid,
          email: credential.user.email,
          displayName: credential.user.displayName || "Firebase User",
          token,
        });
      } else {
        // Mock Auth Sign-in
        const mockProfile: UserProfile = {
          uid: "mock-user-uid",
          email: email,
          displayName: email.split("@")[0].toUpperCase() || "Mock User",
          token: "mock-token",
        };
        await syncUserSession(mockProfile);
      }
    } finally {
      setLoading(false);
    }
  };

  const signUpWithEmail = async (email: string, pass: string, name: string) => {
    setLoading(true);
    try {
      if (isFirebaseConfigured) {
        const credential = await createUserWithEmailAndPassword(auth, email, pass);
        await updateProfile(credential.user, { displayName: name });
        const token = await credential.user.getIdToken();
        await syncUserSession({
          uid: credential.user.uid,
          email: credential.user.email,
          displayName: name,
          token,
        });
      } else {
        // Mock Auth Registration
        const mockProfile: UserProfile = {
          uid: "mock-user-uid",
          email: email,
          displayName: name,
          token: "mock-token",
        };
        await syncUserSession(mockProfile);
      }
    } finally {
      setLoading(false);
    }
  };

  const loginWithGoogle = async () => {
    setLoading(true);
    try {
      if (isFirebaseConfigured) {
        const provider = new GoogleAuthProvider();
        const credential = await signInWithPopup(auth, provider);
        const token = await credential.user.getIdToken();
        await syncUserSession({
          uid: credential.user.uid,
          email: credential.user.email,
          displayName: credential.user.displayName || "Google User",
          token,
        });
      } else {
        // Mock Google sign-in
        const mockProfile: UserProfile = {
          uid: "mock-user-uid",
          email: "mock-user@example.com",
          displayName: "Mock User",
          token: "mock-token",
        };
        await syncUserSession(mockProfile);
      }
    } finally {
      setLoading(false);
    }
  };

  const logout = async () => {
    setLoading(true);
    try {
      if (isFirebaseConfigured) {
        await fbSignOut(auth);
      }
      await syncUserSession(null);
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        isMock: !isFirebaseConfigured,
        loginWithEmail,
        signUpWithEmail,
        loginWithGoogle,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};
