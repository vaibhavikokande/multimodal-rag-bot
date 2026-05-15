"use client";
import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import {
  AreaChart, Area, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend
} from "recharts";
import { MessageSquare, FileText, Zap, Users, TrendingUp, Clock } from "lucide-react";
import { api } from "@/lib/api";

const COLORS = ["#3b82f6", "#8b5cf6", "#10b981", "#f59e0b", "#ef4444"];

export default function AnalyticsPage() {
  const [dashboard, setDashboard] = useState<any>(null);
  const [usage, setUsage] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      api.get("/admin/dashboard"),
      api.get("/admin/analytics/usage?days=30"),
    ]).then(([dashRes, usageRes]) => {
      setDashboard(dashRes.data);
      setUsage(usageRes.data.daily_usage || []);
    }).finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="p-6 grid grid-cols-1 gap-4">
        {[...Array(6)].map((_, i) => (
          <div key={i} className="h-32 rounded-2xl bg-muted animate-pulse" />
        ))}
      </div>
    );
  }

  const stats = [
    { label: "Total Queries", value: dashboard?.queries?.total || 0, icon: MessageSquare, color: "text-blue-500", bg: "bg-blue-500/10" },
    { label: "Documents Indexed", value: dashboard?.documents?.indexed || 0, icon: FileText, color: "text-emerald-500", bg: "bg-emerald-500/10" },
    { label: "Active Users", value: dashboard?.users?.active || 0, icon: Users, color: "text-violet-500", bg: "bg-violet-500/10" },
    { label: "Avg Latency", value: `${dashboard?.queries?.avg_latency_ms || 0}ms`, icon: Clock, color: "text-amber-500", bg: "bg-amber-500/10" },
    { label: "Chat Sessions", value: dashboard?.queries?.sessions || 0, icon: Zap, color: "text-pink-500", bg: "bg-pink-500/10" },
    { label: "Total Users", value: dashboard?.users?.total || 0, icon: TrendingUp, color: "text-cyan-500", bg: "bg-cyan-500/10" },
  ];

  return (
    <div className="p-6 space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold">Analytics</h1>
        <p className="text-muted-foreground">Platform usage insights and performance metrics</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
        {stats.map((stat, i) => (
          <motion.div
            key={stat.label}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.05 }}
            className="p-4 rounded-2xl border border-border bg-card"
          >
            <div className={`w-10 h-10 rounded-xl ${stat.bg} flex items-center justify-center mb-3`}>
              <stat.icon className={`w-5 h-5 ${stat.color}`} />
            </div>
            <div className="text-2xl font-bold">{stat.value}</div>
            <div className="text-sm text-muted-foreground">{stat.label}</div>
          </motion.div>
        ))}
      </div>

      {/* Usage Chart */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="p-6 rounded-2xl border border-border bg-card">
          <h3 className="font-semibold mb-4">Daily Queries (30 days)</h3>
          <ResponsiveContainer width="100%" height={250}>
            <AreaChart data={usage}>
              <defs>
                <linearGradient id="queryGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
              <XAxis dataKey="date" tick={{ fontSize: 11 }} stroke="hsl(var(--muted-foreground))" />
              <YAxis tick={{ fontSize: 11 }} stroke="hsl(var(--muted-foreground))" />
              <Tooltip
                contentStyle={{
                  background: "hsl(var(--card))",
                  border: "1px solid hsl(var(--border))",
                  borderRadius: "12px",
                }}
              />
              <Area type="monotone" dataKey="queries" stroke="#3b82f6" fill="url(#queryGrad)" strokeWidth={2} />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        <div className="p-6 rounded-2xl border border-border bg-card">
          <h3 className="font-semibold mb-4">Avg Latency (ms)</h3>
          <ResponsiveContainer width="100%" height={250}>
            <AreaChart data={usage}>
              <defs>
                <linearGradient id="latGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
              <XAxis dataKey="date" tick={{ fontSize: 11 }} stroke="hsl(var(--muted-foreground))" />
              <YAxis tick={{ fontSize: 11 }} stroke="hsl(var(--muted-foreground))" />
              <Tooltip contentStyle={{ background: "hsl(var(--card))", border: "1px solid hsl(var(--border))", borderRadius: "12px" }} />
              <Area type="monotone" dataKey="avg_latency_ms" stroke="#8b5cf6" fill="url(#latGrad)" strokeWidth={2} />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Model Usage + Doc Status */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="p-6 rounded-2xl border border-border bg-card">
          <h3 className="font-semibold mb-4">Model Usage</h3>
          {dashboard?.model_usage?.length ? (
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={dashboard.model_usage}>
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                <XAxis dataKey="model" tick={{ fontSize: 11 }} stroke="hsl(var(--muted-foreground))" />
                <YAxis tick={{ fontSize: 11 }} stroke="hsl(var(--muted-foreground))" />
                <Tooltip contentStyle={{ background: "hsl(var(--card))", border: "1px solid hsl(var(--border))", borderRadius: "12px" }} />
                <Bar dataKey="count" fill="#3b82f6" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="flex items-center justify-center h-60 text-muted-foreground">No data yet</div>
          )}
        </div>

        <div className="p-6 rounded-2xl border border-border bg-card">
          <h3 className="font-semibold mb-4">Document Status</h3>
          <ResponsiveContainer width="100%" height={250}>
            <PieChart>
              <Pie
                data={[
                  { name: "Indexed", value: dashboard?.documents?.indexed || 0 },
                  { name: "Processing", value: dashboard?.documents?.processing || 0 },
                  { name: "Failed", value: dashboard?.documents?.failed || 0 },
                ]}
                cx="50%"
                cy="50%"
                innerRadius={60}
                outerRadius={100}
                paddingAngle={3}
                dataKey="value"
              >
                {["#10b981", "#f59e0b", "#ef4444"].map((color, i) => (
                  <Cell key={i} fill={color} />
                ))}
              </Pie>
              <Tooltip contentStyle={{ background: "hsl(var(--card))", border: "1px solid hsl(var(--border))", borderRadius: "12px" }} />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Recent Queries */}
      <div className="p-6 rounded-2xl border border-border bg-card">
        <h3 className="font-semibold mb-4">Recent Queries</h3>
        <div className="space-y-2">
          {dashboard?.recent_queries?.map((q: any) => (
            <div key={q.id} className="flex items-center gap-4 p-3 rounded-xl hover:bg-accent/50 transition-colors">
              <MessageSquare className="w-4 h-4 text-muted-foreground flex-shrink-0" />
              <p className="flex-1 text-sm truncate">{q.query}</p>
              <span className="text-xs text-muted-foreground">{q.model}</span>
              <span className="text-xs text-muted-foreground">{q.latency_ms?.toFixed(0)}ms</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
