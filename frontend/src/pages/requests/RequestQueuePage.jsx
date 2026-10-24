import React, { useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { getRequests } from "../../api/requests";
import { BLOOD_GROUPS, REQUEST_STATUSES, URGENCIES } from "../../utils/constants";
import { formatDate } from "../../utils/format";
import { getErrorMessage } from "../../utils/errors";
import Button from "../../components/ui/Button";
import Select from "../../components/ui/Select";
import Table from "../../components/ui/Table";
import Badge from "../../components/ui/Badge";
import Pagination from "../../components/ui/Pagination";
import Spinner from "../../components/ui/Spinner";
import EmptyState from "../../components/ui/EmptyState";
import ErrorBanner from "../../components/ui/ErrorBanner";
import { ClipboardList, Eye } from "lucide-react";

const STATUS_VARIANT = {
  pending: "warning",
  approved: "info",
  issued: "success",
  rejected: "danger",
};

export default function RequestQueuePage() {
  const navigate = useNavigate();
  const [requests, setRequests] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(20);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [statusFilter, setStatusFilter] = useState("");
  const [bloodGroupFilter, setBloodGroupFilter] = useState("");
  const [urgencyFilter, setUrgencyFilter] = useState("");
  const [sortBy, setSortBy] = useState("priority");

  const fetchRequests = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params = { page, page_size: pageSize, sort: sortBy };
      if (statusFilter) params.status = statusFilter;
      if (bloodGroupFilter) params.blood_group = bloodGroupFilter;
      if (urgencyFilter) params.urgency = urgencyFilter;
      const data = await getRequests(params);
      setRequests(data.items);
      setTotal(data.total);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }, [page, pageSize, statusFilter, bloodGroupFilter, urgencyFilter, sortBy]);

  useEffect(() => { fetchRequests(); }, [fetchRequests]);

  const handleReset = () => {
    setStatusFilter("");
    setBloodGroupFilter("");
    setUrgencyFilter("");
    setSortBy("priority");
    setPage(1);
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">Blood Request Queue</h1>
        <p className="text-sm text-slate-500 mt-1">
          Review incoming blood requests — approve, reject, or issue units
        </p>
      </div>

      {error && <ErrorBanner message={error} onDismiss={() => setError(null)} />}

      {/* Filters */}
      <div className="bg-white p-4 rounded-2xl border border-slate-200/80 shadow-sm space-y-3">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          <Select
            value={statusFilter}
            onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }}
            options={[
              { value: "", label: "All Statuses" },
              ...REQUEST_STATUSES.map((s) => ({ value: s.value, label: s.label })),
            ]}
          />
          <Select
            value={bloodGroupFilter}
            onChange={(e) => { setBloodGroupFilter(e.target.value); setPage(1); }}
            options={[
              { value: "", label: "All Blood Groups" },
              ...BLOOD_GROUPS.map((bg) => ({ value: bg, label: `Group ${bg}` })),
            ]}
          />
          <Select
            value={urgencyFilter}
            onChange={(e) => { setUrgencyFilter(e.target.value); setPage(1); }}
            options={[
              { value: "", label: "All Urgencies" },
              ...URGENCIES.map((u) => ({ value: u.value, label: u.label })),
            ]}
          />
          <Select
            value={sortBy}
            onChange={(e) => { setSortBy(e.target.value); setPage(1); }}
            options={[
              { value: "priority", label: "Sort: Priority (Emergency First)" },
              { value: "newest", label: "Sort: Newest First" },
            ]}
          />
        </div>
        {(statusFilter || bloodGroupFilter || urgencyFilter || sortBy !== "priority") && (
          <div className="flex justify-end">
            <button onClick={handleReset} className="text-xs font-semibold text-blood-600 hover:text-blood-700 underline">
              Reset Filters
            </button>
          </div>
        )}
      </div>

      {/* Content */}
      {loading ? (
        <div className="flex justify-center items-center py-20"><Spinner size="lg" /></div>
      ) : requests.length === 0 ? (
        <EmptyState
          icon={ClipboardList}
          title="No requests found"
          description={
            statusFilter || bloodGroupFilter || urgencyFilter
              ? "No requests match your filters."
              : "No blood requests have been submitted yet."
          }
          action={statusFilter || bloodGroupFilter || urgencyFilter ? { label: "Clear Filters", onClick: handleReset } : undefined}
        />
      ) : (
        <div className="space-y-4">
          <div className="text-xs text-slate-500 font-medium">{total} request{total !== 1 ? "s" : ""} found</div>
          <Table
            headers={["ID", "Requester", "Blood Group", "Qty", "Urgency", "Status", "Date", "Issued", "Actions"]}
          >
            {requests.map((req) => (
              <tr key={req.request_id} className="hover:bg-slate-50/75 transition-colors">
                <td className="py-3.5 px-4 font-mono text-xs text-slate-500">#{req.request_id}</td>
                <td className="py-3.5 px-4 text-sm font-semibold text-slate-800">{req.requester_name}</td>
                <td className="py-3.5 px-4">
                  <span className="inline-flex items-center px-2.5 py-1 rounded-md text-xs font-bold bg-blood-100 text-blood-800 border border-blood-200">
                    {req.blood_group}
                  </span>
                </td>
                <td className="py-3.5 px-4 text-sm font-bold text-slate-800">{req.quantity}</td>
                <td className="py-3.5 px-4">
                  <Badge variant={req.urgency === "emergency" ? "danger" : "info"} size="sm">
                    {req.urgency}
                  </Badge>
                </td>
                <td className="py-3.5 px-4">
                  <Badge variant={STATUS_VARIANT[req.status] || "default"} size="sm">
                    {req.status}
                  </Badge>
                </td>
                <td className="py-3.5 px-4 text-xs text-slate-600">{formatDate(req.request_date)}</td>
                <td className="py-3.5 px-4 text-xs font-semibold text-slate-700">{req.issued_count}/{req.quantity}</td>
                <td className="py-3.5 px-4">
                  <Button
                    variant="ghost"
                    size="sm"
                    icon={Eye}
                    onClick={() => navigate(`/requests/${req.request_id}`)}
                  >
                    Manage
                  </Button>
                </td>
              </tr>
            ))}
          </Table>
          <Pagination currentPage={page} totalItems={total} pageSize={pageSize} onPageChange={setPage} />
        </div>
      )}
    </div>
  );
}
