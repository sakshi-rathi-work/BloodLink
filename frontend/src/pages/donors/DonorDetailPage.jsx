import React, { useState, useEffect, useCallback } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { getDonor, recordDonation, getDonationHistory, deleteDonor } from "../../api/donors";
import { formatDate } from "../../utils/format";
import { getErrorMessage } from "../../utils/errors";
import { useAuth } from "../../context/AuthContext";
import { useToast } from "../../context/ToastContext";
import Button from "../../components/ui/Button";
import Badge from "../../components/ui/Badge";
import Table from "../../components/ui/Table";
import Modal from "../../components/ui/Modal";
import ConfirmDialog from "../../components/ui/ConfirmDialog";
import Spinner from "../../components/ui/Spinner";
import ErrorBanner from "../../components/ui/ErrorBanner";
import EmptyState from "../../components/ui/EmptyState";
import {
  ArrowLeft,
  Edit,
  Trash2,
  Heart,
  Droplet,
  CheckCircle2,
  XCircle,
  Calendar,
  Clock,
  Phone,
  MapPin,
  Scale,
  Award,
} from "lucide-react";

export default function DonorDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { role } = useAuth();
  const toast = useToast();

  const [donor, setDonor] = useState(null);
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Modals
  const [donationModalOpen, setDonationModalOpen] = useState(false);
  const [recordingDonation, setRecordingDonation] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [deleting, setDeleting] = useState(false);

  const fetchDonorData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [donorData, historyData] = await Promise.all([
        getDonor(id),
        getDonationHistory(id),
      ]);
      setDonor(donorData);
      setHistory(historyData);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    fetchDonorData();
  }, [fetchDonorData]);

  const handleRecordDonation = async () => {
    setRecordingDonation(true);
    try {
      const unit = await recordDonation(id);
      toast.success(
        `Blood unit #${unit.unit_id} (${unit.blood_group}) recorded with 42-day shelf life.`
      );
      setDonationModalOpen(false);
      await fetchDonorData();
    } catch (err) {
      toast.error(getErrorMessage(err));
    } finally {
      setRecordingDonation(false);
    }
  };

  const handleDeleteDonor = async () => {
    setDeleting(true);
    try {
      await deleteDonor(id);
      toast.success("Donor deleted successfully.");
      navigate("/donors");
    } catch (err) {
      toast.error(getErrorMessage(err));
      setDeleteDialogOpen(false);
    } finally {
      setDeleting(false);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center py-20">
        <Spinner size="lg" />
      </div>
    );
  }

  if (!donor) {
    return (
      <div className="space-y-4">
        <Button variant="ghost" size="sm" icon={ArrowLeft} onClick={() => navigate("/donors")}>
          Back to Donors
        </Button>
        <ErrorBanner message={error || "Donor not found."} />
      </div>
    );
  }

  const isEligible = donor.eligibility?.eligible;
  const reasons = donor.eligibility?.reasons || [];
  const daysUntilEligible = donor.eligibility?.days_until_eligible;

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      {/* Top Navigation & Actions Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div className="flex items-center gap-3">
          <Button
            variant="ghost"
            size="sm"
            icon={ArrowLeft}
            onClick={() => navigate("/donors")}
          >
            Donors
          </Button>
          <div className="h-6 w-px bg-slate-200" />
          <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight flex items-center gap-3">
            {donor.name}
            {donor.is_regular && (
              <Badge variant="regular" size="sm">
                Regular Donor
              </Badge>
            )}
          </h1>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="secondary"
            size="sm"
            icon={Edit}
            onClick={() => navigate(`/donors/${id}/edit`)}
          >
            Edit Profile
          </Button>

          {role === "admin" && (
            <Button
              variant="danger"
              size="sm"
              icon={Trash2}
              onClick={() => setDeleteDialogOpen(true)}
            >
              Delete
            </Button>
          )}
        </div>
      </div>

      {error && <ErrorBanner message={error} onDismiss={() => setError(null)} />}

      {/* Grid: Demographics Card + Eligibility Card */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Demographics Card (2 Cols) */}
        <div className="lg:col-span-2 bg-white p-6 rounded-2xl border border-slate-200/80 shadow-sm space-y-6">
          <div className="flex items-center justify-between border-b border-slate-100 pb-4">
            <h2 className="text-base font-bold text-slate-900">Demographic & Contact Details</h2>
            <span className="inline-flex items-center px-3 py-1 rounded-xl text-base font-extrabold bg-blood-100 text-blood-800 border border-blood-200 shadow-sm">
              <Droplet className="w-4 h-4 mr-1 text-blood-600 fill-blood-600" />
              {donor.blood_group}
            </span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-y-4 gap-x-6 text-sm">
            <div>
              <span className="block text-xs font-semibold text-slate-400 uppercase tracking-wider">
                Full Name
              </span>
              <span className="font-semibold text-slate-900 mt-0.5 block">{donor.name}</span>
            </div>

            <div>
              <span className="block text-xs font-semibold text-slate-400 uppercase tracking-wider">
                Gender & Date of Birth
              </span>
              <span className="font-semibold text-slate-900 mt-0.5 block capitalize">
                {donor.gender} · {formatDate(donor.dob)}
              </span>
            </div>

            <div>
              <span className="block text-xs font-semibold text-slate-400 uppercase tracking-wider">
                Weight
              </span>
              <span className="font-semibold text-slate-900 mt-0.5 flex items-center gap-1.5">
                <Scale className="w-4 h-4 text-slate-400" />
                {donor.weight} kg
              </span>
            </div>

            <div>
              <span className="block text-xs font-semibold text-slate-400 uppercase tracking-wider">
                Contact Phone
              </span>
              <span className="font-semibold text-slate-900 mt-0.5 flex items-center gap-1.5">
                <Phone className="w-4 h-4 text-slate-400" />
                {donor.phone}
              </span>
            </div>

            <div className="sm:col-span-2">
              <span className="block text-xs font-semibold text-slate-400 uppercase tracking-wider">
                Address
              </span>
              <span className="font-medium text-slate-800 mt-0.5 flex items-start gap-1.5">
                <MapPin className="w-4 h-4 text-slate-400 mt-0.5 flex-shrink-0" />
                {donor.address}
              </span>
            </div>

            <div>
              <span className="block text-xs font-semibold text-slate-400 uppercase tracking-wider">
                Last Donation Date
              </span>
              <span className="font-semibold text-slate-900 mt-0.5 flex items-center gap-1.5">
                <Calendar className="w-4 h-4 text-slate-400" />
                {formatDate(donor.last_donation_date)}
              </span>
            </div>

            <div>
              <span className="block text-xs font-semibold text-slate-400 uppercase tracking-wider">
                Total Completed Donations
              </span>
              <span className="font-semibold text-slate-900 mt-0.5 flex items-center gap-1.5">
                <Award className="w-4 h-4 text-purple-600" />
                {donor.donation_count} units
              </span>
            </div>
          </div>
        </div>

        {/* Live Eligibility Card (1 Col) */}
        <div
          className={`p-6 rounded-2xl border shadow-sm flex flex-col justify-between transition-all ${
            isEligible
              ? "bg-emerald-50/50 border-emerald-200/80"
              : "bg-rose-50/40 border-rose-200/80"
          }`}
        >
          <div className="space-y-4">
            <div className="flex items-center gap-2">
              {isEligible ? (
                <CheckCircle2 className="w-6 h-6 text-emerald-600 flex-shrink-0" />
              ) : (
                <XCircle className="w-6 h-6 text-rose-600 flex-shrink-0" />
              )}
              <h2
                className={`text-base font-bold ${
                  isEligible ? "text-emerald-900" : "text-rose-900"
                }`}
              >
                {isEligible ? "Eligible to Donate" : "Ineligible to Donate"}
              </h2>
            </div>

            {isEligible ? (
              <p className="text-xs text-emerald-800 leading-relaxed">
                This donor meets all clinical requirements: age between 18–65, weight ≥ 50 kg, and at least 90 days have elapsed since their last donation.
              </p>
            ) : (
              <div className="space-y-2">
                <p className="text-xs font-semibold text-rose-800">
                  Transfusion safety guidelines prohibit blood collection for the following reason(s):
                </p>
                <ul className="text-xs text-rose-700 space-y-1.5 pl-4 list-disc">
                  {reasons.map((r, idx) => (
                    <li key={idx} className="font-medium">
                      {r}
                    </li>
                  ))}
                </ul>
                {daysUntilEligible && (
                  <div className="mt-3 p-2.5 bg-rose-100/60 rounded-xl text-xs font-bold text-rose-900 flex items-center gap-2">
                    <Clock className="w-4 h-4 text-rose-700" />
                    Eligible in {daysUntilEligible} day(s)
                  </div>
                )}
              </div>
            )}
          </div>

          <div className="pt-6">
            <Button
              variant="blood"
              className="w-full justify-center shadow-md shadow-blood-600/20"
              icon={Heart}
              disabled={!isEligible}
              onClick={() => setDonationModalOpen(true)}
              title={
                !isEligible
                  ? "Donation disabled: Donor does not satisfy eligibility criteria"
                  : "Collect blood unit from this donor"
              }
            >
              Record Donation
            </Button>
            {!isEligible && (
              <p className="text-center text-[11px] text-slate-500 mt-2 font-medium">
                Disabled due to clinical eligibility rules
              </p>
            )}
          </div>
        </div>
      </div>

      {/* Donation History Section */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-bold text-slate-900">Donation History</h2>
          <span className="text-xs text-slate-500">
            {history.length} unit(s) collected
          </span>
        </div>

        {history.length === 0 ? (
          <EmptyState
            icon={Heart}
            title="No donations recorded"
            description="This donor has not completed any blood collections yet."
            action={
              isEligible
                ? {
                    label: "Record First Donation",
                    onClick: () => setDonationModalOpen(true),
                  }
                : undefined
            }
          />
        ) : (
          <Table
            headers={[
              "Unit ID",
              "Blood Group",
              "Collection Date",
              "Expiry Date",
              "Shelf Life Status",
              "Days to Expiry",
            ]}
          >
            {history.map((unit) => (
              <tr key={unit.unit_id} className="hover:bg-slate-50/75 transition-colors">
                <td className="py-3.5 px-4 font-mono font-bold text-xs text-slate-900">
                  #{unit.unit_id}
                </td>
                <td className="py-3.5 px-4">
                  <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-bold bg-blood-50 text-blood-800 border border-blood-200">
                    {unit.blood_group}
                  </span>
                </td>
                <td className="py-3.5 px-4 text-xs text-slate-600 font-medium">
                  {formatDate(unit.collection_date)}
                </td>
                <td className="py-3.5 px-4 text-xs text-slate-600 font-medium">
                  {formatDate(unit.expiry_date)}
                </td>
                <td className="py-3.5 px-4">
                  <Badge variant={unit.status} size="sm">
                    {unit.status.toUpperCase()}
                  </Badge>
                </td>
                <td className="py-3.5 px-4 text-xs font-semibold">
                  {unit.status === "available" ? (
                    unit.days_to_expiry <= 7 ? (
                      <span className="text-rose-600 font-bold">
                        {unit.days_to_expiry} day(s) (Expiring Soon)
                      </span>
                    ) : (
                      <span className="text-emerald-700">
                        {unit.days_to_expiry} day(s) remaining
                      </span>
                    )
                  ) : (
                    <span className="text-slate-400">—</span>
                  )}
                </td>
              </tr>
            ))}
          </Table>
        )}
      </div>

      {/* Record Donation Confirmation Modal */}
      <Modal
        isOpen={donationModalOpen}
        onClose={() => setDonationModalOpen(false)}
        title="Confirm Blood Collection"
        maxWidth="max-w-md"
      >
        <div className="space-y-4">
          <div className="p-4 bg-blood-50/50 rounded-xl border border-blood-100 text-sm space-y-2">
            <div className="flex justify-between">
              <span className="text-slate-500">Donor:</span>
              <span className="font-semibold text-slate-900">{donor.name}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Blood Group:</span>
              <span className="font-bold text-blood-700">{donor.blood_group}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Shelf Life:</span>
              <span className="font-semibold text-slate-900">42 Days</span>
            </div>
          </div>

          <p className="text-xs text-slate-600 leading-relaxed">
            Recording this collection will atomically create an available inventory blood unit, update the donor&apos;s last donation date, and write a tamper-evident audit log.
          </p>

          <div className="flex justify-end gap-3 pt-3">
            <Button
              variant="secondary"
              onClick={() => setDonationModalOpen(false)}
              disabled={recordingDonation}
            >
              Cancel
            </Button>
            <Button
              variant="blood"
              icon={Heart}
              loading={recordingDonation}
              onClick={handleRecordDonation}
            >
              Confirm & Collect Unit
            </Button>
          </div>
        </div>
      </Modal>

      {/* Delete Donor Confirmation Dialog */}
      <ConfirmDialog
        isOpen={deleteDialogOpen}
        onClose={() => setDeleteDialogOpen(false)}
        onConfirm={handleDeleteDonor}
        title="Delete Donor Profile"
        message={`Are you sure you want to delete ${donor.name}? Note: Donors with existing blood units cannot be deleted.`}
        confirmText="Delete Donor"
        confirmVariant="danger"
        loading={deleting}
      />
    </div>
  );
}
