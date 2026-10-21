import React from "react";
import EmptyState from "../../components/ui/EmptyState";
import { UserCheck } from "lucide-react";

export default function DonorDetailPage() {
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">Donor Details</h1>
      <EmptyState
        icon={UserCheck}
        title="Donor Profile & Donations"
        description="Assigned to Phase 2 (Sakshi)."
      />
    </div>
  );
}
