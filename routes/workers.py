from flask import Blueprint, request, jsonify
from datetime import datetime, timezone
from models import db
from models.worker import Worker

bp = Blueprint("workers", __name__)


@bp.route("/workers/register", methods=["POST"])
def register_worker():
    body = request.get_json()
    if not body or "hostname" not in body or "ip" not in body:
        return jsonify({"status": "error", "message": "hostname and ip required"}), 400
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
    body = request.get_json()
    if not body or "hostname" not in body:
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
