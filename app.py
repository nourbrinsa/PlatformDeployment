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

    # Register blueprints here as they are built
    # from routes.auth import auth_bp
    # app.register_blueprint(auth_bp)

    @app.route("/")
    def home():
        return "<h1>Projet 3 — IaC Rental Dashboard</h1><p>It works!</p>"

    @app.route("/health")
    def health():
        return {"status": "ok"}, 200

    return app

app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
