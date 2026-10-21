import React, { useState, useEffect, useCallback } from "react";
import { Link, useNavigate } from "react-router-dom";
import { getDonors } from "../../api/donors";
import { BLOOD_GROUPS } from "../../utils/constants";
import { formatDate } from "../../utils/format";
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
import { Users, Plus, Search, Filter, Eye, Edit } from "lucide-react";

export default function DonorListPage() {
  const navigate = useNavigate();
  const [donors, setDonors] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(15);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Filters
  const [search, setSearch] = useState("");
  const [bloodGroup, setBloodGroup] = useState("");
  const [location, setLocation] = useState("");
  const [regularFilter, setRegularFilter] = useState("");
  const [sortBy, setSortBy] = useState("name");

  const fetchDonors = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params = {
        page,
        page_size: pageSize,
        sort: sortBy,
      };
      if (search.trim()) params.q = search.trim();
      if (bloodGroup) params.blood_group = bloodGroup;
      if (location.trim()) params.location = location.trim();
      if (regularFilter === "true") params.is_regular = true;
      if (regularFilter === "false") params.is_regular = false;

      const data = await getDonors(params);
      setDonors(data.items);
      setTotal(data.total);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }, [page, pageSize, sortBy, search, bloodGroup, location, regularFilter]);

  useEffect(() => {
    fetchDonors();
  }, [fetchDonors]);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    setPage(1);
    fetchDonors();
  };

  const handleResetFilters = () => {
    setSearch("");
    setBloodGroup("");
    setLocation("");
    setRegularFilter("");
    setSortBy("name");
    setPage(1);
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">
            Donor Directory
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Browse registered donors, verify eligibility status, and record blood collections
          </p>
        </div>
        <Button
          variant="primary"
          icon={Plus}
          onClick={() => navigate("/donors/new")}
        >
          Register New Donor
        </Button>
      </div>

      {error && <ErrorBanner message={error} onDismiss={() => setError(null)} />}

      {/* Filter and Search Bar */}
      <div className="bg-white p-4 rounded-2xl border border-slate-200/80 shadow-sm space-y-4">
        <form onSubmit={handleSearchSubmit} className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
          <Input
            placeholder="Search name or phone..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            icon={Search}
          />

          <Select
            value={bloodGroup}
            onChange={(e) => {
              setBloodGroup(e.target.value);
              setPage(1);
            }}
            options={[
              { value: "", label: "All Blood Groups" },
              ...BLOOD_GROUPS.map((bg) => ({ value: bg, label: `Blood Group: ${bg}` })),
            ]}
          />

          <Input
            placeholder="Filter location..."
            value={location}
            onChange={(e) => setLocation(e.target.value)}
            icon={Filter}
          />

          <Select
            value={regularFilter}
            onChange={(e) => {
              setRegularFilter(e.target.value);
              setPage(1);
            }}
            options={[
              { value: "", label: "All Donor Types" },
              { value: "true", label: "Regular Donors Only" },
              { value: "false", label: "Non-Regular Only" },
            ]}
          />

          <Select
            value={sortBy}
            onChange={(e) => {
              setSortBy(e.target.value);
              setPage(1);
            }}
            options={[
              { value: "name", label: "Sort: Name (A-Z)" },
              { value: "last_donation_date", label: "Sort: Last Donation" },
            ]}
          />
        </form>

        {(search || bloodGroup || location || regularFilter || sortBy !== "name") && (
          <div className="flex justify-end">
            <button
              type="button"
              onClick={handleResetFilters}
              className="text-xs font-semibold text-blood-600 hover:text-blood-700 underline"
            >
              Reset All Filters
            </button>
          </div>
        )}
      </div>

      {/* Content Area */}
      {loading ? (
        <div className="flex justify-center items-center py-20">
          <Spinner size="lg" />
        </div>
      ) : donors.length === 0 ? (
        <EmptyState
          icon={Users}
          title="No donors found"
          description={
            search || bloodGroup || location || regularFilter
              ? "No donors match your search filters. Try clearing some criteria."
              : "No donors have been registered yet. Click 'Register New Donor' to create your first donor profile."
          }
          action={
            search || bloodGroup || location || regularFilter
              ? { label: "Clear Filters", onClick: handleResetFilters }
              : { label: "Register New Donor", onClick: () => navigate("/donors/new") }
          }
        />
      ) : (
        <div className="space-y-4">
          <Table
            headers={[
              "Donor Name",
              "Blood Group",
              "Contact",
              "Location",
              "Weight",
              "Last Donation",
              "Donations",
              "Status",
              "Actions",
            ]}
          >
            {donors.map((donor) => (
              <tr key={donor.donor_id} className="hover:bg-slate-50/75 transition-colors">
                <td className="py-3.5 px-4">
                  <div className="font-semibold text-slate-900">
                    <Link
                      to={`/donors/${donor.donor_id}`}
                      className="hover:text-blood-600 transition-colors"
                    >
                      {donor.name}
                    </Link>
                  </div>
                  <div className="text-xs text-slate-400 capitalize">
                    {donor.gender} · DOB: {donor.dob}
                  </div>
                </td>
                <td className="py-3.5 px-4">
                  <span className="inline-flex items-center px-2.5 py-1 rounded-md text-xs font-bold bg-blood-100 text-blood-800 border border-blood-200">
                    {donor.blood_group}
                  </span>
                </td>
                <td className="py-3.5 px-4 font-mono text-xs text-slate-600">
                  {donor.phone}
                </td>
                <td className="py-3.5 px-4 text-xs text-slate-600 max-w-xs truncate" title={donor.address}>
                  {donor.address}
                </td>
                <td className="py-3.5 px-4 text-xs text-slate-700 font-medium">
                  {donor.weight} kg
                </td>
                <td className="py-3.5 px-4 text-xs text-slate-600">
                  {formatDate(donor.last_donation_date)}
                </td>
                <td className="py-3.5 px-4 text-xs font-semibold text-slate-800">
                  {donor.donation_count}
                </td>
                <td className="py-3.5 px-4">
                  {donor.is_regular ? (
                    <Badge variant="regular" size="sm">
                      Regular Donor
                    </Badge>
                  ) : (
                    <span className="text-xs text-slate-400">—</span>
                  )}
                </td>
                <td className="py-3.5 px-4">
                  <div className="flex items-center gap-2">
                    <Button
                      variant="ghost"
                      size="sm"
                      icon={Eye}
                      onClick={() => navigate(`/donors/${donor.donor_id}`)}
                      title="View Details & Eligibility"
                    >
                      View
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      icon={Edit}
                      onClick={() => navigate(`/donors/${donor.donor_id}/edit`)}
                      title="Edit Profile"
                    />
                  </div>
                </td>
              </tr>
            ))}
          </Table>

          {/* Pagination */}
          <Pagination
            currentPage={page}
            totalItems={total}
            pageSize={pageSize}
            onPageChange={setPage}
          />
        </div>
      )}
    </div>
  );
}
