"use client";
import { useEffect, useRef, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Send, Paperclip, Bot, User, ThumbsUp, ThumbsDown, Copy, ChevronDown, Loader2 } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { useChatStore } from "@/lib/store/chat";
import { useWorkspaceStore } from "@/lib/store/workspace";
import { api } from "@/lib/api";
import toast from "react-hot-toast";
import { cn } from "@/lib/utils";

interface ChatWindowProps {
  session: { id: number; title: string; model: string; workspace_id: number };
}

const MODELS = [
  { value: "gpt-4o", label: "GPT-4o" },
  { value: "gpt-4o-mini", label: "GPT-4o Mini" },
  { value: "claude-3-5-sonnet-20241022", label: "Claude 3.5 Sonnet" },
];

export function ChatWindow({ session }: ChatWindowProps) {
  const [messages, setMessages] = useState<any[]>([]);
  const [input, setInput] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [streamContent, setStreamContent] = useState("");
  const [selectedModel, setSelectedModel] = useState(session.model || "gpt-4o");
  const [sources, setSources] = useState<any[]>([]);
  const bottomRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const { currentWorkspace } = useWorkspaceStore();

  useEffect(() => {
    loadMessages();
  }, [session.id]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, streamContent]);

  const loadMessages = async () => {
    try {
      const res = await api.get(`/chat/sessions/${session.id}/messages`);
      setMessages(res.data.messages || []);
    } catch (err) {
      toast.error("Failed to load messages");
    }
  };

  const handleSend = async () => {
    if (!input.trim() || isTyping) return;
    const userMessage = input.trim();
    setInput("");
    setIsTyping(true);
    setStreamContent("");
    setSources([]);

    // Optimistic UI
    setMessages((prev) => [
      ...prev,
      { id: Date.now(), role: "user", content: userMessage, created_at: new Date().toISOString() }
    ]);

    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/chat/stream`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${localStorage.getItem("token")}`,
        },
        body: JSON.stringify({
          message: userMessage,
          session_id: session.id,
          workspace_id: currentWorkspace?.id || session.workspace_id,
          model: selectedModel,
          stream: true,
        }),
      });

      if (!response.ok) throw new Error("Stream request failed");

      const reader = response.body!.getReader();
      const decoder = new TextDecoder();
      let fullContent = "";
      let msgSources: any[] = [];

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const text = decoder.decode(value);
        const lines = text.split("\n");

        for (const line of lines) {
          if (!line.startsWith("data: ")) continue;
          try {
            const data = JSON.parse(line.slice(6));
            if (data.type === "token") {
              fullContent += data.content;
              setStreamContent(fullContent);
            } else if (data.type === "sources") {
              msgSources = data.sources || [];
              setSources(msgSources);
            } else if (data.type === "done") {
              break;
            }
          } catch {}
        }
      }

      setMessages((prev) => [
        ...prev,
        {
          id: Date.now() + 1,
          role: "assistant",
          content: fullContent,
          sources: msgSources,
          created_at: new Date().toISOString(),
        }
      ]);
      setStreamContent("");
    } catch (err) {
      toast.error("Failed to get response");
      setStreamContent("");
    } finally {
      setIsTyping(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    toast.success("Copied!");
  };

  return (
    <div className="flex flex-col h-full">
      {/* Model selector */}
      <div className="flex items-center justify-between px-4 py-2 border-b border-border bg-card/50">
        <p className="text-sm text-muted-foreground truncate max-w-xs">{session.title}</p>
        <select
          value={selectedModel}
          onChange={(e) => setSelectedModel(e.target.value)}
          className="text-sm rounded-lg border border-border bg-background px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-primary/30"
        >
          {MODELS.map((m) => (
            <option key={m.value} value={m.value}>{m.label}</option>
          ))}
        </select>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        <AnimatePresence>
          {messages.map((msg) => (
            <motion.div
              key={msg.id}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              className={cn("flex gap-3 group", msg.role === "user" ? "justify-end" : "justify-start")}
            >
              {msg.role === "assistant" && (
                <div className="w-8 h-8 rounded-xl gradient-brand flex items-center justify-center flex-shrink-0 mt-1">
                  <Bot className="w-4 h-4 text-white" />
                </div>
              )}

              <div className={cn("max-w-2xl", msg.role === "user" ? "order-first" : "")}>
                <div
                  className={cn(
                    "rounded-2xl px-4 py-3 text-sm",
                    msg.role === "user"
                      ? "bg-primary text-primary-foreground rounded-tr-sm"
                      : "bg-card border border-border rounded-tl-sm"
                  )}
                >
                  {msg.role === "assistant" ? (
                    <div className="chat-prose">
                      <ReactMarkdown remarkPlugins={[remarkGfm]}>
                        {msg.content}
                      </ReactMarkdown>
                    </div>
                  ) : (
                    <p className="whitespace-pre-wrap">{msg.content}</p>
                  )}
                </div>

                {/* Sources */}
                {msg.role === "assistant" && msg.sources?.length > 0 && (
                  <div className="mt-2 flex flex-wrap gap-1.5">
                    {msg.sources.map((source: any, i: number) => (
                      <span key={i} className="inline-flex items-center gap-1 px-2 py-1 rounded-lg bg-primary/10 text-primary text-xs font-medium">
                        <span className="w-1.5 h-1.5 rounded-full bg-primary" />
                        Doc #{source.document_id}
                        {source.page_number && ` · P.${source.page_number}`}
                      </span>
                    ))}
                  </div>
                )}

                {/* Message actions */}
                {msg.role === "assistant" && (
                  <div className="flex gap-1 mt-1.5 opacity-0 group-hover:opacity-100 transition-opacity">
                    <button onClick={() => copyToClipboard(msg.content)}
                      className="p-1.5 rounded-lg hover:bg-accent text-muted-foreground hover:text-foreground">
                      <Copy className="w-3.5 h-3.5" />
                    </button>
                    <button className="p-1.5 rounded-lg hover:bg-accent text-muted-foreground hover:text-emerald-500">
                      <ThumbsUp className="w-3.5 h-3.5" />
                    </button>
                    <button className="p-1.5 rounded-lg hover:bg-accent text-muted-foreground hover:text-destructive">
                      <ThumbsDown className="w-3.5 h-3.5" />
                    </button>
                  </div>
                )}
              </div>

              {msg.role === "user" && (
                <div className="w-8 h-8 rounded-xl bg-primary/20 flex items-center justify-center flex-shrink-0 mt-1">
                  <User className="w-4 h-4 text-primary" />
                </div>
              )}
            </motion.div>
          ))}

          {/* Streaming response */}
          {isTyping && (
            <motion.div
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              className="flex gap-3"
            >
              <div className="w-8 h-8 rounded-xl gradient-brand flex items-center justify-center flex-shrink-0 mt-1">
                <Bot className="w-4 h-4 text-white" />
              </div>
              <div className="max-w-2xl">
                <div className="bg-card border border-border rounded-2xl rounded-tl-sm px-4 py-3 text-sm">
                  {streamContent ? (
                    <div className="chat-prose">
                      <ReactMarkdown remarkPlugins={[remarkGfm]}>
                        {streamContent}
                      </ReactMarkdown>
                    </div>
                  ) : (
                    <div className="flex gap-1 items-center h-5">
                      <span className="typing-dot" />
                      <span className="typing-dot" />
                      <span className="typing-dot" />
                    </div>
                  )}
                </div>
                {sources.length > 0 && (
                  <div className="mt-2 flex flex-wrap gap-1.5">
                    {sources.map((source: any, i: number) => (
                      <span key={i} className="inline-flex items-center gap-1 px-2 py-1 rounded-lg bg-primary/10 text-primary text-xs font-medium">
                        <span className="w-1.5 h-1.5 rounded-full bg-primary" />
                        Doc #{source.document_id}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="p-4 border-t border-border">
        <div className="flex items-end gap-3 bg-card border border-border rounded-2xl px-4 py-3 focus-within:ring-2 focus-within:ring-primary/30 focus-within:border-primary transition-all">
          <textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask a question about your documents..."
            rows={1}
            className="flex-1 bg-transparent resize-none text-sm focus:outline-none max-h-32 overflow-y-auto leading-relaxed"
            style={{ minHeight: "24px" }}
          />
          <button
            onClick={handleSend}
            disabled={!input.trim() || isTyping}
            className="w-9 h-9 rounded-xl gradient-brand flex items-center justify-center text-white disabled:opacity-40 hover:opacity-90 transition-opacity flex-shrink-0"
          >
            {isTyping ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
          </button>
        </div>
        <p className="text-xs text-muted-foreground text-center mt-2">
          Enter to send · Shift+Enter for newline
        </p>
      </div>
    </div>
  );
}
