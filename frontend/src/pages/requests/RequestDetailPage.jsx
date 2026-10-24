import React, { useState, useEffect, useCallback } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { getRequest, getRequestMatches, approveRequest, rejectRequest, issueRequest } from "../../api/requests";
import { formatDate } from "../../utils/format";
import { getErrorMessage } from "../../utils/errors";
import Badge from "../../components/ui/Badge";
import Button from "../../components/ui/Button";
import Spinner from "../../components/ui/Spinner";
import ErrorBanner from "../../components/ui/ErrorBanner";
import Table from "../../components/ui/Table";
import ConfirmDialog from "../../components/ui/ConfirmDialog";
import { ArrowLeft, CheckCircle, XCircle, Droplets, AlertTriangle } from "lucide-react";

const STATUS_VARIANT = {
  pending: "warning",
  approved: "info",
  issued: "success",
  rejected: "danger",
};

export default function RequestDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [request, setRequest] = useState(null);
  const [matches, setMatches] = useState(null);
  const [loading, setLoading] = useState(true);
  const [matchesLoading, setMatchesLoading] = useState(false);
  const [error, setError] = useState(null);
  const [actionLoading, setActionLoading] = useState(null); // 'approve' | 'reject' | 'issue'
  const [confirmAction, setConfirmAction] = useState(null); // { type, label, message }

  const loadRequest = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getRequest(id);
      setRequest(data);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }, [id]);

  const loadMatches = useCallback(async () => {
    setMatchesLoading(true);
    try {
      const data = await getRequestMatches(id);
      setMatches(data);
    } catch {
      // silently fail — matches are supplementary info
    } finally {
      setMatchesLoading(false);
    }
  }, [id]);

  useEffect(() => {
    loadRequest();
  }, [loadRequest]);

  useEffect(() => {
    if (request && (request.status === "pending" || request.status === "approved")) {
      loadMatches();
    }
  }, [request, loadMatches]);

  const executeAction = async (type) => {
    setActionLoading(type);
    setError(null);
    try {
      let updated;
      if (type === "approve") updated = await approveRequest(id);
      else if (type === "reject") updated = await rejectRequest(id);
      else if (type === "issue") updated = await issueRequest(id);
      setRequest(updated);
      setMatches(null);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setActionLoading(null);
      setConfirmAction(null);
    }
  };

  if (loading) {
    return <div className="flex justify-center items-center py-20"><Spinner size="lg" /></div>;
  }

  if (error && !request) {
    return (
      <div className="space-y-4">
        <Button variant="ghost" icon={ArrowLeft} onClick={() => navigate("/requests")}>Back to Queue</Button>
        <ErrorBanner message={error} />
      </div>
    );
  }

  const canApprove = request?.status === "pending";
  const canReject = request?.status === "pending" || request?.status === "approved";
  const canIssue = request?.status === "approved";

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <button
          onClick={() => navigate("/requests")}
          className="p-2 rounded-xl text-slate-400 hover:text-slate-700 hover:bg-slate-100 transition-colors"
          aria-label="Back to queue"
        >
          <ArrowLeft size={18} />
        </button>
        <div>
          <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">
            Request #{request.request_id}
          </h1>
          <p className="text-sm text-slate-500 mt-0.5">
            From {request.requester_name} — submitted {formatDate(request.request_date)}
          </p>
        </div>
      </div>

      {error && <ErrorBanner message={error} onDismiss={() => setError(null)} />}

      {/* Summary Card */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 space-y-5">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-xl bg-blood-100 text-blood-700 flex items-center justify-center font-bold text-lg">
              {request.blood_group}
            </div>
            <div>
              <p className="text-xl font-bold text-slate-900">{request.quantity} unit{request.quantity !== 1 ? "s" : ""}</p>
              <p className="text-xs text-slate-500 capitalize">{request.urgency} · {request.issued_count}/{request.quantity} issued</p>
            </div>
          </div>
          <Badge variant={STATUS_VARIANT[request.status] || "default"}>
            {request.status.charAt(0).toUpperCase() + request.status.slice(1)}
          </Badge>
        </div>

        {/* Detail grid */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {[
            { label: "Blood Group", value: request.blood_group },
            { label: "Urgency", value: request.urgency },
            { label: "Requester", value: request.requester_name },
            { label: "Date", value: formatDate(request.request_date) },
          ].map(({ label, value }) => (
            <div key={label} className="p-3 rounded-xl bg-slate-50 border border-slate-100">
              <span className="text-xs font-semibold text-slate-400 block mb-1">{label}</span>
              <span className="text-sm font-semibold text-slate-800 capitalize">{value}</span>
            </div>
          ))}
        </div>

        {/* Action Buttons */}
        {(canApprove || canReject || canIssue) && (
          <div className="border-t border-slate-100 pt-4 flex flex-wrap items-center gap-3">
            {canApprove && (
              <Button
                id="approve-btn"
                variant="primary"
                icon={CheckCircle}
                loading={actionLoading === "approve"}
                disabled={!!actionLoading}
                onClick={() => setConfirmAction({
                  type: "approve",
                  label: "Approve Request",
                  message: `Are you sure you want to approve request #${request.request_id} for ${request.quantity} unit(s) of ${request.blood_group}?`,
                })}
              >
                Approve
              </Button>
            )}
            {canIssue && (
              <Button
                id="issue-btn"
                variant="primary"
                icon={Droplets}
                loading={actionLoading === "issue"}
                disabled={!!actionLoading}
                onClick={() => setConfirmAction({
                  type: "issue",
                  label: "Issue Blood Units",
                  message: `Issue ${request.quantity} unit(s) of ${request.blood_group} for request #${request.request_id}? This action cannot be undone.`,
                })}
              >
                Issue Units
              </Button>
            )}
            {canReject && (
              <Button
                id="reject-btn"
                variant="danger"
                icon={XCircle}
                loading={actionLoading === "reject"}
                disabled={!!actionLoading}
                onClick={() => setConfirmAction({
                  type: "reject",
                  label: "Reject Request",
                  message: `Reject request #${request.request_id} from ${request.requester_name}? This will set the status to rejected.`,
                })}
              >
                Reject
              </Button>
            )}
          </div>
        )}
      </div>

      {/* Candidate Units (Matches) */}
      {(request.status === "pending" || request.status === "approved") && (
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
          <div className="p-4 border-b border-slate-100 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Droplets size={16} className="text-blood-500" />
              <h2 className="text-sm font-bold text-slate-700">Compatible Stock Preview</h2>
            </div>
            {matchesLoading && <Spinner size="sm" />}
          </div>

          {matches && !matchesLoading ? (
            <div className="p-4 space-y-3">
              <div className="flex items-center gap-4 text-xs text-slate-600">
                <span>
                  Available: <strong className={matches.sufficient ? "text-green-700" : "text-red-600"}>
                    {matches.available_compatible_count}
                  </strong> compatible unit{matches.available_compatible_count !== 1 ? "s" : ""}
                </span>
                <span>Needed: <strong>{matches.quantity}</strong></span>
                {!matches.sufficient && (
                  <span className="flex items-center gap-1 text-amber-600 font-semibold">
                    <AlertTriangle size={12} /> Insufficient stock
                  </span>
                )}
              </div>
              {matches.units.length > 0 ? (
                <Table headers={["Unit ID", "Blood Group", "Collection Date", "Expiry Date", "Days to Expiry"]}>
                  {matches.units.slice(0, 10).map((unit) => (
                    <tr
                      key={unit.unit_id}
                      className={`hover:bg-slate-50/75 ${matches.allocation_preview_unit_ids.includes(unit.unit_id) ? "bg-green-50/60" : ""}`}
                    >
                      <td className="py-2.5 px-4 font-mono text-xs text-slate-600">#{unit.unit_id}</td>
                      <td className="py-2.5 px-4">
                        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-bold bg-blood-100 text-blood-800 border border-blood-200">
                          {unit.blood_group}
                        </span>
                      </td>
                      <td className="py-2.5 px-4 text-xs text-slate-600">{formatDate(unit.collection_date)}</td>
                      <td className="py-2.5 px-4 text-xs text-slate-600">{formatDate(unit.expiry_date)}</td>
                      <td className="py-2.5 px-4 text-xs font-semibold">
                        <span className={unit.days_to_expiry <= 7 ? "text-red-600" : unit.days_to_expiry <= 14 ? "text-amber-600" : "text-green-700"}>
                          {unit.days_to_expiry}d
                        </span>
                      </td>
                    </tr>
                  ))}
                </Table>
              ) : (
                <p className="text-xs text-slate-400 text-center py-4">No compatible units available in inventory.</p>
              )}
            </div>
          ) : !matchesLoading && (
            <p className="text-xs text-slate-400 text-center py-6">Loading stock preview...</p>
          )}
        </div>
      )}

      {/* Issued Units */}
      {request.issued_units && request.issued_units.length > 0 && (
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
          <div className="p-4 border-b border-slate-100 flex items-center gap-2">
            <Droplets size={16} className="text-green-500" />
            <h2 className="text-sm font-bold text-slate-700">Issued Blood Units</h2>
          </div>
          <Table headers={["Unit ID", "Blood Group", "Issue Date", "Issued By"]}>
            {request.issued_units.map((unit) => (
              <tr key={unit.issue_id} className="hover:bg-slate-50/75">
                <td className="py-3 px-4 font-mono text-xs text-slate-600">#{unit.unit_id}</td>
                <td className="py-3 px-4">
                  <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-bold bg-blood-100 text-blood-800 border border-blood-200">
                    {unit.blood_group}
                  </span>
                </td>
                <td className="py-3 px-4 text-xs text-slate-600">{formatDate(unit.issue_date)}</td>
                <td className="py-3 px-4 text-xs text-slate-700 font-medium">{unit.issued_by_name}</td>
              </tr>
            ))}
          </Table>
        </div>
      )}

      {/* Confirm Dialog */}
      {confirmAction && (
        <ConfirmDialog
          isOpen={!!confirmAction}
          title={confirmAction.label}
          message={confirmAction.message}
          confirmText={confirmAction.label}
          onConfirm={() => executeAction(confirmAction.type)}
          onClose={() => setConfirmAction(null)}
          loading={!!actionLoading}
          confirmVariant={confirmAction.type === "reject" ? "danger" : "primary"}
        />
      )}
    </div>
  );
}
