import csv
import io
import httpx
from app.services.reports.definitions import REPORT_METADATA


def test_download_all_reports_csv_format(staff_client: httpx.Client):
    for report_type in REPORT_METADATA.keys():
        response = staff_client.get(f"/api/reports/{report_type}?format=csv")
        assert response.status_code == 200, f"Failed for report_type: {report_type}"
        assert "text/csv" in response.headers["Content-Type"]
        assert f"bloodlink_{report_type}_" in response.headers["Content-Disposition"]
        assert response.headers["Content-Disposition"].endswith('.csv"')
        assert response.headers.get("X-Content-Type-Options") == "nosniff"

        # Verify CSV parseable
        content_str = response.text
        reader = list(csv.reader(io.StringIO(content_str)))
        assert len(reader) >= 1  # At least header row exists
        expected_columns = REPORT_METADATA[report_type]["columns"]
        assert reader[0] == expected_columns


def test_download_all_reports_pdf_format(staff_client: httpx.Client):
    for report_type in REPORT_METADATA.keys():
        response = staff_client.get(f"/api/reports/{report_type}?format=pdf")
        assert response.status_code == 200, f"Failed for report_type: {report_type}"
        assert response.headers["Content-Type"] == "application/pdf"
        assert f"bloodlink_{report_type}_" in response.headers["Content-Disposition"]
        assert response.headers["Content-Disposition"].endswith('.pdf"')
        assert response.headers.get("X-Content-Type-Options") == "nosniff"

        # Verify PDF magic bytes
        assert response.content.startswith(b"%PDF-")


def test_download_report_unknown_type_404(staff_client: httpx.Client):
    response = staff_client.get("/api/reports/unknown_xyz?format=csv")
    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "NOT_FOUND"


def test_download_report_invalid_format_422(staff_client: httpx.Client):
    response = staff_client.get("/api/reports/stock?format=docx")
    assert response.status_code == 422


def test_download_report_requester_forbidden(requester_client: httpx.Client):
    response = requester_client.get("/api/reports/stock?format=csv")
    assert response.status_code == 403
    assert response.json()["detail"]["code"] == "FORBIDDEN"
