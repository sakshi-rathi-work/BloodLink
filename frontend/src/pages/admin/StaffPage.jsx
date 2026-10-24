import React, { useState, useEffect, useCallback } from "react";
import { useAuth } from "../../context/AuthContext";
import { useToast } from "../../context/ToastContext";
import { getStaff, createStaff, updateStaff, deleteStaff } from "../../api/staff";
import { getErrorMessage } from "../../utils/errors";
import Button from "../../components/ui/Button";
import Input from "../../components/ui/Input";
import Select from "../../components/ui/Select";
import Table from "../../components/ui/Table";
import Badge from "../../components/ui/Badge";
import Pagination from "../../components/ui/Pagination";
import Spinner from "../../components/ui/Spinner";
import EmptyState from "../../components/ui/EmptyState";
import ErrorBanner from "../../components/ui/ErrorBanner";
import Modal from "../../components/ui/Modal";
import ConfirmDialog from "../../components/ui/ConfirmDialog";
import { UserCog, UserPlus, KeyRound, Edit, Trash2 } from "lucide-react";

export default function StaffPage() {
  const { user: currentUser } = useAuth();
  const toast = useToast();

  const [staffList, setStaffList] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(20);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Modal states
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [editingStaff, setEditingStaff] = useState(null);
  const [passwordStaff, setPasswordStaff] = useState(null);
  const [deleteTarget, setDeleteTarget] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  // Form states
  const [createForm, setCreateForm] = useState({
    name: "",
    username: "",
    password: "",
    role: "staff",
  });
  const [editForm, setEditForm] = useState({
    name: "",
    role: "staff",
    is_active: true,
  });
  const [resetPassword, setResetPassword] = useState("");
  const [formErrors, setFormErrors] = useState({});

  const fetchStaff = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getStaff({ page, page_size: pageSize });
      setStaffList(data.items);
      setTotal(data.total);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }, [page, pageSize]);

  useEffect(() => {
    fetchStaff();
  }, [fetchStaff]);

  // Handle Create Staff
  const handleOpenCreate = () => {
    setCreateForm({ name: "", username: "", password: "", role: "staff" });
    setFormErrors({});
    setIsCreateOpen(true);
  };

  const handleCreateSubmit = async (e) => {
    e.preventDefault();
    const errors = {};
    if (!createForm.name.trim()) errors.name = "Full name is required.";
    if (!createForm.username.trim()) errors.username = "Username is required.";
    if (!createForm.password || createForm.password.length < 8) {
      errors.password = "Password must be at least 8 characters.";
    }
    if (Object.keys(errors).length > 0) {
      setFormErrors(errors);
      return;
    }

    setSubmitting(true);
    setFormErrors({});
    try {
      await createStaff(createForm);
      toast.success(`Account for ${createForm.name} created successfully.`);
      setIsCreateOpen(false);
      fetchStaff();
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setSubmitting(false);
    }
  };

  // Handle Edit Staff
  const handleOpenEdit = (staff) => {
    setEditingStaff(staff);
    setEditForm({
      name: staff.name,
      role: staff.role,
      is_active: staff.is_active,
    });
    setFormErrors({});
  };

  const handleEditSubmit = async (e) => {
    e.preventDefault();
    if (!editForm.name.trim()) {
      setFormErrors({ name: "Full name is required." });
      return;
    }

    setSubmitting(true);
    setFormErrors({});
    try {
      await updateStaff(editingStaff.staff_id, editForm);
      toast.success(`Staff account updated successfully.`);
      setEditingStaff(null);
      fetchStaff();
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setSubmitting(false);
    }
  };

  // Handle Reset Password
  const handleOpenPassword = (staff) => {
    setPasswordStaff(staff);
    setResetPassword("");
    setFormErrors({});
  };

  const handlePasswordSubmit = async (e) => {
    e.preventDefault();
    if (!resetPassword || resetPassword.length < 8) {
      setFormErrors({ password: "Password must be at least 8 characters." });
      return;
    }

    setSubmitting(true);
    setFormErrors({});
    try {
      await updateStaff(passwordStaff.staff_id, { password: resetPassword });
      toast.success(`Password for ${passwordStaff.name} has been reset.`);
      setPasswordStaff(null);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setSubmitting(false);
    }
  };

  // Handle Delete Staff
  const handleDeleteSubmit = async () => {
    if (!deleteTarget) return;
    setSubmitting(true);
    try {
      await deleteStaff(deleteTarget.staff_id);
      toast.success(`Staff account for ${deleteTarget.name} deleted.`);
      setDeleteTarget(null);
      fetchStaff();
    } catch (err) {
      setError(getErrorMessage(err));
      setDeleteTarget(null);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">Staff Management</h1>
          <p className="text-sm text-slate-500 mt-1">Manage staff and administrative user accounts and system permissions</p>
        </div>
        <Button variant="primary" icon={UserPlus} onClick={handleOpenCreate}>
          Add Staff Member
        </Button>
      </div>

      {error && <ErrorBanner message={error} onDismiss={() => setError(null)} />}

      {/* Content */}
      {loading ? (
        <div className="flex justify-center items-center py-24">
          <Spinner size="lg" />
        </div>
      ) : staffList.length === 0 ? (
        <EmptyState
          icon={UserCog}
          title="No staff accounts found"
          description="There are currently no staff accounts created."
          action={{ label: "Add Staff Member", onClick: handleOpenCreate }}
        />
      ) : (
        <div className="space-y-4">
          <div className="text-xs text-slate-500 font-medium">
            {total} account{total !== 1 ? "s" : ""} registered
          </div>
          <Table headers={["ID", "Name", "Username", "Role", "Status", "Actions"]}>
            {staffList.map((member) => {
              const isSelf = currentUser?.user_id === member.user_id;
              return (
                <tr key={member.staff_id} className="hover:bg-slate-50/75 transition-colors">
                  <td className="py-3.5 px-4 font-mono text-xs text-slate-500">#{member.staff_id}</td>
                  <td className="py-3.5 px-4 font-semibold text-slate-900">
                    {member.name}
                    {isSelf && (
                      <span className="ml-2 text-[10px] font-bold uppercase tracking-wider text-blood-600 bg-blood-50 border border-blood-200 px-1.5 py-0.5 rounded-full">
                        You
                      </span>
                    )}
                  </td>
                  <td className="py-3.5 px-4 text-xs font-mono text-slate-600">@{member.username}</td>
                  <td className="py-3.5 px-4">
                    <Badge variant={member.role === "admin" ? "emergency" : "approved"} size="sm">
                      {member.role}
                    </Badge>
                  </td>
                  <td className="py-3.5 px-4">
                    <Badge variant={member.is_active ? "available" : "expired"} size="sm">
                      {member.is_active ? "Active" : "Inactive"}
                    </Badge>
                  </td>
                  <td className="py-3.5 px-4">
                    <div className="flex items-center gap-1.5">
                      <Button
                        variant="ghost"
                        size="sm"
                        icon={Edit}
                        onClick={() => handleOpenEdit(member)}
                        title="Edit staff details"
                      >
                        Edit
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        icon={KeyRound}
                        onClick={() => handleOpenPassword(member)}
                        title="Reset password"
                      />
                      <Button
                        variant="ghost"
                        size="sm"
                        icon={Trash2}
                        onClick={() => setDeleteTarget(member)}
                        disabled={isSelf}
                        title={isSelf ? "You cannot delete your own account" : "Delete account"}
                        className={isSelf ? "opacity-30 cursor-not-allowed" : "text-rose-500 hover:text-rose-700"}
                      />
                    </div>
                  </td>
                </tr>
              );
            })}
          </Table>
          <Pagination currentPage={page} totalItems={total} pageSize={pageSize} onPageChange={setPage} />
        </div>
      )}

      {/* Modal: Create Staff */}
      <Modal isOpen={isCreateOpen} onClose={() => !submitting && setIsCreateOpen(false)} title="Create Staff Account">
        <form onSubmit={handleCreateSubmit} className="space-y-4">
          <Input
            label="Full Name"
            placeholder="e.g. Dr. Priya Sharma"
            value={createForm.name}
            onChange={(e) => setCreateForm({ ...createForm, name: e.target.value })}
            error={formErrors.name}
            required
          />
          <Input
            label="Username"
            placeholder="e.g. priya_s"
            value={createForm.username}
            onChange={(e) => setCreateForm({ ...createForm, username: e.target.value })}
            error={formErrors.username}
            required
          />
          <Input
            label="Initial Password"
            type="password"
            placeholder="Minimum 8 characters"
            value={createForm.password}
            onChange={(e) => setCreateForm({ ...createForm, password: e.target.value })}
            error={formErrors.password}
            required
          />
          <Select
            label="Role"
            value={createForm.role}
            onChange={(e) => setCreateForm({ ...createForm, role: e.target.value })}
            options={[
              { value: "staff", label: "Staff (Operational Access)" },
              { value: "admin", label: "Admin (Full System Access)" },
            ]}
          />
          <div className="flex justify-end gap-3 pt-3 border-t border-slate-100">
            <Button variant="secondary" onClick={() => setIsCreateOpen(false)} disabled={submitting}>
              Cancel
            </Button>
            <Button type="submit" variant="primary" loading={submitting}>
              Create Account
            </Button>
          </div>
        </form>
      </Modal>

      {/* Modal: Edit Staff */}
      {editingStaff && (
        <Modal
          isOpen={!!editingStaff}
          onClose={() => !submitting && setEditingStaff(null)}
          title={`Edit Account: ${editingStaff.name}`}
        >
          <form onSubmit={handleEditSubmit} className="space-y-4">
            <Input
              label="Full Name"
              value={editForm.name}
              onChange={(e) => setEditForm({ ...editForm, name: e.target.value })}
              error={formErrors.name}
              required
            />
            <Select
              label="Role"
              value={editForm.role}
              disabled={currentUser?.user_id === editingStaff.user_id}
              onChange={(e) => setEditForm({ ...editForm, role: e.target.value })}
              options={[
                { value: "staff", label: "Staff" },
                { value: "admin", label: "Admin" },
              ]}
              helperText={
                currentUser?.user_id === editingStaff.user_id
                  ? "You cannot alter your own administrative role."
                  : undefined
              }
            />
            <Select
              label="Account Status"
              value={editForm.is_active ? "active" : "inactive"}
              disabled={currentUser?.user_id === editingStaff.user_id}
              onChange={(e) => setEditForm({ ...editForm, is_active: e.target.value === "active" })}
              options={[
                { value: "active", label: "Active (Can log in)" },
                { value: "inactive", label: "Inactive (Disabled)" },
              ]}
              helperText={
                currentUser?.user_id === editingStaff.user_id
                  ? "You cannot deactivate your own administrative account."
                  : undefined
              }
            />
            <div className="flex justify-end gap-3 pt-3 border-t border-slate-100">
              <Button variant="secondary" onClick={() => setEditingStaff(null)} disabled={submitting}>
                Cancel
              </Button>
              <Button type="submit" variant="primary" loading={submitting}>
                Save Changes
              </Button>
            </div>
          </form>
        </Modal>
      )}

      {/* Modal: Reset Password */}
      {passwordStaff && (
        <Modal
          isOpen={!!passwordStaff}
          onClose={() => !submitting && setPasswordStaff(null)}
          title={`Reset Password: ${passwordStaff.name}`}
        >
          <form onSubmit={handlePasswordSubmit} className="space-y-4">
            <p className="text-sm text-slate-500">
              Enter a new password for <span className="font-semibold text-slate-700">@{passwordStaff.username}</span>.
            </p>
            <Input
              label="New Password"
              type="password"
              placeholder="Minimum 8 characters"
              value={resetPassword}
              onChange={(e) => setResetPassword(e.target.value)}
              error={formErrors.password}
              required
            />
            <div className="flex justify-end gap-3 pt-3 border-t border-slate-100">
              <Button variant="secondary" onClick={() => setPasswordStaff(null)} disabled={submitting}>
                Cancel
              </Button>
              <Button type="submit" variant="primary" loading={submitting}>
                Update Password
              </Button>
            </div>
          </form>
        </Modal>
      )}

      {/* Confirm Delete Dialog */}
      {deleteTarget && (
        <ConfirmDialog
          isOpen={!!deleteTarget}
          title="Delete Staff Account"
          message={`Are you sure you want to permanently delete "${deleteTarget.name}" (@${deleteTarget.username})? If this user has recorded blood unit issuances, they cannot be deleted and should be deactivated instead.`}
          confirmText="Delete Staff"
          onConfirm={handleDeleteSubmit}
          onClose={() => setDeleteTarget(null)}
          loading={submitting}
          confirmVariant="danger"
        />
      )}
    </div>
  );
}
