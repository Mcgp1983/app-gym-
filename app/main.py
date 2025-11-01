from __future__ import annotations

import base64
import datetime as dt
from io import BytesIO
from typing import List

import qrcode
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from . import models, schemas
from .database import Base, engine, get_db

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Gym Access Automation API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)


def ensure_timezone(value: dt.datetime) -> dt.datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=dt.timezone.utc)
    return value


@app.post("/members", response_model=schemas.MemberRead, status_code=status.HTTP_201_CREATED)
def create_member(member: schemas.MemberCreate, db: Session = Depends(get_db)):
    existing = db.query(models.Member).filter_by(email=member.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="E-mail já registado")
    db_member = models.Member(name=member.name, email=member.email, phone=member.phone)
    db.add(db_member)
    db.commit()
    db.refresh(db_member)
    return db_member


@app.get("/members", response_model=List[schemas.MemberRead])
def list_members(db: Session = Depends(get_db)):
    return db.query(models.Member).order_by(models.Member.created_at.desc()).all()


@app.post(
    "/plans", response_model=schemas.MembershipPlanRead, status_code=status.HTTP_201_CREATED
)
def create_plan(plan: schemas.MembershipPlanCreate, db: Session = Depends(get_db)):
    existing = db.query(models.MembershipPlan).filter_by(name=plan.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Plano já existe")
    db_plan = models.MembershipPlan(
        name=plan.name,
        duration_days=plan.duration_days,
        price=plan.price,
        description=plan.description,
    )
    db.add(db_plan)
    db.commit()
    db.refresh(db_plan)
    return db_plan


@app.get("/plans", response_model=List[schemas.MembershipPlanRead])
def list_plans(db: Session = Depends(get_db)):
    return db.query(models.MembershipPlan).order_by(models.MembershipPlan.price).all()


@app.post(
    "/purchases", response_model=schemas.PurchaseSummary, status_code=status.HTTP_201_CREATED
)
def create_purchase(purchase: schemas.PurchaseCreate, db: Session = Depends(get_db)):
    member = db.get(models.Member, purchase.member_id)
    if not member:
        raise HTTPException(status_code=404, detail="Membro não encontrado")
    plan = db.get(models.MembershipPlan, purchase.plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plano não encontrado")

    start = ensure_timezone(purchase.start_date or dt.datetime.utcnow())
    end = start + dt.timedelta(days=plan.duration_days)

    token = models.Purchase.generate_token()
    db_purchase = models.Purchase(
        member_id=member.id,
        plan_id=plan.id,
        start_date=start,
        end_date=end,
        access_token=token,
    )
    db.add(db_purchase)
    db.commit()
    db.refresh(db_purchase)
    return db_purchase


@app.get("/purchases", response_model=List[schemas.PurchaseSummary])
def list_purchases(db: Session = Depends(get_db)):
    return db.query(models.Purchase).order_by(models.Purchase.created_at.desc()).all()


@app.get("/purchases/{purchase_id}", response_model=schemas.PurchaseRead)
def get_purchase(purchase_id: int, db: Session = Depends(get_db)):
    purchase = db.get(models.Purchase, purchase_id)
    if not purchase:
        raise HTTPException(status_code=404, detail="Compra não encontrada")
    return purchase


@app.get("/purchases/{purchase_id}/qr")
def get_purchase_qr(purchase_id: int, db: Session = Depends(get_db)):
    purchase = db.get(models.Purchase, purchase_id)
    if not purchase:
        raise HTTPException(status_code=404, detail="Compra não encontrada")
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(purchase.access_token)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    encoded = base64.b64encode(buffer.getvalue()).decode("utf-8")
    return {"token": purchase.access_token, "qr_base64": encoded}


@app.post("/access/scan", response_model=schemas.AccessScanResult)
def scan_access(payload: schemas.AccessScan, db: Session = Depends(get_db)):
    purchase = (
        db.query(models.Purchase).filter(models.Purchase.access_token == payload.token).first()
    )
    if not purchase:
        raise HTTPException(status_code=404, detail="Token inválido")

    now = dt.datetime.utcnow().replace(tzinfo=dt.timezone.utc)
    allowed = purchase.is_active(now)
    status_value = "allowed" if allowed else "expired"
    log = models.AccessLog(purchase_id=purchase.id, status=status_value)
    if not allowed:
        log.note = "Plano expirado"

    db.add(log)
    db.commit()

    message = "Entrada autorizada" if allowed else "Plano expirado"
    result = schemas.AccessScanResult(
        allowed=allowed,
        message=message,
        purchase=schemas.PurchaseSummary.from_orm(purchase),
    )

    return result


@app.get("/access/logs", response_model=List[schemas.AccessLogRead])
def list_access_logs(db: Session = Depends(get_db)):
    return db.query(models.AccessLog).order_by(models.AccessLog.scanned_at.desc()).all()
