import React from "react";
import EmptyState from "../../components/ui/EmptyState";
import { UserCog } from "lucide-react";

export default function StaffPage() {
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">Staff Account Management</h1>
      <EmptyState
        icon={UserCog}
        title="Admin Staff Management"
        description="Assigned to Phase 5 (Esha)."
      />
    </div>
  );
}
