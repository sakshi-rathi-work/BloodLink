import React from "react";
import EmptyState from "../../components/ui/EmptyState";
import { PlusCircle } from "lucide-react";

export default function NewRequestPage() {
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">Submit New Blood Request</h1>
      <EmptyState
        icon={PlusCircle}
        title="New Blood Request Form"
        description="Assigned to Phase 3 (Saee)."
      />
    </div>
  );
}
