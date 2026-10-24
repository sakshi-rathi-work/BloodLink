import React, { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { getRequest } from "../../api/requests";
import { formatDate } from "../../utils/format";
import { getErrorMessage } from "../../utils/errors";
import Badge from "../../components/ui/Badge";
import Button from "../../components/ui/Button";
import Spinner from "../../components/ui/Spinner";
import ErrorBanner from "../../components/ui/ErrorBanner";
import Table from "../../components/ui/Table";
import { ArrowLeft, ClipboardList, Droplets } from "lucide-react";

const STATUS_VARIANT = {
  pending: "warning",
  approved: "info",
  issued: "success",
  rejected: "danger",
};

export default function MyRequestDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [request, setRequest] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function load() {
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
    }
    load();
  }, [id]);

  if (loading) {
    return <div className="flex justify-center items-center py-20"><Spinner size="lg" /></div>;
  }

  if (error) {
    return (
      <div className="space-y-4">
        <Button variant="ghost" icon={ArrowLeft} onClick={() => navigate("/my/requests")}>Back</Button>
        <ErrorBanner message={error} />
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <button
          onClick={() => navigate("/my/requests")}
          className="p-2 rounded-xl text-slate-400 hover:text-slate-700 hover:bg-slate-100 transition-colors"
          aria-label="Back to requests"
        >
          <ArrowLeft size={18} />
        </button>
        <div>
          <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">
            Request #{request.request_id}
          </h1>
          <p className="text-sm text-slate-500 mt-0.5">Submitted on {formatDate(request.request_date)}</p>
        </div>
      </div>

      {/* Summary Card */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-11 h-11 rounded-xl bg-blood-100 text-blood-700 flex items-center justify-center font-bold">
              {request.blood_group}
            </div>
            <div>
              <p className="text-lg font-bold text-slate-900">{request.quantity} unit{request.quantity !== 1 ? "s" : ""} requested</p>
              <p className="text-xs text-slate-500">{request.issued_count} of {request.quantity} unit{request.quantity !== 1 ? "s" : ""} issued</p>
            </div>
          </div>
          <Badge variant={STATUS_VARIANT[request.status] || "default"}>
            {request.status.charAt(0).toUpperCase() + request.status.slice(1)}
          </Badge>
        </div>

        <div className="grid grid-cols-2 gap-3 pt-2 border-t border-slate-100">
          <div className="p-3 rounded-xl bg-slate-50 border border-slate-100">
            <span className="text-xs font-semibold text-slate-400 block mb-1">Blood Group</span>
            <span className="text-sm font-bold text-blood-700">{request.blood_group}</span>
          </div>
          <div className="p-3 rounded-xl bg-slate-50 border border-slate-100">
            <span className="text-xs font-semibold text-slate-400 block mb-1">Urgency</span>
            <Badge variant={request.urgency === "emergency" ? "danger" : "info"} size="sm">
              {request.urgency}
            </Badge>
          </div>
          <div className="p-3 rounded-xl bg-slate-50 border border-slate-100">
            <span className="text-xs font-semibold text-slate-400 block mb-1">Request Date</span>
            <span className="text-sm font-semibold text-slate-700">{formatDate(request.request_date)}</span>
          </div>
          <div className="p-3 rounded-xl bg-slate-50 border border-slate-100">
            <span className="text-xs font-semibold text-slate-400 block mb-1">Units Issued</span>
            <span className="text-sm font-bold text-slate-700">{request.issued_count} / {request.quantity}</span>
          </div>
        </div>
      </div>

      {/* Issued Units */}
      {request.issued_units && request.issued_units.length > 0 && (
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
          <div className="p-4 border-b border-slate-100 flex items-center gap-2">
            <Droplets size={16} className="text-blood-500" />
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

      {/* Status timeline hint */}
      {request.status === "pending" && (
        <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 text-sm text-amber-800 flex items-start gap-3">
          <ClipboardList size={18} className="mt-0.5 shrink-0 text-amber-500" />
          <div>
            <p className="font-semibold">Awaiting Review</p>
            <p className="text-xs text-amber-700 mt-0.5">Our staff will review your request and approve or reject it shortly.</p>
          </div>
        </div>
      )}
      {request.status === "approved" && (
        <div className="bg-blue-50 border border-blue-200 rounded-xl p-4 text-sm text-blue-800 flex items-start gap-3">
          <ClipboardList size={18} className="mt-0.5 shrink-0 text-blue-500" />
          <div>
            <p className="font-semibold">Request Approved</p>
            <p className="text-xs text-blue-700 mt-0.5">Your request has been approved and units will be issued when stock is available.</p>
          </div>
        </div>
      )}
    </div>
  );
}
