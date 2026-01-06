from app.extensions import db
from flask_login import UserMixin
from datetime import datetime
import os
from sqlalchemy import Enum
from enum import Enum as PyEnum
from app.models.post_files import post_files

class FileStatus(PyEnum):
    visible = "widoczny"
    hidden = "ukryty"
    pending = "oczekujący"

class File(db.Model):
    __tablename__ = "files"
    
    id = db.Column(db.Integer, primary_key=True)
    
    name = db.Column(db.String(120), unique=True, nullable=False)
    filename = db.Column(db.String(200), unique=True, nullable=False)
    
    size = db.Column(db.Integer)
    mimetype = db.Column(db.String(50)) 

    status = db.Column(Enum(FileStatus, name="file_status", native_enum=True, validate_strings=True), nullable=False, default=FileStatus.visible, index=True)

    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    
    author = db.relationship("User", back_populates="files")
    posts = db.relationship("Post", secondary=post_files, back_populates="files", lazy="select")

    def __repr__(self):
        return f"{self.name} ({self.author})"