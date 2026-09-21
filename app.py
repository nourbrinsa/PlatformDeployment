from flask import Flask, render_template, redirect, url_for, request, session
from functools import wraps

app = Flask(__name__)

# Clé utilisée pour les sessions Flask
# Elle devra être déplacée dans une variable d'environnement
# lorsque le projet sera finalisé.
app.secret_key = "cle-secrete-temporaire"


# ============================================================
# DONNEES TEMPORAIRES
# ============================================================

# Utilisateurs
# Pour le moment, ils sont stockés en mémoire.
users = {
    "admin": {
        "password": "admin",
        "email": "admin@example.com"
    }
}


# Instances
instances = [
    {
        "id": 1,
        "name": "instance-01",
        "username": "admin",
        "status": "running",
        "server": "docker-host-01",
        "ip": "192.168.56.10",
        "ssh_port": 2201
    },
    {
        "id": 2,
        "name": "instance-02",
        "username": "admin",
        "status": "stopped",
        "server": "docker-host-01",
        "ip": "192.168.56.10",
        "ssh_port": 2202
    }
]


# ============================================================
# VERIFICATION DE CONNEXION
# ============================================================

def login_required(function):

    @wraps(function)
    def decorated_function(*args, **kwargs):

        if "username" not in session:
            return redirect(url_for("login"))

        return function(*args, **kwargs)

    return decorated_function


# ============================================================
# ACCUEIL
# ============================================================

@app.route("/")
def home():

    if "username" in session:
        return redirect(url_for("dashboard"))

    return redirect(url_for("login"))


# ============================================================
# INSCRIPTION
# ============================================================

@app.route("/register", methods=["GET", "POST"])
def register():

    error = None

    if request.method == "POST":

        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")
        password_confirm = request.form.get("password_confirm")

        # Vérification des champs
        if not username or not email or not password:
            error = "Tous les champs sont obligatoires."

        # Vérification du mot de passe
        elif password != password_confirm:
            error = "Les mots de passe ne correspondent pas."

        # Vérification du nom d'utilisateur
        elif username in users:
            error = "Ce nom d'utilisateur existe déjà."

        else:

            # Création du compte
            users[username] = {
                "password": password,
                "email": email
            }

            # Connexion automatique
            session["username"] = username

            return redirect(url_for("dashboard"))

    return render_template(
        "register.html",
        error=error
    )


# ============================================================
# CONNEXION
# ============================================================

@app.route("/login", methods=["GET", "POST"])
def login():

    error = None

    if request.method == "POST":

        username = request.form.get("username")
        password = request.form.get("password")

        # Vérification du compte
        if username not in users:

            error = "Nom d'utilisateur ou mot de passe incorrect."

        elif users[username]["password"] != password:

            error = "Nom d'utilisateur ou mot de passe incorrect."

        else:

            # Création de la session
            session["username"] = username

            return redirect(url_for("dashboard"))

    return render_template(
        "login.html",
        error=error
    )


# ============================================================
# DECONNEXION
# ============================================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("login"))


# ============================================================
# DASHBOARD
# ============================================================

@app.route("/dashboard")
@login_required
def dashboard():

    username = session["username"]

    # On affiche uniquement les instances
    # appartenant à l'utilisateur connecté.
    user_instances = [
        instance
        for instance in instances
        if instance["username"] == username
    ]

    running = sum(
        1
        for instance in user_instances
        if instance["status"] == "running"
    )

    stopped = sum(
        1
        for instance in user_instances
        if instance["status"] == "stopped"
    )

    return render_template(
        "dashboard.html",
        instances=user_instances,
        running=running,
        stopped=stopped,
        username=username
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

        if not name:

            error = "Le nom de l'instance est obligatoire."

        else:

            # Création d'un nouvel identifiant
            if len(instances) == 0:
                new_id = 1
            else:
                new_id = max(
                    instance["id"]
                    for instance in instances
                ) + 1

            new_instance = {
                "id": new_id,
                "name": name,
                "username": session["username"],
                "status": "running",
                "server": "docker-host-01",
                "ip": "192.168.56.10",
                "ssh_port": 2200 + new_id
            }

            instances.append(new_instance)

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

    username = session["username"]

    instance = next(
        (
            instance
            for instance in instances
            if instance["id"] == instance_id
            and instance["username"] == username
        ),
        None
    )

    if instance is None:
        return "Instance introuvable", 404

    return render_template(
        "instance.html",
        instance=instance
    )


# ============================================================
# DEMARRER
# ============================================================

@app.route("/instances/<int:instance_id>/start")
@login_required
def start_instance(instance_id):

    username = session["username"]

    for instance in instances:

        if (
            instance["id"] == instance_id
            and instance["username"] == username
        ):

            instance["status"] = "running"

    return redirect(url_for("dashboard"))


# ============================================================
# ARRETER
# ============================================================

@app.route("/instances/<int:instance_id>/stop")
@login_required
def stop_instance(instance_id):

    username = session["username"]

    for instance in instances:

        if (
            instance["id"] == instance_id
            and instance["username"] == username
        ):

            instance["status"] = "stopped"

    return redirect(url_for("dashboard"))


# ============================================================
# REDÉMARRER
# ============================================================

@app.route("/instances/<int:instance_id>/restart")
@login_required
def restart_instance(instance_id):

    username = session["username"]

    for instance in instances:

        if (
            instance["id"] == instance_id
            and instance["username"] == username
        ):

            instance["status"] = "running"

    return redirect(url_for("dashboard"))


# ============================================================
# SUPPRIMER
# ============================================================

@app.route("/instances/<int:instance_id>/delete")
@login_required
def delete_instance(instance_id):

    global instances

    username = session["username"]

    instances = [
        instance
        for instance in instances
        if not (
            instance["id"] == instance_id
            and instance["username"] == username
        )
    ]

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