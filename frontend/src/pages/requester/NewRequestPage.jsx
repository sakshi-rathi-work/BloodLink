import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { createRequest } from "../../api/requests";
import { BLOOD_GROUPS, URGENCIES } from "../../utils/constants";
import { getErrorMessage } from "../../utils/errors";
import Button from "../../components/ui/Button";
import Select from "../../components/ui/Select";
import Input from "../../components/ui/Input";
import ErrorBanner from "../../components/ui/ErrorBanner";
import { PlusCircle, ArrowLeft } from "lucide-react";

export default function NewRequestPage() {
  const navigate = useNavigate();
  const [bloodGroup, setBloodGroup] = useState("");
  const [quantity, setQuantity] = useState(1);
  const [urgency, setUrgency] = useState("routine");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!bloodGroup) {
      setError("Please select a blood group.");
      return;
    }
    if (quantity < 1 || quantity > 10) {
      setError("Quantity must be between 1 and 10 units.");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const created = await createRequest({ blood_group: bloodGroup, quantity: Number(quantity), urgency });
      navigate(`/my/requests/${created.request_id}`);
    } catch (err) {
      setError(getErrorMessage(err));
      setLoading(false);
    }
  };

  return (
    <div className="max-w-lg mx-auto space-y-6">
      <div className="flex items-center gap-3">
        <button
          onClick={() => navigate("/my/requests")}
          className="p-2 rounded-xl text-slate-400 hover:text-slate-700 hover:bg-slate-100 transition-colors"
          aria-label="Back to requests"
        >
          <ArrowLeft size={18} />
        </button>
        <div>
          <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">Submit New Blood Request</h1>
          <p className="text-sm text-slate-500 mt-0.5">Fill in the details below and we&apos;ll process your request</p>
        </div>
      </div>

      {error && <ErrorBanner message={error} onDismiss={() => setError(null)} />}

      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6">
        <form id="new-request-form" onSubmit={handleSubmit} className="space-y-5">
          <div>
            <label className="block text-sm font-semibold text-slate-700 mb-1.5" htmlFor="blood-group-select">
              Blood Group Required <span className="text-blood-500">*</span>
            </label>
            <Select
              id="blood-group-select"
              value={bloodGroup}
              onChange={(e) => setBloodGroup(e.target.value)}
              options={[
                { value: "", label: "Select blood group..." },
                ...BLOOD_GROUPS.map((bg) => ({ value: bg, label: `${bg}` })),
              ]}
            />
          </div>

          <div>
            <label className="block text-sm font-semibold text-slate-700 mb-1.5" htmlFor="quantity-input">
              Quantity (units) <span className="text-blood-500">*</span>
            </label>
            <Input
              id="quantity-input"
              type="number"
              min={1}
              max={10}
              value={quantity}
              onChange={(e) => setQuantity(e.target.value)}
              placeholder="Number of units needed"
            />
            <p className="text-xs text-slate-400 mt-1">Maximum 10 units per request</p>
          </div>

          <div>
            <label className="block text-sm font-semibold text-slate-700 mb-1.5" htmlFor="urgency-select">
              Urgency <span className="text-blood-500">*</span>
            </label>
            <Select
              id="urgency-select"
              value={urgency}
              onChange={(e) => setUrgency(e.target.value)}
              options={URGENCIES.map((u) => ({ value: u.value, label: u.label }))}
            />
            <p className="text-xs text-slate-400 mt-1">
              Emergency requests are prioritized over routine requests
            </p>
          </div>

          <div className="border-t border-slate-100 pt-4 flex items-center justify-end gap-3">
            <Button
              type="button"
              variant="secondary"
              onClick={() => navigate("/my/requests")}
              disabled={loading}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              variant="primary"
              icon={PlusCircle}
              loading={loading}
              disabled={loading || !bloodGroup}
            >
              Submit Request
            </Button>
          </div>
        </form>
      </div>

      {/* Info box */}
      <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 text-sm text-amber-800">
        <p className="font-semibold mb-1">What happens next?</p>
        <ol className="list-decimal list-inside space-y-1 text-xs text-amber-700">
          <li>Your request is submitted with <strong>Pending</strong> status.</li>
          <li>Our staff will review and <strong>Approve</strong> or <strong>Reject</strong> it.</li>
          <li>Once approved, available blood units are allocated and marked <strong>Issued</strong>.</li>
        </ol>
      </div>
    </div>
  );
}
