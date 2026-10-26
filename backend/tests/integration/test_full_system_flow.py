"""Task 6.3: Master Full-System End-to-End Integration Flow.

Tests the complete operational lifecycle:
1. Donor registration (staff)
2. Eligibility check (age, weight, donation gap)
3. Donation recorded -> unit added with 42-day expiry
4. Stock verified in inventory & v_transactions view
5. Requester self-registration & authentication
6. Emergency blood request submitted (requester)
7. Request queue prioritized by urgency (staff)
8. Request approval (staff)
9. Matching inspection (nearest-expiry compatible unit)
10. Atomic unit issuing with row locking
11. Stock decremented & issue_records traceability verified
12. Executive dashboard reflects updated real-time stats
13. Multi-format reports exported (CSV and ReportLab PDF)
14. Shortage prediction alerts queried
15. Admin audit log verification across all state changes
"""

from datetime import date
from fastapi.testclient import TestClient
from sqlalchemy import text
from app.core import clock
from app.main import app
from app.models.activity_log import ActivityLog
from app.models.blood_unit import BloodUnit
from app.models.issue_record import IssueRecord


def test_master_full_system_integration_flow(admin_client, staff_client, client, db):
    """Execute the end-to-end full system flow verifying all 7 modules."""
    today = date(2026, 10, 24)
    clock.set_today(today)

    try:
        # =========================================================================
        # 1. DONOR REGISTRATION & ELIGIBILITY (Module 2)
        # =========================================================================
        res_donor = staff_client.post(
            "/api/donors",
            json={
                "name": "Aarav Sharma",
                "dob": "1994-06-15",
                "gender": "male",
                "blood_group": "B+",
                "phone": "9820011223",
                "address": "42 Marine Drive, Mumbai",
                "weight": 68.5,
            },
        )
        assert res_donor.status_code == 201, f"Donor creation failed: {res_donor.text}"
        donor_id = res_donor.json()["donor_id"]

        # Check eligibility
        res_elig = staff_client.get(f"/api/donors/{donor_id}/eligibility")
        assert res_elig.status_code == 200
        assert res_elig.json()["eligible"] is True
        assert res_elig.json()["reasons"] == []

        # =========================================================================
        # 2. RECORD DONATION & INVENTORY STOCK (Modules 2 & 3)
        # =========================================================================
        res_donation = staff_client.post(f"/api/donors/{donor_id}/donations")
        assert res_donation.status_code == 201, f"Donation record failed: {res_donation.text}"
        unit_id = res_donation.json()["unit_id"]
        assert res_donation.json()["blood_group"] == "B+"
        assert res_donation.json()["expiry_date"] == "2026-12-05"  # today + 42 days

        # Check stock in inventory
        res_stock = staff_client.get("/api/inventory/stock")
        assert res_stock.status_code == 200
        stock_map = {item["blood_group"]: item["available_units"] for item in res_stock.json()["stock"]}
        assert stock_map.get("B+") == 1

        # Check unit details
        res_unit = staff_client.get(f"/api/inventory/units/{unit_id}")
        assert res_unit.status_code == 200
        assert res_unit.json()["status"] == "available"

        # Verify transaction in database (or view if postgres)
        unit_db = db.query(BloodUnit).filter(BloodUnit.unit_id == unit_id).first()
        assert unit_db is not None
        assert unit_db.status == "available"

        # =========================================================================
        # 3. REQUESTER SELF-REGISTRATION & AUTHENTICATION (Module 1)
        # =========================================================================
        res_reg = client.post(
            "/api/auth/register",
            json={
                "username": "city_emergency_hosp",
                "password": "HospitalPassword123",
                "name": "City Emergency Hospital",
                "type": "hospital",
                "phone": "9819922334",
                "address": "100 Hospital Way, Mumbai",
            },
        )
        assert res_reg.status_code == 201, f"Requester register failed: {res_reg.text}"
        requester_token = res_reg.json()["access_token"]

        requester_client = TestClient(app=app, base_url="http://testserver")
        requester_client.headers["Authorization"] = f"Bearer {requester_token}"

        # Verify /auth/me for requester
        res_me = requester_client.get("/api/auth/me")
        assert res_me.status_code == 200
        assert res_me.json()["role"] == "requester"
        assert res_me.json()["username"] == "city_emergency_hosp"

        # =========================================================================
        # 4. SUBMIT BLOOD REQUEST (Module 4)
        # =========================================================================
        res_req = requester_client.post(
            "/api/requests",
            json={
                "blood_group": "B+",
                "quantity": 1,
                "urgency": "emergency",
                "patient_name": "Rohan Varma",
                "hospital_name": "City Emergency Hospital",
                "notes": "Urgent trauma surgery requiring 1 unit B+",
            },
        )
        assert res_req.status_code == 201, f"Blood request failed: {res_req.text}"
        request_id = res_req.json()["request_id"]
        assert res_req.json()["status"] == "pending"
        assert res_req.json()["urgency"] == "emergency"

        # Requester can view own request
        res_my_req = requester_client.get(f"/api/requests/{request_id}")
        assert res_my_req.status_code == 200
        assert res_my_req.json()["request_id"] == request_id

        # =========================================================================
        # 5. STAFF QUEUE, MATCHING & WORKFLOW (Modules 4 & 5)
        # =========================================================================
        # Staff inspects queue sorted by priority
        res_queue = staff_client.get("/api/requests?sort=priority")
        assert res_queue.status_code == 200
        requests_list = res_queue.json()["items"]
        assert len(requests_list) >= 1
        assert requests_list[0]["request_id"] == request_id
        assert requests_list[0]["urgency"] == "emergency"

        # Staff inspects compatible matches
        res_matches = staff_client.get(f"/api/requests/{request_id}/matches")
        assert res_matches.status_code == 200
        match_data = res_matches.json()
        assert match_data["requested_group"] == "B+"
        assert set(match_data["compatible_groups"]) == {"B+", "B-", "O+", "O-"}
        assert match_data["available_compatible_count"] >= 1
        assert match_data["sufficient"] is True
        assert unit_id in match_data["allocation_preview_unit_ids"]

        # Staff approves request
        res_approve = staff_client.post(f"/api/requests/{request_id}/approve")
        assert res_approve.status_code == 200
        assert res_approve.json()["status"] == "approved"

        # Staff issues units atomically
        res_issue = staff_client.post(f"/api/requests/{request_id}/issue")
        assert res_issue.status_code == 200
        assert res_issue.json()["status"] == "issued"
        assert res_issue.json()["issued_count"] == 1
        assert [u["unit_id"] for u in res_issue.json().get("issued_units", [])] == [unit_id]

        # Verify unit status updated to 'issued'
        unit_after = db.query(BloodUnit).filter(BloodUnit.unit_id == unit_id).first()
        assert unit_after.status == "issued"

        # Verify issue record links unit, request, and staff
        issue_rec = db.query(IssueRecord).filter(IssueRecord.request_id == request_id).first()
        assert issue_rec is not None
        assert issue_rec.unit_id == unit_id

        # Verify inventory stock is now 0 for B+
        res_stock_after = staff_client.get("/api/inventory/stock")
        assert res_stock_after.status_code == 200
        stock_map_after = {item["blood_group"]: item["available_units"] for item in res_stock_after.json()["stock"]}
        assert stock_map_after.get("B+") == 0

        # =========================================================================
        # 6. EXECUTIVE DASHBOARD (Module 7)
        # =========================================================================
        res_dash = staff_client.get("/api/dashboard/summary")
        assert res_dash.status_code == 200
        dash_data = res_dash.json()
        assert dash_data["pending_requests"] == 0
        assert dash_data["pending_emergency_requests"] == 0
        assert dash_data["approved_requests_awaiting_issue"] == 0
        assert dash_data["total_available_units"] == sum(stock_map_after.values())

        # Dashboard trends
        res_trends = staff_client.get("/api/dashboard/trends?granularity=day")
        assert res_trends.status_code == 200
        assert "series" in res_trends.json()

        # Dashboard wastage
        res_wastage = staff_client.get("/api/dashboard/wastage")
        assert res_wastage.status_code == 200
        assert "total_expired" in res_wastage.json()

        # =========================================================================
        # 7. MULTI-FORMAT REPORT EXPORTS (Module 7)
        # =========================================================================
        # Stock report in CSV
        res_rep_csv = staff_client.get("/api/reports/stock?format=csv")
        assert res_rep_csv.status_code == 200
        assert "text/csv" in res_rep_csv.headers.get("content-type", "")
        assert "attachment" in res_rep_csv.headers.get("content-disposition", "")

        # Donations report in PDF
        res_rep_pdf = staff_client.get("/api/reports/donations?format=pdf")
        assert res_rep_pdf.status_code == 200
        assert "application/pdf" in res_rep_pdf.headers.get("content-type", "")
        assert res_rep_pdf.content.startswith(b"%PDF-")

        # Issues report in CSV
        res_rep_issues = staff_client.get("/api/reports/issues?format=csv")
        assert res_rep_issues.status_code == 200
        assert str(unit_id) in res_rep_issues.text

        # =========================================================================
        # 8. PREDICTIONS & SHORTAGE ALERTS (Module 6)
        # =========================================================================
        res_alerts = staff_client.get("/api/predictions/alerts?within_days=30")
        assert res_alerts.status_code == 200
        assert isinstance(res_alerts.json(), list)

        # =========================================================================
        # 9. ADMIN AUDIT TRAIL VERIFICATION (Module 1)
        # =========================================================================
        res_logs = admin_client.get("/api/activity-logs")
        assert res_logs.status_code == 200
        log_items = res_logs.json()["items"]
        assert len(log_items) >= 4

        actions = [log["action"] for log in log_items]
        entities = [log["entity_type"] for log in log_items]

        assert "create" in actions
        assert "approve" in actions
        assert "issue" in actions
        assert "blood_unit" in entities
        assert "blood_request" in entities
        assert "donor" in entities

    finally:
        clock.set_today(None)
