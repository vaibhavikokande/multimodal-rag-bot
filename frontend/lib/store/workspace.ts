import { create } from "zustand";
import { persist } from "zustand/middleware";
import { api } from "@/lib/api";

interface Workspace {
  id: number;
  name: string;
  slug: string;
  description?: string;
  owner_id: number;
}

interface WorkspaceState {
  workspaces: Workspace[];
  currentWorkspace: Workspace | null;
  isLoading: boolean;
  fetchWorkspaces: () => Promise<void>;
  setCurrentWorkspace: (ws: Workspace) => void;
  createWorkspace: (name: string, description?: string) => Promise<Workspace | null>;
}

export const useWorkspaceStore = create<WorkspaceState>()(
  persist(
    (set, get) => ({
      workspaces: [],
      currentWorkspace: null,
      isLoading: false,

      fetchWorkspaces: async () => {
        set({ isLoading: true });
        try {
          const res = await api.get("/workspaces/");
          const workspaces = res.data.workspaces || [];
          set({ workspaces });

          // Auto-select first workspace if none selected
          if (!get().currentWorkspace && workspaces.length > 0) {
            set({ currentWorkspace: workspaces[0] });
          }
        } catch (err) {
          console.error("Failed to fetch workspaces:", err);
        } finally {
          set({ isLoading: false });
        }
      },

      setCurrentWorkspace: (ws) => set({ currentWorkspace: ws }),

      createWorkspace: async (name, description) => {
        try {
          const res = await api.post("/workspaces/", { name, description });
          const ws = res.data;
          set((state) => ({
            workspaces: [ws, ...state.workspaces],
            currentWorkspace: ws,
          }));
          return ws;
        } catch (err) {
          console.error("Failed to create workspace:", err);
          return null;
        }
      },
    }),
    {
      name: "workspace-storage",
      partialize: (state) => ({ currentWorkspace: state.currentWorkspace }),
    }
  )
);
