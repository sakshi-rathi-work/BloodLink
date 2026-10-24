import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { getMyRequesterProfile, updateMyRequesterProfile } from "../../api/requesters";
import { REQUESTER_TYPES } from "../../utils/constants";
import { getErrorMessage } from "../../utils/errors";
import Button from "../../components/ui/Button";
import Input from "../../components/ui/Input";
import Select from "../../components/ui/Select";
import Spinner from "../../components/ui/Spinner";
import ErrorBanner from "../../components/ui/ErrorBanner";
import { User, Save, Phone, MapPin, Building2, PlusCircle } from "lucide-react";

export default function MyProfilePage() {
  const navigate = useNavigate();
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);

  // Edit form state
  const [name, setName] = useState("");
  const [type, setType] = useState("");
  const [phone, setPhone] = useState("");
  const [address, setAddress] = useState("");
  const [editing, setEditing] = useState(false);

  useEffect(() => {
    async function load() {
      setLoading(true);
      setError(null);
      try {
        const data = await getMyRequesterProfile();
        setProfile(data);
        setName(data.name);
        setType(data.type);
        setPhone(data.phone);
        setAddress(data.address);
      } catch (err) {
        setError(getErrorMessage(err));
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  const handleSave = async (e) => {
    e.preventDefault();
    setSaving(true);
    setError(null);
    setSuccess(false);
    try {
      const updated = await updateMyRequesterProfile({ name, type, phone, address });
      setProfile(updated);
      setEditing(false);
      setSuccess(true);
      setTimeout(() => setSuccess(false), 3000);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setSaving(false);
    }
  };

  const handleCancel = () => {
    if (profile) {
      setName(profile.name);
      setType(profile.type);
      setPhone(profile.phone);
      setAddress(profile.address);
    }
    setEditing(false);
    setError(null);
  };

  if (loading) {
    return <div className="flex justify-center items-center py-20"><Spinner size="lg" /></div>;
  }

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">My Profile</h1>
          <p className="text-sm text-slate-500 mt-1">Manage your requester account details</p>
        </div>
        <Button variant="primary" icon={PlusCircle} onClick={() => navigate("/my/requests/new")}>
          New Request
        </Button>
      </div>

      {error && <ErrorBanner message={error} onDismiss={() => setError(null)} />}

      {success && (
        <div className="bg-green-50 border border-green-200 rounded-xl p-3 text-sm text-green-800 font-medium">
          ✓ Profile updated successfully.
        </div>
      )}

      {profile && (
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm">
          {/* Profile avatar/summary */}
          <div className="p-6 border-b border-slate-100 flex items-center gap-4">
            <div className="w-14 h-14 rounded-2xl bg-blood-100 text-blood-700 flex items-center justify-center font-bold text-xl">
              {profile.name?.[0]?.toUpperCase() || "R"}
            </div>
            <div>
              <p className="text-lg font-bold text-slate-900">{profile.name}</p>
              <p className="text-xs text-slate-400">@{profile.username} · Requester #{profile.requester_id}</p>
            </div>
            {!editing && (
              <button
                className="ml-auto text-xs font-semibold text-blood-600 hover:text-blood-700 underline"
                onClick={() => setEditing(true)}
              >
                Edit Profile
              </button>
            )}
          </div>

          {/* View or Edit */}
          <div className="p-6">
            {editing ? (
              <form onSubmit={handleSave} className="space-y-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-500 mb-1.5">Name</label>
                  <Input
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    icon={User}
                    placeholder="Organization or patient name"
                    required
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-500 mb-1.5">Type</label>
                  <Select
                    value={type}
                    onChange={(e) => setType(e.target.value)}
                    options={REQUESTER_TYPES.map((t) => ({ value: t.value, label: t.label }))}
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-500 mb-1.5">Phone</label>
                  <Input
                    value={phone}
                    onChange={(e) => setPhone(e.target.value)}
                    icon={Phone}
                    placeholder="Contact number"
                    required
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-500 mb-1.5">Address</label>
                  <Input
                    value={address}
                    onChange={(e) => setAddress(e.target.value)}
                    icon={MapPin}
                    placeholder="Full address"
                    required
                  />
                </div>
                <div className="flex justify-end gap-3 pt-2 border-t border-slate-100">
                  <Button type="button" variant="secondary" onClick={handleCancel} disabled={saving}>Cancel</Button>
                  <Button type="submit" variant="primary" icon={Save} loading={saving} disabled={saving}>
                    Save Changes
                  </Button>
                </div>
              </form>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {[
                  { label: "Name", value: profile.name, icon: User },
                  { label: "Type", value: profile.type, icon: Building2 },
                  { label: "Phone", value: profile.phone, icon: Phone },
                  { label: "Address", value: profile.address, icon: MapPin },
                ].map(({ label, value, icon: Icon }) => (
                  <div key={label} className="p-3.5 rounded-xl bg-slate-50 border border-slate-100">
                    <span className="text-xs font-semibold text-slate-400 block mb-1">{label}</span>
                    <span className="text-sm font-semibold text-slate-800 capitalize flex items-center gap-1.5">
                      <Icon size={12} className="text-slate-400" />
                      {value}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
