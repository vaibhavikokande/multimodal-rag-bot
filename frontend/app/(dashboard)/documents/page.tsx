"use client";
import { useState, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useDropzone } from "react-dropzone";
import { Upload, FileText, Image, Video, Music, Search, Filter, MoreVertical, RefreshCw, Trash2, Download, Eye } from "lucide-react";
import { useDocuments } from "@/lib/hooks/useDocuments";
import { useWorkspaceStore } from "@/lib/store/workspace";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { formatBytes, formatDate } from "@/lib/utils";
import toast from "react-hot-toast";

const FILE_TYPE_ICONS: Record<string, any> = {
  pdf: FileText, docx: FileText, pptx: FileText, txt: FileText, csv: FileText,
  image: Image, video: Video, audio: Music,
};

export default function DocumentsPage() {
  const { currentWorkspace } = useWorkspaceStore();
  const [search, setSearch] = useState("");
  const [filterType, setFilterType] = useState("");
  const [filterStatus, setFilterStatus] = useState("");
  const [page, setPage] = useState(1);

  const { documents, total, isLoading, upload, remove, reprocess, refetch } = useDocuments({
    workspaceId: currentWorkspace?.id,
    search,
    docType: filterType,
    status: filterStatus,
    page,
  });

  const onDrop = useCallback(async (files: File[]) => {
    if (!currentWorkspace) {
      toast.error("Select a workspace first");
      return;
    }
    const toastId = toast.loading(`Uploading ${files.length} file(s)...`);
    try {
      await upload(files, currentWorkspace.id);
      toast.success("Files uploaded! Processing in background.", { id: toastId });
      refetch();
    } catch (err: any) {
      toast.error(err.response?.data?.detail || "Upload failed", { id: toastId });
    }
  }, [currentWorkspace, upload, refetch]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      "application/pdf": [".pdf"],
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [".docx"],
      "application/vnd.openxmlformats-officedocument.presentationml.presentation": [".pptx"],
      "text/plain": [".txt"],
      "text/csv": [".csv"],
      "application/vnd.ms-excel": [".xlsx"],
      "image/*": [".png", ".jpg", ".jpeg", ".gif", ".webp"],
      "video/*": [".mp4", ".avi", ".mov"],
      "audio/*": [".mp3", ".wav", ".m4a"],
    },
    maxSize: 500 * 1024 * 1024,
  });

  return (
    <div className="p-6 space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Documents</h1>
          <p className="text-muted-foreground">{total} files in knowledge base</p>
        </div>
        <button onClick={refetch} className="p-2 rounded-lg hover:bg-accent transition-colors">
          <RefreshCw className="w-5 h-5" />
        </button>
      </div>

      {/* Upload Zone */}
      <motion.div whileHover={{ scale: 1.005 }} className="w-full">
      <div
        {...getRootProps()}
        className={`border-2 border-dashed rounded-2xl p-8 text-center cursor-pointer transition-all ${
          isDragActive
            ? "border-primary bg-primary/5"
            : "border-border hover:border-primary/50 hover:bg-accent/30"
        }`}
      >
        <input {...getInputProps()} />
        <div className="flex flex-col items-center gap-3">
          <div className="w-14 h-14 rounded-2xl bg-primary/10 flex items-center justify-center">
            <Upload className="w-7 h-7 text-primary" />
          </div>
          {isDragActive ? (
            <p className="text-primary font-semibold text-lg">Drop files here</p>
          ) : (
            <>
              <p className="font-semibold text-lg">Drag & drop or click to upload</p>
              <p className="text-muted-foreground text-sm">
                PDF, DOCX, PPTX, TXT, CSV, XLSX, Images, Videos, Audio • Max 500MB
              </p>
            </>
          )}
        </div>
      </div>
      </motion.div>

      {/* Filters */}
      <div className="flex gap-3 flex-wrap">
        <div className="relative flex-1 min-w-52">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search documents..."
            className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-border bg-background focus:outline-none focus:ring-2 focus:ring-primary/30 text-sm"
          />
        </div>
        <select
          value={filterType}
          onChange={(e) => setFilterType(e.target.value)}
          className="px-4 py-2.5 rounded-xl border border-border bg-background text-sm focus:outline-none"
        >
          <option value="">All Types</option>
          <option value="pdf">PDF</option>
          <option value="docx">DOCX</option>
          <option value="pptx">PPTX</option>
          <option value="image">Images</option>
          <option value="video">Videos</option>
          <option value="audio">Audio</option>
        </select>
        <select
          value={filterStatus}
          onChange={(e) => setFilterStatus(e.target.value)}
          className="px-4 py-2.5 rounded-xl border border-border bg-background text-sm focus:outline-none"
        >
          <option value="">All Status</option>
          <option value="indexed">Indexed</option>
          <option value="processing">Processing</option>
          <option value="failed">Failed</option>
        </select>
      </div>

      {/* Documents Grid */}
      {isLoading ? (
        <div className="grid grid-cols-1 gap-3">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="h-20 rounded-xl bg-muted animate-pulse" />
          ))}
        </div>
      ) : documents.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-20 text-muted-foreground">
          <FileText className="w-12 h-12 mb-3 opacity-30" />
          <p className="text-lg font-medium">No documents yet</p>
          <p className="text-sm">Upload your first document to get started</p>
        </div>
      ) : (
        <div className="space-y-2">
          <AnimatePresence>
            {documents.map((doc, i) => {
              const Icon = FILE_TYPE_ICONS[doc.doc_type] || FileText;
              return (
                <motion.div
                  key={doc.id}
                  initial={{ opacity: 0, y: 5 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.03 }}
                  className="flex items-center gap-4 p-4 rounded-xl border border-border hover:border-primary/30 hover:bg-accent/30 transition-all group"
                >
                  <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center flex-shrink-0">
                    <Icon className="w-5 h-5 text-primary" />
                  </div>

                  <div className="flex-1 min-w-0">
                    <p className="font-medium truncate">{doc.title}</p>
                    <div className="flex items-center gap-3 mt-0.5 text-xs text-muted-foreground">
                      <span>{doc.file_type.toUpperCase()}</span>
                      <span>{formatBytes(doc.file_size)}</span>
                      <span>{doc.chunk_count} chunks</span>
                      <span>{formatDate(doc.created_at)}</span>
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    {doc.auto_tags?.slice(0, 2).map((tag: string) => (
                      <span key={tag} className="px-2 py-0.5 rounded-full bg-muted text-xs text-muted-foreground">
                        {tag}
                      </span>
                    ))}
                    <StatusBadge status={doc.status} />
                  </div>

                  <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                    {doc.status === "failed" && (
                      <button
                        onClick={() => reprocess(doc.id)}
                        className="p-1.5 rounded-lg hover:bg-accent"
                        title="Reprocess"
                      >
                        <RefreshCw className="w-4 h-4" />
                      </button>
                    )}
                    <button
                      onClick={() => remove(doc.id)}
                      className="p-1.5 rounded-lg hover:bg-destructive/10 hover:text-destructive"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </motion.div>
              );
            })}
          </AnimatePresence>
        </div>
      )}

      {/* Pagination */}
      {total > 20 && (
        <div className="flex justify-center gap-2">
          <button
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={page === 1}
            className="px-4 py-2 rounded-lg border border-border text-sm disabled:opacity-40 hover:bg-accent"
          >
            Previous
          </button>
          <span className="px-4 py-2 text-sm text-muted-foreground">Page {page}</span>
          <button
            onClick={() => setPage((p) => p + 1)}
            disabled={documents.length < 20}
            className="px-4 py-2 rounded-lg border border-border text-sm disabled:opacity-40 hover:bg-accent"
          >
            Next
          </button>
        </div>
      )}
    </div>
  );
}
