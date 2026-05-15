"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { motion } from "framer-motion";
import {
  MessageSquare, FileText, BarChart2, Settings, Shield,
  Bot, Plus, ChevronRight, FolderOpen, LogOut
} from "lucide-react";
import { useAuthStore } from "@/lib/store/auth";
import { useWorkspaceStore } from "@/lib/store/workspace";
import { useChatStore } from "@/lib/store/chat";
import { cn } from "@/lib/utils";

const NAV_ITEMS = [
  { href: "/chat", icon: MessageSquare, label: "Chat" },
  { href: "/documents", icon: FileText, label: "Documents" },
  { href: "/analytics", icon: BarChart2, label: "Analytics" },
  { href: "/workspaces", icon: FolderOpen, label: "Workspaces" },
  { href: "/admin", icon: Shield, label: "Admin", adminOnly: true },
];

export function Sidebar() {
  const pathname = usePathname();
  const { user, logout } = useAuthStore();
  const { currentWorkspace, workspaces } = useWorkspaceStore();
  const { createSession, setCurrentSession } = useChatStore();

  const isAdmin = user?.role === "admin" || user?.role === "superadmin";

  const handleNewChat = async () => {
    if (!currentWorkspace) return;
    const session = await createSession(currentWorkspace.id, "New Chat");
    if (session) setCurrentSession(session);
  };

  return (
    <motion.aside
      initial={{ x: -20, opacity: 0 }}
      animate={{ x: 0, opacity: 1 }}
      className="w-64 h-full border-r border-border bg-card flex flex-col"
    >
      {/* Logo */}
      <div className="p-4 border-b border-border">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-xl gradient-brand flex items-center justify-center">
            <Bot className="w-4 h-4 text-white" />
          </div>
          <div className="flex-1 min-w-0">
            <p className="font-bold text-sm truncate">Enterprise RAG</p>
            <p className="text-xs text-muted-foreground truncate">{currentWorkspace?.name || "Select workspace"}</p>
          </div>
        </div>
      </div>

      {/* New Chat Button */}
      <div className="p-3">
        <button
          onClick={handleNewChat}
          className="w-full flex items-center gap-2 px-4 py-2.5 rounded-xl gradient-brand text-white text-sm font-medium hover:opacity-90 transition-opacity"
        >
          <Plus className="w-4 h-4" />
          New Chat
        </button>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-2 space-y-1">
        {NAV_ITEMS.filter((item) => !item.adminOnly || isAdmin).map((item) => {
          const isActive = pathname.startsWith(item.href);
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm transition-all",
                isActive
                  ? "bg-primary text-primary-foreground font-medium"
                  : "text-muted-foreground hover:text-foreground hover:bg-accent"
              )}
            >
              <item.icon className="w-4 h-4 flex-shrink-0" />
              {item.label}
              {isActive && <ChevronRight className="w-3 h-3 ml-auto" />}
            </Link>
          );
        })}
      </nav>

      {/* Workspace Selector */}
      {workspaces.length > 0 && (
        <div className="p-3 border-t border-border">
          <p className="text-xs text-muted-foreground px-2 mb-2 font-medium uppercase tracking-wide">Workspace</p>
          <div className="space-y-1">
            {workspaces.slice(0, 3).map((ws) => (
              <button
                key={ws.id}
                onClick={() => useWorkspaceStore.getState().setCurrentWorkspace(ws)}
                className={cn(
                  "w-full flex items-center gap-2 px-3 py-2 rounded-lg text-sm transition-all text-left",
                  currentWorkspace?.id === ws.id
                    ? "bg-primary/10 text-primary font-medium"
                    : "text-muted-foreground hover:text-foreground hover:bg-accent"
                )}
              >
                <div className="w-6 h-6 rounded-md gradient-brand flex items-center justify-center text-white text-xs font-bold">
                  {ws.name[0].toUpperCase()}
                </div>
                <span className="truncate">{ws.name}</span>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* User Footer */}
      <div className="p-3 border-t border-border">
        <div className="flex items-center gap-3 px-2 py-2">
          <div className="w-8 h-8 rounded-full gradient-brand flex items-center justify-center text-white text-sm font-semibold">
            {user?.full_name?.[0]?.toUpperCase()}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium truncate">{user?.full_name}</p>
            <p className="text-xs text-muted-foreground truncate">{user?.role}</p>
          </div>
          <button
            onClick={logout}
            className="p-1.5 rounded-lg text-muted-foreground hover:text-foreground hover:bg-accent"
          >
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      </div>
    </motion.aside>
  );
}
