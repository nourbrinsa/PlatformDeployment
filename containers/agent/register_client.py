"""
Module d'enregistrement du Worker Agent aupres du Controller.
Envoie POST /workers/register au demarrage, puis POST /workers/heartbeat
toutes les HEARTBEAT_INTERVAL secondes, dans un thread separe.
"""
import os
import socket
import threading
import time

import requests

CONTROLLER_URL = os.environ.get("CONTROLLER_URL", "http://192.168.56.12:5000")
HEARTBEAT_INTERVAL = 15  # secondes
REQUEST_TIMEOUT = 5


def get_local_ip():
    """Trouve l'IP de cette machine sur le reseau prive (192.168.56.x)."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("192.168.56.1", 80))
        return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"
    finally:
        s.close()


def register():
    hostname = socket.gethostname()
    try:
        requests.post(
            f"{CONTROLLER_URL}/workers/register",
            json={
                "hostname": hostname,
                "ip": get_local_ip(),
                "cpu": os.cpu_count(),
                "memory": 2048,
            },
            timeout=REQUEST_TIMEOUT,
        )
        print(f"[register] enregistre aupres de {CONTROLLER_URL}")
    except requests.exceptions.RequestException as e:
        print(f"[register] Controller injoignable ({e}), on reessaiera au heartbeat")


def _heartbeat_loop():
    hostname = socket.gethostname()
    while True:
        time.sleep(HEARTBEAT_INTERVAL)
        try:
            requests.post(
                f"{CONTROLLER_URL}/workers/heartbeat",
                json={"hostname": hostname},
                timeout=REQUEST_TIMEOUT,
            )
            print("[heartbeat] envoye")
        except requests.exceptions.RequestException as e:
            print(f"[heartbeat] echec ({e})")


def start_background_registration():
    """A appeler une fois au demarrage du Worker Agent."""
    register()
    thread = threading.Thread(target=_heartbeat_loop, daemon=True)
    thread.start()
