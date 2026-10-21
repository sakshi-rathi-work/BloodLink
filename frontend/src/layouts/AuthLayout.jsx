import React from "react";
import { Outlet, Navigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { Activity } from "lucide-react";

export default function AuthLayout() {
  const { isAuthenticated, role } = useAuth();

  if (isAuthenticated) {
    if (role === "admin" || role === "staff") {
      return <Navigate to="/dashboard" replace />;
    }
    return <Navigate to="/my/requests" replace />;
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-slate-100 to-rose-50/30 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md text-center mb-6">
        <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-blood-600 text-white shadow-xl shadow-blood-600/30 mb-4 animate-bounce-short">
          <Activity className="w-8 h-8" />
        </div>
        <h1 className="text-3xl font-extrabold tracking-tight text-slate-900">
          Blood<span className="text-blood-600">Link</span>
        </h1>
        <p className="mt-2 text-sm text-slate-500 font-medium">
          Blood Bank Management & Availability Prediction
        </p>
      </div>

      <div className="sm:mx-auto sm:w-full sm:max-w-md px-4">
        <div className="bg-white py-8 px-6 sm:px-10 shadow-xl shadow-slate-200/50 rounded-3xl border border-slate-100">
          <Outlet />
        </div>
      </div>
    </div>
  );
}
