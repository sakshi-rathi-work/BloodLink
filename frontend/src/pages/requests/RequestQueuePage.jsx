import React from "react";
import EmptyState from "../../components/ui/EmptyState";
import { ClipboardList } from "lucide-react";

export default function RequestQueuePage() {
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">Blood Requests Queue</h1>
      <EmptyState
        icon={ClipboardList}
        title="Request Queue & Matching"
        description="Assigned to Phase 3 (Saee)."
      />
    </div>
  );
}
