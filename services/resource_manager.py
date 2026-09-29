from models.worker import Worker
from models import db


def pick_available_worker():
    return Worker.query.filter_by(status="AVAILABLE").first()


def mark_worker_busy(worker):
    worker.status = "BUSY"
    db.session.commit()


def mark_worker_available(worker):
    worker.status = "AVAILABLE"
    db.session.commit()
