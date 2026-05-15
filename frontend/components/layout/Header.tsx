"use client";
import { usePathname } from "next/navigation";
import { Sun, Moon, Bell, Search } from "lucide-react";
import { useTheme } from "next-themes";
import { useAuthStore } from "@/lib/store/auth";

const PAGE_TITLES: Record<string, string> = {
  "/chat": "AI Chat",
  "/documents": "Knowledge Base",
  "/analytics": "Analytics",
  "/admin": "Admin Panel",
  "/workspaces": "Workspaces",
};

export function Header() {
  const pathname = usePathname();
  const { resolvedTheme, setTheme } = useTheme();
  const { user } = useAuthStore();

  const title = PAGE_TITLES[pathname] || "Dashboard";

  return (
    <header className="h-14 border-b border-border bg-card/50 backdrop-blur-sm flex items-center px-6 gap-4">
      <h1 className="font-semibold">{title}</h1>

      <div className="flex-1" />

      {/* Theme toggle */}
      <button
        onClick={() => setTheme(resolvedTheme === "dark" ? "light" : "dark")}
        className="p-2 rounded-lg hover:bg-accent transition-colors text-muted-foreground"
      >
        {resolvedTheme === "dark" ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
      </button>

      {/* Notifications */}
      <button className="p-2 rounded-lg hover:bg-accent transition-colors text-muted-foreground relative">
        <Bell className="w-4 h-4" />
        <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-primary" />
      </button>

      {/* User avatar */}
      <div className="w-8 h-8 rounded-full gradient-brand flex items-center justify-center text-white text-sm font-semibold">
        {user?.full_name?.[0]?.toUpperCase()}
      </div>
    </header>
  );
}
