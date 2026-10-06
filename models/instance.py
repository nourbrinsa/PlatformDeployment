from datetime import datetime, timezone
from . import db

class Instance(db.Model):
    __tablename__ = "instances"

    id              = db.Column(db.Integer, primary_key=True)
    container_id    = db.Column(db.String(255), unique=True, nullable=True)  # set after container starts
    worker_id       = db.Column(db.Integer, db.ForeignKey("workers.id"), nullable=False)
    distribution_id = db.Column(db.Integer, db.ForeignKey("distributions.id"), nullable=False)
    ssh_port        = db.Column(db.Integer, nullable=False)  # unique par worker (voir __table_args__)
    status          = db.Column(db.String(20), default="pending")
    # status values: pending | running | stopped | error
    created_at      = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        db.UniqueConstraint("worker_id", "ssh_port", name="uq_worker_port"),
    )

    rental = db.relationship("Rental", backref="instance", lazy=True, uselist=False)

    def __repr__(self):
        return f"<Instance id={self.id} port={self.ssh_port} status={self.status}>"
