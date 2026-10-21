import React from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import ProtectedRoute from "./ProtectedRoute";

// Layouts
import AuthLayout from "../layouts/AuthLayout";
import StaffLayout from "../layouts/StaffLayout";
import RequesterLayout from "../layouts/RequesterLayout";

// Auth Pages
import LoginPage from "../pages/auth/LoginPage";
import RegisterPage from "../pages/auth/RegisterPage";
import NotFoundPage from "../pages/NotFoundPage";

// Staff & Admin Pages
import DashboardPage from "../pages/dashboard/DashboardPage";
import DonorListPage from "../pages/donors/DonorListPage";
import DonorFormPage from "../pages/donors/DonorFormPage";
import DonorDetailPage from "../pages/donors/DonorDetailPage";
import InventoryPage from "../pages/inventory/InventoryPage";
import RequestQueuePage from "../pages/requests/RequestQueuePage";
import RequestDetailPage from "../pages/requests/RequestDetailPage";
import RequestersPage from "../pages/requesters/RequestersPage";
import PredictionsPage from "../pages/predictions/PredictionsPage";
import CampsPage from "../pages/camps/CampsPage";
import ReportsPage from "../pages/reports/ReportsPage";
import StaffPage from "../pages/admin/StaffPage";
import ActivityLogPage from "../pages/admin/ActivityLogPage";

// Requester Pages
import MyRequestsPage from "../pages/requester/MyRequestsPage";
import NewRequestPage from "../pages/requester/NewRequestPage";
import MyRequestDetailPage from "../pages/requester/MyRequestDetailPage";
import MyProfilePage from "../pages/requester/MyProfilePage";

function RootRedirect() {
  const { isAuthenticated, role, loading } = useAuth();
  if (loading) return null;
  if (!isAuthenticated) return <Navigate to="/login" replace />;
  if (role === "admin" || role === "staff") return <Navigate to="/dashboard" replace />;
  return <Navigate to="/my/requests" replace />;
}

export default function AppRoutes() {
  return (
    <Routes>
      {/* Root redirect */}
      <Route path="/" element={<RootRedirect />} />

      {/* Public Auth Routes */}
      <Route element={<AuthLayout />}>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
      </Route>

      {/* Staff & Admin Routes */}
      <Route
        element={
          <ProtectedRoute allowedRoles={["admin", "staff"]}>
            <StaffLayout />
          </ProtectedRoute>
        }
      >
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/donors" element={<DonorListPage />} />
        <Route path="/donors/new" element={<DonorFormPage />} />
        <Route path="/donors/:id/edit" element={<DonorFormPage />} />
        <Route path="/donors/:id" element={<DonorDetailPage />} />
        <Route path="/inventory" element={<InventoryPage />} />
        <Route path="/requests" element={<RequestQueuePage />} />
        <Route path="/requests/:id" element={<RequestDetailPage />} />
        <Route path="/requesters" element={<RequestersPage />} />
        <Route path="/predictions" element={<PredictionsPage />} />
        <Route path="/camps" element={<CampsPage />} />
        <Route path="/reports" element={<ReportsPage />} />

        {/* Admin only subroutes */}
        <Route
          path="/admin/staff"
          element={
            <ProtectedRoute allowedRoles={["admin"]}>
              <StaffPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/admin/activity-log"
          element={
            <ProtectedRoute allowedRoles={["admin"]}>
              <ActivityLogPage />
            </ProtectedRoute>
          }
        />
      </Route>

      {/* Requester Portal Routes */}
      <Route
        element={
          <ProtectedRoute allowedRoles={["requester"]}>
            <RequesterLayout />
          </ProtectedRoute>
        }
      >
        <Route path="/my/requests" element={<MyRequestsPage />} />
        <Route path="/my/requests/new" element={<NewRequestPage />} />
        <Route path="/my/requests/:id" element={<MyRequestDetailPage />} />
        <Route path="/my/profile" element={<MyProfilePage />} />
      </Route>

      {/* Catch-all 404 */}
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  );
}
