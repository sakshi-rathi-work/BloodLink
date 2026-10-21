import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";
import { useToast } from "../../context/ToastContext";
import { getErrorMessage } from "../../utils/errors";
import { REQUESTER_TYPES } from "../../utils/constants";
import Input from "../../components/ui/Input";
import Select from "../../components/ui/Select";
import Button from "../../components/ui/Button";

export default function RegisterPage() {
  const [formData, setFormData] = useState({
    username: "",
    password: "",
    name: "",
    type: "hospital",
    phone: "",
    address: "",
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const { register } = useAuth();
  const toast = useToast();
  const navigate = useNavigate();

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);

    if (formData.password.length < 8) {
      setError("Password must be at least 8 characters long.");
      return;
    }

    setLoading(true);

    try {
      const user = await register(formData);
      toast.success(`Account created! Welcome, ${user.name}.`);
      navigate("/my/requests");
    } catch (err) {
      const msg = getErrorMessage(err);
      setError(msg);
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-slate-900 tracking-tight">Create Requester Account</h2>
        <p className="text-sm text-slate-500 mt-1">
          Register your hospital or clinic to submit blood requests
        </p>
      </div>

      {error && (
        <div className="mb-5 p-3.5 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-sm font-medium">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        <Input
          label="Organization / Patient Name"
          name="name"
          placeholder="e.g. City General Hospital"
          value={formData.name}
          onChange={handleChange}
          required
        />

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <Select
            label="Requester Type"
            name="type"
            value={formData.type}
            onChange={handleChange}
            options={REQUESTER_TYPES}
            required
          />

          <Input
            label="Contact Phone"
            name="phone"
            type="tel"
            placeholder="e.g. 9876543210"
            value={formData.phone}
            onChange={handleChange}
            required
          />
        </div>

        <Input
          label="Physical Address"
          name="address"
          placeholder="Full hospital or clinic address"
          value={formData.address}
          onChange={handleChange}
          required
        />

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <Input
            label="Username"
            name="username"
            placeholder="Choose username"
            value={formData.username}
            onChange={handleChange}
            required
            autoComplete="username"
          />

          <Input
            label="Password (min 8 chars)"
            name="password"
            type="password"
            placeholder="••••••••"
            value={formData.password}
            onChange={handleChange}
            required
            autoComplete="new-password"
          />
        </div>

        <Button
          type="submit"
          variant="primary"
          size="lg"
          loading={loading}
          className="w-full mt-3"
        >
          Create Account & Sign In
        </Button>
      </form>

      <div className="mt-8 pt-6 border-t border-slate-100 text-center">
        <p className="text-sm text-slate-600">
          Already have an account?{" "}
          <Link
            to="/login"
            className="font-bold text-blood-600 hover:text-blood-700 transition-colors"
          >
            Sign In here
          </Link>
        </p>
      </div>
    </div>
  );
}
