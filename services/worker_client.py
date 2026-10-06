import os
import requests

WORKER_AGENT_PORT = 5001
TIMEOUT_SECONDS = 15
HEADERS = {"X-Worker-Token": os.environ.get("WORKER_TOKEN", "")}


class WorkerAgentError(Exception):
    pass


def create_instance(worker_ip, user_id, distribution, duration_minutes):
    url = f"http://{worker_ip}:{WORKER_AGENT_PORT}/instances"
    try:
        response = requests.post(url, json={"user_id": str(user_id), "distribution": distribution, "duration_minutes": duration_minutes}, timeout=TIMEOUT_SECONDS, headers=HEADERS)
    except requests.exceptions.RequestException as e:
        raise WorkerAgentError(f"worker {worker_ip} unreachable: {e}")
    data = response.json()
    if data.get("status") == "running":
        data["host"] = worker_ip
    return data, response.status_code


def get_instance_status(worker_ip, instance_id):
    url = f"http://{worker_ip}:{WORKER_AGENT_PORT}/instances/{instance_id}"
    try:
        response = requests.get(url, timeout=TIMEOUT_SECONDS, headers=HEADERS)
    except requests.exceptions.RequestException as e:
        raise WorkerAgentError(f"worker {worker_ip} unreachable: {e}")
    return response.json(), response.status_code


def delete_instance(worker_ip, instance_id):
    url = f"http://{worker_ip}:{WORKER_AGENT_PORT}/instances/{instance_id}"
    try:
        response = requests.delete(url, timeout=TIMEOUT_SECONDS, headers=HEADERS)
    except requests.exceptions.RequestException as e:
        raise WorkerAgentError(f"worker {worker_ip} unreachable: {e}")
    return response.json(), response.status_code


def check_health(worker_ip):
    url = f"http://{worker_ip}:{WORKER_AGENT_PORT}/health"
    try:
        response = requests.get(url, timeout=5, headers=HEADERS)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False
