import csv
import io
from decimal import Decimal

from fpdf import FPDF
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog
from app.models.expense import Expense, ExpenseStatus
from app.models.settlement import Settlement, SettlementStatus
from app.models.trip import Trip
from app.models.user import User
from app.schemas.balance import MemberBalance
from app.schemas.report import CategoryBreakdownItem, ReportSummary
from app.schemas.settlement import SettlementOut
from app.schemas.trip import TripOut
from app.services.balance_service import compute_trip_balances, total_active_expenses
from app.utils.money import quantize


def build_report_summary(db: Session, trip: Trip) -> ReportSummary:
    balances = compute_trip_balances(db, trip.id)
    users = {u.id: u for u in db.query(User).filter(User.id.in_(balances.keys()))}

    member_balances = [
        MemberBalance(
            user=users[uid],
            total_paid=b.paid,
            total_owed=b.owed,
            net_balance=b.net,
        )
        for uid, b in sorted(balances.items(), key=lambda kv: kv[0])
        if uid in users
    ]

    active_count = db.query(Expense).filter(Expense.trip_id == trip.id, Expense.status == ExpenseStatus.ACTIVE).count()
    voided_count = db.query(Expense).filter(Expense.trip_id == trip.id, Expense.status == ExpenseStatus.VOIDED).count()
    total = total_active_expenses(db, trip.id)

    category_totals: dict[str, Decimal] = {}
    for category, amount in db.query(Expense.category, Expense.amount).filter(
        Expense.trip_id == trip.id, Expense.status == ExpenseStatus.ACTIVE
    ):
        key = category.value
        category_totals[key] = category_totals.get(key, Decimal("0")) + Decimal(amount)

    category_breakdown = [
        CategoryBreakdownItem(
            category=cat,
            total=quantize(amt),
            percentage_of_total=quantize((amt / total * 100) if total > 0 else Decimal("0")),
        )
        for cat, amt in sorted(category_totals.items(), key=lambda kv: kv[1], reverse=True)
    ]

    settlements = (
        db.query(Settlement)
        .filter(Settlement.trip_id == trip.id)
        .order_by(Settlement.date.desc(), Settlement.id.desc())
        .all()
    )

    return ReportSummary(
        trip=TripOut.model_validate(trip),
        total_expenses=total,
        active_expense_count=active_count,
        voided_expense_count=voided_count,
        balances=member_balances,
        settlements=[SettlementOut.model_validate(s) for s in settlements],
        category_breakdown=category_breakdown,
    )


def expenses_csv(db: Session, trip: Trip) -> str:
    expenses = db.query(Expense).filter(Expense.trip_id == trip.id).order_by(Expense.date.asc()).all()
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["id", "date", "description", "category", "amount", "currency", "paid_by_user_id", "split_method", "status"])
    for e in expenses:
        writer.writerow([e.id, e.date.isoformat(), e.description, e.category.value, e.amount, e.currency, e.paid_by, e.split_method.value, e.status.value])
    return buffer.getvalue()


def balances_csv(db: Session, trip: Trip) -> str:
    balances = compute_trip_balances(db, trip.id)
    users = {u.id: u for u in db.query(User).filter(User.id.in_(balances.keys()))}
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["user_id", "name", "email", "total_paid", "total_owed", "net_balance"])
    for uid, b in sorted(balances.items(), key=lambda kv: kv[0]):
        user = users.get(uid)
        writer.writerow([uid, user.full_name if user else "", user.email if user else "", b.paid, b.owed, b.net])
    return buffer.getvalue()


def settlements_csv(db: Session, trip: Trip) -> str:
    settlements = db.query(Settlement).filter(Settlement.trip_id == trip.id).order_by(Settlement.date.asc()).all()
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["id", "date", "payer_user_id", "receiver_user_id", "amount", "currency", "status", "note"])
    for s in settlements:
        writer.writerow([s.id, s.date.isoformat(), s.payer_id, s.receiver_id, s.amount, s.currency, s.status.value, s.note or ""])
    return buffer.getvalue()


def audit_csv(db: Session, trip: Trip) -> str:
    records = db.query(AuditLog).filter(AuditLog.trip_id == trip.id).order_by(AuditLog.id.asc()).all()
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["id", "event_type", "actor_id", "entity_type", "entity_id", "timestamp", "previous_hash", "current_hash"])
    for r in records:
        writer.writerow([r.id, r.event_type, r.actor_id, r.entity_type, r.entity_id, r.timestamp.isoformat(), r.previous_hash, r.current_hash])
    return buffer.getvalue()


def trip_summary_pdf(summary: ReportSummary) -> bytes:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, f"SplitSmart Report: {summary.trip.name}", new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 8, f"Destination: {summary.trip.destination or '-'}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(
        0,
        8,
        f"Total expenses: {summary.trip.currency} {summary.total_expenses} ({summary.active_expense_count} active, {summary.voided_expense_count} voided)",
        new_x="LMARGIN",
        new_y="NEXT",
    )
    pdf.ln(4)

    pdf.set_font("Helvetica", "B", 13)
    pdf.cell(0, 8, "Member Balances", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    for b in summary.balances:
        pdf.cell(
            0,
            7,
            f"{b.user.full_name}: paid {b.total_paid}, owed {b.total_owed}, net {b.net_balance}",
            new_x="LMARGIN",
            new_y="NEXT",
        )
    pdf.ln(4)

    pdf.set_font("Helvetica", "B", 13)
    pdf.cell(0, 8, "Spending by Category", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    for c in summary.category_breakdown:
        pdf.cell(0, 7, f"{c.category}: {c.total} ({c.percentage_of_total}%)", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    pdf.set_font("Helvetica", "B", 13)
    pdf.cell(0, 8, "Settlements", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    if not summary.settlements:
        pdf.cell(0, 7, "No settlements recorded.", new_x="LMARGIN", new_y="NEXT")
    for s in summary.settlements:
        pdf.cell(
            0,
            7,
            f"{s.date}: {s.payer.full_name} -> {s.receiver.full_name}: {s.currency} {s.amount} ({s.status.value})",
            new_x="LMARGIN",
            new_y="NEXT",
        )

    return bytes(pdf.output())
