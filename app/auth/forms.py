from flask_wtf import FlaskForm
from wtforms import EmailField, PasswordField, SubmitField, StringField, HiddenField
from wtforms.validators import Email, DataRequired, EqualTo

from app.validators import PersonExists, PersonNotRegistered, EmailNotRegistered, EmailRegistered

class LoginForm(FlaskForm):
    email = EmailField("Email", validators=[DataRequired(message="Pole wymagane"), Email(message="Wprowadź prawidłowy adres email")])
    password = PasswordField("Hasło", validators=[DataRequired(message="Pole wymagane")])
    submit = SubmitField("Zaloguj")
    
class StartSignupForm(FlaskForm):
    login = StringField("Login", validators=[DataRequired(message="Pole wymagane"), PersonExists(), PersonNotRegistered()])
    submit = SubmitField("Dalej")
    
class ConfirmSignupForm(FlaskForm):
    email = EmailField("Email", validators=[DataRequired(message="Pole wymagane"), Email(message="Wprowadź prawidłowy adres email"), EmailNotRegistered()])
    password = PasswordField("Nowe hasło", validators=[DataRequired(message = "Pole wymagane")])
    confirm_password = PasswordField("Powtórz nowe hasło", validators=[DataRequired(message = "Pole wymagane"), EqualTo("password", message="Podane hasła nie były identyczne")])
    submit = SubmitField("Potwierdź")
    
class RequestPasswordResetForm(FlaskForm):
    email = EmailField("Email", validators=[DataRequired(message="Pole wymagane"), Email(message="Wprowadź prawidłowy adres email"), EmailRegistered()])
    submit = SubmitField("Wyślij wiadomość")
    
class ResetPasswordForm(FlaskForm):
    password = PasswordField("Nowe hasło", validators=[DataRequired(message = "Pole wymagane")])
    confirm_password = PasswordField("Powtórz nowe hasło", validators=[DataRequired(message = "Pole wymagane"), EqualTo("password", message="Podane hasła nie były identyczne")])
    submit = SubmitField("Potwierdź zmianę")