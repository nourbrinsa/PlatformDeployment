from flask import Flask, render_template
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from config import Config
from models import db
from models.user import User

csrf = CSRFProtect()


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Refus de démarrer avec une configuration non sécurisée
    if not app.config.get("SECRET_KEY"):
        raise RuntimeError("SECRET_KEY manquant : définissez-le dans .env")
    if not app.config.get("WORKER_TOKEN"):
        raise RuntimeError("WORKER_TOKEN manquant : définissez-le dans .env")

    db.init_app(app)
    Migrate(app, db)
    csrf.init_app(app)

    login_manager = LoginManager()
    login_manager.login_view = "auth.login"
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    # Import all models so Flask-Migrate detects them
    from models.distribution import Distribution
    from models.worker import Worker
    from models.instance import Instance
    from models.rental import Rental

    # Register blueprints
    from routes.auth import bp as auth_bp
    from routes.dashboard import bp as dashboard_bp
    from routes.rental import bp as rental_bp
    from routes.workers import bp as workers_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(rental_bp)
    app.register_blueprint(workers_bp)

    # Les routes machine-à-machine s'authentifient par jeton, pas par cookie/CSRF
    csrf.exempt(workers_bp)

    @app.route("/")
    def home():
        return "<meta http-equiv='refresh' content='0;url=/dashboard'>"

    @app.route("/health")
    def health():
        return {"status": "ok"}, 200

    # --- Gestion des erreurs : pages génériques, pas de stack trace ---
    @app.errorhandler(400)
    def bad_request(e):
        return render_template("error.html", code=400, message="Requête invalide."), 400

    @app.errorhandler(403)
    def forbidden(e):
        return render_template("error.html", code=403, message="Accès refusé."), 403

    @app.errorhandler(404)
    def not_found(e):
        return render_template("error.html", code=404, message="Page introuvable."), 404

    @app.errorhandler(500)
    def server_error(e):
        db.session.rollback()
        return render_template("error.html", code=500, message="Erreur interne du serveur."), 500

    # --- En-têtes de sécurité ---
    @app.after_request
    def security_headers(resp):
        resp.headers["X-Content-Type-Options"] = "nosniff"
        resp.headers["X-Frame-Options"] = "DENY"
        resp.headers["Referrer-Policy"] = "same-origin"
        resp.headers["Content-Security-Policy"] = (
            "default-src 'self'; style-src 'self' 'unsafe-inline'; frame-ancestors 'none'"
        )
        return resp

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=app.config["DEBUG"])
