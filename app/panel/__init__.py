from flask import Blueprint

bp = Blueprint("panel", __name__, template_folder="../templates/panel")

from app.panel import routes