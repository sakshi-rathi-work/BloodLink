import React, { useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import {
  getDashboardSummary,
  getDashboardTrends,
  getDashboardWastage,
} from "../../api/dashboard";
import { getExpiringUnits } from "../../api/inventory";
import { getPredictionAlerts } from "../../api/predictions";
import { getErrorMessage } from "../../utils/errors";
import { formatDate } from "../../utils/format";
import { BLOOD_GROUPS } from "../../utils/constants";
import StatCard from "../../components/ui/StatCard";
import Button from "../../components/ui/Button";
import Select from "../../components/ui/Select";
import Badge from "../../components/ui/Badge";
import Spinner from "../../components/ui/Spinner";
import ErrorBanner from "../../components/ui/ErrorBanner";
import StockBarChart from "../../components/charts/StockBarChart";
import TrendsLineChart from "../../components/charts/TrendsLineChart";
import WastageBarChart from "../../components/charts/WastageBarChart";
import {
  Droplets,
  Clock,
  AlertTriangle,
  Activity,
  ArrowRight,
  RefreshCw,
  TrendingUp,
  BarChart3,
} from "lucide-react";

export default function DashboardPage() {
  const navigate = useNavigate();

  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState(null);

  // Dashboard Data
  const [summary, setSummary] = useState(null);
  const [trends, setTrends] = useState([]);
  const [granularity, setGranularity] = useState("week");
  const [trendBloodGroup, setTrendBloodGroup] = useState("");
  const [wastageData, setWastageData] = useState(null);
  const [expiringUnits, setExpiringUnits] = useState([]);
  const [shortageAlerts, setShortageAlerts] = useState([]);

  // Fetch full dashboard data
  const loadDashboardData = useCallback(async () => {
    setError(null);
    try {
      const [sumData, wastageRes, expiringRes, alertsRes] = await Promise.all([
        getDashboardSummary(),
        getDashboardWastage(),
        getExpiringUnits(7),
        getPredictionAlerts(30).catch(() => []),
      ]);

      setSummary(sumData);
      setWastageData(wastageRes);
      setExpiringUnits(expiringRes || []);
      setShortageAlerts(alertsRes || []);
    } catch (err) {
      setError(getErrorMessage(err));
    }
  }, []);

  // Fetch trends separately when granularity/bloodGroup changes
  const loadTrends = useCallback(async () => {
    try {
      const params = { granularity };
      if (trendBloodGroup) params.blood_group = trendBloodGroup;
      const res = await getDashboardTrends(params);
      setTrends(res.series || []);
    } catch (err) {
      console.error("Failed to load trends:", err);
    }
  }, [granularity, trendBloodGroup]);

  useEffect(() => {
    async function init() {
      setLoading(true);
      await loadDashboardData();
      await loadTrends();
      setLoading(false);
    }
    init();
  }, [loadDashboardData, loadTrends]);

  const handleRefresh = async () => {
    setRefreshing(true);
    await loadDashboardData();
    await loadTrends();
    setRefreshing(false);
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-32 space-y-4">
        <Spinner size="lg" />
        <p className="text-sm font-medium text-slate-500">Loading operational analytics...</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">Executive Dashboard</h1>
          <p className="text-sm text-slate-500 mt-1">
            Real-time blood bank inventory, request queues, and predictive operational insights
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Button
            variant="secondary"
            size="sm"
            icon={RefreshCw}
            onClick={handleRefresh}
            loading={refreshing}
          >
            Refresh Data
          </Button>
        </div>
      </div>

      {error && <ErrorBanner message={error} onDismiss={() => setError(null)} />}

      {/* KPI Stat Cards */}
      {summary && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <StatCard
            title="Total Units Available"
            value={summary.total_available_units}
            icon={Droplets}
            variant="blood"
            subtext="Available unexpired units across all groups"
          />
          <StatCard
            title="Pending Requests"
            value={summary.pending_requests}
            icon={Clock}
            variant="warning"
            subtext={
              summary.pending_emergency_requests > 0
                ? `${summary.pending_emergency_requests} emergency priority`
                : "Awaiting staff review"
            }
          />
          <StatCard
            title="Expiring Soon (7d)"
            value={summary.expiring_soon?.count ?? 0}
            icon={AlertTriangle}
            variant={summary.expiring_soon?.count > 0 ? "danger" : "default"}
            subtext="Units reaching 42-day limit within 7 days"
          />
          <StatCard
            title="Predicted Shortages"
            value={
              summary.predicted_shortage_alert_count != null
                ? summary.predicted_shortage_alert_count
                : "None"
            }
            icon={Activity}
            variant={
              summary.predicted_shortage_alert_count > 0 ? "danger" : "default"
            }
            subtext="Blood groups projected to drop below safe min"
          />
        </div>
      )}

      {/* Row 1: Stock by Group & Donation vs Issue Trends */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Current Inventory Levels */}
        <div className="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-sm flex flex-col justify-between">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-lg bg-sky-50 text-sky-600 flex items-center justify-center">
                <BarChart3 className="w-4 h-4" />
              </div>
              <div>
                <h2 className="text-base font-bold text-slate-900">Current Stock by Blood Group</h2>
                <p className="text-xs text-slate-500">Available units vs safe minimum threshold</p>
              </div>
            </div>
            <Button
              variant="ghost"
              size="sm"
              icon={ArrowRight}
              onClick={() => navigate("/inventory")}
              className="text-xs text-blood-600 hover:text-blood-700"
            >
              Inventory
            </Button>
          </div>

          <StockBarChart data={summary?.stock_by_group || []} />
        </div>

        {/* Operational Flow Trends */}
        <div className="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-sm flex flex-col justify-between">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-lg bg-emerald-50 text-emerald-600 flex items-center justify-center">
                <TrendingUp className="w-4 h-4" />
              </div>
              <div>
                <h2 className="text-base font-bold text-slate-900">Donations vs Issues Inflow/Outflow</h2>
                <p className="text-xs text-slate-500">Activity trends across time</p>
              </div>
            </div>

            {/* Granularity and Group Selector */}
            <div className="flex items-center gap-2">
              <div className="inline-flex rounded-lg bg-slate-100 p-0.5 border border-slate-200 text-xs">
                {["day", "week", "month"].map((g) => (
                  <button
                    key={g}
                    onClick={() => setGranularity(g)}
                    className={`px-2.5 py-1 rounded-md font-medium capitalize transition-all ${
                      granularity === g
                        ? "bg-white text-slate-900 font-bold shadow-sm"
                        : "text-slate-600 hover:text-slate-900"
                    }`}
                  >
                    {g}
                  </button>
                ))}
              </div>
              <div className="w-28">
                <Select
                  value={trendBloodGroup}
                  onChange={(e) => setTrendBloodGroup(e.target.value)}
                  options={[
                    { value: "", label: "All Groups" },
                    ...BLOOD_GROUPS.map((bg) => ({ value: bg, label: bg })),
                  ]}
                  className="text-xs"
                />
              </div>
            </div>
          </div>

          <TrendsLineChart data={trends} granularity={granularity} />
        </div>
      </div>

      {/* Row 2: Expired Units Wastage Analysis */}
      {wastageData && (
        <div className="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-sm space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-100 pb-3">
            <div>
              <h2 className="text-base font-bold text-slate-900">Blood Unit Wastage (Expired Units)</h2>
              <p className="text-xs text-slate-500">
                Tracking units that expired without being issued ({formatDate(wastageData.start_date)} – {formatDate(wastageData.end_date)})
              </p>
            </div>
            <div className="text-right">
              <span className="text-xs text-slate-500 block">Total Wastage in Period</span>
              <span className="text-lg font-extrabold text-rose-600 font-mono">
                {wastageData.total_expired} units
              </span>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 pt-2">
            <div className="lg:col-span-2">
              <WastageBarChart data={wastageData.by_month || []} />
            </div>
            <div className="bg-slate-50 p-4 rounded-xl border border-slate-200 flex flex-col justify-between">
              <div>
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-600 mb-3">
                  Wastage by Blood Group
                </h3>
                <div className="grid grid-cols-2 gap-2 text-xs">
                  {wastageData.by_blood_group?.map((item) => (
                    <div
                      key={item.blood_group}
                      className="flex items-center justify-between p-2 rounded-lg bg-white border border-slate-200"
                    >
                      <span className="font-bold text-slate-800">{item.blood_group}</span>
                      <span
                        className={`font-mono font-bold ${
                          item.expired_units > 0 ? "text-rose-600" : "text-slate-400"
                        }`}
                      >
                        {item.expired_units}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
              <p className="text-[11px] text-slate-400 italic mt-3">
                Automatic daily expiry sweeps ensure no expired units remain eligible for matching.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Row 3: Actionable Operational Lists */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Units Expiring Soon */}
        <div className="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-sm flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 text-amber-500" />
                <h3 className="text-base font-bold text-slate-900">Units Expiring Soon</h3>
              </div>
              <Button
                variant="ghost"
                size="sm"
                icon={ArrowRight}
                onClick={() => navigate("/inventory")}
                className="text-xs text-blood-600"
              >
                View Inventory
              </Button>
            </div>

            {expiringUnits.length === 0 ? (
              <div className="py-10 text-center text-xs text-slate-400 italic">
                No units are nearing the 7-day shelf-life limit.
              </div>
            ) : (
              <div className="space-y-2">
                {expiringUnits.slice(0, 5).map((u) => (
                  <div
                    key={u.unit_id}
                    className="flex items-center justify-between p-3 rounded-xl bg-amber-50/50 border border-amber-200/60 text-xs"
                  >
                    <div className="flex items-center gap-3">
                      <Badge variant="warning" size="sm">
                        {u.blood_group}
                      </Badge>
                      <div>
                        <span className="font-mono font-semibold text-slate-800">Unit #{u.unit_id}</span>
                        <span className="text-slate-400 block text-[11px]">
                          Collected: {formatDate(u.collection_date)}
                        </span>
                      </div>
                    </div>
                    <div className="text-right">
                      <span className="font-semibold text-amber-900 block">
                        Expires {formatDate(u.expiry_date)}
                      </span>
                      <span className="text-[11px] text-amber-700 font-bold">
                        {u.days_to_expiry} day{u.days_to_expiry !== 1 ? "s" : ""} left
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Shortage Prediction Alerts */}
        <div className="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-sm flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <Activity className="w-4 h-4 text-blood-500" />
                <h3 className="text-base font-bold text-slate-900">Predicted Shortage Alerts</h3>
              </div>
              <Button
                variant="ghost"
                size="sm"
                icon={ArrowRight}
                onClick={() => navigate("/predictions")}
                className="text-xs text-blood-600"
              >
                ML Forecasts
              </Button>
            </div>

            {shortageAlerts.length === 0 ? (
              <div className="py-10 text-center text-xs text-slate-400 italic">
                No upcoming shortages projected within the 30-day forecast horizon.
              </div>
            ) : (
              <div className="space-y-2">
                {shortageAlerts.slice(0, 5).map((alert) => (
                  <div
                    key={alert.blood_group}
                    className="flex items-center justify-between p-3 rounded-xl bg-rose-50/60 border border-rose-200 text-xs"
                  >
                    <div className="flex items-center gap-3">
                      <Badge variant="emergency" size="sm">
                        {alert.blood_group}
                      </Badge>
                      <div>
                        <span className="font-semibold text-slate-900">
                          Shortage in {alert.days_until_shortage} days
                        </span>
                        <span className="text-slate-500 block text-[11px]">
                          Projected deficit on {formatDate(alert.first_shortage_date)}
                        </span>
                      </div>
                    </div>
                    <div className="text-right">
                      <span className="font-mono text-slate-700 block">
                        Stock: <span className="font-bold">{alert.current_stock}</span> / Min:{" "}
                        <span className="font-bold">{alert.safe_minimum}</span>
                      </span>
                      <span className="text-[11px] text-rose-600 font-bold">
                        Dips to {alert.min_predicted_stock} units
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
