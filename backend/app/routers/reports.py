from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.audit.audit_service import record_event
from app.audit.events import AuditEvent
from app.database import get_db
from app.models.trip import Trip
from app.models.trip_member import TripMember
from app.models.user import User
from app.schemas.report import ReportSummary
from app.security.deps import get_current_user, require_trip_member
from app.services import report_service

router = APIRouter(prefix="/api/reports", tags=["reports"])


def _get_trip_or_404(db: Session, trip_id: int) -> Trip:
    trip = db.get(Trip, trip_id)
    if trip is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trip not found")
    return trip


@router.get("/{trip_id}", response_model=ReportSummary)
def get_report_summary(
    trip_id: int,
    current_user: User = Depends(get_current_user),
    membership: TripMember = Depends(require_trip_member),
    db: Session = Depends(get_db),
):
    trip = _get_trip_or_404(db, trip_id)
    summary = report_service.build_report_summary(db, trip)

    record_event(
        db,
        event_type=AuditEvent.REPORT_GENERATED,
        entity_type="report",
        actor_id=current_user.id,
        trip_id=trip.id,
        entity_id=trip.id,
        event_data={"report_type": "trip_summary"},
    )
    db.commit()
    return summary


@router.get("/{trip_id}/export/csv")
def export_csv(
    trip_id: int,
    type: str = Query(pattern="^(expenses|balances|settlements|audit)$"),
    current_user: User = Depends(get_current_user),
    membership: TripMember = Depends(require_trip_member),
    db: Session = Depends(get_db),
):
    trip = _get_trip_or_404(db, trip_id)

    generators = {
        "expenses": report_service.expenses_csv,
        "balances": report_service.balances_csv,
        "settlements": report_service.settlements_csv,
        "audit": report_service.audit_csv,
    }
    csv_content = generators[type](db, trip)

    record_event(
        db,
        event_type=AuditEvent.REPORT_GENERATED,
        entity_type="report",
        actor_id=current_user.id,
        trip_id=trip.id,
        entity_id=trip.id,
        event_data={"report_type": f"{type}_csv"},
    )
    db.commit()

    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{trip.name}_{type}.csv"'},
    )


@router.get("/{trip_id}/export/pdf")
def export_pdf(
    trip_id: int,
    current_user: User = Depends(get_current_user),
    membership: TripMember = Depends(require_trip_member),
    db: Session = Depends(get_db),
):
    trip = _get_trip_or_404(db, trip_id)
    summary = report_service.build_report_summary(db, trip)
    pdf_bytes = report_service.trip_summary_pdf(summary)

    record_event(
        db,
        event_type=AuditEvent.REPORT_GENERATED,
        entity_type="report",
        actor_id=current_user.id,
        trip_id=trip.id,
        entity_id=trip.id,
        event_data={"report_type": "trip_summary_pdf"},
    )
    db.commit()

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{trip.name}_summary.pdf"'},
    )
