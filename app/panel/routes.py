import os
import uuid
from email.utils import parseaddr

import bleach
from flask import current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from itsdangerous import URLSafeTimedSerializer
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

from app.extensions import db
from app.mail import send_button_message
from app.models import File, FileStatus, Post, PostStatus, Tag, User
from app.panel import bp


def get_assignable_tags():
    return (
        Tag.query.filter(
            (Tag.is_restricted == False) | (Tag.allowed_users.any(id=current_user.id))
        )
        .order_by(Tag.name)
        .all()
    )


@bp.route("/")
@login_required
def panel_home():
    space_used = round(current_user.space_used / (1024 * 1024), 2)
    percents = 100 * round(space_used / current_user.quota, 2)
    return render_template("index.html", space_used=space_used, percents=percents)


def sanitize_html(text):
    return bleach.clean(
        text,
        tags=["a"],
        attributes={"a": ["href"]},
        protocols=["http", "https"],
        strip=True,
    )

from .forms import CreatePostForm

@bp.route("/create", methods=["GET", "POST"])
@login_required
def create():
    form = CreatePostForm()
    if form.validate_on_submit():
        title = form.title.data
        content = form.content.data
        status = PostStatus.pending
        # if current_user.reputation >= 60:
        #     status = PostStatus.visible
        tags = [
            int(tid)
            for tid in request.form.get("tags", "").split(",")
            if tid.strip().isdigit()
        ]
        assignable_tags = (
            Tag.query.filter(
                (Tag.is_restricted == False)
                | (Tag.allowed_users.any(id=current_user.id))
            )
            .filter(Tag.id.in_(tags))
            .all()
        )
        if len(assignable_tags) > 5:
            flash("Możesz wybrać do 5 kategorii!", "error")
            return render_template("create.html", assignable_tags=get_assignable_tags(), form=form)
        fileids = [
            int(fid)
            for fid in request.form.get("files", "").split(",")
            if fid.strip().isdigit()
        ]
        files = File.query.filter(
            File.user_id == current_user.id, File.id.in_(fileids)
        ).all()
        post = Post(
            title=title,
            content=sanitize_html(content),
            author=current_user,
            status=status,
            tags=assignable_tags,
            files=files,
        )
        db.session.add(post)
        db.session.commit()
        if status == PostStatus.visible:
            flash("Twoje ogłoszenie zostało opublikowane!", "success")
        else:
            flash("Twoje ogłoszenie zostało wysłane do weryfikacji!", "success")
        #log_action(f"CREATED POST {post.id}")
        return redirect(url_for("panel.news"))
    flash("W trakcie kampanii wyborczej, wszystkie publikowane ogłoszenia wymagają zatwierdzenia.", "warning")
    return render_template("create.html", assignable_tags=get_assignable_tags(), form=form)


from .forms import DeleteFileForm

@bp.route("/files")
@login_required
def files():
    form = DeleteFileForm()
    return render_template("files.html", form=form)


from .forms import DeletePostForm

@bp.route("/posts")
@login_required
def news():
    form = DeletePostForm()
    return render_template("news.html", form=form)


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

from .forms import PasswordModalForm, PersonalDataModalForm

@bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    password_form = PasswordModalForm()
    personal_data_form = PersonalDataModalForm()
    
    if password_form.submit_password.data:
        if password_form.validate_on_submit():
            user = User.query.get(current_user.id)
            user.password_hash = generate_password_hash(password_form.new_password.data)
            user.force_password_change = False
            db.session.commit()
            flash("Hasło zostało zmienione!", "success")
            #log_action(f"CHANGED PASSWORD")
    if personal_data_form.submit_personal.data:
        if personal_data_form.validate_on_submit():
            user = User.query.get(current_user.id)
            user.email = personal_data_form.email.data
            user.email_confirmed = False
            db.session.commit()
            send_button_message(
                "Potwierdzenie adresu email w systemie ITOS",
                "Aby potwierdzić adres email w systemie ITOS, kliknij poniższy przycisk.",
                [current_user.email],
                "Potwierdź",
                url_for(
                    "auth.confirm_email",
                    token=generate_token(current_user.email),
                    _external=True,
                ),
            )
            flash(
                "Adres email zmieniony pomyślnie! Na nowy adres wysłaliśmy maila z linkiem pozwalającym na jego weryfikację.", "success"
            )
            #log_action(f"CHANGED PERSONAL DATA")
    return render_template("profile.html", password_form=password_form, personal_data_form=personal_data_form)


ALLOWED_EXTENSIONS = ["png", "jpg", "jpeg", "gif", "pdf", "txt"]


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

from .forms import FileUploadForm

@bp.route("/upload", methods=["GET", "POST"])
@login_required
def upload():
    form = FileUploadForm()
    
    if form.validate_on_submit():
        name = form.name.data
        file = request.files["file"]

        secured_filename = secure_filename(
            name + "." + file.filename.rsplit(".", 1)[1].lower()
        )
        filename = f"{uuid.uuid4().hex}_{secured_filename}"

        file.seek(0, os.SEEK_END)
        size = file.tell()
        file.seek(0)
        
        status = FileStatus.pending
        # if current_user.reputation >= 60:
        #     status = FileStatus.visible

        new_file = File(
            name=name,
            filename=filename,
            user_id=current_user.id,
            mimetype=file.mimetype,
            size=size,
            status=status,
        )
        db.session.add(new_file)

        db.session.commit()

        file_path = os.path.join(current_app.root_path, "uploads", filename)
        file.save(file_path)

        if status == FileStatus.visible:
            flash("Twój plik został zapisany.", "success")
        else:
            flash("Twój plik został wysłany do weryfikacji.", "success")
        #log_action(f"UPLOADED FILE {file.id}")
        return redirect(url_for("panel.files"))
    flash("W trakcie kampanii wyborczej, wszystkie publikowane pliki wymagają zatwierdzenia.", "warning")
    return render_template("upload.html", form=form)


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
    #log_action(f"DELETED FILE {file.id}")
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
    #log_action(f"DELETED POST {post.id}")
    return redirect(url_for("panel.news"))


@bp.route("/edit-post", methods=["GET", "POST"])
@login_required
def edit_post():
    form = CreatePostForm()
    
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
    if form.validate_on_submit():
        title = form.title.data
        content = form.content.data
        status = PostStatus.pending
        # if current_user.reputation >= 60 and post.status == PostStatus.visible:
        #     status = PostStatus.visible
        tags = [
            int(tid)
            for tid in request.form.get("tags", "").split(",")
            if tid.strip().isdigit()
        ]
        assignable_tags = (
            Tag.query.filter(
                (Tag.is_restricted == False)
                | (Tag.allowed_users.any(id=current_user.id))
            )
            .filter(Tag.id.in_(tags))
            .all()
        )
        if len(assignable_tags) > 5:
            flash("Możesz wybrać do 5 kategorii!", "error")
            return render_template(
                "edit-post.html", post=post, assignable_tags=get_assignable_tags(), form=form
            )
        fileids = [
            int(fid)
            for fid in request.form.get("files", "").split(",")
            if fid.strip().isdigit()
        ]
        files = File.query.filter(
            File.user_id == current_user.id, File.id.in_(fileids)
        ).all()
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
        #log_action(f"EDITED POST {post.id}")
        return redirect(url_for("panel.news"))
    flash("W trakcie kampanii wyborczej, wszystkie publikowane zmiany wymagają zatwierdzenia.", "warning")
    return render_template(
        "edit-post.html", post=post, assignable_tags=get_assignable_tags(), form=form
    )


@bp.before_request
def check_if_email_confirmed():
    if (
        current_user.is_authenticated
        and not current_user.email_confirmed
        and request.endpoint != "panel.profile"
    ):
        return redirect(url_for("panel.profile"))
    elif (
        current_user.is_authenticated
        and not current_user.email_confirmed
        and request.endpoint == "panel.profile"
    ):
        flash(
            f"""Potwierdź swój adres email, klikając link w wysłanej wiadomoścni, aby korzystać z portalu! <a href="{url_for("auth.resend_confirmation_email")}" class="font-normal text-brand-500 underline">Wyślij wiadomość ponownie</a>""",
            category="warning",
        )


@bp.before_request
def check_reputation():
    if (
        current_user.is_authenticated
        and current_user.reputation < 40
        and request.endpoint != "panel.panel_home"
    ):
        return redirect(url_for("panel.panel_home"))
    elif (
        current_user.is_authenticated
        and current_user.reputation < 40
        and request.endpoint == "panel.panel_home"
    ):
        flash(
            "Niestety, ze względu na zbyt niską reputację nie możesz korzystać z portalu.",
            category="warning",
        )


@bp.before_request
def force_password_change():
    if current_user.is_authenticated:
        if (
            current_user.force_password_change
            and current_user.reputation >= 40
            and request.endpoint != "panel.profile"
        ):
            return redirect(url_for("panel.profile"))
    if current_user.is_authenticated:
        if (
            current_user.force_password_change
            and current_user.reputation >= 40
            and request.endpoint == "panel.profile"
        ):
            flash(
                "Ze względów bezpieczeństwa, musisz teraz zmienić swoje hasło.",
                category="warning",
            )
