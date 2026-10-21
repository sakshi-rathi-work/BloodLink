import React, { useState, useEffect } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { createDonor, getDonor, updateDonor } from "../../api/donors";
import { BLOOD_GROUPS, GENDERS } from "../../utils/constants";
import { getErrorMessage } from "../../utils/errors";
import { useToast } from "../../context/ToastContext";
import Button from "../../components/ui/Button";
import Input from "../../components/ui/Input";
import Select from "../../components/ui/Select";
import Spinner from "../../components/ui/Spinner";
import ErrorBanner from "../../components/ui/ErrorBanner";
import { ArrowLeft, Save, AlertCircle } from "lucide-react";

export default function DonorFormPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const toast = useToast();
  const isEdit = Boolean(id);

  const [loading, setLoading] = useState(isEdit);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  const [formData, setFormData] = useState({
    name: "",
    dob: "",
    gender: "male",
    blood_group: "A+",
    phone: "",
    address: "",
    weight: "",
    last_donation_date: "",
  });

  const [initialBloodGroup, setInitialBloodGroup] = useState("");
  const [hasDonations, setHasDonations] = useState(false);

  useEffect(() => {
    if (!isEdit) return;

    async function loadDonor() {
      try {
        setLoading(true);
        const data = await getDonor(id);
        setFormData({
          name: data.name || "",
          dob: data.dob || "",
          gender: data.gender || "male",
          blood_group: data.blood_group || "A+",
          phone: data.phone || "",
          address: data.address || "",
          weight: data.weight ? String(data.weight) : "",
          last_donation_date: data.last_donation_date || "",
        });
        setInitialBloodGroup(data.blood_group);
        setHasDonations((data.donation_count || 0) > 0);
      } catch (err) {
        setError(getErrorMessage(err));
      } finally {
        setLoading(false);
      }
    }

    loadDonor();
  }, [id, isEdit]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);

    // Basic validation
    if (!formData.name.trim()) {
      setError("Donor name is required.");
      return;
    }
    if (!formData.dob) {
      setError("Date of birth is required.");
      return;
    }
    if (!formData.phone.trim()) {
      setError("Phone number is required.");
      return;
    }
    if (!formData.address.trim()) {
      setError("Residential address is required.");
      return;
    }
    const weightNum = parseFloat(formData.weight);
    if (isNaN(weightNum) || weightNum <= 0) {
      setError("Please enter a valid donor weight in kg.");
      return;
    }

    setSubmitting(true);
    try {
      if (isEdit) {
        const payload = {
          name: formData.name.trim(),
          dob: formData.dob,
          gender: formData.gender,
          blood_group: formData.blood_group,
          phone: formData.phone.trim(),
          address: formData.address.trim(),
          weight: weightNum,
          last_donation_date: formData.last_donation_date || null,
        };
        await updateDonor(id, payload);
        toast.success("Donor profile updated successfully.");
        navigate(`/donors/${id}`);
      } else {
        const payload = {
          name: formData.name.trim(),
          dob: formData.dob,
          gender: formData.gender,
          blood_group: formData.blood_group,
          phone: formData.phone.trim(),
          address: formData.address.trim(),
          weight: weightNum,
          last_donation_date: formData.last_donation_date || null,
        };
        const created = await createDonor(payload);
        toast.success("New donor registered successfully.");
        navigate(`/donors/${created.donor_id}`);
      }
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center py-20">
        <Spinner size="lg" />
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <Button
          variant="ghost"
          size="sm"
          icon={ArrowLeft}
          onClick={() => navigate(isEdit ? `/donors/${id}` : "/donors")}
        >
          Back
        </Button>
        <div>
          <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">
            {isEdit ? "Edit Donor Profile" : "Register New Donor"}
          </h1>
          <p className="text-sm text-slate-500">
            {isEdit
              ? "Update donor demographic, contact, and health details"
              : "Capture new voluntary donor registration details"}
          </p>
        </div>
      </div>

      {error && <ErrorBanner message={error} onDismiss={() => setError(null)} />}

      {/* Blood Group Warning in Edit mode if donations exist */}
      {isEdit && hasDonations && (
        <div className="flex items-start gap-3 p-4 bg-amber-50 border border-amber-200 rounded-xl text-amber-800 text-sm">
          <AlertCircle className="w-5 h-5 flex-shrink-0 text-amber-600 mt-0.5" />
          <div>
            <p className="font-semibold">Blood Group Modification Locked</p>
            <p className="text-xs text-amber-700 mt-0.5">
              This donor has recorded blood collections. To preserve transfusion safety and historical traceability, the blood group ({initialBloodGroup}) cannot be modified.
            </p>
          </div>
        </div>
      )}

      {/* Form Container */}
      <form onSubmit={handleSubmit} className="bg-white p-6 sm:p-8 rounded-2xl border border-slate-200/80 shadow-sm space-y-6">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
          <div className="sm:col-span-2">
            <Input
              label="Full Name"
              name="name"
              placeholder="e.g. Ramesh Kumar"
              value={formData.name}
              onChange={handleChange}
              required
            />
          </div>

          <div>
            <Input
              label="Date of Birth"
              name="dob"
              type="date"
              value={formData.dob}
              onChange={handleChange}
              helperText="Donors must be between 18 and 65 years old to donate"
              required
            />
          </div>

          <div>
            <Select
              label="Gender"
              name="gender"
              value={formData.gender}
              onChange={handleChange}
              options={GENDERS}
              required
            />
          </div>

          <div>
            <Select
              label="Blood Group"
              name="blood_group"
              value={formData.blood_group}
              onChange={handleChange}
              options={BLOOD_GROUPS.map((bg) => ({ value: bg, label: bg }))}
              disabled={isEdit && hasDonations}
              helperText={isEdit && hasDonations ? "Cannot be changed after donations are recorded" : undefined}
              required
            />
          </div>

          <div>
            <Input
              label="Weight (kg)"
              name="weight"
              type="number"
              step="0.5"
              min="30"
              max="200"
              placeholder="e.g. 65.5"
              value={formData.weight}
              onChange={handleChange}
              helperText="Minimum weight requirement is 50.0 kg for whole blood donation"
              required
            />
          </div>

          <div className="sm:col-span-2">
            <Input
              label="Phone Number"
              name="phone"
              type="tel"
              placeholder="e.g. 9876543210"
              value={formData.phone}
              onChange={handleChange}
              required
            />
          </div>

          <div className="sm:col-span-2">
            <label className="block text-sm font-semibold text-slate-700 mb-1.5">
              Residential Address
            </label>
            <textarea
              name="address"
              rows={3}
              className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 bg-white text-slate-900 text-sm shadow-sm placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-blood-500/20 focus:border-blood-600 transition-all duration-200"
              placeholder="e.g. Flat 402, Shivajinagar, Pune"
              value={formData.address}
              onChange={handleChange}
              required
            />
          </div>

          <div>
            <Input
              label="Last Donation Date (Optional)"
              name="last_donation_date"
              type="date"
              value={formData.last_donation_date}
              onChange={handleChange}
              helperText="Leave empty if this donor has never donated before"
            />
          </div>
        </div>

        {/* Actions */}
        <div className="flex items-center justify-end gap-3 pt-6 border-t border-slate-100">
          <Button
            type="button"
            variant="secondary"
            onClick={() => navigate(isEdit ? `/donors/${id}` : "/donors")}
            disabled={submitting}
          >
            Cancel
          </Button>
          <Button
            type="submit"
            variant="primary"
            icon={Save}
            loading={submitting}
          >
            {isEdit ? "Update Donor" : "Save Donor"}
          </Button>
        </div>
      </form>
    </div>
  );
}
