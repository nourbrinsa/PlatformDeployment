from . import db

class Distribution(db.Model):
    __tablename__ = "distributions"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    docker_image = db.Column(db.String(100), nullable=False)
    version = db.Column(db.String(20))
    status = db.Column(db.String(20), default="active")

    instances = db.relationship("Instance", backref="distribution", lazy=True)
