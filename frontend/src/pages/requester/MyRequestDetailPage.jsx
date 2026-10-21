import React from "react";
import EmptyState from "../../components/ui/EmptyState";
import { FileCheck } from "lucide-react";

export default function MyRequestDetailPage() {
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">Request Details</h1>
      <EmptyState
        icon={FileCheck}
        title="Request Status & Fulfilled Units"
        description="Assigned to Phase 3 (Saee)."
      />
    </div>
  );
}
