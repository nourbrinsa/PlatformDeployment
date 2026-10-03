from flask import Blueprint, request, flash, redirect, url_for, render_template, current_app
from flask_login import login_required, current_user
from datetime import datetime, timezone
from models import db
from models.instance import Instance
from models.rental import Rental
from models.distribution import Distribution
from services.resource_manager import pick_candidate_workers

bp = Blueprint("rental", __name__)


def get_worker_client():
    if current_app.config.get("USE_MOCK_WORKER_AGENT", True):
        from services import worker_client_mock as wc
    else:
        from services import worker_client as wc
    return wc


def reconcile_worker_instances(worker, wc):
    """
    Avant de créer une nouvelle instance sur ce worker, vérifie que les
    instances marquées 'running' en base existent encore réellement côté
    Worker Agent. Celles qui ont expiré / été nettoyées côté worker
    (cleanup.sh) sont marquées 'expired' en base, pour libérer leur port
    et ne plus bloquer la contrainte d'unicité (worker_id, ssh_port).
    """
    stale = Instance.query.filter_by(worker_id=worker.id, status="running").all()
    for inst in stale:
        try:
            data, _ = wc.get_instance_status(worker.ip, inst.container_id)
        except wc.WorkerAgentError:
            continue
        if data.get("status") == "absent":
            inst.status = "expired"
            if inst.rental:
                inst.rental.status = "expired"
    db.session.commit()


@bp.route("/rent", methods=["POST"])
@login_required
def rent():
    wc = get_worker_client()
    distribution_name = request.form.get("distribution", "").strip()
    try:
        duration_minutes = int(request.form.get("duration_minutes", "60"))
        assert 1 <= duration_minutes <= 1440
    except (ValueError, AssertionError):
        flash("Durée invalide (entre 1 et 1440 minutes).")
        return redirect(url_for("dashboard.index"))

    distribution = Distribution.query.filter_by(name=distribution_name, status="active").first()
    if distribution is None:
        flash("Distribution invalide.")
        return redirect(url_for("dashboard.index"))

    candidates = pick_candidate_workers()
    if not candidates:
        flash("Aucun Worker configuré.")
        return redirect(url_for("dashboard.index"))

    worker = None
    data = None

    for candidate in candidates:
        if not wc.check_health(candidate.ip):
            candidate.status = "OFFLINE"
            db.session.commit()
            continue

        try:
            attempt, status_code = wc.create_instance(
                candidate.ip, current_user.id, distribution_name, duration_minutes
            )
        except wc.WorkerAgentError:
            candidate.status = "OFFLINE"
            db.session.commit()
            continue

        if attempt.get("status") == "error":
            # Erreur métier renvoyée par le Worker Agent (ex: distribution
            # invalide) : pas la peine d'essayer un autre worker, ce sera
            # la même erreur partout. On s'arrête et on l'affiche.
            flash(f"Erreur Worker : {attempt.get('message')}")
            return redirect(url_for("dashboard.index"))

        # Succès : ce worker a répondu et créé l'instance.
        candidate.status = "AVAILABLE"
        db.session.commit()
        worker = candidate
        data = attempt
        break

    if worker is None:
        flash("Tous les Workers sont injoignables. Réessayez dans quelques instants.")
        return redirect(url_for("dashboard.index"))

    # Nettoie les anciennes instances expirées sur CE worker avant d'insérer
    # la nouvelle, pour éviter un conflit sur (worker_id, ssh_port).
    reconcile_worker_instances(worker, wc)

    expires_at = datetime.strptime(data["expires_at"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)

    instance = Instance(
        container_id=data["instance_id"],
        worker_id=worker.id,
        distribution_id=distribution.id,
        ssh_port=data["ssh_port"],
        status="running",
    )
    db.session.add(instance)
    db.session.flush()

    rental = Rental(
        user_id=current_user.id,
        instance_id=instance.id,
        start_time=datetime.now(timezone.utc),
        end_time=expires_at,
        status="active",
    )
    db.session.add(rental)
    db.session.commit()

    return render_template(
        "rental_created.html",
        ssh_command=f"ssh {data['ssh_user']}@{data['host']} -p {data['ssh_port']}",
        password=data["ssh_password"],
        expires_at=data["expires_at"],
    )


@bp.route("/instances/<int:instance_id>/stop", methods=["POST"])
@login_required
def stop_instance(instance_id):
    wc = get_worker_client()
    instance = Instance.query.get_or_404(instance_id)
    rental = instance.rental
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
        rental.status = "stopped"
        db.session.commit()
        flash("Instance arrêtée.")

    return redirect(url_for("dashboard.index"))
