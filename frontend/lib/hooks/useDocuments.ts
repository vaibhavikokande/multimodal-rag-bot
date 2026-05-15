import { useEffect, useState, useCallback } from "react";
import { api } from "@/lib/api";

interface UseDocumentsOptions {
  workspaceId?: number;
  search?: string;
  docType?: string;
  status?: string;
  page?: number;
}

export function useDocuments({
  workspaceId,
  search = "",
  docType = "",
  status = "",
  page = 1,
}: UseDocumentsOptions) {
  const [documents, setDocuments] = useState<any[]>([]);
  const [total, setTotal] = useState(0);
  const [isLoading, setIsLoading] = useState(false);

  const fetchDocuments = useCallback(async () => {
    if (!workspaceId) return;
    setIsLoading(true);
    try {
      const res = await api.get("/documents/", {
        params: {
          workspace_id: workspaceId,
          search: search || undefined,
          doc_type: docType || undefined,
          status: status || undefined,
          page,
          per_page: 20,
        },
      });
      setDocuments(res.data.documents || []);
      setTotal(res.data.total || 0);
    } catch (err) {
      console.error("Failed to fetch documents:", err);
    } finally {
      setIsLoading(false);
    }
  }, [workspaceId, search, docType, status, page]);

  useEffect(() => {
    fetchDocuments();
  }, [fetchDocuments]);

  const upload = async (files: File[], wsId: number, tags: string = "") => {
    const formData = new FormData();
    files.forEach((f) => formData.append("files", f));
    formData.append("workspace_id", String(wsId));
    formData.append("tags", tags);
    await api.post("/documents/upload", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
  };

  const remove = async (docId: number) => {
    await api.delete(`/documents/${docId}`);
    setDocuments((prev) => prev.filter((d) => d.id !== docId));
    setTotal((t) => t - 1);
  };

  const reprocess = async (docId: number) => {
    await api.post(`/documents/${docId}/reprocess`);
    await fetchDocuments();
  };

  return { documents, total, isLoading, upload, remove, reprocess, refetch: fetchDocuments };
}
