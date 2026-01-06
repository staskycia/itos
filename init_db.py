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

from app.extensions import db

from app.models import User, Post

from werkzeug.security import generate_password_hash
admin = User(email = "stanislaw.stask@gmail.com", first_name="Staś", last_name="Kycia", password=generate_password_hash("admin"), is_admin=True)

with app.app_context():
    db.create_all()
    
    db.session.add(admin)
    
    db.session.commit()