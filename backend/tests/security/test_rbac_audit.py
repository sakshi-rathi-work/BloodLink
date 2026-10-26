"""Task 6.1: Exhaustive RBAC Audit Test Suite.

Walks every registered FastAPI route in `app.routes` and asserts exact compliance
with the Section 6.1 access matrix:
- Public vs. Admin vs. Staff vs. Requester
- 401 NOT_AUTHENTICATED when unauthenticated
- 403 FORBIDDEN when accessed by disallowed roles
- 403 ACCOUNT_DISABLED for disabled accounts
- Strictly Admin-only deletion across all entities
"""

import pytest
from fastapi.routing import APIRoute
from app.core.security import create_access_token, hash_password
from app.main import app
from app.models.user import User


def _resolve_sample_path(path_template: str) -> str:
    """Replace path parameters with safe sample IDs."""
    return (
        path_template.replace("{staff_id}", "1")
        .replace("{donor_id}", "1")
        .replace("{unit_id}", "1")
        .replace("{request_id}", "1")
        .replace("{requester_id}", "1")
        .replace("{camp_id}", "1")
        .replace("{report_type}", "stock")
    )


def _get_api_routes():
    """Retrieve all operational application routes registered under /api."""
    api_routes = []
    for route in app.routes:
        if isinstance(route, APIRoute) and route.path.startswith("/api"):
            for method in route.methods:
                if method not in ("HEAD", "OPTIONS"):
                    api_routes.append((method, route.path))

    if not api_routes:
        from app.api.router import api_router
        for ir in api_router.routes:
            router = getattr(ir, "original_router", None) or ir
            for r in getattr(router, "routes", []):
                if isinstance(r, APIRoute):
                    full_path = f"/api{r.path}"
                    for m in r.methods:
                        if m not in ("HEAD", "OPTIONS"):
                            api_routes.append((m, full_path))

    return sorted(list(set(api_routes)), key=lambda x: (x[1], x[0]))


PUBLIC_ROUTES = {
    ("GET", "/api/health"),
    ("POST", "/api/auth/login"),
    ("POST", "/api/auth/register"),
}

ADMIN_ONLY_PREFIXES = [
    "/api/staff",
    "/api/activity-logs",
]

REQUESTER_ONLY_ROUTES = {
    ("POST", "/api/requests"),
    ("GET", "/api/requesters/me"),
    ("PATCH", "/api/requesters/me"),
}

STAFF_AND_ADMIN_ROUTES = {
    ("GET", "/api/donors"),
    ("POST", "/api/donors"),
    ("GET", "/api/donors/{donor_id}"),
    ("PATCH", "/api/donors/{donor_id}"),
    ("GET", "/api/donors/{donor_id}/eligibility"),
    ("POST", "/api/donors/{donor_id}/donations"),
    ("GET", "/api/donors/{donor_id}/donations"),
    ("GET", "/api/inventory/stock"),
    ("GET", "/api/inventory/units"),
    ("GET", "/api/inventory/units/{unit_id}"),
    ("GET", "/api/inventory/expiring"),
    ("POST", "/api/inventory/expire-overdue"),
    ("GET", "/api/matching/units"),
    ("GET", "/api/requests/{request_id}/matches"),
    ("POST", "/api/requests/{request_id}/approve"),
    ("POST", "/api/requests/{request_id}/reject"),
    ("POST", "/api/requests/{request_id}/issue"),
    ("GET", "/api/requesters"),
    ("GET", "/api/requesters/{requester_id}"),
    ("GET", "/api/predictions/latest"),
    ("POST", "/api/predictions/run"),
    ("GET", "/api/predictions/alerts"),
    ("GET", "/api/predictions/evaluation"),
    ("GET", "/api/camps"),
    ("POST", "/api/camps"),
    ("GET", "/api/camps/{camp_id}"),
    ("PATCH", "/api/camps/{camp_id}"),
    ("GET", "/api/dashboard/summary"),
    ("GET", "/api/dashboard/trends"),
    ("GET", "/api/dashboard/wastage"),
    ("GET", "/api/reports/{report_type}"),
}


class TestRBACExhaustiveAudit:
    """Automated security audit walking every route for role authorization."""

    def test_all_registered_routes_exist_in_audit_matrix(self):
        """Ensure every route registered in FastAPI is accounted for."""
        routes = _get_api_routes()
        assert len(routes) > 0, "No API routes found on app.routes"

        for method, path in routes:
            is_public = (method, path) in PUBLIC_ROUTES
            is_admin = any(path.startswith(prefix) for prefix in ADMIN_ONLY_PREFIXES) or method == "DELETE"
            is_requester = (method, path) in REQUESTER_ONLY_ROUTES
            is_staff_admin = (method, path) in STAFF_AND_ADMIN_ROUTES
            is_common = (method, path) in {
                ("GET", "/api/auth/me"),
                ("GET", "/api/matching/compatibility"),
                ("GET", "/api/requests"),
                ("GET", "/api/requests/{request_id}"),
            }

            accounted_for = is_public or is_admin or is_requester or is_staff_admin or is_common
            assert accounted_for, f"Route {method} {path} is not accounted for in RBAC security audit matrix!"

    def test_unauthenticated_access_rejected_on_all_protected_routes(self, client):
        """Verify that every protected route returns 401 NOT_AUTHENTICATED without a token."""
        routes = _get_api_routes()
        for method, path in routes:
            if (method, path) in PUBLIC_ROUTES:
                continue

            sample_url = _resolve_sample_path(path)
            res = client.request(method, sample_url)

            # Route must reject unauthenticated requests with 401
            assert res.status_code == 401, (
                f"Expected 401 for unauthenticated {method} {sample_url}, got {res.status_code}: {res.text}"
            )
            detail = res.json().get("detail", {})
            assert detail.get("code") == "NOT_AUTHENTICATED"

    def test_staff_cannot_access_admin_only_routes(self, staff_client):
        """Verify that staff gets 403 on all Admin-only routes."""
        routes = _get_api_routes()
        for method, path in routes:
            is_admin_only = any(path.startswith(prefix) for prefix in ADMIN_ONLY_PREFIXES) or method == "DELETE"
            if not is_admin_only:
                continue

            sample_url = _resolve_sample_path(path)
            res = staff_client.request(method, sample_url)
            assert res.status_code == 403, (
                f"Expected 403 for staff on admin route {method} {sample_url}, got {res.status_code}: {res.text}"
            )
            assert res.json().get("detail", {}).get("code") == "FORBIDDEN"

    def test_requester_cannot_access_admin_or_staff_routes(self, requester_client):
        """Verify that requester gets 403 on staff and admin operational routes."""
        routes = _get_api_routes()
        for method, path in routes:
            is_admin_only = any(path.startswith(prefix) for prefix in ADMIN_ONLY_PREFIXES) or method == "DELETE"
            is_staff_admin = (method, path) in STAFF_AND_ADMIN_ROUTES

            if is_admin_only or is_staff_admin:
                sample_url = _resolve_sample_path(path)
                res = requester_client.request(method, sample_url)
                assert res.status_code == 403, (
                    f"Expected 403 for requester on {method} {sample_url}, got {res.status_code}: {res.text}"
                )
                assert res.json().get("detail", {}).get("code") == "FORBIDDEN"

    def test_admin_and_staff_cannot_create_requests(self, admin_client, staff_client):
        """Verify only Requesters can create blood requests per Section 6.1."""
        res_admin = admin_client.post("/api/requests", json={})
        assert res_admin.status_code == 403
        assert res_admin.json().get("detail", {}).get("code") == "FORBIDDEN"

        res_staff = staff_client.post("/api/requests", json={})
        assert res_staff.status_code == 403
        assert res_staff.json().get("detail", {}).get("code") == "FORBIDDEN"

    def test_disabled_user_rejected_on_all_requests(self, client, db):
        """Verify that disabled users (is_active=False) receive 403 ACCOUNT_DISABLED."""
        inactive_user = User(
            username="disabled_audit_user",
            password_hash=hash_password("password123"),
            role="staff",
            is_active=False,
        )
        db.add(inactive_user)
        db.commit()
        db.refresh(inactive_user)

        token = create_access_token(user_id=inactive_user.user_id, role="staff")
        client.headers["Authorization"] = f"Bearer {token}"

        res = client.get("/api/auth/me")
        assert res.status_code == 403
        assert res.json().get("detail", {}).get("code") == "ACCOUNT_DISABLED"

        res_donors = client.get("/api/donors")
        assert res_donors.status_code == 403
        assert res_donors.json().get("detail", {}).get("code") == "ACCOUNT_DISABLED"
