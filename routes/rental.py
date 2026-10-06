from flask import Blueprint, request, flash, redirect, url_for, render_template, current_app, make_response
from flask_login import login_required, current_user
from datetime import datetime, timezone
from models import db
from models.instance import Instance
from models.rental import Rental
from models.distribution import Distribution
from services.resource_manager import pick_available_worker

bp = Blueprint("rental", __name__)


def get_worker_client():
    if current_app.config.get("USE_MOCK_WORKER_AGENT", True):
        from services import worker_client_mock as wc
    else:
        from services import worker_client as wc
    return wc


@bp.route("/rent", methods=["POST"])
@login_required
def rent():
    wc = get_worker_client()
    distribution_name = request.form.get("distribution", "").strip()
    try:
        duration_minutes = int(request.form.get("duration_minutes", "60"))
    except ValueError:
        duration_minutes = 0
    if not 1 <= duration_minutes <= 1440:   # pas d'assert : désactivé avec python -O
        flash("Durée invalide (entre 1 et 1440 minutes).")
        return redirect(url_for("dashboard.index"))

    distribution = Distribution.query.filter_by(name=distribution_name, status="active").first()
    if distribution is None:
        flash("Distribution invalide.")
        return redirect(url_for("dashboard.index"))

    worker = pick_available_worker()
    if worker is None:
        flash("Aucun Worker disponible pour le moment.")
        return redirect(url_for("dashboard.index"))

    try:
        data, status_code = wc.create_instance(worker.ip, current_user.id, distribution_name, duration_minutes)
    except wc.WorkerAgentError:
        flash("Le serveur ne répond pas. Réessayez.")
        return redirect(url_for("dashboard.index"))

    if data.get("status") == "error":
        flash(f"Erreur Worker : {data.get('message')}")
        return redirect(url_for("dashboard.index"))

    expires_at = datetime.strptime(data["expires_at"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)

    instance = Instance(container_id=data["instance_id"], worker_id=worker.id, distribution_id=distribution.id, ssh_port=data["ssh_port"], status="running")
    db.session.add(instance)
    db.session.flush()

    rental = Rental(user_id=current_user.id, instance_id=instance.id, start_time=datetime.now(timezone.utc), end_time=expires_at, status="active")
    db.session.add(rental)
    db.session.commit()

    resp = make_response(render_template("rental_created.html", ssh_command=f"ssh {data['ssh_user']}@{data['host']} -p {data['ssh_port']}", password=data["ssh_password"], expires_at=data["expires_at"]))
    resp.headers["Cache-Control"] = "no-store"   # la page contient un mot de passe
    return resp


@bp.route("/instances/<int:instance_id>/stop", methods=["POST"])
@login_required
def stop_instance(instance_id):
    wc = get_worker_client()
    instance = Instance.query.get_or_404(instance_id)
    rental   = instance.rental
    if rental is None or rental.user_id != current_user.id:
        flash("Instance introuvable.")
        return redirect(url_for("dashboard.index"))
    try:
        data, _ = wc.delete_instance(instance.worker.ip, instance.container_id)
    except wc.WorkerAgentError:
        flash("Impossible de contacter le serveur.")
        return redirect(url_for("dashboard.index"))
    if data.get("status") == "deleted":
        instance.status = "stopped"
        rental.status   = "stopped"
        db.session.commit()
        flash("Instance arrêtée.")
    return redirect(url_for("dashboard.index"))
