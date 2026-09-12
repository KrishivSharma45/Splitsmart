from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, EmailStr

from app.models.trip import TripStatus
from app.models.trip_member import MemberStatus, TripRole
from app.schemas.user import UserSummary


class TripCreate(BaseModel):
    name: str
    description: str | None = None
    destination: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    currency: str = "INR"


class TripUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    destination: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    currency: str | None = None


class TripOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None
    destination: str | None
    start_date: date | None
    end_date: date | None
    currency: str
    status: TripStatus
    created_by: int
    created_at: datetime
    updated_at: datetime
    my_role: TripRole | None = None


class TripListItem(TripOut):
    total_expenses: Decimal = Decimal("0")
    member_count: int = 0
    my_net_balance: Decimal = Decimal("0")


class TripMemberOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    trip_id: int
    role: TripRole
    status: MemberStatus
    joined_at: datetime
    user: UserSummary


class MemberAddRequest(BaseModel):
    email: EmailStr
    role: TripRole = TripRole.MEMBER


class RoleChangeRequest(BaseModel):
    role: TripRole
