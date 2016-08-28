from flask_wtf import Form
from flask_wtf.file import FileField
from wtforms import StringField, BooleanField
from wtforms.validators import DataRequired, Length, Regexp, ValidationError

from .models import Emote, db

def no_consecutive_underscores(form, field):
    if '__' in field.data:
        raise ValidationError("Emote name must not have consecutive underscores.")

def unique_emote_name(form, field):
    if db.session.query(db.exists().where(Emote.name == form.name.data)).scalar():
        raise ValidationError('An emote already exists with this name.')

class EmoteUploadForm(Form):
    emote  = FileField('Emote', validators=[DataRequired()])
    name   = StringField('Name', validators=[DataRequired(),
                                             Length(min=3, max=20),
                                             Regexp(r'^([a-zA-Z0-9][a-zA-Z0-9_]{2,19})$',
                                                    message="Emote name must be alphanumeric with underscores and must "
                                                            "not start with an underscore."),
                                             no_consecutive_underscores,
                                             unique_emote_name])
    shared = BooleanField('Enable sharing')

