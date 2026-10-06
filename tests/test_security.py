import pytest
from datetime import datetime, timedelta, timezone
from app import create_app
from config import TestConfig
from models import db
from models.user import User
from models.worker import Worker
from models.distribution import Distribution
from models.instance import Instance
from models.rental import Rental

TOKEN = {"X-Worker-Token": "test-worker-token"}


@pytest.fixture
def app():
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()
        db.session.add(Distribution(name="ubuntu", docker_image="ubuntu:24.04", version="24.04"))
        db.session.add(Worker(hostname="worker1", ip="192.168.56.11", status="AVAILABLE"))
        db.session.commit()
        yield app
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


def signup(client, username="alice", email="a@x.fr", password="motdepasse1"):
    return client.post("/register", data={"username": username, "email": email, "password": password})


def test_dashboard_requires_login(client):
    r = client.get("/dashboard")
    assert r.status_code == 302 and "/login" in r.headers["Location"]


def test_password_is_hashed(app, client):
    signup(client)
    u = User.query.filter_by(username="alice").first()
    assert u.password_hash != "motdepasse1" and u.check_password("motdepasse1")


@pytest.mark.parametrize("username,email,password", [
    ("a", "a@x.fr", "motdepasse1"),                 # username trop court
    ("<script>", "a@x.fr", "motdepasse1"),          # caractères interdits
    ("alice", "pas-un-email", "motdepasse1"),       # email invalide
    ("alice", "a@x.fr", "court"),                   # mot de passe trop court
])
def test_register_validation(client, username, email, password):
    signup(client, username, email, password)
    assert User.query.count() == 0


def test_register_sql_injection_is_inert(client):
    signup(client, username="x' OR '1'='1", email="a@x.fr")
    assert User.query.count() == 0


def test_worker_routes_need_token(client):
    assert client.get("/workers").status_code == 401
    assert client.post("/workers/register", json={"hostname": "w9", "ip": "10.0.0.9"}).status_code == 401
    assert client.get("/workers", headers={"X-Worker-Token": "mauvais"}).status_code == 401


def test_worker_register_ok_and_validated(client):
    ok = client.post("/workers/register", json={"hostname": "w9", "ip": "10.0.0.9", "cpu": 2, "memory": 2048}, headers=TOKEN)
    assert ok.status_code == 201
    bad_ip = client.post("/workers/register", json={"hostname": "w9", "ip": "pas-une-ip"}, headers=TOKEN)
    assert bad_ip.status_code == 400
    bad_host = client.post("/workers/register", json={"hostname": "w;rm -rf", "ip": "10.0.0.9"}, headers=TOKEN)
    assert bad_host.status_code == 400


def test_cannot_stop_someone_elses_instance(app, client):
    signup(client, "alice", "a@x.fr")
    alice = User.query.filter_by(username="alice").first()
    w = Worker.query.first(); d = Distribution.query.first()
    inst = Instance(container_id="rent-1-abc", worker_id=w.id, distribution_id=d.id, ssh_port=32768, status="running")
    db.session.add(inst); db.session.flush()
    db.session.add(Rental(user_id=alice.id, instance_id=inst.id, end_time=datetime.now(timezone.utc) + timedelta(hours=1)))
    db.session.commit()
    client.post("/logout")
    signup(client, "bob", "b@x.fr")
    client.post(f"/instances/{inst.id}/stop")
    assert db.session.get(Instance, inst.id).status == "running"


def test_invalid_duration_rejected(client):
    signup(client)
    client.post("/rent", data={"distribution": "ubuntu", "duration_minutes": "99999"})
    assert Rental.query.count() == 0


def test_security_headers_and_404(client):
    r = client.get("/nexiste-pas")
    assert r.status_code == 404 and b"Traceback" not in r.data
    assert r.headers["X-Frame-Options"] == "DENY"
    assert "Content-Security-Policy" in r.headers


def test_csrf_enforced_when_enabled():
    class Cfg(TestConfig):
        WTF_CSRF_ENABLED = True
    app = create_app(Cfg)
    with app.app_context():
        db.create_all()
        c = app.test_client()
        assert c.post("/login", data={"email": "a@x.fr", "password": "x"}).status_code == 400
        # le jeton worker reste utilisable sans CSRF
        assert c.post("/workers/register", json={"hostname": "w", "ip": "10.0.0.1"}, headers=TOKEN).status_code == 201


def test_app_refuses_to_start_without_secret():
    class Cfg(TestConfig):
        SECRET_KEY = None
    with pytest.raises(RuntimeError):
        create_app(Cfg)
