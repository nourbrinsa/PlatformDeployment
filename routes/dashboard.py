from flask import Blueprint, render_template
from flask_login import login_required, current_user
from models.rental import Rental
from models.distribution import Distribution

bp = Blueprint("dashboard", __name__)


@bp.route("/dashboard")
@login_required
def index():
    rentals = (
        Rental.query
        .filter_by(user_id=current_user.id)
        .order_by(Rental.start_time.desc())
        .all()
    )
    distributions = Distribution.query.filter_by(status="active").all()
    return render_template("dashboard.html", rentals=rentals, distributions=distributions)
