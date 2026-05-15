"use client";
import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Users, Shield, Search, CheckCircle, XCircle, MoreHorizontal } from "lucide-react";
import { api } from "@/lib/api";
import { formatDate } from "@/lib/utils";
import toast from "react-hot-toast";

export default function AdminPage() {
  const [users, setUsers] = useState<any[]>([]);
  const [total, setTotal] = useState(0);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);

  useEffect(() => {
    fetchUsers();
  }, [page, search]);

  const fetchUsers = async () => {
    setLoading(true);
    try {
      const res = await api.get("/admin/users", {
        params: { page, per_page: 20, search: search || undefined },
      });
      setUsers(res.data.users);
      setTotal(res.data.total);
    } catch (err) {
      toast.error("Failed to load users");
    } finally {
      setLoading(false);
    }
  };

  const updateUser = async (userId: number, data: any) => {
    try {
      await api.put(`/admin/users/${userId}`, data);
      toast.success("User updated");
      fetchUsers();
    } catch {
      toast.error("Update failed");
    }
  };

  const ROLES = ["viewer", "user", "manager", "admin", "superadmin"];

  return (
    <div className="p-6 space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Shield className="w-6 h-6 text-primary" />
            Admin Panel
          </h1>
          <p className="text-muted-foreground">{total} total users</p>
        </div>
      </div>

      {/* Search */}
      <div className="relative max-w-md">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
        <input
          value={search}
          onChange={(e) => { setSearch(e.target.value); setPage(1); }}
          placeholder="Search users..."
          className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-border bg-background focus:outline-none focus:ring-2 focus:ring-primary/30 text-sm"
        />
      </div>

      {/* Users Table */}
      <div className="rounded-2xl border border-border overflow-hidden bg-card">
        <table className="w-full">
          <thead>
            <tr className="border-b border-border bg-muted/50">
              <th className="px-4 py-3 text-left text-sm font-medium text-muted-foreground">User</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-muted-foreground">Role</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-muted-foreground">Status</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-muted-foreground">Organization</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-muted-foreground">Last Login</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-muted-foreground">Actions</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              [...Array(5)].map((_, i) => (
                <tr key={i} className="border-b border-border">
                  <td colSpan={6} className="px-4 py-3">
                    <div className="h-8 bg-muted rounded animate-pulse" />
                  </td>
                </tr>
              ))
            ) : (
              users.map((user, i) => (
                <motion.tr
                  key={user.id}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: i * 0.03 }}
                  className="border-b border-border last:border-0 hover:bg-accent/30 transition-colors"
                >
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 rounded-full gradient-brand flex items-center justify-center text-white text-sm font-semibold">
                        {user.full_name?.[0]?.toUpperCase()}
                      </div>
                      <div>
                        <p className="font-medium text-sm">{user.full_name}</p>
                        <p className="text-xs text-muted-foreground">{user.email}</p>
                      </div>
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <select
                      value={user.role}
                      onChange={(e) => updateUser(user.id, { role: e.target.value })}
                      className="text-sm rounded-lg border border-border bg-background px-2 py-1 focus:outline-none"
                    >
                      {ROLES.map((r) => (
                        <option key={r} value={r}>{r}</option>
                      ))}
                    </select>
                  </td>
                  <td className="px-4 py-3">
                    <button
                      onClick={() => updateUser(user.id, { is_active: !user.is_active })}
                      className={`flex items-center gap-1.5 text-sm ${user.is_active ? "text-emerald-600" : "text-muted-foreground"}`}
                    >
                      {user.is_active ? <CheckCircle className="w-4 h-4" /> : <XCircle className="w-4 h-4" />}
                      {user.is_active ? "Active" : "Inactive"}
                    </button>
                  </td>
                  <td className="px-4 py-3 text-sm text-muted-foreground">{user.organization || "—"}</td>
                  <td className="px-4 py-3 text-sm text-muted-foreground">
                    {user.last_login ? formatDate(user.last_login) : "Never"}
                  </td>
                  <td className="px-4 py-3">
                    <button className="p-1.5 rounded-lg hover:bg-accent">
                      <MoreHorizontal className="w-4 h-4" />
                    </button>
                  </td>
                </motion.tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {total > 20 && (
        <div className="flex justify-center gap-2">
          <button onClick={() => setPage(p => Math.max(1, p-1))} disabled={page === 1}
            className="px-4 py-2 rounded-lg border border-border text-sm disabled:opacity-40 hover:bg-accent">
            Previous
          </button>
          <span className="px-4 py-2 text-sm text-muted-foreground">Page {page}</span>
          <button onClick={() => setPage(p => p+1)} disabled={users.length < 20}
            className="px-4 py-2 rounded-lg border border-border text-sm disabled:opacity-40 hover:bg-accent">
            Next
          </button>
        </div>
      )}
    </div>
  );
}
