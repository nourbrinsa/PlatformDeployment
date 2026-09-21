from datetime import datetime, timezone
from . import db

class Rental(db.Model):
    __tablename__ = "rentals"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    container_name = db.Column(db.String(255), unique=True, nullable=False)
    os_image = db.Column(db.String(50), nullable=False)
    ssh_port = db.Column(db.Integer, unique=True, nullable=False)

    started_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    expires_at = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), default="pending")

    def is_expired(self):
        return datetime.now(timezone.utc) > self.expires_at
