import React from "react";
import EmptyState from "../../components/ui/EmptyState";
import { History } from "lucide-react";

export default function ActivityLogPage() {
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">System Activity Logs</h1>
      <EmptyState
        icon={History}
        title="Admin Activity Logs"
        description="Assigned to Phase 5 (Esha)."
      />
    </div>
  );
}
