import React from "react";
import EmptyState from "../../components/ui/EmptyState";
import { ClipboardCheck } from "lucide-react";

export default function RequestDetailPage() {
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">Request Details & Allocation</h1>
      <EmptyState
        icon={ClipboardCheck}
        title="Matching & Issue Allocation"
        description="Assigned to Phase 3 (Saee)."
      />
    </div>
  );
}
