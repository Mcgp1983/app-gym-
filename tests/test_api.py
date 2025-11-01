import datetime as dt

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app


def setup_test_db(tmp_path):
    db_path = tmp_path / "test.db"
    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    return engine


def test_member_plan_purchase_flow(tmp_path):
    engine = setup_test_db(tmp_path)
    client = TestClient(app)

    member_payload = {"name": "João Silva", "email": "joao@example.com", "phone": "912345678"}
    member_resp = client.post("/members", json=member_payload)
    assert member_resp.status_code == 201
    member_id = member_resp.json()["id"]

    plan_payload = {"name": "Mensal 24h", "duration_days": 30, "price": 35.5}
    plan_resp = client.post("/plans", json=plan_payload)
    assert plan_resp.status_code == 201
    plan_id = plan_resp.json()["id"]

    start_date = dt.datetime.utcnow().isoformat()
    purchase_payload = {
        "member_id": member_id,
        "plan_id": plan_id,
        "start_date": start_date,
    }
    purchase_resp = client.post("/purchases", json=purchase_payload)
    assert purchase_resp.status_code == 201
    purchase_body = purchase_resp.json()
    assert purchase_body["member_id"] == member_id
    assert purchase_body["plan_id"] == plan_id
    assert "access_token" in purchase_body

    qr_resp = client.get(f"/purchases/{purchase_body['id']}/qr")
    assert qr_resp.status_code == 200
    qr_data = qr_resp.json()
    assert qr_data["token"] == purchase_body["access_token"]
    assert len(qr_data["qr_base64"]) > 100

    scan_resp = client.post("/access/scan", json={"token": purchase_body["access_token"]})
    assert scan_resp.status_code == 200
    scan_data = scan_resp.json()
    assert scan_data["allowed"] is True
    assert scan_data["purchase"]["id"] == purchase_body["id"]

    # Expire membership by manipulating dates
    with engine.begin() as connection:
        connection.execute(
            text("UPDATE purchases SET end_date = :end WHERE id = :id"),
            {
                "end": dt.datetime.utcnow() - dt.timedelta(days=1),
                "id": purchase_body["id"],
            },
        )

    expired_resp = client.post("/access/scan", json={"token": purchase_body["access_token"]})
    assert expired_resp.status_code == 200
    assert expired_resp.json()["allowed"] is False
