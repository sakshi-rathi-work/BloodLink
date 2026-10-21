import React from "react";
import EmptyState from "../../components/ui/EmptyState";
import { FileText } from "lucide-react";

export default function ReportsPage() {
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">Export Reports</h1>
      <EmptyState
        icon={FileText}
        title="PDF & CSV Report Generator"
        description="Assigned to Phase 5 (Esha)."
      />
    </div>
  );
}
