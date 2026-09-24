from . import db

class Worker(db.Model):
    __tablename__ = "workers"

    id = db.Column(db.Integer, primary_key=True)
    hostname = db.Column(db.String(100), unique=True, nullable=False)
    ip = db.Column(db.String(45), nullable=False)
    status = db.Column(db.String(20), default="AVAILABLE")
    cpu = db.Column(db.Float)
    memory = db.Column(db.Float)
    last_heartbeat = db.Column(db.DateTime)

    instances = db.relationship("Instance", backref="worker", lazy=True)
