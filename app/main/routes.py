from flask import render_template, url_for, request, redirect, current_app, send_file, abort, make_response
from flask_login import current_user
from app.extensions import db
from app.models import Post, File, PostStatus, FileStatus, Tag, User, UserRole
import os
from datetime import datetime

from app.main import bp


@bp.route("/")
def home():
    tagid = request.args.get("tag", None, type=int)
    
    query = Post.query.filter_by(status=PostStatus.visible).order_by(Post.created_at.desc())
    if tagid:
        query = query.filter(Post.tags.any(Tag.id == tagid))
    
    page = request.args.get('page', 1, type=int)
        
    pagination = query.paginate(page=page, per_page=10, error_out=False)
    
    last_read_str = request.cookies.get('last_read')
    last_read = None
    if last_read_str:
        try:
            last_read = datetime.fromisoformat(last_read_str)
        except ValueError:
            last_read = None

    newest_post = max((p.created_at for p in pagination.items), default=None)
    
    resp = make_response(render_template("board.html", pagination=pagination, tagid=tagid, last_read=last_read))
    
    if newest_post:
        resp.set_cookie('last_read', newest_post.isoformat(), max_age=60*60*24*365, samesite='Lax', path='/')

            
    return resp

@bp.route("/favicon.ico")
def favicon():
    return redirect(url_for("static", filename="icons/favicon.ico"))

@bp.route("/uploads/<filename>")
def userfile(filename):
    path = os.path.join("uploads", filename)
    
    file = File.query.filter_by(filename=filename).first_or_404()
    
    if file.status != FileStatus.visible and not (current_user.is_authenticated and (current_user.role == UserRole.superadmin or current_user.role == UserRole.admin)):
        return render_template("file-blocked.html", name=file.name)

    return send_file(path, mimetype=file.mimetype)