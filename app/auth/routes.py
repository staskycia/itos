from flask import current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user
from itsdangerous import URLSafeTimedSerializer
from werkzeug.security import check_password_hash, generate_password_hash

from app.auth import bp
from app.extensions import db
from app.mail import send_button_message
from app.models import Person, Setting, User

from .forms import LoginForm

@bp.route("/signin", methods=["GET", "POST"])
def signin():
    if current_user.is_authenticated:
        return redirect(url_for("panel.panel_home"))
    
    login_form = LoginForm()
    
    if login_form.validate_on_submit():
        user = User.query.filter_by(email=login_form.email.data).first()
        if not user or not check_password_hash(user.password_hash, login_form.password.data):
            flash("Niepoprawy email i/lub hasło!", category="error")
        else:
            #log_action("LOGGED IN")
            login_user(user)
            return redirect(url_for("panel.panel_home"))

    return render_template("signin.html", form=login_form)


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


from email_validator import EmailNotValidError, validate_email


def is_valid_email(value: str) -> bool:
    try:
        validate_email(value)
        return True
    except EmailNotValidError:
        return False

from .forms import StartSignupForm, ConfirmSignupForm

@bp.route("/signup", methods=["GET", "POST"])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for("panel.panel_home"))
    if Setting.get("registration_disabled") == True:
        flash("Możliwość rejestracji została wyłączona przez administratora!", "error")
        return redirect(url_for("main.home"))
    
    start_signup_form = StartSignupForm()
    
    if start_signup_form.validate_on_submit():
        login = start_signup_form.login.data
        send_button_message(
            "Rejestracja w systemie ITOS",
            "Aby kontunuować rejestrację w systemie ITOS, kliknij w poniższy link i potwierdź swoją tożsamość.",
            [login + "@staszic.waw.pl"],
            "Potwierdź",
            url_for(
                "auth.confirm_signup", token=generate_token(login), _external=True
            ),
        )
        #log_action(f"STARTED SIGNUP AS {login}")
        return render_template("confirmation-mail-sent.html", login=login)
    return render_template("signup.html", form=start_signup_form)


@bp.route("/signup/<token>", methods=["GET", "POST"])
def confirm_signup(token):
    if current_user.is_authenticated:
        return redirect(url_for("panel.panel_home"))

    login = confirm_token(token)
    if not login:
        flash("Twój link wygasł lub jest nieprawidłowy!", "error")
        return redirect(url_for("auth.signup"))
    if User.query.filter_by(
        person_id=Person.query.filter_by(login=login).first().id
    ).first():
        flash("Z tym kontem szkolnym jest już powiązane konto!", "error")
        return redirect(url_for("auth.signin"))
    person = Person.query.filter_by(login=login).first()
    
    form = ConfirmSignupForm()
    
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        email_confirmed = False
        if email == login + "@staszic.waw.pl":
            email_confirmed = True
        else:
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
        user = User(
            first_name=person.first_name,
            last_name=person.last_name,
            email=email,
            ldap_group=person.ldap_group,
            person=person,
            password_hash=generate_password_hash(password),
            email_confirmed=email_confirmed,
        )
        db.session.add(user)
        db.session.commit()
        flash("Rejestracja przebiegła pomyślnie!", "success")
        #log_action(f"FINISHED SIGNUP AS {login}")
        return redirect(url_for("auth.signin"))
    
    return render_template("confirm-signup.html", person=person, token=token, form=form)


@bp.route("/confirm-email/<token>")
def confirm_email(token):
    email = confirm_token(token)
    if not email:
        flash("Twój link wygasł lub jest nieprawidłowy!", "error")
        return redirect(url_for("auth.signup"))
    user = User.query.filter_by(email=email).first()
    if not user:
        flash("Twój link wygasł lub jest nieprawidłowy!", "error")
        return redirect(url_for("auth.signup"))
    if user.email_confirmed:
        flash("Adres email był już potwierdzony.", "success")
        return redirect(url_for("panel.panel_home"))
    user.email_confirmed = True
    db.session.commit()
    flash("Adres email został potwierdzony!", "success")
    #log_action("CONFIRMED EMAIL")
    return redirect(url_for("panel.panel_home"))


@bp.route("/resend-confirmation-email")
@login_required
def resend_confirmation_email():
    if not current_user.email_confirmed:
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
        flash("Wiadomość została wysłana ponownie!", "success")
    return redirect(url_for("panel.panel_home"))

from .forms import RequestPasswordResetForm

@bp.route("/reset-password", methods=["GET", "POST"])
def request_password_reset():
    if current_user.is_authenticated:
        return redirect(url_for("panel.panel_home"))

    form = RequestPasswordResetForm()

    if form.validate_on_submit():
        email = form.email.data

        send_button_message(
            "Zmiana hasła w systemie ITOS",
            "Aby zmienić hasło do konta w systemie ITOS, kliknij poniższy przycisk.",
            [email],
            "Zmień hasło",
            url_for(
                "auth.reset_password", token=generate_token(email), _external=True
            ),
        )

        flash(
            "Wiadomość została wysłana.",
            "success",
        )
        #log_action(f"REQUESTED PASSWORD RESET FOR {email}")

    return render_template("request-password-reset.html", form=form)

from .forms import ResetPasswordForm

@bp.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for("panel.panel_home"))

    email = confirm_token(token)

    if not email:
        flash("Twój link wygasł lub jest nieprawidłowy!", "error")
        return redirect(url_for("auth.signin"))

    user = User.query.filter_by(email=email).first()
    if not user:
        flash("Twój link wygasł lub jest nieprawidłowy!", "error")
        return redirect(url_for("auth.request_password_reset"))

    form = ResetPasswordForm()

    if form.validate_on_submit():
        password = form.password.data
        confirm_password = form.confirm_password.data

        user.password_hash = generate_password_hash(password)
        db.session.commit()

        flash("Twoje hasło zostało zmienione. Możesz się teraz zalogować.", "success")
        #log_action(f"SUCCESFULLY RESETED PASSWORD FOR {email}")
        return redirect(url_for("auth.signin"))

    return render_template("reset-password.html", token=token, form=form)


@bp.route("/logout")
@login_required
def logout():
    #log_action(f"LOGGED OUT")
    logout_user()
    flash("Wylogowano pomyślnie!", category="success")
    return redirect(url_for("auth.signin"))
