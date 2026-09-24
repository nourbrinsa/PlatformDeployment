from datetime import datetime, timezone
from . import db

class Instance(db.Model):
    __tablename__ = "instances"

    id = db.Column(db.Integer, primary_key=True)
    container_id = db.Column(db.String(255), unique=True)
    worker_id = db.Column(db.Integer, db.ForeignKey("workers.id"), nullable=False)
    distribution_id = db.Column(db.Integer, db.ForeignKey("distributions.id"), nullable=False)
    ssh_port = db.Column(db.Integer, unique=True, nullable=False)
    ssh_user = db.Column(db.String(50), default="student")
    ssh_password = db.Column(db.String(255))
    status = db.Column(db.String(20), default="pending")
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    rentals = db.relationship("Rental", backref="instance", lazy=True)
