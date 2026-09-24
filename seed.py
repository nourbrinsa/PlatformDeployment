from app import app
from models import db
from models.user import User
from models.distribution import Distribution
from models.worker import Worker
from models.instance import Instance
from models.rental import Rental

with app.app_context():
    if Distribution.query.first():
        print("Already seeded — skipping.")
    else:
        db.session.add_all([
            Distribution(name="Ubuntu",  docker_image="ubuntu:24.04",   version="24.04", status="active"),
            Distribution(name="Debian",  docker_image="debian:13",      version="13",    status="active"),
            Distribution(name="Alpine",  docker_image="alpine:latest",  version="latest",status="active"),
        ])
        db.session.commit()
        print("Distributions seeded.")
