"use client";
import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Plus, FolderOpen, Users, FileText, Settings, Loader2 } from "lucide-react";
import { useWorkspaceStore } from "@/lib/store/workspace";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import toast from "react-hot-toast";
import { cn } from "@/lib/utils";

const schema = z.object({
  name: z.string().min(2, "Name required"),
  description: z.string().optional(),
});

export default function WorkspacesPage() {
  const { workspaces, currentWorkspace, createWorkspace, setCurrentWorkspace, isLoading } = useWorkspaceStore();
  const [showCreate, setShowCreate] = useState(false);

  const { register, handleSubmit, reset, formState: { errors, isSubmitting } } = useForm({
    resolver: zodResolver(schema),
  });

  const onSubmit = async (data: any) => {
    const ws = await createWorkspace(data.name, data.description);
    if (ws) {
      toast.success("Workspace created!");
      setShowCreate(false);
      reset();
    } else {
      toast.error("Failed to create workspace");
    }
  };

  return (
    <div className="p-6 space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Workspaces</h1>
          <p className="text-muted-foreground">Organize your knowledge base into workspaces</p>
        </div>
        <button
          onClick={() => setShowCreate(true)}
          className="flex items-center gap-2 px-4 py-2 rounded-xl gradient-brand text-white text-sm font-medium hover:opacity-90 transition-opacity"
        >
          <Plus className="w-4 h-4" />
          New Workspace
        </button>
      </div>

      {/* Create Modal */}
      <AnimatePresence>
        {showCreate && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="p-5 rounded-2xl border border-primary/30 bg-primary/5"
          >
            <h3 className="font-semibold mb-4">Create New Workspace</h3>
            <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
              <div>
                <input
                  {...register("name")}
                  placeholder="Workspace name (e.g. Finance Team)"
                  className="w-full px-4 py-2.5 rounded-xl border border-border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-primary/30"
                />
                {errors.name && <p className="text-destructive text-xs mt-1">{String(errors.name.message)}</p>}
              </div>
              <textarea
                {...register("description")}
                placeholder="Description (optional)"
                rows={2}
                className="w-full px-4 py-2.5 rounded-xl border border-border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 resize-none"
              />
              <div className="flex gap-2">
                <button type="submit" disabled={isSubmitting}
                  className="px-4 py-2 rounded-xl gradient-brand text-white text-sm font-medium hover:opacity-90 disabled:opacity-50 flex items-center gap-2">
                  {isSubmitting ? <Loader2 className="w-4 h-4 animate-spin" /> : null}
                  Create
                </button>
                <button type="button" onClick={() => { setShowCreate(false); reset(); }}
                  className="px-4 py-2 rounded-xl border border-border text-sm hover:bg-accent">
                  Cancel
                </button>
              </div>
            </form>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Workspaces Grid */}
      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="h-40 rounded-2xl bg-muted animate-pulse" />
          ))}
        </div>
      ) : workspaces.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-20 text-muted-foreground">
          <FolderOpen className="w-12 h-12 mb-3 opacity-30" />
          <p className="text-lg font-medium">No workspaces yet</p>
          <p className="text-sm">Create your first workspace to start organizing documents</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {workspaces.map((ws, i) => (
            <motion.div
              key={ws.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.05 }}
              onClick={() => setCurrentWorkspace(ws)}
              className={cn(
                "p-5 rounded-2xl border cursor-pointer transition-all hover:shadow-md",
                currentWorkspace?.id === ws.id
                  ? "border-primary bg-primary/5 shadow-sm"
                  : "border-border hover:border-primary/40 bg-card"
              )}
            >
              <div className="flex items-center gap-3 mb-4">
                <div className="w-10 h-10 rounded-xl gradient-brand flex items-center justify-center text-white font-bold text-lg">
                  {ws.name[0].toUpperCase()}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="font-semibold truncate">{ws.name}</p>
                  {currentWorkspace?.id === ws.id && (
                    <span className="text-xs text-primary font-medium">Active</span>
                  )}
                </div>
              </div>

              {ws.description && (
                <p className="text-sm text-muted-foreground mb-4 line-clamp-2">{ws.description}</p>
              )}

              <div className="flex items-center gap-4 text-xs text-muted-foreground">
                <span className="flex items-center gap-1"><FileText className="w-3.5 h-3.5" /> Documents</span>
                <span className="flex items-center gap-1"><Users className="w-3.5 h-3.5" /> Members</span>
              </div>
            </motion.div>
          ))}
        </div>
      )}
    </div>
  );
}
