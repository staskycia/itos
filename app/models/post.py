from app.extensions import db
from datetime import datetime
from sqlalchemy import Enum
from enum import Enum as PyEnum

from app.models.post_tags import post_tags
from app.models.post_files import post_files

class PostStatus(PyEnum):
    visible = "widoczny"
    hidden = "ukryty"
    pending = "oczekujący"

class Post(db.Model):
    __tablename__ = "posts"
    
    id = db.Column(db.Integer, primary_key=True)
    
    title = db.Column(db.String(120), unique=False, nullable=False)
    content = db.Column(db.Text, unique=False, nullable=False)
    
    status = db.Column(Enum(PostStatus, name="post_status", native_enum=True, validate_strings=True), nullable=False, default=PostStatus.visible, index=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    
    author = db.relationship("User", back_populates="posts")
    
    tags = db.relationship("Tag", secondary=post_tags, back_populates="posts", lazy="select")
    files = db.relationship("File", secondary=post_files, back_populates="posts", lazy="select")

    def __repr__(self):
        return f"{self.title} ({self.author})"