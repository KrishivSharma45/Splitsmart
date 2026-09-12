import uuid
from datetime import date as date_type
from decimal import Decimal
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.models.expense import Expense, ExpenseCategory, ExpenseStatus
from app.models.expense_split import ExpenseSplit
from app.models.receipt import Receipt
from app.models.trip import Trip
from app.models.trip_member import ROLE_RANK, TripMember, TripRole
from app.models.user import User
from app.schemas.expense import ExpenseCreate, ExpenseOut, ExpenseUpdate, VoidExpenseRequest
from app.security.deps import get_current_user, get_trip_membership, require_trip_member
from app.services import expense_service

router = APIRouter(prefix="/api", tags=["expenses"])
settings = get_settings()

ALLOWED_RECEIPT_TYPES = {"image/png", "image/jpeg", "image/webp", "application/pdf"}
EXT_BY_CONTENT_TYPE = {
    "image/png": ".png",
    "image/jpeg": ".jpg",
    "image/webp": ".webp",
    "application/pdf": ".pdf",
}


def _get_expense_or_404(db: Session, expense_id: int) -> Expense:
    expense = db.get(Expense, expense_id)
    if expense is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expense not found")
    return expense


def serialize_expense(expense: Expense) -> ExpenseOut:
    return ExpenseOut(
        id=expense.id,
        trip_id=expense.trip_id,
        description=expense.description,
        amount=expense.amount,
        currency=expense.currency,
        paid_by=expense.payer,
        category=expense.category,
        split_method=expense.split_method,
        date=expense.date,
        notes=expense.notes,
        status=expense.status,
        void_reason=expense.void_reason,
        created_by=expense.created_by,
        created_at=expense.created_at,
        updated_at=expense.updated_at,
        splits=list(expense.splits),
        has_receipt=len(expense.receipts) > 0,
    )


@router.get("/trips/{trip_id}/expenses", response_model=list[ExpenseOut])
def list_expenses(
    trip_id: int,
    category: ExpenseCategory | None = None,
    paid_by: int | None = None,
    participant: int | None = None,
    date_from: date_type | None = None,
    date_to: date_type | None = None,
    amount_min: Decimal | None = None,
    amount_max: Decimal | None = None,
    search: str | None = None,
    status_filter: ExpenseStatus | None = Query(default=ExpenseStatus.ACTIVE, alias="status"),
    sort_by: str = Query(default="date", pattern="^(date|amount|category|created_at)$"),
    sort_dir: str = Query(default="desc", pattern="^(asc|desc)$"),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    membership: TripMember = Depends(require_trip_member),
    db: Session = Depends(get_db),
):
    q = db.query(Expense).filter(Expense.trip_id == trip_id)

    if status_filter is not None:
        q = q.filter(Expense.status == status_filter)
    if category is not None:
        q = q.filter(Expense.category == category)
    if paid_by is not None:
        q = q.filter(Expense.paid_by == paid_by)
    if date_from is not None:
        q = q.filter(Expense.date >= date_from)
    if date_to is not None:
        q = q.filter(Expense.date <= date_to)
    if amount_min is not None:
        q = q.filter(Expense.amount >= amount_min)
    if amount_max is not None:
        q = q.filter(Expense.amount <= amount_max)
    if search:
        like = f"%{search}%"
        q = q.filter(or_(Expense.description.ilike(like), Expense.notes.ilike(like)))
    if participant is not None:
        q = q.join(ExpenseSplit, ExpenseSplit.expense_id == Expense.id).filter(ExpenseSplit.user_id == participant)

    sort_column = {
        "date": Expense.date,
        "amount": Expense.amount,
        "category": Expense.category,
        "created_at": Expense.created_at,
    }[sort_by]
    sort_column = sort_column.desc() if sort_dir == "desc" else sort_column.asc()

    expenses = q.order_by(sort_column).offset(offset).limit(limit).all()
    return [serialize_expense(e) for e in expenses]


@router.post("/trips/{trip_id}/expenses", response_model=ExpenseOut, status_code=status.HTTP_201_CREATED)
def create_expense(
    trip_id: int,
    data: ExpenseCreate,
    current_user: User = Depends(get_current_user),
    membership: TripMember = Depends(require_trip_member),
    db: Session = Depends(get_db),
):
    trip = db.get(Trip, trip_id)
    if trip is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trip not found")
    expense = expense_service.create_expense(db, trip, current_user, data)
    return serialize_expense(expense)


@router.get("/expenses/{expense_id}", response_model=ExpenseOut)
def get_expense(expense_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    expense = _get_expense_or_404(db, expense_id)
    get_trip_membership(expense.trip_id, db, current_user)
    return serialize_expense(expense)


def _require_edit_rights(db: Session, expense: Expense, current_user: User) -> None:
    membership = get_trip_membership(expense.trip_id, db, current_user)
    if expense.created_by != current_user.id and ROLE_RANK[membership.role] < ROLE_RANK[TripRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the expense creator or a trip admin/owner can modify this expense",
        )


@router.put("/expenses/{expense_id}", response_model=ExpenseOut)
def update_expense(
    expense_id: int,
    data: ExpenseUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    expense = _get_expense_or_404(db, expense_id)
    _require_edit_rights(db, expense, current_user)
    trip = db.get(Trip, expense.trip_id)
    expense = expense_service.update_expense(db, expense, trip, current_user, data)
    return serialize_expense(expense)


@router.post("/expenses/{expense_id}/void", response_model=ExpenseOut)
def void_expense(
    expense_id: int,
    data: VoidExpenseRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    expense = _get_expense_or_404(db, expense_id)
    _require_edit_rights(db, expense, current_user)
    expense = expense_service.void_expense(db, expense, current_user, data.reason)
    return serialize_expense(expense)


@router.post("/expenses/{expense_id}/receipt", status_code=status.HTTP_201_CREATED)
async def upload_receipt(
    expense_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    expense = _get_expense_or_404(db, expense_id)
    get_trip_membership(expense.trip_id, db, current_user)

    if file.content_type not in ALLOWED_RECEIPT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type. Allowed: {', '.join(sorted(ALLOWED_RECEIPT_TYPES))}",
        )

    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    contents = await file.read()
    if len(contents) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"File exceeds the {settings.MAX_UPLOAD_SIZE_MB}MB limit"
        )

    ext = EXT_BY_CONTENT_TYPE[file.content_type]
    stored_name = f"{uuid.uuid4().hex}{ext}"
    trip_dir = settings.upload_dir_path / "receipts" / str(expense.trip_id)
    trip_dir.mkdir(parents=True, exist_ok=True)
    stored_path = trip_dir / stored_name
    stored_path.write_bytes(contents)

    receipt = Receipt(
        expense_id=expense.id,
        filename=file.filename or stored_name,
        stored_path=str(stored_path),
        content_type=file.content_type,
        size_bytes=len(contents),
        uploaded_by=current_user.id,
    )
    db.add(receipt)
    db.commit()
    return {"id": receipt.id, "filename": receipt.filename, "size_bytes": receipt.size_bytes}


@router.get("/expenses/{expense_id}/receipt")
def get_receipt(expense_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    expense = _get_expense_or_404(db, expense_id)
    get_trip_membership(expense.trip_id, db, current_user)

    receipt = db.query(Receipt).filter(Receipt.expense_id == expense_id).order_by(Receipt.id.desc()).first()
    if receipt is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No receipt attached to this expense")

    file_path = Path(receipt.stored_path)
    if not file_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Receipt file is missing")

    return FileResponse(path=file_path, media_type=receipt.content_type, filename=receipt.filename)
