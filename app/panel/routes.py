from flask import render_template, url_for, request, flash, redirect, current_app
from flask_login import current_user, login_required
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
from app.extensions import db
from app.models import User, Post, File, FileStatus, PostStatus, Tag
from itsdangerous import URLSafeTimedSerializer
from email.utils import parseaddr
from app.mail import send_button_message
import bleach
import os
import uuid

from app.panel import bp

def get_assignable_tags():
    return Tag.query.filter((Tag.is_restricted == False) | (Tag.allowed_users.any(id=current_user.id))).order_by(Tag.name).all()

@bp.route("/")
@login_required
def panel_home():
    space_used = round(current_user.space_used / (1024*1024), 2)
    percents = round(space_used/current_user.quota, 2)
    return render_template("index.html", space_used=space_used, percents=percents)

def sanitize_html(text):
    return bleach.clean(
        text,
        tags=["a"],
        attributes={
            "a": ["href"]
        },
        protocols=["http", "https"],
        strip=True
    )

@bp.route("/create", methods=["GET", "POST"])
@login_required
def create():
    if request.method == "POST":
        title = request.form.get("title")
        content = request.form.get("content")
        if not title or not content:
            flash("Nie wypełniono wszystkich wymaganych pól!", "error")
            return render_template("create.html", assignable_tags=get_assignable_tags())
        status = PostStatus.pending
        if current_user.reputation >= 60:
            status = PostStatus.visible
        tags = [int(tid) for tid in request.form.get("tags", "").split(",") if tid.strip().isdigit()]
        assignable_tags = Tag.query.filter((Tag.is_restricted == False) | (Tag.allowed_users.any(id=current_user.id))).filter(Tag.id.in_(tags)).all()
        if(len(assignable_tags) > 5):
            flash("Możesz wybrać do 5 kategorii!", "error")
            return render_template("create.html", assignable_tags=get_assignable_tags())
        fileids = [int(fid) for fid in request.form.get("files", "").split(",") if fid.strip().isdigit()]
        files = File.query.filter(File.user_id == current_user.id, File.id.in_(fileids)).all()
        post = Post(title=title, content=sanitize_html(content), author=current_user, status=status, tags=assignable_tags, files=files)
        db.session.add(post)
        db.session.commit()
        if status == PostStatus.visible:
            flash("Twoje ogłoszenie zostało opublikowane!", "success")
        else:
            flash("Twoje ogłoszenie zostało wysłane do weryfikacji!", "success")
        return redirect(url_for("panel.news"))
    return render_template("create.html", assignable_tags=get_assignable_tags())

@bp.route("/files")
@login_required
def files():
    return render_template("files.html")

@bp.route("/posts")
@login_required
def news():
    return render_template("news.html")

def generate_token(value):
    serializer = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
    return serializer.dumps(value, salt="email-confirmaion")

def confirm_token(token, expiration=1800):
    serializer = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
    try:
        value = serializer.loads(token, salt="email-confirmaion", max_age=expiration)
        return value
    except Exception:
        return None

def is_valid_email(value: str) -> bool:
    return "@" in parseaddr(value)[1]

@bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    if request.method == "POST":
        mode = request.form.get("mode")
        if mode == "password":
            password = request.form.get("password")
            new_password = request.form.get("new_password")
            confirm_new_password = request.form.get("confirm_new_password")
            if not password or not new_password or not confirm_new_password:
                flash("Nie wypełniono wszystkich wymaganych pól!", "error")
                return render_template("profile.html")
            if not check_password_hash(current_user.password_hash, password):
                flash("Błędne aktualne hasło!", "error")
                return render_template("profile.html")
            if new_password != confirm_new_password:
                flash("Hasła nie były identyczne!", "error")
                return render_template("profile.html")
            if check_password_hash(current_user.password_hash, new_password):
                flash("Nowe hasło nie może być takie samo jak aktualne!", "error")
                return render_template("profile.html")  
            user = User.query.get(current_user.id)            
            user.password_hash = generate_password_hash(new_password)
            user.force_password_change = False
            db.session.commit()
            flash("Hasło zostało zmienione!", "success")
        elif mode == "personal":
            email = request.form.get("email")
            if email and email != current_user.email and is_valid_email(email):
                if User.query.filter_by(email=email).first():
                    flash("Konto o podanym adresie email już istnieje!", "error")
                    return render_template("profile.html")
                user = User.query.get(current_user.id)   
                user.email = email
                user.email_confirmed = False
                db.session.commit()
                send_button_message("Potwierdzenie adresu email w systemie ITOS", "Aby potwierdzić adres email w systemie ITOS, kliknij poniższy przycisk.", [current_user.email], "Potwierdź", url_for("auth.confirm_email", token=generate_token(current_user.email), _external=True))
                flash("Adres email zmieniony pomyślnie! Na nowy adres wysłaliśmy maila z linkiem pozwalającym na jego weryfikację.")
        else:
            flash("Nie mogliśmy rozpoznać formularza, który wypełniłeś. Jeśli problem się powtórzy, skontaktuj się z administratorem.", "error")
            return render_template("profile.html")
    return render_template("profile.html")

ALLOWED_EXTENSIONS = ["png", "jpg", "jpeg", "gif", "pdf", "txt"]

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

@bp.route("/upload", methods=["GET", "POST"])
@login_required
def upload():
    if request.method == "POST":
        name = request.form.get("name")
        file = request.files["file"]
        if not name or not file:
            flash("Nie wypełniono wszystkich wymaganych pól!", "error")
            return render_template("upload.html")
        if not allowed_file(file.filename):
            message = "Niedozwolony format pliku! (Akceptujemy "
            for i in range(len(ALLOWED_EXTENSIONS) - 1):
                message += ALLOWED_EXTENSIONS[i] + ", "
            message += ALLOWED_EXTENSIONS[-1] + ")"
            flash(message, "error")
            return render_template("upload.html")
        
        if File.query.filter_by(user_id=current_user.id, name=name).first():
            flash("Masz już plik o tej nazwie!", "error")
            return render_template("upload.html")
        
        secured_filename = secure_filename(name + "." + file.filename.rsplit(".", 1)[1].lower())
        filename = f"{uuid.uuid4().hex}_{secured_filename}"
        
        file.seek(0, os.SEEK_END)
        size = file.tell()
        file.seek(0) 
        
        if size > current_user.quota * 1024 * 1024- current_user.space_used:
            flash("Masz na koncie zbyt mało miejsca, aby wgrać ten plik!", "error")
            return render_template("upload.html")
        
        status = FileStatus.pending
        if current_user.reputation >= 60:
            status = FileStatus.visible
        
        new_file = File(name=name, filename=filename, user_id=current_user.id, mimetype=file.mimetype, size=size, status=status)
        db.session.add(new_file)
        
        db.session.commit()
        
        file_path = os.path.join(current_app.root_path, "uploads", filename)
        file.save(file_path)
        
        if status == FileStatus.visible:
            flash("Twój plik został zapisany.", "success")
        else:
            flash("Twój plik został wysłany do weryfikacji.", "success")
        return redirect(url_for("panel.files"))
    return render_template("upload.html")

@bp.route("/delete-file", methods=["POST"])
@login_required
def delete_file():
    fileid = request.form.get("id")
    if not fileid:
        return redirect(url_for("panel.files"))
    file = File.query.get(fileid)
    if not file:
        return redirect(url_for("panel.files"))
    db.session.delete(file)
    db.session.commit()
    flash("Plik został usunięty.", "success")
    return redirect(url_for("panel.files"))

@bp.route("/delete-post", methods=["POST"])
@login_required
def delete_post():
    postid = request.form.get("id")
    if not postid:
        return redirect(url_for("panel.news"))
    post = Post.query.get(postid)
    if not post:
        return redirect(url_for("panel.news"))
    db.session.delete(post)
    db.session.commit()
    flash("Ogłoszenie zostało usunięte.", "success")
    return redirect(url_for("panel.news"))

@bp.route("/edit-post", methods=["GET", "POST"])
@login_required
def edit_post():
    postid = request.args.get("id")
    if not postid:
        return redirect(url_for("panel.create"))
    try:
        postid = int(postid)
    except Exception:
        return redirect(url_for("panel.create"))
    post = Post.query.get(int(postid))
    if not post:
        return redirect(url_for("panel.create"))
    if request.method == "POST":
        title = request.form.get("title")
        content = request.form.get("content")
        if not title or not content:
            flash("Nie wypełniono wszystkich wymaganych pól!", "error")
            return redirect(url_for("panel.create"))
        status = PostStatus.pending
        if current_user.reputation >= 60 and post.status == PostStatus.visible:
            status = PostStatus.visible
        tags = [int(tid) for tid in request.form.get("tags", "").split(",") if tid.strip().isdigit()]
        assignable_tags = Tag.query.filter((Tag.is_restricted == False) | (Tag.allowed_users.any(id=current_user.id))).filter(Tag.id.in_(tags)).all()
        if(len(assignable_tags) > 5):
            flash("Możesz wybrać do 5 kategorii!", "error")
            return render_template("edit-post.html", post=post, assignable_tags=get_assignable_tags())
        fileids = [int(fid) for fid in request.form.get("files", "").split(",") if fid.strip().isdigit()]
        files = File.query.filter(File.user_id == current_user.id, File.id.in_(fileids)).all()
        post.tags = assignable_tags
        post.files = files
        post.title = title
        post.content = sanitize_html(content)
        post.status = status
        db.session.commit()
        if post.status == PostStatus.visible:
            flash("Twoje ogłoszenie zostało zmienione.", "success")
        else:
            flash("Twoje zmiany zostały wysłane do weryfikacji.", "success")
        return redirect(url_for("panel.news"))
    return render_template("edit-post.html", post=post, assignable_tags=get_assignable_tags())

@bp.before_request
def check_if_email_confirmed():
    if current_user.is_authenticated and not current_user.email_confirmed and request.endpoint != "panel.profile":
        return redirect(url_for("panel.profile"))
    elif current_user.is_authenticated and not current_user.email_confirmed and request.endpoint == "panel.profile":
        flash(f"""Potwierdź swój adres email, klikając link w wysłanej wiadomoścni, aby korzystać z portalu! <a href="{url_for("auth.resend_confirmation_email")}" class="font-normal text-brand-500 underline">Wyślij wiadomość ponownie</a>""", category="warning")
        
@bp.before_request
def check_reputation():
    if current_user.is_authenticated and current_user.reputation < 40 and request.endpoint != "panel.panel_home":
        return redirect(url_for("panel.panel_home"))
    elif current_user.is_authenticated and current_user.reputation < 40 and request.endpoint == "panel.panel_home":
        flash("Niestety, ze względu na zbyt niską reputację nie możesz korzystać z portalu.", category="warning")
        
@bp.before_request
def force_password_change():
    if current_user.is_authenticated:
        if current_user.force_password_change and current_user.reputation >= 40 and request.endpoint != "panel.profile":
            return redirect(url_for("panel.profile"))
    elif current_user.is_authenticated:
        if current_user.force_password_change and current_user.reputation >= 40 and request.endpoint == "panel.profile":
            flash("Ze względów bezpieczeństwa, musisz teraz zmienić swoje hasło.", category="warning")