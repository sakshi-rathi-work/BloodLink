import React, { useState, useEffect, useCallback } from "react";
import { Link } from "react-router-dom";
import { getStock, getUnits, getExpiringUnits, runExpirySweep, deleteUnit } from "../../api/inventory";
import { BLOOD_GROUPS, UNIT_STATUSES } from "../../utils/constants";
import { formatDate } from "../../utils/format";
import { getErrorMessage } from "../../utils/errors";
import { useAuth } from "../../context/AuthContext";
import { useToast } from "../../context/ToastContext";
import Button from "../../components/ui/Button";
import Select from "../../components/ui/Select";
import Input from "../../components/ui/Input";
import Table from "../../components/ui/Table";
import Badge from "../../components/ui/Badge";
import Pagination from "../../components/ui/Pagination";
import ConfirmDialog from "../../components/ui/ConfirmDialog";
import Spinner from "../../components/ui/Spinner";
import EmptyState from "../../components/ui/EmptyState";
import ErrorBanner from "../../components/ui/ErrorBanner";
import {
  Package,
  Droplet,
  Clock,
  RefreshCw,
  AlertTriangle,
  Trash2,
  CheckCircle,
} from "lucide-react";

export default function InventoryPage() {
  const { role } = useAuth();
  const toast = useToast();

  const [activeTab, setActiveTab] = useState("all"); // "all" | "expiring"
  const [stockData, setStockData] = useState(null);
  const [stockLoading, setStockLoading] = useState(true);

  // All Units state
  const [units, setUnits] = useState([]);
  const [totalUnits, setTotalUnits] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(15);
  const [unitsLoading, setUnitsLoading] = useState(true);

  // Expiring units state
  const [expiringUnits, setExpiringUnits] = useState([]);
  const [expiringDays, setExpiringDays] = useState(7);
  const [expiringLoading, setExpiringLoading] = useState(false);

  // Filters
  const [bloodGroupFilter, setBloodGroupFilter] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [expiringWithinDaysFilter, setExpiringWithinDaysFilter] = useState("");

  // Action states
  const [sweeping, setSweeping] = useState(false);
  const [deleteUnitId, setDeleteUnitId] = useState(null);
  const [deleting, setDeleting] = useState(false);
  const [error, setError] = useState(null);

  // Safe minimum threshold (default 10 units)
  const SAFE_MINIMUM = 10;

  // 1. Fetch Stock Summary
  const fetchStock = useCallback(async () => {
    setStockLoading(true);
    try {
      const data = await getStock();
      setStockData(data);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setStockLoading(false);
    }
  }, []);

  // 2. Fetch All Units
  const fetchUnits = useCallback(async () => {
    setUnitsLoading(true);
    try {
      const params = {
        page,
        page_size: pageSize,
      };
      if (bloodGroupFilter) params.blood_group = bloodGroupFilter;
      if (statusFilter) params.status = statusFilter;
      if (expiringWithinDaysFilter) params.expiring_within_days = parseInt(expiringWithinDaysFilter, 10);

      const data = await getUnits(params);
      setUnits(data.items);
      setTotalUnits(data.total);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setUnitsLoading(false);
    }
  }, [page, pageSize, bloodGroupFilter, statusFilter, expiringWithinDaysFilter]);

  // 3. Fetch Expiring Units
  const fetchExpiring = useCallback(async () => {
    setExpiringLoading(true);
    try {
      const data = await getExpiringUnits(expiringDays);
      setExpiringUnits(data);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setExpiringLoading(false);
    }
  }, [expiringDays]);

  useEffect(() => {
    fetchStock();
  }, [fetchStock]);

  useEffect(() => {
    if (activeTab === "all") {
      fetchUnits();
    } else {
      fetchExpiring();
    }
  }, [activeTab, fetchUnits, fetchExpiring]);

  // Handle Manual Expiry Sweep
  const handleRunExpirySweep = async () => {
    setSweeping(true);
    try {
      const res = await runExpirySweep();
      if (res.expired_count > 0) {
        toast.info(`Expiry sweep marked ${res.expired_count} overdue unit(s) as expired.`);
      } else {
        toast.success("All inventory units are current. No expired units detected.");
      }
      await Promise.all([fetchStock(), fetchUnits(), fetchExpiring()]);
    } catch (err) {
      toast.error(getErrorMessage(err));
    } finally {
      setSweeping(false);
    }
  };

  // Handle Delete Unit
  const handleDeleteUnit = async () => {
    if (!deleteUnitId) return;
    setDeleting(true);
    try {
      await deleteUnit(deleteUnitId);
      toast.success(`Blood unit #${deleteUnitId} deleted.`);
      setDeleteUnitId(null);
      await Promise.all([fetchStock(), fetchUnits()]);
    } catch (err) {
      toast.error(getErrorMessage(err));
    } finally {
      setDeleting(false);
    }
  };

  return (
    <div className="space-y-8">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">
            Blood Stock & Inventory
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Real-time blood reserves, 42-day shelf-life tracking, and automated expiry sweeps
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Button
            variant="secondary"
            icon={RefreshCw}
            loading={sweeping}
            onClick={handleRunExpirySweep}
            title="Scan inventory and mark overdue units as expired"
          >
            Run Expiry Sweep
          </Button>
        </div>
      </div>

      {error && <ErrorBanner message={error} onDismiss={() => setError(null)} />}

      {/* Stock Cards Grid */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-bold text-slate-700 uppercase tracking-wider">
            Available Stock by Blood Group
          </h2>
          {stockData && (
            <span className="text-xs font-semibold text-slate-500">
              Total Available:{" "}
              <strong className="text-slate-900 font-extrabold text-sm">
                {stockData.total_available_units} units
              </strong>
            </span>
          )}
        </div>

        {stockLoading ? (
          <div className="flex justify-center items-center py-10">
            <Spinner size="md" />
          </div>
        ) : (
          <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-3">
            {stockData?.stock?.map((item) => {
              const isLow = item.available_units < SAFE_MINIMUM;
              return (
                <div
                  key={item.blood_group}
                  className={`p-4 rounded-2xl border text-center transition-all duration-200 shadow-sm ${
                    isLow
                      ? "bg-rose-50/60 border-rose-300 text-rose-900"
                      : "bg-white border-slate-200/80 text-slate-900 hover:border-slate-300"
                  }`}
                >
                  <div className="text-xs font-black tracking-wider uppercase flex items-center justify-center gap-1">
                    <Droplet
                      className={`w-3.5 h-3.5 ${
                        isLow ? "text-rose-600 fill-rose-600" : "text-blood-600 fill-blood-600"
                      }`}
                    />
                    {item.blood_group}
                  </div>
                  <div className="text-2xl font-black mt-2 tracking-tight">
                    {item.available_units}
                  </div>
                  <div className="mt-1">
                    {isLow ? (
                      <span className="inline-block px-1.5 py-0.5 text-[10px] font-bold bg-rose-200/80 text-rose-800 rounded">
                        Low Stock
                      </span>
                    ) : (
                      <span className="text-[11px] font-medium text-slate-400">Optimal</span>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Tab Navigation */}
      <div className="border-b border-slate-200">
        <nav className="flex space-x-8">
          <button
            type="button"
            onClick={() => setActiveTab("all")}
            className={`py-3.5 px-1 border-b-2 font-bold text-sm transition-all duration-150 flex items-center gap-2 ${
              activeTab === "all"
                ? "border-blood-600 text-blood-600"
                : "border-transparent text-slate-500 hover:text-slate-700"
            }`}
          >
            <Package className="w-4 h-4" />
            All Blood Units ({totalUnits})
          </button>

          <button
            type="button"
            onClick={() => setActiveTab("expiring")}
            className={`py-3.5 px-1 border-b-2 font-bold text-sm transition-all duration-150 flex items-center gap-2 ${
              activeTab === "expiring"
                ? "border-blood-600 text-blood-600"
                : "border-transparent text-slate-500 hover:text-slate-700"
            }`}
          >
            <Clock className="w-4 h-4" />
            Expiring Soon (<span className="text-rose-600 font-extrabold">{expiringUnits.length}</span>)
          </button>
        </nav>
      </div>

      {/* TAB 1: ALL UNITS */}
      {activeTab === "all" && (
        <div className="space-y-4">
          {/* Filters Bar */}
          <div className="bg-white p-4 rounded-2xl border border-slate-200/80 shadow-sm grid grid-cols-1 sm:grid-cols-3 lg:grid-cols-4 gap-3">
            <Select
              value={bloodGroupFilter}
              onChange={(e) => {
                setBloodGroupFilter(e.target.value);
                setPage(1);
              }}
              options={[
                { value: "", label: "All Blood Groups" },
                ...BLOOD_GROUPS.map((bg) => ({ value: bg, label: bg })),
              ]}
            />

            <Select
              value={statusFilter}
              onChange={(e) => {
                setStatusFilter(e.target.value);
                setPage(1);
              }}
              options={[
                { value: "", label: "All Unit Statuses" },
                ...UNIT_STATUSES.map((st) => ({ value: st.value, label: st.label })),
              ]}
            />

            <Input
              type="number"
              min="1"
              max="42"
              placeholder="Expiring within days..."
              value={expiringWithinDaysFilter}
              onChange={(e) => {
                setExpiringWithinDaysFilter(e.target.value);
                setPage(1);
              }}
            />

            {(bloodGroupFilter || statusFilter || expiringWithinDaysFilter) && (
              <div className="flex items-center">
                <button
                  type="button"
                  onClick={() => {
                    setBloodGroupFilter("");
                    setStatusFilter("");
                    setExpiringWithinDaysFilter("");
                    setPage(1);
                  }}
                  className="text-xs font-semibold text-blood-600 hover:text-blood-700 underline"
                >
                  Clear Filters
                </button>
              </div>
            )}
          </div>

          {unitsLoading ? (
            <div className="flex justify-center items-center py-20">
              <Spinner size="lg" />
            </div>
          ) : units.length === 0 ? (
            <EmptyState
              icon={Package}
              title="No blood units found"
              description="No inventory units match the selected criteria."
            />
          ) : (
            <div className="space-y-4">
              <Table
                headers={[
                  "Unit ID",
                  "Blood Group",
                  "Donor",
                  "Collection Date",
                  "Expiry Date",
                  "Status",
                  "Shelf Life Remaining",
                  "Actions",
                ]}
              >
                {units.map((unit) => (
                  <tr key={unit.unit_id} className="hover:bg-slate-50/75 transition-colors">
                    <td className="py-3.5 px-4 font-mono font-bold text-xs text-slate-900">
                      #{unit.unit_id}
                    </td>
                    <td className="py-3.5 px-4">
                      <span className="inline-flex items-center px-2.5 py-1 rounded-md text-xs font-black bg-blood-100 text-blood-800 border border-blood-200">
                        {unit.blood_group}
                      </span>
                    </td>
                    <td className="py-3.5 px-4 text-xs font-medium text-slate-800">
                      {unit.donor_name ? (
                        <Link
                          to={`/donors/${unit.donor_id}`}
                          className="hover:text-blood-600 underline-offset-2 hover:underline"
                        >
                          {unit.donor_name}
                        </Link>
                      ) : (
                        `Donor #${unit.donor_id}`
                      )}
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
                          <span className="text-rose-600 font-bold flex items-center gap-1">
                            <AlertTriangle className="w-3.5 h-3.5" />
                            {unit.days_to_expiry} day(s) left
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
                    <td className="py-3.5 px-4">
                      {role === "admin" && (
                        <Button
                          variant="ghost"
                          size="sm"
                          icon={Trash2}
                          className="text-rose-600 hover:text-rose-700 hover:bg-rose-50"
                          disabled={unit.status === "issued"}
                          onClick={() => setDeleteUnitId(unit.unit_id)}
                          title={
                            unit.status === "issued"
                              ? "Issued units cannot be deleted"
                              : "Delete blood unit"
                          }
                        />
                      )}
                    </td>
                  </tr>
                ))}
              </Table>

              <Pagination
                currentPage={page}
                totalItems={totalUnits}
                pageSize={pageSize}
                onPageChange={setPage}
              />
            </div>
          )}
        </div>
      )}

      {/* TAB 2: EXPIRING SOON */}
      {activeTab === "expiring" && (
        <div className="space-y-4">
          <div className="flex items-center justify-between bg-amber-50/70 p-4 rounded-2xl border border-amber-200 text-amber-900 text-sm">
            <div className="flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-amber-600 flex-shrink-0" />
              <span>
                Showing available units expiring within <strong>{expiringDays} days</strong>, sorted nearest-expiry first to minimize wastage.
              </span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-semibold text-slate-600">Threshold:</span>
              <select
                value={expiringDays}
                onChange={(e) => setExpiringDays(Number(e.target.value))}
                className="text-xs font-bold border border-slate-300 rounded-lg px-2.5 py-1 bg-white text-slate-900 focus:outline-none focus:ring-2 focus:ring-blood-500"
              >
                <option value={3}>3 Days (Critical)</option>
                <option value={7}>7 Days (Standard)</option>
                <option value={14}>14 Days (Upcoming)</option>
              </select>
            </div>
          </div>

          {expiringLoading ? (
            <div className="flex justify-center items-center py-20">
              <Spinner size="lg" />
            </div>
          ) : expiringUnits.length === 0 ? (
            <EmptyState
              icon={CheckCircle}
              title="No units expiring soon"
              description={`There are currently no available blood units expiring within the next ${expiringDays} days.`}
            />
          ) : (
            <Table
              headers={[
                "Unit ID",
                "Blood Group",
                "Donor",
                "Collection Date",
                "Expiry Date",
                "Urgency Level",
                "Days Until Expiry",
              ]}
            >
              {expiringUnits.map((unit) => {
                const isCritical = unit.days_to_expiry <= 3;
                return (
                  <tr key={unit.unit_id} className="hover:bg-slate-50/75 transition-colors">
                    <td className="py-3.5 px-4 font-mono font-bold text-xs text-slate-900">
                      #{unit.unit_id}
                    </td>
                    <td className="py-3.5 px-4">
                      <span className="inline-flex items-center px-2.5 py-1 rounded-md text-xs font-black bg-blood-100 text-blood-800 border border-blood-200">
                        {unit.blood_group}
                      </span>
                    </td>
                    <td className="py-3.5 px-4 text-xs font-medium text-slate-800">
                      {unit.donor_name ? (
                        <Link to={`/donors/${unit.donor_id}`} className="hover:underline">
                          {unit.donor_name}
                        </Link>
                      ) : (
                        `Donor #${unit.donor_id}`
                      )}
                    </td>
                    <td className="py-3.5 px-4 text-xs text-slate-600 font-medium">
                      {formatDate(unit.collection_date)}
                    </td>
                    <td className="py-3.5 px-4 text-xs text-slate-600 font-medium">
                      {formatDate(unit.expiry_date)}
                    </td>
                    <td className="py-3.5 px-4">
                      {isCritical ? (
                        <Badge variant="emergency" size="sm">
                          CRITICAL (&le;3d)
                        </Badge>
                      ) : (
                        <Badge variant="warning" size="sm">
                          EXPIRING SOON
                        </Badge>
                      )}
                    </td>
                    <td className="py-3.5 px-4 font-mono font-bold text-xs text-rose-600">
                      {unit.days_to_expiry} day(s)
                    </td>
                  </tr>
                );
              })}
            </Table>
          )}
        </div>
      )}

      {/* Delete Unit Confirmation Dialog */}
      <ConfirmDialog
        isOpen={Boolean(deleteUnitId)}
        onClose={() => setDeleteUnitId(null)}
        onConfirm={handleDeleteUnit}
        title="Delete Blood Unit"
        message={`Are you sure you want to delete blood unit #${deleteUnitId}? Issued blood units cannot be deleted.`}
        confirmText="Delete Unit"
        confirmVariant="danger"
        loading={deleting}
      />
    </div>
  );
}
