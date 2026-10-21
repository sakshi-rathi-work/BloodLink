import React from "react";
import EmptyState from "../../components/ui/EmptyState";
import { Package } from "lucide-react";

export default function InventoryPage() {
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">Blood Inventory</h1>
      <EmptyState
        icon={Package}
        title="Inventory & Expiry Management"
        description="Assigned to Phase 2 (Sakshi)."
      />
    </div>
  );
}
