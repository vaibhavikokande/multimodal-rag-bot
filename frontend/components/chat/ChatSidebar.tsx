"use client";
import { useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { MessageSquare, Plus, Trash2, Loader2 } from "lucide-react";
import { useChatStore } from "@/lib/store/chat";
import { useWorkspaceStore } from "@/lib/store/workspace";
import { formatDate, cn } from "@/lib/utils";

export function ChatSidebar() {
  const { sessions, currentSession, fetchSessions, createSession, setCurrentSession, deleteSession, isLoading } = useChatStore();
  const { currentWorkspace } = useWorkspaceStore();

  useEffect(() => {
    if (currentWorkspace) {
      fetchSessions(currentWorkspace.id);
    }
  }, [currentWorkspace?.id]);

  const handleNew = async () => {
    if (!currentWorkspace) return;
    const session = await createSession(currentWorkspace.id, "New Chat");
    if (session) setCurrentSession(session);
  };

  return (
    <div className="w-60 flex flex-col border-r border-border bg-card/30">
      <div className="p-3 border-b border-border">
        <button
          onClick={handleNew}
          className="w-full flex items-center gap-2 px-3 py-2 rounded-xl text-sm border border-dashed border-border hover:border-primary/50 hover:bg-accent/50 transition-all text-muted-foreground hover:text-foreground"
        >
          <Plus className="w-4 h-4" />
          New conversation
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-2">
        {isLoading ? (
          <div className="flex justify-center py-8">
            <Loader2 className="w-5 h-5 animate-spin text-muted-foreground" />
          </div>
        ) : sessions.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground">
            <MessageSquare className="w-8 h-8 mx-auto mb-2 opacity-30" />
            <p className="text-sm">No conversations yet</p>
          </div>
        ) : (
          <AnimatePresence>
            {sessions.map((session, i) => (
              <motion.button
                key={session.id}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.03 }}
                onClick={() => setCurrentSession(session)}
                className={cn(
                  "w-full text-left px-3 py-2.5 rounded-xl text-sm transition-all group relative mb-1",
                  currentSession?.id === session.id
                    ? "bg-primary/10 text-primary"
                    : "hover:bg-accent/50 text-muted-foreground hover:text-foreground"
                )}
              >
                <p className="font-medium truncate pr-6">{session.title}</p>
                <p className="text-xs opacity-60 mt-0.5">{session.message_count} messages</p>

                <button
                  onClick={(e) => { e.stopPropagation(); deleteSession(session.id); }}
                  className="absolute right-2 top-1/2 -translate-y-1/2 p-1 rounded-lg opacity-0 group-hover:opacity-100 hover:bg-destructive/10 hover:text-destructive transition-all"
                >
                  <Trash2 className="w-3 h-3" />
                </button>
              </motion.button>
            ))}
          </AnimatePresence>
        )}
      </div>
    </div>
  );
}
