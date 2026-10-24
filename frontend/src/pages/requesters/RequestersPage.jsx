import React, { useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { getRequesters, deleteRequester } from "../../api/requesters";
import { REQUESTER_TYPES } from "../../utils/constants";
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
import ConfirmDialog from "../../components/ui/ConfirmDialog";
import { Users, Search, Eye, Trash2 } from "lucide-react";

export default function RequestersPage() {
  const navigate = useNavigate();
  const [requesters, setRequesters] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(20);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [search, setSearch] = useState("");
  const [typeFilter, setTypeFilter] = useState("");
  const [deleteTarget, setDeleteTarget] = useState(null);
  const [deleting, setDeleting] = useState(false);

  const fetchRequesters = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params = { page, page_size: pageSize };
      if (search.trim()) params.q = search.trim();
      if (typeFilter) params.type = typeFilter;
      const data = await getRequesters(params);
      setRequesters(data.items);
      setTotal(data.total);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }, [page, pageSize, search, typeFilter]);

  useEffect(() => { fetchRequesters(); }, [fetchRequesters]);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    setPage(1);
    fetchRequesters();
  };

  const handleReset = () => {
    setSearch("");
    setTypeFilter("");
    setPage(1);
  };

  const handleDelete = async () => {
    if (!deleteTarget) return;
    setDeleting(true);
    try {
      await deleteRequester(deleteTarget.requester_id);
      setDeleteTarget(null);
      fetchRequesters();
    } catch (err) {
      setError(getErrorMessage(err));
      setDeleteTarget(null);
    } finally {
      setDeleting(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">Requesters Directory</h1>
        <p className="text-sm text-slate-500 mt-1">Browse hospitals and patients registered as blood requesters</p>
      </div>

      {error && <ErrorBanner message={error} onDismiss={() => setError(null)} />}

      {/* Filters */}
      <div className="bg-white p-4 rounded-2xl border border-slate-200/80 shadow-sm space-y-3">
        <form onSubmit={handleSearchSubmit} className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <Input
            placeholder="Search name or phone..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            icon={Search}
          />
          <Select
            value={typeFilter}
            onChange={(e) => { setTypeFilter(e.target.value); setPage(1); }}
            options={[
              { value: "", label: "All Types" },
              ...REQUESTER_TYPES.map((t) => ({ value: t.value, label: t.label })),
            ]}
          />
          <Button type="submit" variant="secondary" icon={Search}>Search</Button>
        </form>
        {(search || typeFilter) && (
          <div className="flex justify-end">
            <button onClick={handleReset} className="text-xs font-semibold text-blood-600 hover:text-blood-700 underline">
              Reset Filters
            </button>
          </div>
        )}
      </div>

      {/* Content */}
      {loading ? (
        <div className="flex justify-center items-center py-20"><Spinner size="lg" /></div>
      ) : requesters.length === 0 ? (
        <EmptyState
          icon={Users}
          title="No requesters found"
          description={
            search || typeFilter
              ? "No requesters match your search."
              : "No requesters have been registered yet."
          }
          action={search || typeFilter ? { label: "Clear Filters", onClick: handleReset } : undefined}
        />
      ) : (
        <div className="space-y-4">
          <div className="text-xs text-slate-500 font-medium">{total} requester{total !== 1 ? "s" : ""} found</div>
          <Table headers={["ID", "Name", "Type", "Username", "Phone", "Address", "Actions"]}>
            {requesters.map((r) => (
              <tr key={r.requester_id} className="hover:bg-slate-50/75 transition-colors">
                <td className="py-3.5 px-4 font-mono text-xs text-slate-500">#{r.requester_id}</td>
                <td className="py-3.5 px-4 font-semibold text-slate-900">{r.name}</td>
                <td className="py-3.5 px-4">
                  <Badge variant={r.type === "hospital" ? "info" : "default"} size="sm">
                    {r.type}
                  </Badge>
                </td>
                <td className="py-3.5 px-4 text-xs text-slate-500">@{r.username}</td>
                <td className="py-3.5 px-4 font-mono text-xs text-slate-600">{r.phone}</td>
                <td className="py-3.5 px-4 text-xs text-slate-600 max-w-xs truncate" title={r.address}>{r.address}</td>
                <td className="py-3.5 px-4">
                  <div className="flex items-center gap-2">
                    <Button
                      variant="ghost"
                      size="sm"
                      icon={Eye}
                      onClick={() => navigate(`/requests?requester_id=${r.requester_id}`)}
                      title="View requests from this requester"
                    >
                      Requests
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      icon={Trash2}
                      onClick={() => setDeleteTarget(r)}
                      title="Delete requester account"
                      className="text-red-500 hover:text-red-700"
                    />
                  </div>
                </td>
              </tr>
            ))}
          </Table>
          <Pagination currentPage={page} totalItems={total} pageSize={pageSize} onPageChange={setPage} />
        </div>
      )}

      {/* Confirm Delete */}
      {deleteTarget && (
        <ConfirmDialog
          isOpen={!!deleteTarget}
          title="Delete Requester Account"
          message={`Permanently delete requester "${deleteTarget.name}" (@${deleteTarget.username})? This cannot be undone.`}
          confirmText="Delete"
          onConfirm={handleDelete}
          onClose={() => setDeleteTarget(null)}
          loading={deleting}
          confirmVariant="danger"
        />
      )}
    </div>
  );
}
