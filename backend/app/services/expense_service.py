from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.audit.audit_service import record_event
from app.audit.events import AuditEvent
from app.models.expense import Expense, ExpenseStatus, SplitMethod
from app.models.expense_split import ExpenseSplit
from app.models.trip import Trip
from app.models.trip_member import MemberStatus, TripMember
from app.models.user import User
from app.schemas.expense import ExpenseCreate, ExpenseParticipantInput, ExpenseUpdate
from app.services.notification_service import create_notification
from app.utils.money import quantize, split_equal, split_exact, split_percentage, split_shares


def _active_member_ids(db: Session, trip_id: int) -> set[int]:
    return {
        m.user_id
        for m in db.query(TripMember).filter(TripMember.trip_id == trip_id, TripMember.status == MemberStatus.ACTIVE)
    }


def compute_splits(
    split_method: SplitMethod, amount: Decimal, participants: list[ExpenseParticipantInput]
) -> dict[int, Decimal]:
    user_ids = [p.user_id for p in participants]
    if len(set(user_ids)) != len(user_ids):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Duplicate participant in split")

    try:
        if split_method == SplitMethod.EQUAL:
            return split_equal(amount, user_ids)

        if split_method == SplitMethod.EXACT:
            exact_amounts: dict[int, Decimal] = {}
            for p in participants:
                if p.amount is None:
                    raise ValueError(f"Exact amount required for user {p.user_id}")
                exact_amounts[p.user_id] = p.amount
            return split_exact(amount, exact_amounts)

        if split_method == SplitMethod.PERCENTAGE:
            percentages: dict[int, Decimal] = {}
            for p in participants:
                if p.percentage is None:
                    raise ValueError(f"Percentage required for user {p.user_id}")
                percentages[p.user_id] = p.percentage
            return split_percentage(amount, percentages)

        if split_method == SplitMethod.SHARES:
            shares: dict[int, int] = {}
            for p in participants:
                if p.shares is None:
                    raise ValueError(f"Shares required for user {p.user_id}")
                shares[p.user_id] = p.shares
            return split_shares(amount, shares)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown split method")


def _validate_members(db: Session, trip_id: int, paid_by: int, participants: list[ExpenseParticipantInput]) -> None:
    active_ids = _active_member_ids(db, trip_id)
    if paid_by not in active_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="paid_by must be an active member of this trip"
        )
    invalid = {p.user_id for p in participants} - active_ids
    if invalid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Users {sorted(invalid)} are not active members of this trip",
        )


def _persist_splits(
    db: Session, expense: Expense, split_method: SplitMethod, splits: dict[int, Decimal], participants: list[ExpenseParticipantInput]
) -> None:
    input_by_user = {p.user_id: p for p in participants}
    for user_id, share_amount in splits.items():
        p = input_by_user[user_id]
        db.add(
            ExpenseSplit(
                expense_id=expense.id,
                user_id=user_id,
                share_amount=share_amount,
                percentage=p.percentage if split_method == SplitMethod.PERCENTAGE else None,
                shares=p.shares if split_method == SplitMethod.SHARES else None,
            )
        )
    db.flush()


def create_expense(db: Session, trip: Trip, current_user: User, data: ExpenseCreate) -> Expense:
    _validate_members(db, trip.id, data.paid_by, data.participants)
    splits = compute_splits(data.split_method, data.amount, data.participants)

    expense = Expense(
        trip_id=trip.id,
        description=data.description,
        amount=quantize(data.amount),
        currency=data.currency,
        paid_by=data.paid_by,
        category=data.category,
        split_method=data.split_method,
        date=data.date,
        notes=data.notes,
        created_by=current_user.id,
    )
    db.add(expense)
    db.flush()

    _persist_splits(db, expense, data.split_method, splits, data.participants)

    record_event(
        db,
        event_type=AuditEvent.EXPENSE_CREATED,
        entity_type="expense",
        actor_id=current_user.id,
        trip_id=trip.id,
        entity_id=expense.id,
        event_data={
            "description": expense.description,
            "amount": str(expense.amount),
            "currency": expense.currency,
            "paid_by": expense.paid_by,
            "split_method": expense.split_method.value,
            "participants": sorted(splits.keys()),
        },
    )

    other_member_ids = [uid for uid in _active_member_ids(db, trip.id) if uid != current_user.id]
    for uid in other_member_ids:
        create_notification(
            db,
            user_id=uid,
            type="EXPENSE_CREATED",
            message=f"{current_user.full_name} recorded a {expense.currency} {expense.amount} expense: {expense.description}.",
            trip_id=trip.id,
            entity_type="expense",
            entity_id=expense.id,
        )

    db.commit()
    db.refresh(expense)
    return expense


def _expense_snapshot(expense: Expense) -> dict:
    return {
        "description": expense.description,
        "amount": str(expense.amount),
        "currency": expense.currency,
        "paid_by": expense.paid_by,
        "category": expense.category.value,
        "split_method": expense.split_method.value,
        "date": expense.date.isoformat(),
        "notes": expense.notes,
        "splits": sorted(
            [{"user_id": s.user_id, "share_amount": str(s.share_amount)} for s in expense.splits],
            key=lambda x: x["user_id"],
        ),
    }


def update_expense(db: Session, expense: Expense, trip: Trip, current_user: User, data: ExpenseUpdate) -> Expense:
    if expense.status == ExpenseStatus.VOIDED:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Cannot edit a voided expense")

    previous_state = _expense_snapshot(expense)
    update_data = data.model_dump(exclude_unset=True)

    recompute_needed = any(field in update_data for field in ("amount", "split_method", "participants"))
    if recompute_needed and "participants" not in update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="participants must be provided when amount or split_method changes",
        )

    new_amount = update_data.get("amount", expense.amount)
    new_split_method = update_data.get("split_method", expense.split_method)
    new_paid_by = update_data.get("paid_by", expense.paid_by)

    if recompute_needed:
        participants = [
            p if isinstance(p, ExpenseParticipantInput) else ExpenseParticipantInput(**p)
            for p in update_data["participants"]
        ]
        _validate_members(db, trip.id, new_paid_by, participants)
        splits = compute_splits(new_split_method, new_amount, participants)

        for field in ("description", "amount", "currency", "paid_by", "category", "split_method", "date", "notes"):
            if field in update_data:
                setattr(expense, field, update_data[field])
        expense.amount = quantize(new_amount)

        for existing_split in list(expense.splits):
            db.delete(existing_split)
        db.flush()

        _persist_splits(db, expense, new_split_method, splits, participants)
    else:
        for field, value in update_data.items():
            setattr(expense, field, value)

    db.flush()
    db.refresh(expense)
    new_state = _expense_snapshot(expense)

    record_event(
        db,
        event_type=AuditEvent.EXPENSE_UPDATED,
        entity_type="expense",
        actor_id=current_user.id,
        trip_id=trip.id,
        entity_id=expense.id,
        event_data={"previous": previous_state, "new": new_state},
    )
    db.commit()
    db.refresh(expense)
    return expense


def void_expense(db: Session, expense: Expense, current_user: User, reason: str | None) -> Expense:
    if expense.status == ExpenseStatus.VOIDED:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Expense is already voided")

    expense.status = ExpenseStatus.VOIDED
    expense.void_reason = reason
    db.flush()

    record_event(
        db,
        event_type=AuditEvent.EXPENSE_VOIDED,
        entity_type="expense",
        actor_id=current_user.id,
        trip_id=expense.trip_id,
        entity_id=expense.id,
        event_data={"reason": reason, "amount": str(expense.amount), "description": expense.description},
    )
    db.commit()
    db.refresh(expense)
    return expense
