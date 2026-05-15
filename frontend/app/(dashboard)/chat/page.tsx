"use client";
import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ChatSidebar } from "@/components/chat/ChatSidebar";
import { ChatWindow } from "@/components/chat/ChatWindow";
import { useChatStore } from "@/lib/store/chat";
import { useWorkspaceStore } from "@/lib/store/workspace";
import { MessageSquare } from "lucide-react";

export default function ChatPage() {
  const { currentSession } = useChatStore();
  const { currentWorkspace } = useWorkspaceStore();

  return (
    <div className="flex h-full">
      <ChatSidebar />
      <div className="flex-1 flex flex-col min-w-0">
        <AnimatePresence mode="wait">
          {currentSession ? (
            <motion.div
              key={currentSession.id}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="flex-1 flex flex-col"
            >
              <ChatWindow session={currentSession} />
            </motion.div>
          ) : (
            <motion.div
              key="empty"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="flex-1 flex flex-col items-center justify-center gap-6 p-8"
            >
              <div className="w-20 h-20 rounded-3xl gradient-brand flex items-center justify-center shadow-xl">
                <MessageSquare className="w-10 h-10 text-white" />
              </div>
              <div className="text-center max-w-md">
                <h2 className="text-2xl font-bold mb-3">Ask anything about your knowledge base</h2>
                <p className="text-muted-foreground leading-relaxed">
                  Start a new conversation to query documents, analyze images, extract insights from videos, and get citation-backed answers.
                </p>
              </div>
              <div className="grid grid-cols-2 gap-3 w-full max-w-lg">
                {[
                  "Summarize the Q3 financial report",
                  "What are the key findings from the research paper?",
                  "Explain the architecture diagram on slide 5",
                  "What did the speaker say about roadmap?",
                ].map((suggestion, i) => (
                  <SuggestionCard key={i} text={suggestion} />
                ))}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}

function SuggestionCard({ text }: { text: string }) {
  const { createSession, setCurrentSession } = useChatStore();
  const { currentWorkspace } = useWorkspaceStore();

  const handleClick = async () => {
    if (!currentWorkspace) return;
    const session = await createSession(currentWorkspace.id, text.slice(0, 40));
    if (session) setCurrentSession(session);
  };

  return (
    <button
      onClick={handleClick}
      className="p-4 text-left rounded-xl border border-border hover:border-primary/50 hover:bg-accent/50 transition-all text-sm text-muted-foreground hover:text-foreground"
    >
      {text}
    </button>
  );
}
