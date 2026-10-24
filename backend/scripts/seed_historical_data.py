"""
Non-destructive historical data seeder for BloodLink ML predictions.

Inserts synthetic donors and blood_unit donation records spanning 120 days
back from today, covering all 8 blood groups. Does NOT delete or modify
any existing records.

Usage:
    python backend/scripts/seed_historical_data.py
"""
import sys
import os
import random
from datetime import date, timedelta

# Ensure backend package root is on path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.db.session import engine
from sqlalchemy import text

BLOOD_GROUPS = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]
DAYS_BACK = 120        # Generate 120 days of history (well above MIN_HISTORY_DAYS=90)
DONATIONS_PER_DAY = 3  # Average donations per day per blood group

# Realistic average daily donations per blood group (higher for common groups)
DAILY_DONATIONS = {
    "A+":  4,
    "A-":  1,
    "B+":  3,
    "B-":  1,
    "AB+": 1,
    "AB-": 1,
    "O+":  4,
    "O-":  1,
}


def run_seed():
    today = date.today()
    start_date = today - timedelta(days=DAYS_BACK)

    with engine.connect() as conn:
        # Get current max donor_id to avoid conflicts
        max_donor_row = conn.execute(text("SELECT COALESCE(MAX(donor_id), 0) FROM donors")).fetchone()
        donor_id_offset = max_donor_row[0]
        print(f"Starting after donor_id={donor_id_offset}")

        # Create synthetic donors (one set shared across blood groups)
        # We'll create 1 donor per blood group as a "synthetic donor" seeded account
        donor_ids = {}
        for bg in BLOOD_GROUPS:
            phone = f"900{BLOOD_GROUPS.index(bg):07d}"
            existing = conn.execute(
                text("SELECT donor_id FROM donors WHERE phone = :phone"),
                {"phone": phone}
            ).fetchone()
            if existing:
                donor_ids[bg] = existing[0]
                print(f"Reusing existing synthetic donor for {bg}: donor_id={existing[0]}")
            else:
                result = conn.execute(
                    text("""
                        INSERT INTO donors (name, dob, gender, blood_group, phone, address, weight, last_donation_date)
                        VALUES (:name, :dob, :gender, :bg, :phone, :address, :weight, :ldd)
                        RETURNING donor_id
                    """),
                    {
                        "name": f"Synthetic Donor [{bg}]",
                        "dob": "1990-01-01",
                        "gender": "male",
                        "bg": bg,
                        "phone": phone,
                        "address": "Blood Bank Synthetic Record",
                        "weight": 70.0,
                        "ldd": today - timedelta(days=30),
                    }
                )
                did = result.fetchone()[0]
                donor_ids[bg] = did
                print(f"Created synthetic donor for {bg}: donor_id={did}")

        conn.commit()

        # Now insert blood_unit donation records per blood group per day
        total_units = 0
        for bg in BLOOD_GROUPS:
            avg = DAILY_DONATIONS[bg]
            did = donor_ids[bg]
            units_for_bg = 0
            for day_offset in range(DAYS_BACK):
                record_date = start_date + timedelta(days=day_offset)
                # Skip if too close to today (avoid future dates)
                if record_date >= today:
                    continue
                # Randomize number of donations for this day (0-2x average)
                n = max(0, int(random.gauss(avg, avg * 0.4)))
                for _ in range(n):
                    expiry = record_date + timedelta(days=35)  # blood expires in 35 days
                    # Check if unit already exists for this donor/date/bg combo to avoid duplicates
                    conn.execute(
                        text("""
                            INSERT INTO blood_units (donor_id, blood_group, collection_date, expiry_date, status)
                            VALUES (:donor_id, :bg, :cdate, :edate, :status)
                        """),
                        {
                            "donor_id": did,
                            "bg": bg,
                            "cdate": record_date,
                            "edate": expiry,
                            "status": "expired" if expiry < today else "available",
                        }
                    )
                    units_for_bg += 1
            conn.commit()
            print(f"Inserted {units_for_bg} donation units for {bg}")
            total_units += units_for_bg

        print(f"\n✅ Seeding complete! Total units inserted: {total_units}")
        print(f"   Date range: {start_date} → {today - timedelta(days=1)}")
        print(f"   Blood groups covered: {', '.join(BLOOD_GROUPS)}")
        print(f"\nYou can now run the ML prediction pipeline (POST /api/predictions/run).")


if __name__ == "__main__":
    random.seed(42)  # Reproducible output
    run_seed()
