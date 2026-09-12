"""Demo/seed data for SplitSmart.

Creates the "Goa Trip" example from the product spec: four users, a mix of
expenses using every split method, a couple of settlements, and a chain
verification run -- so the Security Center and Audit Ledger have real data
to show immediately after a fresh clone.

Usage:
    venv/Scripts/python.exe seed.py
"""

import os
from pathlib import Path

DB_PATH = Path(__file__).parent / "splitsmart.db"
if DB_PATH.exists():
    DB_PATH.unlink()
    print(f"Removed existing dev database at {DB_PATH}")

os.environ.setdefault("DATABASE_URL", f"sqlite:///{DB_PATH.name}")

from app.audit.audit_service import record_event  # noqa: E402
from app.audit.events import AuditEvent  # noqa: E402
from app.audit.verification_service import verify_chain  # noqa: E402
from app.database import Base, SessionLocal, engine  # noqa: E402
from app.models.trip_member import TripRole  # noqa: E402
from app.models.user import User  # noqa: E402
from app.schemas.expense import ExpenseCreate, ExpenseParticipantInput  # noqa: E402
from app.schemas.settlement import SettlementCreate  # noqa: E402
from app.schemas.trip import TripCreate  # noqa: E402
from app.security.password import hash_password  # noqa: E402
from app.services import expense_service, settlement_service, trip_service  # noqa: E402

Base.metadata.create_all(bind=engine)

DEMO_PASSWORD = "Demo1234!"

DEMO_USERS = [
    ("krishiv@splitsmart.demo", "Krishiv Sharma"),
    ("rahul@splitsmart.demo", "Rahul Verma"),
    ("arjun@splitsmart.demo", "Arjun Mehta"),
    ("aditya@splitsmart.demo", "Aditya Rao"),
]


def create_user(db, email: str, full_name: str) -> User:
    user = User(email=email, full_name=full_name, hashed_password=hash_password(DEMO_PASSWORD))
    db.add(user)
    db.flush()
    record_event(
        db,
        event_type=AuditEvent.USER_REGISTERED,
        entity_type="user",
        actor_id=user.id,
        entity_id=user.id,
        event_data={"email": user.email, "full_name": user.full_name},
    )
    db.commit()
    db.refresh(user)
    return user


def main():
    db = SessionLocal()
    try:
        print("Creating demo users...")
        users = {}
        for email, full_name in DEMO_USERS:
            users[email] = create_user(db, email, full_name)

        krishiv, rahul, arjun, aditya = (users[e] for e, _ in DEMO_USERS)

        print("Creating Goa Trip...")
        trip = trip_service.create_trip(
            db,
            krishiv,
            TripCreate(
                name="Goa Trip",
                description="Annual friends trip to Goa",
                destination="Goa, India",
                start_date="2026-01-10",
                end_date="2026-01-14",
                currency="INR",
            ),
        )
        trip_service.add_member(db, trip, krishiv, "rahul@splitsmart.demo", TripRole.ADMIN)
        trip_service.add_member(db, trip, krishiv, "arjun@splitsmart.demo", TripRole.MEMBER)
        trip_service.add_member(db, trip, krishiv, "aditya@splitsmart.demo", TripRole.MEMBER)

        all_ids = [krishiv.id, rahul.id, arjun.id, aditya.id]

        print("Recording expenses...")
        expense_service.create_expense(
            db,
            trip,
            krishiv,
            ExpenseCreate(
                description="Hotel (Tivoli Avenida)",
                amount="8000",
                paid_by=krishiv.id,
                category="ACCOMMODATION",
                split_method="EQUAL",
                date="2026-01-10",
                notes="3 nights, sea-facing room",
                participants=[ExpenseParticipantInput(user_id=uid) for uid in all_ids],
            ),
        )

        expense_service.create_expense(
            db,
            trip,
            rahul,
            ExpenseCreate(
                description="Group dinner at Belcanto",
                amount="4800",
                paid_by=rahul.id,
                category="FOOD",
                split_method="PERCENTAGE",
                date="2026-01-11",
                participants=[
                    ExpenseParticipantInput(user_id=krishiv.id, percentage="30"),
                    ExpenseParticipantInput(user_id=rahul.id, percentage="30"),
                    ExpenseParticipantInput(user_id=arjun.id, percentage="20"),
                    ExpenseParticipantInput(user_id=aditya.id, percentage="20"),
                ],
            ),
        )

        expense_service.create_expense(
            db,
            trip,
            arjun,
            ExpenseCreate(
                description="Airport taxi",
                amount="1600",
                paid_by=arjun.id,
                category="TRANSPORT",
                split_method="EXACT",
                date="2026-01-10",
                participants=[
                    ExpenseParticipantInput(user_id=krishiv.id, amount="400"),
                    ExpenseParticipantInput(user_id=rahul.id, amount="400"),
                    ExpenseParticipantInput(user_id=arjun.id, amount="400"),
                    ExpenseParticipantInput(user_id=aditya.id, amount="400"),
                ],
            ),
        )

        expense_service.create_expense(
            db,
            trip,
            aditya,
            ExpenseCreate(
                description="Scuba diving activity",
                amount="6000",
                paid_by=aditya.id,
                category="ENTERTAINMENT",
                split_method="SHARES",
                date="2026-01-12",
                notes="Krishiv and Rahul did the advanced package (2x cost)",
                participants=[
                    ExpenseParticipantInput(user_id=krishiv.id, shares=2),
                    ExpenseParticipantInput(user_id=rahul.id, shares=2),
                    ExpenseParticipantInput(user_id=arjun.id, shares=1),
                    ExpenseParticipantInput(user_id=aditya.id, shares=1),
                ],
            ),
        )

        expense_service.create_expense(
            db,
            trip,
            krishiv,
            ExpenseCreate(
                description="Beach shack lunch",
                amount="1240",
                paid_by=krishiv.id,
                category="FOOD",
                split_method="EQUAL",
                date="2026-01-12",
                participants=[ExpenseParticipantInput(user_id=uid) for uid in all_ids],
            ),
        )

        print("Recording settlements...")
        settlement_service.create_settlement(
            db,
            trip,
            arjun,
            SettlementCreate(payer_id=arjun.id, receiver_id=krishiv.id, amount="1500", date="2026-01-13", note="Partial settle-up"),
        )
        settlement_service.create_settlement(
            db,
            trip,
            aditya,
            SettlementCreate(payer_id=aditya.id, receiver_id=rahul.id, amount="800", date="2026-01-13", note="Dinner IOU"),
        )

        print("Running audit chain verification...")
        result = verify_chain(db)
        record_event(
            db,
            event_type=AuditEvent.AUDIT_VERIFICATION_RUN,
            entity_type="audit_ledger",
            actor_id=krishiv.id,
            trip_id=trip.id,
            entity_id=None,
            event_data={
                "status": result.status,
                "records_checked": result.records_checked,
                "broken_links": result.broken_links,
                "affected_record": result.affected_record,
            },
        )
        db.commit()

        print()
        print("=" * 60)
        print("Seed complete.")
        print(f"Audit chain status: {result.status} ({result.records_checked} records checked)")
        print()
        print("Demo login credentials (all users share the same password):")
        for email, full_name in DEMO_USERS:
            print(f"  {email:30s}  {full_name:20s}  password: {DEMO_PASSWORD}")
        print("=" * 60)
    finally:
        db.close()


if __name__ == "__main__":
    main()
