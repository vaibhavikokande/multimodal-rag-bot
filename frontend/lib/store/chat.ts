import { create } from "zustand";
import { api } from "@/lib/api";

interface ChatSession {
  id: number;
  title: string;
  model: string;
  message_count: number;
  workspace_id: number;
  created_at: string;
}

interface ChatState {
  sessions: ChatSession[];
  currentSession: ChatSession | null;
  isLoading: boolean;
  fetchSessions: (workspaceId: number) => Promise<void>;
  createSession: (workspaceId: number, title?: string) => Promise<ChatSession | null>;
  setCurrentSession: (session: ChatSession | null) => void;
  deleteSession: (sessionId: number) => Promise<void>;
}

export const useChatStore = create<ChatState>((set, get) => ({
  sessions: [],
  currentSession: null,
  isLoading: false,

  fetchSessions: async (workspaceId) => {
    set({ isLoading: true });
    try {
      const res = await api.get("/chat/sessions", { params: { workspace_id: workspaceId } });
      set({ sessions: res.data.sessions || [] });
    } catch (err) {
      console.error("Failed to fetch sessions:", err);
    } finally {
      set({ isLoading: false });
    }
  },

  createSession: async (workspaceId, title = "New Chat") => {
    try {
      const res = await api.post("/chat/sessions", {
        workspace_id: workspaceId,
        title,
      });
      const session = res.data;
      set((state) => ({
        sessions: [session, ...state.sessions],
        currentSession: session,
      }));
      return session;
    } catch (err) {
      console.error("Failed to create session:", err);
      return null;
    }
  },

  setCurrentSession: (session) => set({ currentSession: session }),

  deleteSession: async (sessionId) => {
    try {
      await api.delete(`/chat/sessions/${sessionId}`);
      set((state) => {
        const sessions = state.sessions.filter((s) => s.id !== sessionId);
        const currentSession =
          state.currentSession?.id === sessionId ? null : state.currentSession;
        return { sessions, currentSession };
      });
    } catch (err) {
      console.error("Failed to delete session:", err);
    }
  },
}));
