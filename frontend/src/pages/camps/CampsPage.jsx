import React, { useState, useEffect, useCallback } from "react";
import { useAuth } from "../../context/AuthContext";
import { useToast } from "../../context/ToastContext";
import { getCamps, createCamp, updateCamp, deleteCamp } from "../../api/camps";
import { getErrorMessage } from "../../utils/errors";
import { formatDate } from "../../utils/format";
import Button from "../../components/ui/Button";
import Input from "../../components/ui/Input";
import Table from "../../components/ui/Table";
import Badge from "../../components/ui/Badge";
import Pagination from "../../components/ui/Pagination";
import Spinner from "../../components/ui/Spinner";
import EmptyState from "../../components/ui/EmptyState";
import ErrorBanner from "../../components/ui/ErrorBanner";
import Modal from "../../components/ui/Modal";
import ConfirmDialog from "../../components/ui/ConfirmDialog";
import { Tent, Plus, Edit, Trash2, Calendar, Search } from "lucide-react";

export default function CampsPage() {
  const { user } = useAuth();
  const toast = useToast();

  const [camps, setCamps] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(20);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Filters
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");

  // Modal states
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [editingCamp, setEditingCamp] = useState(null);
  const [deleteTarget, setDeleteTarget] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  // Form states
  const [createForm, setCreateForm] = useState({
    location: "",
    camp_date: "",
    target_units: 50,
    units_collected: 0,
  });
  const [editForm, setEditForm] = useState({
    location: "",
    camp_date: "",
    target_units: 50,
    units_collected: 0,
  });
  const [formErrors, setFormErrors] = useState({});

  const todayStr = new Date().toISOString().split("T")[0];

  const fetchCamps = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params = { page, page_size: pageSize };
      if (startDate) params.start_date = startDate;
      if (endDate) params.end_date = endDate;
      const data = await getCamps(params);
      setCamps(data.items);
      setTotal(data.total);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }, [page, pageSize, startDate, endDate]);

  useEffect(() => {
    fetchCamps();
  }, [fetchCamps]);

  // Handle Search & Reset
  const handleFilterSubmit = (e) => {
    e.preventDefault();
    setPage(1);
    fetchCamps();
  };

  const handleResetFilters = () => {
    setStartDate("");
    setEndDate("");
    setPage(1);
  };

  const hasActiveFilters = startDate || endDate;

  // Handle Create Camp
  const handleOpenCreate = () => {
    setCreateForm({
      location: "",
      camp_date: todayStr,
      target_units: 50,
      units_collected: 0,
    });
    setFormErrors({});
    setIsCreateOpen(true);
  };

  const handleCreateSubmit = async (e) => {
    e.preventDefault();
    const errors = {};
    if (!createForm.location.trim()) errors.location = "Camp location is required.";
    if (!createForm.camp_date) errors.camp_date = "Camp date is required.";
    if (!createForm.target_units || Number(createForm.target_units) <= 0) {
      errors.target_units = "Target units must be greater than 0.";
    }
    if (Number(createForm.units_collected) < 0) {
      errors.units_collected = "Units collected cannot be negative.";
    }
    if (Object.keys(errors).length > 0) {
      setFormErrors(errors);
      return;
    }

    setSubmitting(true);
    setFormErrors({});
    try {
      await createCamp({
        location: createForm.location.trim(),
        camp_date: createForm.camp_date,
        target_units: parseInt(createForm.target_units, 10),
        units_collected: parseInt(createForm.units_collected, 10) || 0,
      });
      toast.success("Donation camp scheduled successfully.");
      setIsCreateOpen(false);
      fetchCamps();
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setSubmitting(false);
    }
  };

  // Handle Edit Camp
  const handleOpenEdit = (camp) => {
    setEditingCamp(camp);
    setEditForm({
      location: camp.location,
      camp_date: camp.camp_date,
      target_units: camp.target_units,
      units_collected: camp.units_collected,
    });
    setFormErrors({});
  };

  const handleEditSubmit = async (e) => {
    e.preventDefault();
    const errors = {};
    if (!editForm.location.trim()) errors.location = "Camp location is required.";
    if (!editForm.camp_date) errors.camp_date = "Camp date is required.";
    if (!editForm.target_units || Number(editForm.target_units) <= 0) {
      errors.target_units = "Target units must be greater than 0.";
    }
    if (Number(editForm.units_collected) < 0) {
      errors.units_collected = "Units collected cannot be negative.";
    }
    if (Object.keys(errors).length > 0) {
      setFormErrors(errors);
      return;
    }

    setSubmitting(true);
    setFormErrors({});
    try {
      await updateCamp(editingCamp.camp_id, {
        location: editForm.location.trim(),
        camp_date: editForm.camp_date,
        target_units: parseInt(editForm.target_units, 10),
        units_collected: parseInt(editForm.units_collected, 10) || 0,
      });
      toast.success("Camp details updated successfully.");
      setEditingCamp(null);
      fetchCamps();
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setSubmitting(false);
    }
  };

  // Handle Delete Camp
  const handleDeleteSubmit = async () => {
    if (!deleteTarget) return;
    setSubmitting(true);
    try {
      await deleteCamp(deleteTarget.camp_id);
      toast.success("Donation camp deleted successfully.");
      setDeleteTarget(null);
      fetchCamps();
    } catch (err) {
      setError(getErrorMessage(err));
      setDeleteTarget(null);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Title & Actions */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">Donation Camps</h1>
          <p className="text-sm text-slate-500 mt-1">
            Schedule, monitor and track blood donation drives and unit collection targets
          </p>
        </div>
        <Button variant="primary" icon={Plus} onClick={handleOpenCreate}>
          Schedule Camp
        </Button>
      </div>

      {error && <ErrorBanner message={error} onDismiss={() => setError(null)} />}

      {/* Date Filter Toolbar */}
      <div className="bg-white p-4 rounded-2xl border border-slate-200/80 shadow-sm space-y-3">
        <form onSubmit={handleFilterSubmit} className="grid grid-cols-1 sm:grid-cols-3 lg:grid-cols-4 gap-3">
          <Input
            type="date"
            placeholder="From Date"
            value={startDate}
            onChange={(e) => {
              setStartDate(e.target.value);
              setPage(1);
            }}
            icon={Calendar}
          />
          <Input
            type="date"
            placeholder="To Date"
            value={endDate}
            onChange={(e) => {
              setEndDate(e.target.value);
              setPage(1);
            }}
            icon={Calendar}
          />
          <div className="flex items-center gap-2">
            <Button type="submit" variant="secondary" icon={Search} className="w-full">
              Filter
            </Button>
            {hasActiveFilters && (
              <Button type="button" variant="ghost" onClick={handleResetFilters} className="text-xs text-blood-600">
                Reset
              </Button>
            )}
          </div>
        </form>
      </div>

      {/* Main Table */}
      {loading ? (
        <div className="flex justify-center items-center py-24">
          <Spinner size="lg" />
        </div>
      ) : camps.length === 0 ? (
        <EmptyState
          icon={Tent}
          title="No donation camps found"
          description={
            hasActiveFilters
              ? "No donation camps match the selected date filters."
              : "No donation drives have been scheduled yet."
          }
          action={
            hasActiveFilters
              ? { label: "Clear Filters", onClick: handleResetFilters }
              : { label: "Schedule Camp", onClick: handleOpenCreate }
          }
        />
      ) : (
        <div className="space-y-4">
          <div className="text-xs text-slate-500 font-medium">
            {total} donation drive{total !== 1 ? "s" : ""} on record
          </div>
          <Table headers={["ID", "Date", "Location", "Target", "Collected", "Progress", "Status", "Actions"]}>
            {camps.map((camp) => {
              const percentage =
                camp.target_units > 0
                  ? Math.round((camp.units_collected / camp.target_units) * 100)
                  : 0;

              let statusVariant = "routine";
              let statusLabel = "Completed";
              if (camp.camp_date > todayStr) {
                statusVariant = "info";
                statusLabel = "Upcoming";
              } else if (camp.camp_date === todayStr) {
                statusVariant = "warning";
                statusLabel = "Today";
              }

              return (
                <tr key={camp.camp_id} className="hover:bg-slate-50/75 transition-colors">
                  <td className="py-3.5 px-4 font-mono text-xs text-slate-500">#{camp.camp_id}</td>
                  <td className="py-3.5 px-4 text-xs font-semibold text-slate-900 whitespace-nowrap">
                    {formatDate(camp.camp_date)}
                  </td>
                  <td className="py-3.5 px-4 text-sm font-medium text-slate-800 max-w-xs truncate" title={camp.location}>
                    {camp.location}
                  </td>
                  <td className="py-3.5 px-4 font-mono text-xs text-slate-700">
                    {camp.target_units} units
                  </td>
                  <td className="py-3.5 px-4 font-mono text-xs font-bold text-slate-900">
                    {camp.units_collected} units
                  </td>
                  <td className="py-3.5 px-4 min-w-[140px]">
                    <div className="flex items-center gap-2">
                      <div className="flex-1 bg-slate-100 rounded-full h-2 overflow-hidden border border-slate-200">
                        <div
                          className={`h-full rounded-full transition-all duration-300 ${
                            percentage >= 100 ? "bg-emerald-500" : "bg-blood-500"
                          }`}
                          style={{ width: `${Math.min(100, percentage)}%` }}
                        />
                      </div>
                      <span className="text-[11px] font-mono font-semibold text-slate-600 w-9 text-right">
                        {percentage}%
                      </span>
                    </div>
                  </td>
                  <td className="py-3.5 px-4">
                    <Badge variant={statusVariant} size="sm">
                      {statusLabel}
                    </Badge>
                  </td>
                  <td className="py-3.5 px-4">
                    <div className="flex items-center gap-1.5">
                      <Button
                        variant="ghost"
                        size="sm"
                        icon={Edit}
                        onClick={() => handleOpenEdit(camp)}
                        title="Edit camp details"
                      >
                        Edit
                      </Button>
                      {user?.role === "admin" && (
                        <Button
                          variant="ghost"
                          size="sm"
                          icon={Trash2}
                          onClick={() => setDeleteTarget(camp)}
                          title="Delete camp"
                          className="text-rose-500 hover:text-rose-700"
                        />
                      )}
                    </div>
                  </td>
                </tr>
              );
            })}
          </Table>
          <Pagination currentPage={page} totalItems={total} pageSize={pageSize} onPageChange={setPage} />
        </div>
      )}

      {/* Modal: Schedule Camp */}
      <Modal isOpen={isCreateOpen} onClose={() => !submitting && setIsCreateOpen(false)} title="Schedule Donation Camp">
        <form onSubmit={handleCreateSubmit} className="space-y-4">
          <Input
            label="Drive Location"
            placeholder="e.g. St. Xavier's College Campus, Churchgate"
            value={createForm.location}
            onChange={(e) => setCreateForm({ ...createForm, location: e.target.value })}
            error={formErrors.location}
            required
          />
          <Input
            label="Camp Date"
            type="date"
            value={createForm.camp_date}
            onChange={(e) => setCreateForm({ ...createForm, camp_date: e.target.value })}
            error={formErrors.camp_date}
            required
          />
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Input
              label="Target Units"
              type="number"
              min="1"
              value={createForm.target_units}
              onChange={(e) => setCreateForm({ ...createForm, target_units: e.target.value })}
              error={formErrors.target_units}
              required
            />
            <Input
              label="Initial Collected Units"
              type="number"
              min="0"
              value={createForm.units_collected}
              onChange={(e) => setCreateForm({ ...createForm, units_collected: e.target.value })}
              error={formErrors.units_collected}
            />
          </div>
          <div className="flex justify-end gap-3 pt-3 border-t border-slate-100">
            <Button variant="secondary" onClick={() => setIsCreateOpen(false)} disabled={submitting}>
              Cancel
            </Button>
            <Button type="submit" variant="primary" loading={submitting}>
              Schedule Drive
            </Button>
          </div>
        </form>
      </Modal>

      {/* Modal: Edit Camp */}
      {editingCamp && (
        <Modal
          isOpen={!!editingCamp}
          onClose={() => !submitting && setEditingCamp(null)}
          title={`Edit Donation Camp #${editingCamp.camp_id}`}
        >
          <form onSubmit={handleEditSubmit} className="space-y-4">
            <Input
              label="Drive Location"
              value={editForm.location}
              onChange={(e) => setEditForm({ ...editForm, location: e.target.value })}
              error={formErrors.location}
              required
            />
            <Input
              label="Camp Date"
              type="date"
              value={editForm.camp_date}
              onChange={(e) => setEditForm({ ...editForm, camp_date: e.target.value })}
              error={formErrors.camp_date}
              required
            />
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <Input
                label="Target Units"
                type="number"
                min="1"
                value={editForm.target_units}
                onChange={(e) => setEditForm({ ...editForm, target_units: e.target.value })}
                error={formErrors.target_units}
                required
              />
              <Input
                label="Units Collected"
                type="number"
                min="0"
                value={editForm.units_collected}
                onChange={(e) => setEditForm({ ...editForm, units_collected: e.target.value })}
                error={formErrors.units_collected}
                required
              />
            </div>
            <div className="flex justify-end gap-3 pt-3 border-t border-slate-100">
              <Button variant="secondary" onClick={() => setEditingCamp(null)} disabled={submitting}>
                Cancel
              </Button>
              <Button type="submit" variant="primary" loading={submitting}>
                Save Changes
              </Button>
            </div>
          </form>
        </Modal>
      )}

      {/* Confirm Delete Dialog */}
      {deleteTarget && (
        <ConfirmDialog
          isOpen={!!deleteTarget}
          title="Delete Donation Camp"
          message={`Are you sure you want to delete the camp at "${deleteTarget.location}" scheduled for ${formatDate(
            deleteTarget.camp_date
          )}? This cannot be undone.`}
          confirmText="Delete Camp"
          onConfirm={handleDeleteSubmit}
          onClose={() => setDeleteTarget(null)}
          loading={submitting}
          confirmVariant="danger"
        />
      )}
    </div>
  );
}
