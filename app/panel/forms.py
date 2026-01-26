from flask_wtf import FlaskForm
from wtforms import PasswordField, SubmitField, StringField, EmailField, HiddenField, TextAreaField
from wtforms.validators import DataRequired, EqualTo, Length, Email
from flask_wtf.file import FileField, FileRequired, FileAllowed
from flask_uploads import UploadSet, IMAGES, TEXT, DOCUMENTS

from app.validators import CurrentPassword, EmailNotRegistered, FitsQuota, FileNameNotInUse

class PasswordModalForm(FlaskForm):
    password = PasswordField("Aktualne hasło", validators=[DataRequired(message = "Pole wymagane"), CurrentPassword()])
    new_password = PasswordField("Nowe hasło", validators=[DataRequired(message = "Pole wymagane")])
    confirm_new_password = PasswordField("Powtórz nowe hasło", validators=[DataRequired(message = "Pole wymagane"), EqualTo("new_password", message="Podane hasła nie były identyczne")])
    submit_password = SubmitField("Zapisz zmiany")
    
class PersonalDataModalForm(FlaskForm):
    email = EmailField("Adres email", validators=[Email(message="Nieprawidłowy adres email"), EmailNotRegistered()])
    submit_personal = SubmitField("Zapisz zmiany")
    
class DeleteFileForm(FlaskForm):
    id = HiddenField(validators=[DataRequired()])
    submit = SubmitField()
    
class DeletePostForm(FlaskForm):
    id = HiddenField(validators=[DataRequired()])
    submit = SubmitField()
    
class CreatePostForm(FlaskForm):
    title = StringField("Tytuł", validators=[DataRequired(message= "Pole wymagane"), Length(max=120, message="Długość tytułu nie może przekraczać 120 znaków")])
    content = TextAreaField("Treść", validators=[DataRequired("Pole wymagane")])
    
    tags = HiddenField("Kategorie")
    files = HiddenField("Załączniki")
    
class FileUploadForm(FlaskForm):
    name = StringField("Nazwa (bez rozszerzenia)", validators=[DataRequired(message= "Pole wymagane"), Length(max=120, message="Długość nazwy nie może przekraczać 120 znaków"), FileNameNotInUse()])
    file = FileField("Plik", validators=[FileRequired(message="Wybierz plik"), FileAllowed(IMAGES + TEXT + DOCUMENTS, "Niedozwolony typ pliku"), FitsQuota()])