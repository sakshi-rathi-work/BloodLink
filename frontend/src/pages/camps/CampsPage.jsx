import React from "react";
import EmptyState from "../../components/ui/EmptyState";
import { Tent } from "lucide-react";

export default function CampsPage() {
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">Donation Camps</h1>
      <EmptyState
        icon={Tent}
        title="Donation Camps Schedule"
        description="Assigned to Phase 5 (Esha)."
      />
    </div>
  );
}
