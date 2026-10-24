import React, { useState } from "react";
import { useToast } from "../../context/ToastContext";
import { downloadReport } from "../../api/reports";
import { getErrorMessage } from "../../utils/errors";
import Button from "../../components/ui/Button";
import Input from "../../components/ui/Input";
import ErrorBanner from "../../components/ui/ErrorBanner";
import {
  FileText,
  FileSpreadsheet,
  Download,
  Package,
  HeartHandshake,
  Send,
  AlertOctagon,
  Users,
  ClipboardList,
  TrendingUp,
  CheckCircle2,
} from "lucide-react";

const REPORT_TYPES = [
  {
    id: "stock",
    title: "Inventory Stock Summary",
    description: "Current unexpired stock counts across all 8 blood groups with safe minimums and low-stock alerts.",
    icon: Package,
    color: "sky",
    dateFiltered: false,
    columns: ["Blood Group", "Available Units", "Safe Minimum", "Status"],
  },
  {
    id: "donations",
    title: "Donation Collections Log",
    description: "Chronological log of all blood units collected from registered donors, collection and expiry dates.",
    icon: HeartHandshake,
    color: "emerald",
    dateFiltered: true,
    columns: ["Unit ID", "Donor ID", "Donor Name", "Blood Group", "Collection Date", "Expiry Date", "Status"],
  },
  {
    id: "issues",
    title: "Blood Issuance Log",
    description: "Traceable log of fulfilled blood requests linking units, patient requesters, and authorizing staff.",
    icon: Send,
    color: "blood",
    dateFiltered: true,
    columns: ["Issue ID", "Request ID", "Requester", "Unit ID", "Blood Group", "Issue Date", "Issued By"],
  },
  {
    id: "wastage",
    title: "Expired Units Wastage Audit",
    description: "Auditable accounting of units discarded after exceeding the 42-day whole blood shelf life.",
    icon: AlertOctagon,
    color: "rose",
    dateFiltered: true,
    columns: ["Unit ID", "Blood Group", "Collection Date", "Expiry Date"],
  },
  {
    id: "donors",
    title: "Registered Donors Directory",
    description: "Demographics, contact info, total donation history, and regular donor qualification status.",
    icon: Users,
    color: "purple",
    dateFiltered: false,
    columns: ["Donor ID", "Name", "Blood Group", "Phone", "Address", "Last Donation", "Total Donations", "Regular"],
  },
  {
    id: "requests",
    title: "Blood Requests & Fulfillment",
    description: "Incoming patient and hospital blood requests, urgency triage, quantities, and completion states.",
    icon: ClipboardList,
    color: "amber",
    dateFiltered: true,
    columns: ["Request ID", "Requester", "Blood Group", "Quantity", "Urgency", "Status", "Request Date"],
  },
  {
    id: "predictions",
    title: "Shortage Prediction Forecast",
    description: "Projections from the latest ML forecasting run (Linear Regression, Holt-Winters, ARIMA) with safe minimums.",
    icon: TrendingUp,
    color: "blue",
    dateFiltered: false,
    columns: ["Blood Group", "Model", "Forecast Date", "Predicted Stock", "Safe Minimum", "Below Min"],
  },
];

export default function ReportsPage() {
  const toast = useToast();

  const [selectedType, setSelectedType] = useState("stock");
  const [format, setFormat] = useState("pdf");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [downloading, setDownloading] = useState(false);
  const [error, setError] = useState(null);

  const activeReport = REPORT_TYPES.find((r) => r.id === selectedType) || REPORT_TYPES[0];

  const handleDownload = async (e) => {
    e.preventDefault();
    setDownloading(true);
    setError(null);
    try {
      const result = await downloadReport(selectedType, {
        format,
        startDate: activeReport.dateFiltered ? startDate : "",
        endDate: activeReport.dateFiltered ? endDate : "",
      });
      toast.success(`Successfully downloaded ${result.filename}`);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setDownloading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Title */}
      <div>
        <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">Export Operational Reports</h1>
        <p className="text-sm text-slate-500 mt-1">
          Generate official audit-ready reports in structured CSV spreadsheet or landscape ReportLab PDF
        </p>
      </div>

      {error && <ErrorBanner message={error} onDismiss={() => setError(null)} />}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Select Report Type (2 cols) */}
        <div className="lg:col-span-2 space-y-4">
          <label className="block text-xs font-bold uppercase tracking-wider text-slate-500">
            Select Report Domain
          </label>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5">
            {REPORT_TYPES.map((rep) => {
              const Icon = rep.icon;
              const isSelected = selectedType === rep.id;
              return (
                <div
                  key={rep.id}
                  onClick={() => setSelectedType(rep.id)}
                  className={`cursor-pointer p-4 rounded-2xl border transition-all duration-200 relative ${
                    isSelected
                      ? "bg-blood-50/40 border-blood-500 shadow-md shadow-blood-500/10 ring-1 ring-blood-500"
                      : "bg-white border-slate-200/80 hover:border-slate-300 hover:shadow-sm"
                  }`}
                >
                  <div className="flex items-start justify-between mb-2">
                    <div
                      className={`w-9 h-9 rounded-xl flex items-center justify-center ${
                        isSelected
                          ? "bg-blood-600 text-white"
                          : "bg-slate-100 text-slate-600"
                      }`}
                    >
                      <Icon className="w-4 h-4" />
                    </div>
                    {isSelected && (
                      <CheckCircle2 className="w-5 h-5 text-blood-600 animate-scale-up" />
                    )}
                  </div>
                  <h3 className="text-sm font-bold text-slate-900 mb-1">{rep.title}</h3>
                  <p className="text-xs text-slate-500 leading-relaxed">{rep.description}</p>
                </div>
              );
            })}
          </div>
        </div>

        {/* Right Column: Configuration & Export Action */}
        <div className="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-sm space-y-6 h-fit sticky top-6">
          <div className="border-b border-slate-100 pb-3">
            <h2 className="text-base font-bold text-slate-900">Export Settings</h2>
            <p className="text-xs text-slate-500 mt-0.5">
              Configuring <span className="font-semibold text-slate-700">{activeReport.title}</span>
            </p>
          </div>

          <form onSubmit={handleDownload} className="space-y-5">
            {/* Format Selector */}
            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-2">
                File Format
              </label>
              <div className="grid grid-cols-2 gap-3">
                <button
                  type="button"
                  onClick={() => setFormat("pdf")}
                  className={`flex flex-col items-center justify-center p-3 rounded-xl border text-xs font-semibold transition-all ${
                    format === "pdf"
                      ? "bg-blood-50 border-blood-500 text-blood-800 shadow-sm"
                      : "bg-white border-slate-200 text-slate-600 hover:bg-slate-50"
                  }`}
                >
                  <FileText className="w-5 h-5 mb-1.5 text-blood-600" />
                  <span>PDF Document</span>
                  <span className="text-[10px] text-slate-400 font-normal">Landscape & Paginated</span>
                </button>
                <button
                  type="button"
                  onClick={() => setFormat("csv")}
                  className={`flex flex-col items-center justify-center p-3 rounded-xl border text-xs font-semibold transition-all ${
                    format === "csv"
                      ? "bg-emerald-50 border-emerald-500 text-emerald-800 shadow-sm"
                      : "bg-white border-slate-200 text-slate-600 hover:bg-slate-50"
                  }`}
                >
                  <FileSpreadsheet className="w-5 h-5 mb-1.5 text-emerald-600" />
                  <span>CSV Spreadsheet</span>
                  <span className="text-[10px] text-slate-400 font-normal">UTF-8 Raw Data</span>
                </button>
              </div>
            </div>

            {/* Date Filters */}
            {activeReport.dateFiltered ? (
              <div className="space-y-3 pt-1">
                <label className="block text-xs font-bold uppercase tracking-wider text-slate-700">
                  Date Range (Optional)
                </label>
                <Input
                  type="date"
                  label="From Date"
                  value={startDate}
                  onChange={(e) => setStartDate(e.target.value)}
                />
                <Input
                  type="date"
                  label="To Date"
                  value={endDate}
                  onChange={(e) => setEndDate(e.target.value)}
                />
              </div>
            ) : (
              <div className="p-3.5 bg-slate-50 rounded-xl border border-slate-200 text-xs text-slate-500">
                <span className="font-semibold text-slate-700 block mb-0.5">Snapshot Report</span>
                This report exports the complete live database state or latest prediction run without date restrictions.
              </div>
            )}

            {/* Included Columns Preview */}
            <div>
              <span className="block text-[11px] font-bold uppercase tracking-wider text-slate-400 mb-1.5">
                Included Data Columns
              </span>
              <div className="flex flex-wrap gap-1.5">
                {activeReport.columns.map((col) => (
                  <span
                    key={col}
                    className="text-[10px] bg-slate-100 text-slate-600 font-mono px-2 py-0.5 rounded-md border border-slate-200"
                  >
                    {col}
                  </span>
                ))}
              </div>
            </div>

            {/* Download Button */}
            <div className="pt-2">
              <Button
                type="submit"
                variant="primary"
                icon={Download}
                loading={downloading}
                className="w-full justify-center shadow-lg shadow-blood-600/20"
              >
                {downloading ? "Compiling Report..." : `Download ${format.toUpperCase()}`}
              </Button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
