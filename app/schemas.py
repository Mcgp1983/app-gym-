from __future__ import annotations

import datetime as dt
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class MemberBase(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None


class MemberCreate(MemberBase):
    pass


class MemberRead(MemberBase):
    id: int
    created_at: dt.datetime

    class Config:
        orm_mode = True


class MembershipPlanBase(BaseModel):
    name: str
    duration_days: int = Field(gt=0)
    price: float = Field(gt=0)
    description: Optional[str] = None


class MembershipPlanCreate(MembershipPlanBase):
    pass


class MembershipPlanRead(MembershipPlanBase):
    id: int

    class Config:
        orm_mode = True


class PurchaseCreate(BaseModel):
    member_id: int
    plan_id: int
    start_date: Optional[dt.datetime] = None


class PurchaseRead(BaseModel):
    id: int
    member: MemberRead
    plan: MembershipPlanRead
    start_date: dt.datetime
    end_date: dt.datetime
    access_token: str

    class Config:
        orm_mode = True


class PurchaseSummary(BaseModel):
    id: int
    member_id: int
    plan_id: int
    start_date: dt.datetime
    end_date: dt.datetime
    access_token: str

    class Config:
        orm_mode = True


class AccessScan(BaseModel):
    token: str


class AccessLogRead(BaseModel):
    id: int
    purchase_id: int
    scanned_at: dt.datetime
    status: str
    note: Optional[str] = None

    class Config:
        orm_mode = True


class AccessScanResult(BaseModel):
    allowed: bool
    message: str
    purchase: Optional[PurchaseSummary] = None
