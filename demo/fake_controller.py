"""
Faux Controller minimal, JETABLE.
Sert uniquement a recevoir les appels register/heartbeat du Worker Agent
pendant que la vraie partie Flask n'existe pas encore.

Usage :
    pip install flask
    python3 fake_controller.py

Ecoute sur le port 5000, comme le vrai Controller le fera plus tard.
"""
from datetime import datetime, timezone

from flask import Flask, jsonify, request

app = Flask(__name__)

# Stockage en memoire, juste pour voir ce qui arrive pendant la demo
KNOWN_WORKERS = {}


@app.route("/workers/register", methods=["POST"])
def register():
    body = request.get_json(silent=True) or {}
    hostname = body.get("hostname", "unknown")
    KNOWN_WORKERS[hostname] = {
        "ip": body.get("ip"),
        "cpu": body.get("cpu"),
        "memory": body.get("memory"),
        "status": "AVAILABLE",
        "last_heartbeat": datetime.now(timezone.utc).isoformat(),
    }
    print(f"[REGISTER] {hostname} -> {KNOWN_WORKERS[hostname]}")
    return jsonify({"status": "registered"}), 201


@app.route("/workers/heartbeat", methods=["POST"])
def heartbeat():
    body = request.get_json(silent=True) or {}
    hostname = body.get("hostname", "unknown")
    if hostname not in KNOWN_WORKERS:
        return jsonify({"status": "error", "message": "unknown worker"}), 404

    KNOWN_WORKERS[hostname]["last_heartbeat"] = datetime.now(timezone.utc).isoformat()
    print(f"[HEARTBEAT] {hostname} OK")
    return jsonify({"status": "ok"}), 200


@app.route("/workers", methods=["GET"])
def list_workers():
    """Route pratique pour voir en un coup d'oeil ce qui s'est enregistre."""
    return jsonify(KNOWN_WORKERS), 200


if __name__ == "__main__":
    print("Fake Controller demarre sur http://0.0.0.0:5000")
    print("Routes: POST /workers/register, POST /workers/heartbeat, GET /workers")
    app.run(host="0.0.0.0", port=5000)
