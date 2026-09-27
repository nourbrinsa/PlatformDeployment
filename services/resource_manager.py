from models.worker import Worker
from models import db


def pick_available_worker():
    return Worker.query.filter_by(status="available").first()


def mark_worker_busy(worker):
    worker.status = "busy"
    db.session.commit()


def mark_worker_available(worker):
    worker.status = "available"
    db.session.commit()
