from datetime import datetime, timezone
from . import db

class Rental(db.Model):
    __tablename__ = "rentals"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    instance_id = db.Column(db.Integer, db.ForeignKey("instances.id"), nullable=False)

    start_time = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    end_time = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), default="pending")

    def is_expired(self):
        return datetime.now(timezone.utc) > self.end_time
