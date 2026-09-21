from flask import Flask
from flask_login import LoginManager
from flask_migrate import Migrate
from config import Config
from models import db
from models.user import User
from models.rental import Rental

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
migrate = Migrate(app, db)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route("/")
def home():
    return "<h1>Projet 3 - IaC Rental Dashboard</h1><p>It works!</p>"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
