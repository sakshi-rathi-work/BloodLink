import React from "react";
import StatCard from "../../components/ui/StatCard";
import { Activity, Clock, AlertTriangle, Droplets } from "lucide-react";

export default function DashboardPage() {
  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">Staff Dashboard</h1>
          <p className="text-sm text-slate-500">Real-time blood bank inventory and operational overview</p>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard title="Total Units Available" value="—" icon={Droplets} variant="blood" />
        <StatCard title="Pending Requests" value="—" icon={Clock} variant="warning" />
        <StatCard title="Expiring Soon (7d)" value="—" icon={AlertTriangle} variant="danger" />
        <StatCard title="Shortage Alerts" value="—" icon={Activity} variant="warning" />
      </div>

      <div className="p-8 bg-white rounded-2xl border border-slate-200 text-center text-slate-500">
        <p className="text-base font-semibold text-slate-700">Full Dashboard Analytics & Charts</p>
        <p className="text-sm mt-1">Configured for Phase 5 (Esha).</p>
      </div>
    </div>
  );
}
