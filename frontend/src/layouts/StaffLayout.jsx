import React, { useState } from "react";
import { Outlet, NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import {
  LayoutDashboard,
  Users,
  Package,
  ClipboardList,
  Building2,
  TrendingUp,
  Tent,
  FileText,
  UserCog,
  History,
  LogOut,
  Menu,
  X,
  Activity,
  Shield,
} from "lucide-react";

export default function StaffLayout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [mobileOpen, setMobileOpen] = useState(false);

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  const navItems = [
    { to: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
    { to: "/donors", label: "Donors", icon: Users },
    { to: "/inventory", label: "Inventory", icon: Package },
    { to: "/requests", label: "Requests Queue", icon: ClipboardList },
    { to: "/requesters", label: "Requesters", icon: Building2 },
    { to: "/predictions", label: "Predictions & ML", icon: TrendingUp },
    { to: "/camps", label: "Donation Camps", icon: Tent },
    { to: "/reports", label: "Export Reports", icon: FileText },
  ];

  const adminItems = [
    { to: "/admin/staff", label: "Staff Accounts", icon: UserCog },
    { to: "/admin/activity-log", label: "Activity Logs", icon: History },
  ];

  return (
    <div className="min-h-screen bg-slate-50 flex">
      {/* Mobile Sidebar Overlay */}
      {mobileOpen && (
        <div
          className="fixed inset-0 z-40 bg-slate-900/40 backdrop-blur-sm lg:hidden"
          onClick={() => setMobileOpen(false)}
        />
      )}

      {/* Sidebar Navigation */}
      <aside
        className={`fixed inset-y-0 left-0 z-50 w-64 bg-slate-900 text-white flex flex-col transition-transform duration-300 lg:translate-x-0 lg:static lg:inset-auto ${
          mobileOpen ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        {/* Brand */}
        <div className="h-20 flex items-center justify-between px-6 border-b border-slate-800">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-blood-600 flex items-center justify-center text-white shadow-lg shadow-blood-600/30">
              <Activity className="w-6 h-6" />
            </div>
            <div>
              <span className="text-xl font-extrabold tracking-tight">
                Blood<span className="text-blood-500">Link</span>
              </span>
              <span className="block text-[10px] uppercase font-bold text-slate-400 tracking-wider">
                Staff Portal
              </span>
            </div>
          </div>
          <button
            onClick={() => setMobileOpen(false)}
            className="lg:hidden text-slate-400 hover:text-white"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Navigation Links */}
        <nav className="flex-1 px-4 py-6 space-y-1.5 overflow-y-auto">
          <div className="px-3 pb-2 text-[11px] font-bold uppercase text-slate-400 tracking-wider">
            Operations
          </div>
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.to}
                to={item.to}
                onClick={() => setMobileOpen(false)}
                className={({ isActive }) =>
                  `flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-sm font-medium transition-all ${
                    isActive
                      ? "bg-blood-600 text-white font-semibold shadow-md shadow-blood-600/30"
                      : "text-slate-300 hover:bg-slate-800 hover:text-white"
                  }`
                }
              >
                <Icon className="w-4 h-4 flex-shrink-0" />
                {item.label}
              </NavLink>
            );
          })}

          {user?.role === "admin" && (
            <>
              <div className="pt-6 px-3 pb-2 text-[11px] font-bold uppercase text-slate-400 tracking-wider flex items-center gap-1.5">
                <Shield className="w-3.5 h-3.5 text-blood-500" />
                Administration
              </div>
              {adminItems.map((item) => {
                const Icon = item.icon;
                return (
                  <NavLink
                    key={item.to}
                    to={item.to}
                    onClick={() => setMobileOpen(false)}
                    className={({ isActive }) =>
                      `flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-sm font-medium transition-all ${
                        isActive
                          ? "bg-blood-600 text-white font-semibold shadow-md shadow-blood-600/30"
                          : "text-slate-300 hover:bg-slate-800 hover:text-white"
                      }`
                    }
                  >
                    <Icon className="w-4 h-4 flex-shrink-0" />
                    {item.label}
                  </NavLink>
                );
              })}
            </>
          )}
        </nav>

        {/* User Footer & Logout */}
        <div className="p-4 border-t border-slate-800 bg-slate-950/40">
          <div className="flex items-center justify-between mb-3 px-1">
            <div className="overflow-hidden">
              <p className="text-sm font-bold text-white truncate">{user?.name || user?.username}</p>
              <span className="inline-block text-[11px] px-2 py-0.5 rounded-full bg-slate-800 text-slate-300 font-medium capitalize">
                {user?.role}
              </span>
            </div>
            <button
              onClick={handleLogout}
              title="Sign Out"
              className="p-2 text-slate-400 hover:text-rose-400 hover:bg-slate-800 rounded-xl transition-colors"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Top bar on mobile */}
        <header className="h-16 lg:hidden bg-white border-b border-slate-200 px-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setMobileOpen(true)}
              className="p-2 text-slate-600 hover:bg-slate-100 rounded-xl"
            >
              <Menu className="w-5 h-5" />
            </button>
            <span className="font-bold text-slate-800">BloodLink</span>
          </div>
          <span className="text-xs px-2.5 py-1 rounded-full bg-slate-100 text-slate-600 font-medium capitalize">
            {user?.role}
          </span>
        </header>

        {/* Page Content */}
        <main className="flex-1 overflow-y-auto p-4 sm:p-6 lg:p-8">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
