import hmac
import ipaddress
import re
from flask import Blueprint, request, jsonify, current_app
from datetime import datetime, timezone
from models import db
from models.worker import Worker

bp = Blueprint("workers", __name__)

HOSTNAME_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9.-]{0,98}")


@bp.before_request
def require_worker_token():
    """Toutes les routes /workers* exigent le jeton partagé (comparaison à temps constant)."""
    sent = request.headers.get("X-Worker-Token", "")
    expected = current_app.config["WORKER_TOKEN"]
    if not hmac.compare_digest(sent.encode(), expected.encode()):
        return jsonify({"status": "error", "message": "unauthorized"}), 401


def _valid_ip(value):
    try:
        ipaddress.ip_address(value)
        return True
    except (ValueError, TypeError):
        return False


@bp.route("/workers/register", methods=["POST"])
def register_worker():
    body = request.get_json(silent=True)
    if not isinstance(body, dict) or "hostname" not in body or "ip" not in body:
        return jsonify({"status": "error", "message": "hostname and ip required"}), 400
    if not isinstance(body["hostname"], str) or not HOSTNAME_RE.fullmatch(body["hostname"]):
        return jsonify({"status": "error", "message": "invalid hostname"}), 400
    if not _valid_ip(body["ip"]):
        return jsonify({"status": "error", "message": "invalid ip"}), 400
    for field in ("cpu", "memory"):
        if body.get(field) is not None and not isinstance(body[field], (int, float)):
            return jsonify({"status": "error", "message": f"invalid {field}"}), 400
    worker = Worker.query.filter_by(hostname=body["hostname"]).first()
    if worker is None:
        worker = Worker(hostname=body["hostname"])
        db.session.add(worker)
    worker.ip             = body["ip"]
    worker.cpu            = body.get("cpu")
    worker.memory         = body.get("memory")
    worker.status         = "AVAILABLE"
    worker.last_heartbeat = datetime.now(timezone.utc)
    db.session.commit()
    return jsonify({"status": "registered", "worker_id": worker.id}), 201


@bp.route("/workers/heartbeat", methods=["POST"])
def heartbeat():
    body = request.get_json(silent=True)
    if not isinstance(body, dict) or not isinstance(body.get("hostname"), str):
        return jsonify({"status": "error", "message": "hostname required"}), 400
    worker = Worker.query.filter_by(hostname=body["hostname"]).first()
    if worker is None:
        return jsonify({"status": "error", "message": "unknown worker"}), 404
    worker.last_heartbeat = datetime.now(timezone.utc)
    worker.status         = "AVAILABLE"
    db.session.commit()
    return jsonify({"status": "ok"}), 200


@bp.route("/workers", methods=["GET"])
def list_workers():
    workers = Worker.query.all()
    return jsonify([{"id": w.id, "hostname": w.hostname, "ip": w.ip, "status": w.status, "cpu": w.cpu, "memory": w.memory, "last_heartbeat": w.last_heartbeat.isoformat() if w.last_heartbeat else None} for w in workers]), 200
