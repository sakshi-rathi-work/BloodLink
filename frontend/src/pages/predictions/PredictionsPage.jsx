import React from "react";
import EmptyState from "../../components/ui/EmptyState";
import { TrendingUp } from "lucide-react";

export default function PredictionsPage() {
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">Shortage Predictions & Analytics</h1>
      <EmptyState
        icon={TrendingUp}
        title="Predictive Forecasting Engine"
        description="Assigned to Phase 4 (Saee)."
      />
    </div>
  );
}
