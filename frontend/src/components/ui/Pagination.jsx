import React from "react";
import Button from "./Button";
import { ChevronLeft, ChevronRight } from "lucide-react";

export default function Pagination({
  page = 1,
  currentPage,
  pageSize = 20,
  total,
  totalItems,
  onPageChange,
  className = "",
}) {
  const activePage = currentPage ?? page;
  const totalCount = totalItems ?? total ?? 0;
  const totalPages = Math.max(1, Math.ceil(totalCount / pageSize));
  const startItem = totalCount === 0 ? 0 : (activePage - 1) * pageSize + 1;
  const endItem = Math.min(activePage * pageSize, totalCount);

  return (
    <div className={`flex flex-col sm:flex-row items-center justify-between gap-4 py-3 px-2 ${className}`}>
      <div className="text-xs text-slate-500 font-medium">
        Showing <span className="font-semibold text-slate-700">{startItem}</span> to{" "}
        <span className="font-semibold text-slate-700">{endItem}</span> of{" "}
        <span className="font-semibold text-slate-700">{totalCount}</span> results
      </div>

      <div className="flex items-center gap-2">
        <Button
          variant="secondary"
          size="sm"
          onClick={() => onPageChange?.(activePage - 1)}
          disabled={activePage <= 1}
        >
          <ChevronLeft className="w-4 h-4" />
          Previous
        </Button>

        <span className="text-xs font-semibold text-slate-600 px-2">
          Page {activePage} of {totalPages}
        </span>

        <Button
          variant="secondary"
          size="sm"
          onClick={() => onPageChange?.(activePage + 1)}
          disabled={activePage >= totalPages}
        >
          Next
          <ChevronRight className="w-4 h-4" />
        </Button>
      </div>
    </div>
  );
}
