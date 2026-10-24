"""
Synthetic Data Generator for BloodLink.
Simulates realistic 365-day operational history for donors, inventory, requests, and issuing.

Calibration Parameters:
- Days simulated: 365 days ending yesterday.
- Donor pool: 180 donors across the 8 blood groups with realistic weights.
- Blood group distribution:
    A+: 0.22, A-: 0.02, B+: 0.30, B-: 0.02, AB+: 0.07, AB-: 0.01, O+: 0.34, O-: 0.02
- Safe minimums calibrated:
    A+: 15, A-: 5, B+: 15, B-: 5, AB+: 8, AB-: 3, O+: 20, O-: 8
- Realistic supply & demand guarantees non-negative stock and >= 180 days of history per group.
- Leaves recent pending and approved requests for live UI demonstrations.
"""

import argparse
import random
import sys
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Dict, List, Optional
from sqlalchemy import create_engine, text
from sqlalchemy.engine.url import make_url
from sqlalchemy.orm import Session, sessionmaker

from app.core import clock
from app.core.config import settings
from app.core.security import hash_password
from app.models.activity_log import ActivityLog
from app.models.blood_request import BloodRequest
from app.models.blood_unit import BloodUnit
from app.models.donation_camp import DonationCamp
from app.models.donor import Donor
from app.models.issue_record import IssueRecord
from app.models.requester import Requester
from app.models.shortage_prediction import ShortagePrediction
from app.models.staff import Staff
from app.models.user import User
from app.services.compatibility import get_compatible_donor_groups

BLOOD_GROUP_WEIGHTS = {
    "A+": 0.22,
    "A-": 0.02,
    "B+": 0.30,
    "B-": 0.02,
    "AB+": 0.07,
    "AB-": 0.01,
    "O+": 0.34,
    "O-": 0.02,
}

BLOOD_GROUPS = list(BLOOD_GROUP_WEIGHTS.keys())
WEIGHTS_LIST = list(BLOOD_GROUP_WEIGHTS.values())

ALLOWED_DBS = {"bloodlink", "bloodlink_test"}
LOOPBACK_HOSTS = {"localhost", "127.0.0.1"}


def validate_safety_guards(db_url: str, is_reset: bool, auto_confirm: bool) -> None:
    """Enforce Technical Decision D3 safety guards before running destructive or seeding ops."""
    url = make_url(db_url)
    
    # Dialect check
    if not (url.drivername.startswith("postgresql") or url.drivername.startswith("sqlite")):
        raise ValueError(f"Safety Guard: Database dialect '{url.drivername}' is not supported. Must be PostgreSQL or SQLite.")

    # If PostgreSQL, verify host is loopback
    if url.drivername.startswith("postgresql"):
        host = url.host or "localhost"
        if host not in LOOPBACK_HOSTS:
            raise ValueError(f"Safety Guard: Seeder can only target local database ({LOOPBACK_HOSTS}), but got '{host}'.")
        
        # Allowlist check
        db_name = url.database
        if db_name not in ALLOWED_DBS:
            raise ValueError(f"Safety Guard: Database '{db_name}' not in allowed list {ALLOWED_DBS}.")

    # Reset confirmation
    if is_reset and not auto_confirm:
        print("\n" + "!" * 60)
        print("WARNING: --reset will TRUNCATE domain tables in database!")
        print("!" * 60)
        user_input = input("Type 'RESET' to confirm database wipe: ").strip()
        if user_input != "RESET":
            print("Operation aborted by user.")
            sys.exit(1)


def seed_data(
    db_url: str,
    days: int = 365,
    seed: int = 42,
    reset: bool = False,
    auto_confirm: bool = False,
) -> None:
    validate_safety_guards(db_url, is_reset=reset, auto_confirm=auto_confirm)

    random.seed(seed)
    engine = create_engine(db_url)
    SessionClass = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    session: Session = SessionClass()

    today = clock.today()
    start_date = today - timedelta(days=days)
    yesterday = today - timedelta(days=1)

    print(f"Starting synthetic data generation: {days} days from {start_date} to {yesterday} (Seed={seed})...")

    try:
        from app.db.base import Base
        Base.metadata.create_all(bind=engine)

        # Ensure v_transactions view exists on postgresql
        url = make_url(db_url)
        if url.drivername.startswith("postgresql"):
            with engine.connect() as v_conn:
                v_conn.execute(text("""
                    CREATE OR REPLACE VIEW v_transactions AS
                    SELECT 'donation'::text AS transaction_type,
                           u.unit_id, u.blood_group, u.collection_date AS transaction_date,
                           u.donor_id, NULL::integer AS request_id, NULL::integer AS staff_id
                    FROM blood_units u
                    UNION ALL
                    SELECT 'issue'::text, i.unit_id, u.blood_group, i.issue_date,
                           u.donor_id, i.request_id, i.issued_by
                    FROM issue_records i
                    JOIN blood_units u ON u.unit_id = i.unit_id
                    UNION ALL
                    SELECT 'wastage'::text, u.unit_id, u.blood_group, u.expiry_date,
                           u.donor_id, NULL::integer, NULL::integer
                    FROM blood_units u
                    WHERE u.status = 'expired';
                """))
                v_conn.commit()

        if reset:
            print("Resetting existing domain tables...")
            # Clean in reverse foreign key order
            session.query(ActivityLog).delete()
            session.query(ShortagePrediction).delete()
            session.query(IssueRecord).delete()
            session.query(BloodRequest).delete()
            session.query(BloodUnit).delete()
            session.query(DonationCamp).delete()
            session.query(Donor).delete()
            session.query(Requester).delete()
            session.query(Staff).delete()
            session.query(User).delete()
            session.flush()

        # 1. Create or ensure standard demo accounts
        admin_user = session.query(User).filter_by(username="admin").first()
        if not admin_user:
            admin_user = User(
                username="admin",
                password_hash=hash_password("admin12345"),
                role="admin",
                is_active=True,
            )
            session.add(admin_user)
            session.flush()
            admin_staff = Staff(user_id=admin_user.user_id, name="System Administrator")
            session.add(admin_staff)

        staff_user = session.query(User).filter_by(username="staff").first()
        if not staff_user:
            staff_user = User(
                username="staff",
                password_hash=hash_password("staff12345"),
                role="staff",
                is_active=True,
            )
            session.add(staff_user)
            session.flush()
            staff_profile = Staff(user_id=staff_user.user_id, name="Main Blood Bank Staff")
            session.add(staff_profile)
            session.flush()
        else:
            staff_profile = staff_user.staff_profile

        hospital_user = session.query(User).filter_by(username="hospital").first()
        if not hospital_user:
            hospital_user = User(
                username="hospital",
                password_hash=hash_password("hospital12345"),
                role="requester",
                is_active=True,
            )
            session.add(hospital_user)
            session.flush()
            hospital_requester = Requester(
                user_id=hospital_user.user_id,
                name="City General Hospital",
                type="hospital",
                phone="+91 98765 43210",
                address="100 Hospital Road, Central City",
            )
            session.add(hospital_requester)
            session.flush()
        else:
            hospital_requester = hospital_user.requester_profile

        # 2. Create additional requesters
        requester_pool: List[Requester] = [hospital_requester]
        additional_requesters_data = [
            ("Metro Trauma Center", "hospital", "+91 98220 11111", "54 North Ring Road"),
            ("Grace Children Hospital", "hospital", "+91 98220 22222", "12 Park Avenue"),
            ("Apollo Healthcare Clinic", "hospital", "+91 98220 33333", "78 Market Street"),
            ("Rajesh Sharma", "patient", "+91 98220 44444", "Flat 302, Sunrise Apartments"),
            ("Priya Patel", "patient", "+91 98220 55555", "B-14 Green Meadows"),
        ]

        for r_name, r_type, r_phone, r_addr in additional_requesters_data:
            u_name = r_name.lower().replace(" ", "_")[:20]
            existing_u = session.query(User).filter_by(username=u_name).first()
            if not existing_u:
                u = User(
                    username=u_name,
                    password_hash=hash_password("password123"),
                    role="requester",
                    is_active=True,
                )
                session.add(u)
                session.flush()
                req = Requester(
                    user_id=u.user_id,
                    name=r_name,
                    type=r_type,
                    phone=r_phone,
                    address=r_addr,
                )
                session.add(req)
                session.flush()
                requester_pool.append(req)

        # 3. Create donor pool (180 donors)
        first_names = ["Amit", "Sneha", "Rahul", "Pooja", "Vikram", "Anjali", "Rohan", "Deepa", "Sanjay", "Kavita", "Arjun", "Neha"]
        last_names = ["Shah", "Patel", "Mehta", "Deshmukh", "Joshi", "Verma", "Rao", "Nair", "Kulkarni", "Gupta"]

        donor_pool: List[Donor] = []
        for i in range(180):
            bg = random.choices(BLOOD_GROUPS, weights=WEIGHTS_LIST, k=1)[0]
            fn = random.choice(first_names)
            ln = random.choice(last_names)
            donor_name = f"{fn} {ln} {i+1}"
            age_years = random.randint(20, 58)
            dob = today - timedelta(days=age_years * 365 + random.randint(1, 300))
            gender = random.choice(["male", "female"])
            weight = Decimal(str(round(random.uniform(53.0, 88.0), 1)))
            phone = f"+91 98{random.randint(10000000, 99999999)}"
            address = f"Street {random.randint(1, 50)}, Sector {random.randint(1, 20)}"

            donor = Donor(
                name=donor_name,
                dob=dob,
                gender=gender,
                blood_group=bg,
                phone=phone,
                address=address,
                weight=weight,
                last_donation_date=None,
            )
            session.add(donor)
            donor_pool.append(donor)

        session.flush()

        # 4. Day-by-day simulation
        current_day = start_date
        shelf_life = timedelta(days=settings.BLOOD_SHELF_LIFE_DAYS)

        camp_interval = 21  # Camp every 21 days
        next_camp_day = start_date + timedelta(days=7)

        # Inventory in memory for fast matching
        # unit_id -> BloodUnit
        available_units_by_group: Dict[str, List[BloodUnit]] = {bg: [] for bg in BLOOD_GROUPS}

        total_units_created = 0
        total_requests_created = 0
        total_issued = 0

        while current_day <= yesterday:
            # 4a. Expiry sweep for current day
            for bg in BLOOD_GROUPS:
                active_list = []
                for u in available_units_by_group[bg]:
                    if u.expiry_date < current_day:
                        u.status = "expired"
                    else:
                        active_list.append(u)
                available_units_by_group[bg] = active_list

            # 4b. Donation Camp check
            is_camp_day = current_day == next_camp_day
            if is_camp_day:
                camp = DonationCamp(
                    location=f"Community Hall Sector {random.randint(1, 15)}",
                    camp_date=current_day,
                    target_units=random.randint(20, 30),
                    units_collected=0,
                )
                session.add(camp)
                session.flush()
                next_camp_day = current_day + timedelta(days=camp_interval)

            # 4c. Generate daily donations
            if is_camp_day:
                num_donations = random.randint(14, 26)
            elif current_day.weekday() in [5, 6]:  # Weekend
                num_donations = random.randint(4, 8)
            else:
                num_donations = random.randint(2, 5)

            # Find eligible donors
            eligible_donors = [
                d for d in donor_pool
                if d.last_donation_date is None or (current_day - d.last_donation_date).days >= settings.MIN_DONATION_GAP_DAYS
            ]

            if eligible_donors:
                selected_donors = random.sample(eligible_donors, min(num_donations, len(eligible_donors)))
                for d in selected_donors:
                    b_unit = BloodUnit(
                        donor_id=d.donor_id,
                        blood_group=d.blood_group,
                        collection_date=current_day,
                        expiry_date=current_day + shelf_life,
                        status="available",
                    )
                    session.add(b_unit)
                    session.flush()

                    d.last_donation_date = current_day
                    available_units_by_group[d.blood_group].append(b_unit)
                    total_units_created += 1

                    if is_camp_day:
                        camp.units_collected += 1

            # 4d. Generate daily blood requests
            num_requests = random.randint(1, 4)
            for _ in range(num_requests):
                req_group = random.choices(BLOOD_GROUPS, weights=WEIGHTS_LIST, k=1)[0]
                req_qty = random.choices([1, 2, 3], weights=[0.70, 0.25, 0.05], k=1)[0]
                urgency = random.choices(["routine", "emergency"], weights=[0.8, 0.2], k=1)[0]
                requester = random.choice(requester_pool)

                # Check compatible units (nearest expiry first)
                compatible_groups = get_compatible_donor_groups(req_group)
                candidates: List[BloodUnit] = []
                for cg in compatible_groups:
                    candidates.extend(available_units_by_group[cg])

                # Sort by expiry_date ASC, unit_id ASC
                candidates.sort(key=lambda u: (u.expiry_date, u.unit_id))

                if len(candidates) >= req_qty:
                    # Issue request
                    req = BloodRequest(
                        requester_id=requester.requester_id,
                        blood_group=req_group,
                        quantity=req_qty,
                        urgency=urgency,
                        status="issued",
                        request_date=current_day,
                    )
                    session.add(req)
                    session.flush()

                    units_to_issue = candidates[:req_qty]
                    for u in units_to_issue:
                        u.status = "issued"
                        available_units_by_group[u.blood_group].remove(u)
                        issue_rec = IssueRecord(
                            request_id=req.request_id,
                            unit_id=u.unit_id,
                            issue_date=current_day,
                            issued_by=staff_profile.staff_id,
                        )
                        session.add(issue_rec)
                        total_issued += 1

                    total_requests_created += 1
                else:
                    # Reject request due to insufficient stock
                    req = BloodRequest(
                        requester_id=requester.requester_id,
                        blood_group=req_group,
                        quantity=req_qty,
                        urgency=urgency,
                        status="rejected",
                        request_date=current_day,
                    )
                    session.add(req)
                    session.flush()
                    total_requests_created += 1

            current_day += timedelta(days=1)

        # 5. Live items for today/yesterday in queue (pending & approved)
        recent_req_1 = BloodRequest(
            requester_id=hospital_requester.requester_id,
            blood_group="O+",
            quantity=2,
            urgency="emergency",
            status="pending",
            request_date=yesterday,
        )
        recent_req_2 = BloodRequest(
            requester_id=requester_pool[1].requester_id,
            blood_group="A+",
            quantity=1,
            urgency="routine",
            status="approved",
            request_date=yesterday,
        )
        recent_req_3 = BloodRequest(
            requester_id=hospital_requester.requester_id,
            blood_group="B+",
            quantity=2,
            urgency="routine",
            status="pending",
            request_date=today,
        )
        session.add_all([recent_req_1, recent_req_2, recent_req_3])
        session.flush()

        # Commit everything in a single atomic transaction
        session.commit()
        print(f"Synthetic data seeding completed successfully!")
        print(f"Summary: {total_units_created} units created, {total_requests_created} historical requests, {total_issued} units issued.")
        print("Demo Accounts:")
        print("  Admin:     admin / admin12345")
        print("  Staff:     staff / staff12345")
        print("  Hospital:  hospital / hospital12345")

    except Exception as e:
        session.rollback()
        print(f"Error seeding synthetic data: {e}", file=sys.stderr)
        raise
    finally:
        session.close()


def main():
    parser = argparse.ArgumentParser(description="Seed realistic synthetic operational data for BloodLink.")
    parser.add_argument("--days", type=int, default=365, help="Number of days of history to simulate (default: 365).")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility (default: 42).")
    parser.add_argument("--reset", action="store_true", help="Truncate domain tables and recreate accounts before seeding.")
    parser.add_argument("--yes", "-y", action="store_true", help="Bypass interactive confirmation for --reset.")
    parser.add_argument("--db-url", type=str, default=None, help="Database URL (defaults to DATABASE_URL from settings).")

    args = parser.parse_args()
    db_url = args.db_url or settings.DATABASE_URL

    seed_data(
        db_url=db_url,
        days=args.days,
        seed=args.seed,
        reset=args.reset,
        auto_confirm=args.yes,
    )


if __name__ == "__main__":
    main()
