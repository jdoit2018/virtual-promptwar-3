"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "../context/AuthContext";
import { Leaf, Flame, Calendar, Award, Target, LogOut, User as UserIcon } from "lucide-react";
import { api } from "../lib/api/client";

export default function Navbar() {
  const pathname = usePathname();
  const { user, logout } = useAuth();
  const [streak, setStreak] = useState(0);

  useEffect(() => {
    if (user) {
      api.users.me()
        .then((profile) => {
          if (profile && profile.current_streak !== undefined) {
            setStreak(profile.current_streak);
          }
        })
        .catch((err) => console.error("Error fetching user profile for navbar:", err));
    }
  }, [user, pathname]);

  const navItems = [
    { name: "Dashboard", href: "/dashboard", icon: Leaf },
    { name: "Daily Log", href: "/log", icon: Calendar },
    { name: "Goals", href: "/goals", icon: Target },
    { name: "Eco-Challenges", href: "/insights", icon: Award },
  ];

  if (!user) return null;

  return (
    <nav className="glass-panel sticky top-0 z-50 px-6 py-4 flex items-center justify-between border-b border-brand-border shadow-lg">
      <div className="flex items-center gap-3">
        <div className="bg-gradient-to-tr from-brand-primary to-brand-secondary p-2 rounded-xl text-brand-bg shadow-md">
          <Leaf className="w-6 h-6 animate-pulse-slow" />
        </div>
        <span className="font-extrabold text-xl tracking-tight bg-gradient-to-r from-brand-primary via-brand-secondary to-brand-accent bg-clip-text text-transparent">
          AuraCarbon
        </span>
      </div>

      <div className="hidden md:flex items-center gap-1">
        {navItems.map((item) => {
          const isActive = pathname === item.href;
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-semibold transition-all duration-300 ${
                isActive
                  ? "bg-brand-primary/10 text-brand-primary border border-brand-primary/20 shadow-sm"
                  : "text-gray-400 hover:text-gray-100 hover:bg-brand-border/40 border border-transparent"
              }`}
            >
              <Icon className="w-4 h-4" />
              {item.name}
            </Link>
          );
        })}
      </div>

      <div className="flex items-center gap-4">
        {/* Streak Flame Badge */}
        <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-orange-500/10 border border-orange-500/25 text-orange-400 text-sm font-bold shadow-inner">
          <Flame className="w-4 h-4 fill-orange-400 animate-pulse" />
          <span>{streak} day{streak !== 1 && "s"}</span>
        </div>

        {/* User profile dropdown & logout */}
        <div className="flex items-center gap-3 pl-3 border-l border-brand-border">
          <div className="hidden lg:flex flex-col text-right">
            <span className="text-sm font-bold text-gray-200">{user.displayName || "User"}</span>
            <span className="text-xs text-gray-500 truncate max-w-[150px]">{user.email}</span>
          </div>
          <div className="w-8 h-8 rounded-full bg-brand-accent/20 border border-brand-accent/35 flex items-center justify-center text-brand-accent">
            <UserIcon className="w-4 h-4" />
          </div>
          <button
            onClick={logout}
            className="p-2 rounded-lg text-gray-400 hover:text-red-400 hover:bg-red-500/10 transition-all duration-300 border border-transparent"
            title="Log Out"
          >
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      </div>
    </nav>
  );
}
