import apiClient from "./client";

/**
 * Download a system report in CSV or ReportLab PDF format.
 * Triggers a native browser file download using filename from Content-Disposition.
 */
export async function downloadReport(reportType, { format = "csv", startDate = "", endDate = "" } = {}) {
  const params = { format };
  if (startDate) params.start_date = startDate;
  if (endDate) params.end_date = endDate;

  try {
    const response = await apiClient.get(`/reports/${reportType}`, {
      params,
      responseType: "blob",
    });

    // Extract filename from Content-Disposition header
    let filename = `bloodlink_${reportType}.${format}`;
    const disposition = response.headers["content-disposition"];
    if (disposition) {
      const match = disposition.match(/filename=["']?([^"';]+)["']?/);
      if (match && match[1]) {
        filename = match[1];
      }
    }

    const mimeType = format === "pdf" ? "application/pdf" : "text/csv;charset=utf-8";
    const blob = new Blob([response.data], { type: mimeType });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.setAttribute("download", filename);
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);

    return { filename };
  } catch (error) {
    // If backend returned error JSON inside blob response, unpack and rethrow
    if (error.response?.data instanceof Blob) {
      try {
        const text = await error.response.data.text();
        const parsed = JSON.parse(text);
        if (parsed.detail) {
          const msg =
            typeof parsed.detail === "object"
              ? parsed.detail.message || parsed.detail.code
              : parsed.detail;
          throw new Error(msg);
        }
      } catch (jsonErr) {
        if (jsonErr.message && !jsonErr.message.includes("JSON")) {
          throw jsonErr;
        }
      }
    }
    throw error;
  }
}
