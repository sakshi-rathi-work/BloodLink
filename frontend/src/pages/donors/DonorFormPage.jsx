import React from "react";
import EmptyState from "../../components/ui/EmptyState";
import { UserPlus } from "lucide-react";

export default function DonorFormPage() {
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">Register / Edit Donor</h1>
      <EmptyState
        icon={UserPlus}
        title="Donor Form"
        description="Assigned to Phase 2 (Sakshi)."
      />
    </div>
  );
}
