from .person import Person
from .user import User, UserRole
from .post import Post, PostStatus
from .tag import Tag
from .file import File, FileStatus

from sqlalchemy import event
import os
from flask import current_app

@event.listens_for(File, "after_delete")
def delete_file_on_disk(mapper, connection, target):
    file_path = os.path.join(current_app.root_path, "uploads", target.filename)  # adjust your uploads folder
    
    if os.path.exists(file_path):
        os.remove(file_path)