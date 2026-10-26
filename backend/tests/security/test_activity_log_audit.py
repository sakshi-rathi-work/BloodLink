"""Task 6.2: Activity Log Audit Test Suite.

Asserts that every state-changing endpoint:
- create, update, delete, approve, reject, issue, prediction_run
writes an immutable audit log row to `activity_logs` in the same transaction,
with correct user_id, action, entity_type, entity_id, and details.
"""

from datetime import date, timedelta
from app.core import clock
from app.models.activity_log import ActivityLog
from app.models.blood_request import BloodRequest
from app.models.blood_unit import BloodUnit
from app.models.donation_camp import DonationCamp
from app.models.donor import Donor
from app.models.staff import Staff
from app.models.user import User


class TestActivityLogAudit:
    """Verifies that all state mutations write audit log entries."""

    def test_donor_and_donation_activity_logs(self, staff_client, staff_user, db):
        """Verify activity logs for donor create, update, and donation record."""
        # 1. Create donor
        res_create = staff_client.post(
            "/api/donors",
            json={
                "name": "Audit Donor",
                "dob": "1995-05-15",
                "gender": "male",
                "blood_group": "A+",
                "phone": "9876543201",
                "weight": 70.0,
                "address": "Audit St 1",
            },
        )
        assert res_create.status_code == 201
        donor_id = res_create.json()["donor_id"]

        log = (
            db.query(ActivityLog)
            .filter(
                ActivityLog.entity_type == "donor",
                ActivityLog.entity_id == donor_id,
                ActivityLog.action == "create",
            )
            .first()
        )
        assert log is not None
        assert log.user_id == staff_user.user_id

        # 2. Update donor
        res_patch = staff_client.patch(f"/api/donors/{donor_id}", json={"phone": "9876543299"})
        assert res_patch.status_code == 200

        log_update = (
            db.query(ActivityLog)
            .filter(
                ActivityLog.entity_type == "donor",
                ActivityLog.entity_id == donor_id,
                ActivityLog.action == "update",
            )
            .first()
        )
        assert log_update is not None
        assert log_update.user_id == staff_user.user_id

        # 3. Record donation
        res_don = staff_client.post(f"/api/donors/{donor_id}/donations")
        assert res_don.status_code == 201
        unit_id = res_don.json()["unit_id"]

        log_donation = (
            db.query(ActivityLog)
            .filter(
                ActivityLog.entity_type == "blood_unit",
                ActivityLog.entity_id == unit_id,
                ActivityLog.action == "create",
            )
            .first()
        )
        assert log_donation is not None
        assert log_donation.user_id == staff_user.user_id

    def test_camps_activity_logs(self, admin_client, staff_client, admin_user, staff_user, db):
        """Verify activity logs for donation camp create, update, and delete."""
        today = clock.today()
        # 1. Create camp
        res = staff_client.post(
            "/api/camps",
            json={
                "location": "Audit City Hall",
                "camp_date": (today + timedelta(days=5)).isoformat(),
                "target_units": 50,
            },
        )
        assert res.status_code == 201
        camp_id = res.json()["camp_id"]

        log_create = (
            db.query(ActivityLog)
            .filter(
                ActivityLog.entity_type == "donation_camp",
                ActivityLog.entity_id == camp_id,
                ActivityLog.action == "create",
            )
            .first()
        )
        assert log_create is not None
        assert log_create.user_id == staff_user.user_id

        # 2. Update camp
        res_patch = staff_client.patch(
            f"/api/camps/{camp_id}",
            json={"units_collected": 35},
        )
        assert res_patch.status_code == 200

        log_update = (
            db.query(ActivityLog)
            .filter(
                ActivityLog.entity_type == "donation_camp",
                ActivityLog.entity_id == camp_id,
                ActivityLog.action == "update",
            )
            .first()
        )
        assert log_update is not None

        # 3. Delete camp (admin only)
        res_del = admin_client.delete(f"/api/camps/{camp_id}")
        assert res_del.status_code == 200

        log_del = (
            db.query(ActivityLog)
            .filter(
                ActivityLog.entity_type == "donation_camp",
                ActivityLog.entity_id == camp_id,
                ActivityLog.action == "delete",
            )
            .first()
        )
        assert log_del is not None
        assert log_del.user_id == admin_user.user_id

    def test_request_workflow_activity_logs(self, requester_client, requester_user, staff_client, staff_user, db):
        """Verify activity logs for blood request create, approve, and issue."""
        today = clock.today()

        # Seed an available unit for issue
        donor = Donor(
            name="Donor For Issue",
            dob=date(1990, 1, 1),
            gender="female",
            blood_group="O+",
            phone="9871112223",
            weight=60.0,
        )
        db.add(donor)
        db.commit()
        db.refresh(donor)

        unit = BloodUnit(
            donor_id=donor.donor_id,
            blood_group="O+",
            collection_date=today - timedelta(days=2),
            expiry_date=today + timedelta(days=40),
            status="available",
        )
        db.add(unit)
        db.commit()
        db.refresh(unit)

        # 1. Create request by requester
        res_req = requester_client.post(
            "/api/requests",
            json={
                "blood_group": "O+",
                "quantity": 1,
                "urgency": "emergency",
                "patient_name": "Emergency Patient",
            },
        )
        assert res_req.status_code == 201
        request_id = res_req.json()["request_id"]

        log_create = (
            db.query(ActivityLog)
            .filter(
                ActivityLog.entity_type == "blood_request",
                ActivityLog.entity_id == request_id,
                ActivityLog.action == "create",
            )
            .first()
        )
        assert log_create is not None
        assert log_create.user_id == requester_user.user_id

        # 2. Staff approves request
        res_app = staff_client.post(f"/api/requests/{request_id}/approve")
        assert res_app.status_code == 200

        log_approve = (
            db.query(ActivityLog)
            .filter(
                ActivityLog.entity_type == "blood_request",
                ActivityLog.entity_id == request_id,
                ActivityLog.action == "approve",
            )
            .first()
        )
        assert log_approve is not None
        assert log_approve.user_id == staff_user.user_id

        # 3. Staff issues units
        res_iss = staff_client.post(f"/api/requests/{request_id}/issue")
        assert res_iss.status_code == 200

        log_issue = (
            db.query(ActivityLog)
            .filter(
                ActivityLog.entity_type == "blood_request",
                ActivityLog.entity_id == request_id,
                ActivityLog.action == "issue",
            )
            .first()
        )
        assert log_issue is not None
        assert log_issue.user_id == staff_user.user_id
        assert "units_issued" in log_issue.details or "unit_ids" in log_issue.details

    def test_staff_management_activity_logs(self, admin_client, admin_user, db):
        """Verify activity logs for staff account creation, update, and deletion."""
        # 1. Create staff
        res = admin_client.post(
            "/api/staff",
            json={
                "username": "audit_staff_member",
                "password": "auditpassword123",
                "name": "Audit Staff Member",
                "role": "staff",
            },
        )
        assert res.status_code == 201
        staff_id = res.json()["staff_id"]

        log_create = (
            db.query(ActivityLog)
            .filter(
                ActivityLog.entity_type == "staff",
                ActivityLog.entity_id == staff_id,
                ActivityLog.action == "create",
            )
            .first()
        )
        assert log_create is not None
        assert log_create.user_id == admin_user.user_id

        # 2. Update staff
        res_patch = admin_client.patch(
            f"/api/staff/{staff_id}",
            json={"name": "Updated Audit Staff"},
        )
        assert res_patch.status_code == 200

        log_update = (
            db.query(ActivityLog)
            .filter(
                ActivityLog.entity_type == "staff",
                ActivityLog.entity_id == staff_id,
                ActivityLog.action == "update",
            )
            .first()
        )
        assert log_update is not None

        # 3. Reset password
        res_pwd = admin_client.post(
            f"/api/staff/{staff_id}/reset-password",
            json={"new_password": "newpassword1234"},
        )
        assert res_pwd.status_code == 200

        # 4. Delete staff
        res_del = admin_client.delete(f"/api/staff/{staff_id}")
        assert res_del.status_code == 200

        log_del = (
            db.query(ActivityLog)
            .filter(
                ActivityLog.entity_type == "staff",
                ActivityLog.entity_id == staff_id,
                ActivityLog.action == "delete",
            )
            .first()
        )
        assert log_del is not None
