import { useAuth } from "../../context/AuthContext";

export default function MyProfilePage() {
  const { user } = useAuth();

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">Requester Profile</h1>
        <p className="text-sm text-slate-500">Your organization account details</p>
      </div>

      <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm space-y-4">
        <div className="flex items-center gap-3 pb-4 border-b border-slate-100">
          <div className="w-12 h-12 rounded-2xl bg-blood-100 text-blood-700 flex items-center justify-center font-bold text-lg">
            {user?.name?.[0]?.toUpperCase() || "R"}
          </div>
          <div>
            <h2 className="text-lg font-bold text-slate-900">{user?.name}</h2>
            <p className="text-xs text-slate-500">Username: @{user?.username}</p>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2">
          <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-100">
            <span className="text-xs font-semibold text-slate-400 block mb-1">Account Role</span>
            <span className="text-sm font-bold text-slate-700 capitalize">{user?.role}</span>
          </div>

          <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-100">
            <span className="text-xs font-semibold text-slate-400 block mb-1">Requester ID</span>
            <span className="text-sm font-bold text-slate-700">#{user?.profile_id || "—"}</span>
          </div>
        </div>
      </div>
    </div>
  );
}
