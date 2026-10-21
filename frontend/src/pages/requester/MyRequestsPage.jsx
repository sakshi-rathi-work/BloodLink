import React from "react";
import EmptyState from "../../components/ui/EmptyState";
import { ClipboardList } from "lucide-react";

export default function MyRequestsPage() {
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">My Blood Requests</h1>
      <EmptyState
        icon={ClipboardList}
        title="Requester Requests"
        description="Assigned to Phase 3 (Saee)."
      />
    </div>
  );
}
