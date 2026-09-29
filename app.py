from datetime import datetime, timezone, timedelta

from flask import Flask, render_template, redirect, url_for, request
from flask_login import (
    LoginManager,
    login_required,
    login_user,
    logout_user,
    current_user
)
from flask_migrate import Migrate

from config import Config
from models import db
from models.user import User
from models.rental import Rental


# ============================================================
# APPLICATION
# ============================================================

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)

migrate = Migrate(app, db)


# ============================================================
# FLASK-LOGIN
# ============================================================

login_manager = LoginManager()
login_manager.init_app(app)

login_manager.login_view = "login"


@login_manager.user_loader
def load_user(user_id):

    return User.query.get(int(user_id))


# ============================================================
# ACCUEIL
# ============================================================

@app.route("/")
def home():

    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    return redirect(url_for("login"))


# ============================================================
# CONNEXION
# ============================================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    error = None

    if request.method == "POST":

        email = request.form.get("username")
        password = request.form.get("password")

        # Votre modèle User utilise un email
        user = User.query.filter_by(email=email).first()

        if user is None:

            error = "Adresse e-mail ou mot de passe incorrect."

        elif not user.check_password(password):

            error = "Adresse e-mail ou mot de passe incorrect."

        else:

            login_user(user)

            return redirect(url_for("dashboard"))

    return render_template(
        "login.html",
        error=error
    )


# ============================================================
# INSCRIPTION
# ============================================================

@app.route("/register", methods=["GET", "POST"])
def register():

    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    error = None

    if request.method == "POST":

        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")
        password_confirm = request.form.get("password_confirm")

        # Vérification des champs
        if not username or not email or not password:

            error = "Tous les champs sont obligatoires."

        elif password != password_confirm:

            error = "Les mots de passe ne correspondent pas."

        elif User.query.filter_by(email=email).first():

            error = "Cette adresse e-mail existe déjà."

        else:

            # Votre modèle User ne possède pas de username.
            # On conserve donc le nom d'utilisateur uniquement
            # pour l'affichage dans cette version.

            user = User(
                email=email
            )

            user.set_password(password)

            db.session.add(user)
            db.session.commit()

            login_user(user)

            return redirect(url_for("dashboard"))

    return render_template(
        "register.html",
        error=error
    )


# ============================================================
# DECONNEXION
# ============================================================

@app.route("/logout")
@login_required
def logout():

    logout_user()

    return redirect(url_for("login"))


# ============================================================
# DASHBOARD
# ============================================================

@app.route("/dashboard")
@login_required
def dashboard():

    # Récupération des locations de l'utilisateur
    user_rentals = Rental.query.filter_by(
        user_id=current_user.id
    ).all()

    # Mise à jour éventuelle des locations expirées
    now = datetime.now(timezone.utc)

    for rental in user_rentals:

        if rental.expires_at and rental.expires_at < now:

            rental.status = "expired"

    db.session.commit()

    # Instances en fonctionnement
    running = sum(
        1
        for rental in user_rentals
        if rental.status == "running"
    )

    # Instances arrêtées
    stopped = sum(
        1
        for rental in user_rentals
        if rental.status == "stopped"
    )

    return render_template(
        "dashboard.html",
        instances=user_rentals,
        running=running,
        stopped=stopped,
        username=current_user.email
    )


# ============================================================
# CREATION D'UNE INSTANCE
# ============================================================

@app.route("/instances/create", methods=["GET", "POST"])
@login_required
def create_instance():

    error = None

    if request.method == "POST":

        name = request.form.get("name")
        os_image = request.form.get("os_image", "ubuntu")

        if not name:

            error = "Le nom de l'instance est obligatoire."

        elif Rental.query.filter_by(
            container_name=name
        ).first():

            error = "Ce nom d'instance existe déjà."

        else:

            # Pour le moment :
            # durée temporaire de 60 minutes.
            #
            # Elle pourra ensuite venir du formulaire
            # et être envoyée au Worker.

            expires_at = (
                datetime.now(timezone.utc)
                + timedelta(minutes=60)
            )

            # Choix temporaire du port SSH.
            # Cette partie devra ensuite être gérée
            # par le Worker Docker.

            existing_ports = [
                rental.ssh_port
                for rental in Rental.query.all()
            ]

            ssh_port = 2200

            while ssh_port in existing_ports:
                ssh_port += 1

            rental = Rental(
                user_id=current_user.id,
                container_name=name,
                os_image=os_image,
                ssh_port=ssh_port,
                started_at=datetime.now(timezone.utc),
                expires_at=expires_at,
                status="running"
            )

            db.session.add(rental)
            db.session.commit()

            return redirect(url_for("dashboard"))

    return render_template(
        "create_instance.html",
        error=error
    )


# ============================================================
# DETAILS D'UNE INSTANCE
# ============================================================

@app.route("/instances/<int:instance_id>")
@login_required
def instance_details(instance_id):

    rental = Rental.query.filter_by(
        id=instance_id,
        user_id=current_user.id
    ).first()

    if rental is None:

        return "Instance introuvable", 404

    return render_template(
        "instance.html",
        instance=rental
    )


# ============================================================
# DEMARRER
# ============================================================

@app.route("/instances/<int:instance_id>/start")
@login_required
def start_instance(instance_id):

    rental = Rental.query.filter_by(
        id=instance_id,
        user_id=current_user.id
    ).first()

    if rental is None:
        return "Instance introuvable", 404

    rental.status = "running"

    db.session.commit()

    return redirect(url_for("dashboard"))


# ============================================================
# ARRETER
# ============================================================

@app.route("/instances/<int:instance_id>/stop")
@login_required
def stop_instance(instance_id):

    rental = Rental.query.filter_by(
        id=instance_id,
        user_id=current_user.id
    ).first()

    if rental is None:
        return "Instance introuvable", 404

    rental.status = "stopped"

    db.session.commit()

    return redirect(url_for("dashboard"))


# ============================================================
# REDEMARRER
# ============================================================

@app.route("/instances/<int:instance_id>/restart")
@login_required
def restart_instance(instance_id):

    rental = Rental.query.filter_by(
        id=instance_id,
        user_id=current_user.id
    ).first()

    if rental is None:
        return "Instance introuvable", 404

    rental.status = "running"

    db.session.commit()

    return redirect(url_for("dashboard"))


# ============================================================
# SUPPRIMER
# ============================================================

@app.route("/instances/<int:instance_id>/delete")
@login_required
def delete_instance(instance_id):

    rental = Rental.query.filter_by(
        id=instance_id,
        user_id=current_user.id
    ).first()

    if rental is None:
        return "Instance introuvable", 404

    db.session.delete(rental)
    db.session.commit()

    return redirect(url_for("dashboard"))


# ============================================================
# LANCEMENT
# ============================================================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )
