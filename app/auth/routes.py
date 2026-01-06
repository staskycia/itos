from flask import render_template, request, flash, redirect, url_for, current_app
from flask_login import login_user, current_user, logout_user, login_required
from werkzeug.security import check_password_hash, generate_password_hash
from itsdangerous import URLSafeTimedSerializer
from app.extensions import db
from app.mail import send_button_message

from app.models import User, Person

from app.auth import bp

@bp.route("/signin", methods=["GET", "POST"])
def signin():
    if current_user.is_authenticated:
        return redirect(url_for("panel.panel_home"))
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        if not email or not password:
            flash("Wypełnij wszystkie wymagane pola!", category="error")
            return render_template("signin.html")
        user = User.query.filter_by(email=email).first()
        if not user or not check_password_hash(user.password_hash, password):
            flash("Niepoprawy email i/lub hasło!", category="error")
        else:
            login_user(user)
            return redirect(url_for("panel.panel_home"))
            
    return render_template("signin.html")

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

from email_validator import validate_email, EmailNotValidError

def is_valid_email(value: str) -> bool:
    try:
        validate_email(value)
        return True
    except EmailNotValidError:
        return False

    

@bp.route("/signup", methods=["GET", "POST"])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for("panel.panel_home"))
    if request.method == "POST":
        mode = request.form.get("mode")
        if mode == "start":
            login = request.form.get("login")
            if not login:
                flash("Pole login jest wymagane!", "error")
                return render_template("signup.html")
            person = Person.query.filter_by(login=login).first()
            if not person:
                flash("Nie znaleziono w systemie szkolnym konta o podanym loginie!", "error")
                return render_template("signup.html")
            user = User.query.filter_by(person_id=person.id).first()
            if user:
                flash("Z tym kontem szkolnym jest już powiązane konto!", "error")
                return redirect(url_for("auth.signin"))
            send_button_message("Rejestracja w systemie ITOS", "Aby kontunuować rejestrację w systemie ITOS, kliknij w poniższy link i potwierdź swoją tożsamość.", [login+"@staszic.waw.pl"], "Potwierdź", url_for("auth.confirm_signup", token=generate_token(login), _external=True))
            return render_template("confirmation-mail-sent.html", login=login)
        elif mode == "confirm":
            email = request.form.get("email")
            password = request.form.get("password")
            confirm_password = request.form.get("confirm_password")
            token = request.form.get("token")
            if not email or not password or not confirm_password or not token:
                flash("Wypełnij wszystkie wymagane pola!", "error")
                if token:
                    return redirect(url_for("auth.confirm_signup", token=token))
                else:
                    return redirect(url_for("auth.signup"))
            if password != confirm_password:
                flash("Podane hasła nie były identyczne!", "error")
                return redirect(url_for("auth.confirm_signup", token=token))
            if User.query.filter_by(email=email).first():
                flash("Konto o podanym adresie email już istnieje!", "error")
                return redirect(url_for("auth.confirm_signup", token=token))
            if not is_valid_email(email):
                flash("Wprowadź poprawny adres email!", "error")
                return redirect(url_for("auth.confirm_signup", token=token))
            login = confirm_token(token)
            person = Person.query.filter_by(login=login).first()
            email_confirmed = False
            if(email == login+"@staszic.waw.pl"):
                email_confirmed = True
            else:
                send_button_message("Potwierdzenie adresu email w systemie ITOS", "Aby potwierdzić adres email w systemie ITOS, kliknij poniższy przycisk.", [current_user.email], "Potwierdź", url_for("auth.confirm_email", token=generate_token(current_user.email), _external=True))
            user = User(first_name=person.first_name, last_name=person.last_name, email=email, ldap_group=person.ldap_group, person=person, password_hash=generate_password_hash(password), email_confirmed=email_confirmed)
            db.session.add(user)
            db.session.commit()
            flash("Rejestracja przebiegła pomyślnie!", "success")
            return redirect(url_for("auth.signin"))
            

        else:
            flash("Nie mogliśmy rozpoznać formularza, który wypełniłeś. Jeśli problem się powtórzy, skontaktuj się z administratorem.", "error")
    return render_template("signup.html")

@bp.route("/signup/<token>")
def confirm_signup(token):
    if current_user.is_authenticated:
        return redirect(url_for("panel.panel_home"))
    login = confirm_token(token)
    if not login:
        flash("Twój link wygasł lub jest niewżany!", "error")
        return redirect(url_for("auth.signup"))
    if User.query.filter_by(person_id=Person.query.filter_by(login=login).first().id).first():
        flash("Z tym kontem szkolnym jest już powiązane konto!", "error")
        return redirect(url_for("auth.signin"))
    person = Person.query.filter_by(login=login).first()
    return render_template("confirm-signup.html", person=person, token=token)
    

@bp.route("/confirm-email/<token>")
def confirm_email(token):
    email = confirm_token(token)
    if not email:
        flash("Twój link wygasł lub jest niewżany!", "error")
        return redirect(url_for("auth.signup"))
    user = User.query.filter_by(email=email).first()
    if not user:
        flash("Twój link wygasł lub jest niewżany!", "error")
        return redirect(url_for("auth.signup"))
    if user.email_confirmed:
        flash("Adres email był już potwierdzony.", "success")
        return redirect(url_for("panel.panel_home"))
    user.email_confirmed = True
    db.session.commit()
    flash("Adres email został potwierdzony!", "success")
    return redirect(url_for("panel.panel_home"))

@bp.route("/resend-confirmation-email")
@login_required
def resend_confirmation_email():
    if not current_user.email_confirmed:
        send_button_message("Potwierdzenie adresu email w systemie ITOS", "Aby potwierdzić adres email w systemie ITOS, kliknij poniższy przycisk.", [current_user.email], "Potwierdź", url_for("auth.confirm_email", token=generate_token(current_user.email), _external=True))
        flash("Wiadomość została wysłana ponownie!", "success")
    return redirect(url_for("panel.panel_home"))

@bp.route("/reset-password", methods=["GET", "POST"])
def request_password_reset():
    if current_user.is_authenticated:
        return redirect(url_for("panel.panel_home"))
    
    if request.method == "POST":
        email = request.form.get("email") 
    
        if not email or not is_valid_email(email):
            flash("Wpisz prawidłowy adres email!", "error")
            return render_template("request-password-reset.html")

        user = User.query.filter_by(email=email).first()
        
        if user:
            send_button_message("Zmiana hasła w systemie ITOS", "Aby zmienić hasło do konta w systemie ITOS, kliknij poniższy przycisk.", [email], "Zmień hasło", url_for("auth.reset_password", token=generate_token(email), _external=True))
    
        flash("Jeśli konto o takim adresie email istnieje, wiadomość została wysłana.", "success")
        
    return render_template("request-password-reset.html")

@bp.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for("panel.panel_home"))
    
    email = confirm_token(token)
    
    if not email:
        flash("Twój link wygasł lub jest niewżany!", "error")
        return redirect(url_for("auth.signin"))    
    
    user = User.query.filter_by(email=email).first()
    if not user:
        flash("Twój link wygasł lub jest niewżany!", "error")
        return redirect(url_for("auth.request_password_reset"))
    
    if request.method == "POST":
        password = request.form.get("password")
        confirmpassword = request.form.get("confirmpassword")
        
        
        if not password or not confirmpassword:
            flash("Wypełnij wszystkie wymagane pola!", category="error")
            return render_template("reset-password.html", token=token)
            
        if password != confirmpassword:
            flash("Podane hasła nie były identyczne!", "error")
            return render_template("reset-password.html", token=token)
            
        user.password_hash = generate_password_hash(password)
        db.session.commit()
        
        flash("Twoje hasło zostało zmienione. Możesz się teraz zalogować.", "success")
        return redirect(url_for("auth.signin"))
    
    return render_template("reset-password.html", token=token)

@bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Wylogowano pomyślnie!", category="success")
    return redirect(url_for("auth.signin"))