import os
import secrets

key_path = os.path.abspath(os.path.join(__file__, "..", "secret_key.txt"))
os.makedirs(os.path.dirname(key_path), exist_ok=True)

if not os.path.exists(key_path):
    key = secrets.token_urlsafe(64)
    with open(key_path, "w") as f:
        f.write(key)

from app import create_app

app = create_app()

from werkzeug.security import generate_password_hash

from app.extensions import db
from app.models import Post, User

admin = User(
    email="admin@itos.com",
    first_name="Admin",
    last_name="Admin",
    password_hash=generate_password_hash("admin"),
    is_admin=True,
)

with app.app_context():
    db.create_all()

    db.session.add(admin)

    db.session.commit()
