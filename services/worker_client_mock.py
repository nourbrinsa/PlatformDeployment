import uuid
from datetime import datetime, timedelta, timezone


class WorkerAgentError(Exception):
    pass


def create_instance(worker_ip, user_id, distribution, duration_minutes):
    instance_id = f"rent-{user_id}-{uuid.uuid4().hex[:6]}"
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=duration_minutes)
    return {"status": "running", "instance_id": instance_id, "distribution": distribution, "host": worker_ip, "ssh_port": 32768, "ssh_user": "student", "ssh_password": "mockpassword123", "expires_at": expires_at.strftime("%Y-%m-%dT%H:%M:%SZ")}, 201


def get_instance_status(worker_ip, instance_id):
    return {"status": "running", "instance_id": instance_id}, 200


def delete_instance(worker_ip, instance_id):
    return {"status": "deleted", "instance_id": instance_id}, 200


def check_health(worker_ip):
    return True
