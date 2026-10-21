import React from "react";
import { AlertCircle, RefreshCw } from "lucide-react";
import Button from "./Button";

export default function ErrorBanner({
  message = "Failed to load data.",
  onRetry,
  className = "",
}) {
  return (
    <div
      className={`flex flex-col sm:flex-row items-center justify-between gap-4 p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-900 ${className}`}
    >
      <div className="flex items-center gap-3">
        <AlertCircle className="w-5 h-5 text-rose-600 flex-shrink-0" />
        <span className="text-sm font-medium">{message}</span>
      </div>

      {onRetry && (
        <Button
          variant="outline"
          size="sm"
          onClick={onRetry}
          className="border-rose-300 text-rose-700 hover:bg-rose-100 flex-shrink-0"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          Retry
        </Button>
      )}
    </div>
  );
}
