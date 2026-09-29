"""
Worker Agent : expose en HTTP les actions de gestion des conteneurs.
Tourne sur chaque machine Worker. Appelle les scripts bash existants
(containers/scripts/) qui, eux, pilotent Docker directement.
"""
import json
import subprocess
from pathlib import Path

from flask import Flask, jsonify, request

from register_client import start_background_registration

app = Flask(__name__)

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"


def run_script(script_name, *args):
    """Exécute un script du contrat et renvoie son JSON parsé + son code retour."""
    script_path = SCRIPTS_DIR / script_name
    result = subprocess.run(
        [str(script_path), *args],
        capture_output=True, text=True, timeout=300
    )
    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        data = {"status": "error", "message": "invalid script output"}
    return data, result.returncode


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200


@app.route("/instances", methods=["POST"])
def create_instance():
    body = request.get_json(silent=True) or {}
    user_id = str(body.get("user_id", ""))
    distribution = body.get("distribution", "")
    duration = str(body.get("duration_minutes", ""))

    data, code = run_script("create_instance.sh", user_id, distribution, duration)
    http_status = 201 if data.get("status") == "running" else 400
    return jsonify(data), http_status


@app.route("/instances/<instance_id>", methods=["DELETE"])
def delete_instance(instance_id):
    data, code = run_script("delete_instance.sh", instance_id)
    http_status = 200 if data.get("status") == "deleted" else 400
    return jsonify(data), http_status


@app.route("/instances/<instance_id>", methods=["GET"])
def get_status(instance_id):
    data, code = run_script("get_status.sh", instance_id)
    return jsonify(data), 200


if __name__ == "__main__":
    # host="0.0.0.0" : accessible depuis d'autres machines du réseau (le Controller),
    # pas seulement depuis localhost. Indispensable pour une vraie architecture distribuée.
    start_background_registration()
    app.run(host="0.0.0.0", port=5001)
