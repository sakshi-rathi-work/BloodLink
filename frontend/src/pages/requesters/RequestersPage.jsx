import React from "react";
import EmptyState from "../../components/ui/EmptyState";
import { Building2 } from "lucide-react";

export default function RequestersPage() {
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">Requesters Directory</h1>
      <EmptyState
        icon={Building2}
        title="Registered Hospitals & Patients"
        description="Assigned to Phase 3 (Saee)."
      />
    </div>
  );
}
