import React from "react";
import { Outlet, NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { Activity, ClipboardList, PlusCircle, User, LogOut } from "lucide-react";

export default function RequesterLayout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  const navItems = [
    { to: "/my/requests", label: "My Requests", icon: ClipboardList, end: true },
    { to: "/my/requests/new", label: "Submit Request", icon: PlusCircle },
    { to: "/my/profile", label: "Profile", icon: User },
  ];

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col">
      {/* Top Navbar */}
      <header className="bg-white border-b border-slate-200 sticky top-0 z-30">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center gap-8">
            <div className="flex items-center gap-2.5">
              <div className="w-9 h-9 rounded-xl bg-blood-600 flex items-center justify-center text-white shadow-md shadow-blood-600/30">
                <Activity className="w-5 h-5" />
              </div>
              <div>
                <span className="text-lg font-extrabold tracking-tight text-slate-900">
                  Blood<span className="text-blood-600">Link</span>
                </span>
                <span className="hidden sm:inline-block ml-2 text-[11px] uppercase font-bold text-slate-400">
                  Requester Portal
                </span>
              </div>
            </div>

            <nav className="hidden md:flex items-center gap-1">
              {navItems.map((item) => {
                const Icon = item.icon;
                return (
                  <NavLink
                    key={item.to}
                    to={item.to}
                    end={item.end}
                    className={({ isActive }) =>
                      `flex items-center gap-2 px-3.5 py-2 rounded-xl text-sm font-medium transition-colors ${
                        isActive
                          ? "bg-blood-50 text-blood-700 font-semibold"
                          : "text-slate-600 hover:text-slate-900 hover:bg-slate-100"
                      }`
                    }
                  >
                    <Icon className="w-4 h-4" />
                    {item.label}
                  </NavLink>
                );
              })}
            </nav>
          </div>

          <div className="flex items-center gap-4">
            <div className="hidden sm:block text-right">
              <p className="text-sm font-bold text-slate-800">{user?.name || user?.username}</p>
              <p className="text-xs text-slate-500 capitalize">{user?.role}</p>
            </div>

            <button
              onClick={handleLogout}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold text-slate-600 hover:text-rose-600 hover:bg-rose-50 transition-colors border border-slate-200 hover:border-rose-200"
            >
              <LogOut className="w-3.5 h-3.5" />
              Sign Out
            </button>
          </div>
        </div>

        {/* Mobile Subnav */}
        <div className="md:hidden flex items-center justify-around border-t border-slate-100 px-2 py-1 bg-slate-50/50">
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.end}
                className={({ isActive }) =>
                  `flex flex-col items-center py-1.5 px-3 rounded-lg text-xs font-medium ${
                    isActive ? "text-blood-600 font-bold" : "text-slate-500"
                  }`
                }
              >
                <Icon className="w-4 h-4 mb-0.5" />
                {item.label}
              </NavLink>
            );
          })}
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Outlet />
      </main>
    </div>
  );
}
