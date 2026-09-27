from flask import Flask
from flask_login import LoginManager
from flask_migrate import Migrate
from config import Config
from models import db
from models.user import User


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    Migrate(app, db)

    login_manager = LoginManager()
    login_manager.login_view = "auth.login"
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Import all models so Flask-Migrate detects them
    from models.user import User
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

    @app.route("/")
    def home():
        return "<meta http-equiv='refresh' content='0;url=/dashboard'>"

    @app.route("/health")
    def health():
        return {"status": "ok"}, 200

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
