from datetime import datetime, timezone
from . import db

class Worker(db.Model):
    __tablename__ = "workers"

    id             = db.Column(db.Integer, primary_key=True)
    hostname       = db.Column(db.String(100), unique=True, nullable=False)
    ip             = db.Column(db.String(45), nullable=False)
    status         = db.Column(db.String(20), default="available")
    # status values: available | busy | offline
    cpu            = db.Column(db.Float, nullable=True)     # e.g. 4.0 (cores)
    memory         = db.Column(db.Float, nullable=True)     # e.g. 8.0 (GB)
    last_heartbeat = db.Column(db.DateTime, nullable=True)

    instances = db.relationship("Instance", backref="worker", lazy=True)

    def is_alive(self, timeout_seconds=30):
        if not self.last_heartbeat:
            return False
        delta = datetime.now(timezone.utc) - self.last_heartbeat.replace(tzinfo=timezone.utc)
        return delta.total_seconds() < timeout_seconds

    def __repr__(self):
        return f"<Worker {self.hostname} ({self.ip}) status={self.status}>"
