from app import app
from models import db
from models.user import User
from models.distribution import Distribution
from models.worker import Worker
from models.instance import Instance
from models.rental import Rental

with app.app_context():
    # Distributions
    if not Distribution.query.first():
        db.session.add_all([
            Distribution(name="ubuntu", docker_image="ubuntu:24.04", version="24.04", status="active"),
            Distribution(name="debian", docker_image="debian:13",    version="13",    status="active"),
        ])
        db.session.commit()
        print("Distributions seeded.")
    else:
        print("Distributions already seeded — skipping.")

    # Workers (Nour's machines — for dev/test)
    if not Worker.query.first():
        db.session.add_all([
            Worker(hostname="worker1", ip="192.168.56.11", status="available"),
            Worker(hostname="worker2", ip="192.168.56.12", status="available"),
        ])
        db.session.commit()
        print("Workers seeded.")
    else:
        print("Workers already seeded — skipping.")
