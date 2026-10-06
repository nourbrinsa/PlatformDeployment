import re
from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user
from models import db
from models.user import User

bp = Blueprint("auth", __name__)

USERNAME_RE = re.compile(r"[A-Za-z0-9_-]{3,30}")
EMAIL_RE    = re.compile(r"[^@\s]{1,64}@[^@\s]{1,255}\.[^@\s]{2,}")
PASSWORD_MIN_LEN = 8


@bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email    = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        if not username or not email or not password:
            flash("Tous les champs sont obligatoires.")
            return render_template("register.html")
        if not USERNAME_RE.fullmatch(username):
            flash("Nom d'utilisateur : 3 à 30 caractères (lettres, chiffres, _ et -).")
            return render_template("register.html")
        if len(email) > 255 or not EMAIL_RE.fullmatch(email):
            flash("Adresse email invalide.")
            return render_template("register.html")
        if len(password) < PASSWORD_MIN_LEN or len(password) > 128:
            flash(f"Mot de passe : entre {PASSWORD_MIN_LEN} et 128 caractères.")
            return render_template("register.html")
        if User.query.filter_by(email=email).first():
            flash("Un compte avec cet email existe déjà.")
            return render_template("register.html")
        if User.query.filter_by(username=username).first():
            flash("Ce nom d'utilisateur est déjà pris.")
            return render_template("register.html")
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        login_user(user)
        return redirect(url_for("dashboard.index"))
    return render_template("register.html")


@bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))
    if request.method == "POST":
        email    = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = User.query.filter_by(email=email).first()
        if user is None or not user.check_password(password):
            flash("Email ou mot de passe incorrect.")
            return render_template("login.html")
        login_user(user)
        return redirect(url_for("dashboard.index"))
    return render_template("login.html")


@bp.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.login"))
