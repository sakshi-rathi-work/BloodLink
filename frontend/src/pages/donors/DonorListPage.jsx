import React from "react";
import EmptyState from "../../components/ui/EmptyState";
import { Users } from "lucide-react";

export default function DonorListPage() {
  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">Donor Directory</h1>
          <p className="text-sm text-slate-500">Manage registered donors, eligibility, and donations</p>
        </div>
      </div>
      <EmptyState
        icon={Users}
        title="Donor Directory"
        description="Assigned to Phase 2 (Sakshi)."
      />
    </div>
  );
}
