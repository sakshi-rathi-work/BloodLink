import React, { useState, useEffect, useCallback } from "react";
import { getActivityLogs } from "../../api/activityLogs";
import { getErrorMessage } from "../../utils/errors";
import { formatDateTime } from "../../utils/format";
import Button from "../../components/ui/Button";
import Input from "../../components/ui/Input";
import Select from "../../components/ui/Select";
import Table from "../../components/ui/Table";
import Badge from "../../components/ui/Badge";
import Pagination from "../../components/ui/Pagination";
import Spinner from "../../components/ui/Spinner";
import EmptyState from "../../components/ui/EmptyState";
import ErrorBanner from "../../components/ui/ErrorBanner";
import Modal from "../../components/ui/Modal";
import { History, Search, FileJson, Calendar } from "lucide-react";

const ACTIONS = [
  { value: "", label: "All Actions" },
  { value: "create", label: "Create" },
  { value: "update", label: "Update" },
  { value: "delete", label: "Delete" },
  { value: "approve", label: "Approve" },
  { value: "reject", label: "Reject" },
  { value: "issue", label: "Issue" },
  { value: "prediction_run", label: "Prediction Run" },
];

const ENTITY_TYPES = [
  { value: "", label: "All Entity Types" },
  { value: "user", label: "User" },
  { value: "staff", label: "Staff" },
  { value: "requester", label: "Requester" },
  { value: "donor", label: "Donor" },
  { value: "blood_unit", label: "Blood Unit" },
  { value: "blood_request", label: "Blood Request" },
  { value: "donation_camp", label: "Donation Camp" },
  { value: "prediction_run", label: "Prediction Run" },
];

function getActionBadgeVariant(action) {
  switch (action) {
    case "create":
      return "available";
    case "update":
      return "info";
    case "delete":
      return "emergency";
    case "approve":
      return "approved";
    case "reject":
      return "rejected";
    case "issue":
      return "regular";
    case "prediction_run":
      return "warning";
    default:
      return "default";
  }
}

export default function ActivityLogPage() {
  const [logs, setLogs] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(25);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Filters
  const [actionFilter, setActionFilter] = useState("");
  const [entityFilter, setEntityFilter] = useState("");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");

  // Inspect details modal
  const [selectedLog, setSelectedLog] = useState(null);

  const fetchLogs = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params = { page, page_size: pageSize };
      if (actionFilter) params.action = actionFilter;
      if (entityFilter) params.entity_type = entityFilter;
      if (startDate) params.start_date = startDate;
      if (endDate) params.end_date = endDate;

      const data = await getActivityLogs(params);
      setLogs(data.items);
      setTotal(data.total);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }, [page, pageSize, actionFilter, entityFilter, startDate, endDate]);

  useEffect(() => {
    fetchLogs();
  }, [fetchLogs]);

  const handleSearch = (e) => {
    e.preventDefault();
    setPage(1);
    fetchLogs();
  };

  const handleResetFilters = () => {
    setActionFilter("");
    setEntityFilter("");
    setStartDate("");
    setEndDate("");
    setPage(1);
  };

  const hasActiveFilters = actionFilter || entityFilter || startDate || endDate;

  return (
    <div className="space-y-6">
      {/* Page Title */}
      <div>
        <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">System Activity Logs</h1>
        <p className="text-sm text-slate-500 mt-1">
          Complete, immutable audit trail of operational changes, inventory updates, and administrative events
        </p>
      </div>

      {error && <ErrorBanner message={error} onDismiss={() => setError(null)} />}

      {/* Filter Controls */}
      <div className="bg-white p-4 rounded-2xl border border-slate-200/80 shadow-sm space-y-3">
        <form onSubmit={handleSearch} className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
          <Select
            value={actionFilter}
            onChange={(e) => {
              setActionFilter(e.target.value);
              setPage(1);
            }}
            options={ACTIONS}
          />
          <Select
            value={entityFilter}
            onChange={(e) => {
              setEntityFilter(e.target.value);
              setPage(1);
            }}
            options={ENTITY_TYPES}
          />
          <Input
            type="date"
            placeholder="From Date"
            value={startDate}
            onChange={(e) => {
              setStartDate(e.target.value);
              setPage(1);
            }}
            icon={Calendar}
          />
          <Input
            type="date"
            placeholder="To Date"
            value={endDate}
            onChange={(e) => {
              setEndDate(e.target.value);
              setPage(1);
            }}
            icon={Calendar}
          />
          <div className="flex items-center gap-2">
            <Button type="submit" variant="secondary" icon={Search} className="w-full">
              Filter
            </Button>
            {hasActiveFilters && (
              <Button type="button" variant="ghost" onClick={handleResetFilters} className="text-xs text-blood-600">
                Reset
              </Button>
            )}
          </div>
        </form>
      </div>

      {/* Audit Log Table */}
      {loading ? (
        <div className="flex justify-center items-center py-24">
          <Spinner size="lg" />
        </div>
      ) : logs.length === 0 ? (
        <EmptyState
          icon={History}
          title="No activity logs found"
          description={
            hasActiveFilters
              ? "No system logs match the selected filter criteria."
              : "No activity has been logged in the system yet."
          }
          action={hasActiveFilters ? { label: "Clear Filters", onClick: handleResetFilters } : undefined}
        />
      ) : (
        <div className="space-y-4">
          <div className="text-xs text-slate-500 font-medium">
            Showing {logs.length} of {total} audit records
          </div>
          <Table headers={["Log ID", "Timestamp", "User", "Action", "Entity", "Entity ID", "Details"]}>
            {logs.map((log) => (
              <tr key={log.log_id} className="hover:bg-slate-50/75 transition-colors">
                <td className="py-3.5 px-4 font-mono text-xs text-slate-500">#{log.log_id}</td>
                <td className="py-3.5 px-4 text-xs text-slate-600 whitespace-nowrap">
                  {formatDateTime(log.created_at)}
                </td>
                <td className="py-3.5 px-4 text-xs font-semibold text-slate-900">
                  @{log.username}
                </td>
                <td className="py-3.5 px-4">
                  <Badge variant={getActionBadgeVariant(log.action)} size="sm">
                    {log.action}
                  </Badge>
                </td>
                <td className="py-3.5 px-4 text-xs font-mono text-slate-700">
                  {log.entity_type}
                </td>
                <td className="py-3.5 px-4 font-mono text-xs text-slate-500">
                  {log.entity_id != null ? `#${log.entity_id}` : "—"}
                </td>
                <td className="py-3.5 px-4">
                  {log.details && Object.keys(log.details).length > 0 ? (
                    <Button
                      variant="ghost"
                      size="sm"
                      icon={FileJson}
                      onClick={() => setSelectedLog(log)}
                      className="text-xs text-slate-600 hover:text-slate-900"
                    >
                      Inspect JSON
                    </Button>
                  ) : (
                    <span className="text-xs text-slate-400 italic">None</span>
                  )}
                </td>
              </tr>
            ))}
          </Table>
          <Pagination currentPage={page} totalItems={total} pageSize={pageSize} onPageChange={setPage} />
        </div>
      )}

      {/* Log Details Modal */}
      {selectedLog && (
        <Modal
          isOpen={!!selectedLog}
          onClose={() => setSelectedLog(null)}
          title={`Log #${selectedLog.log_id} — Payload Details`}
          maxWidth="max-w-xl"
        >
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-3 text-xs bg-slate-50 p-3.5 rounded-xl border border-slate-200">
              <div>
                <span className="text-slate-500">Performed By:</span>{" "}
                <span className="font-semibold text-slate-800">@{selectedLog.username}</span>
              </div>
              <div>
                <span className="text-slate-500">Timestamp:</span>{" "}
                <span className="font-mono text-slate-800">{formatDateTime(selectedLog.created_at)}</span>
              </div>
              <div>
                <span className="text-slate-500">Action:</span>{" "}
                <span className="font-semibold uppercase tracking-wider text-slate-800">{selectedLog.action}</span>
              </div>
              <div>
                <span className="text-slate-500">Target Entity:</span>{" "}
                <span className="font-mono text-slate-800">
                  {selectedLog.entity_type} {selectedLog.entity_id ? `(#${selectedLog.entity_id})` : ""}
                </span>
              </div>
            </div>

            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-slate-500 mb-1.5">
                Raw JSON Context
              </label>
              <pre className="p-4 bg-slate-900 text-emerald-400 text-xs font-mono rounded-xl overflow-x-auto max-h-80 border border-slate-800 leading-relaxed">
                {JSON.stringify(selectedLog.details, null, 2)}
              </pre>
            </div>

            <div className="flex justify-end pt-2">
              <Button variant="secondary" onClick={() => setSelectedLog(null)}>
                Close
              </Button>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
}
