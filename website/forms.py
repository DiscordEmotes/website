from flask_wtf import Form
from flask_wtf.file import FileField
from wtforms import StringField, BooleanField
from wtforms.validators import DataRequired, Length, Regexp, ValidationError

def no_consecutive_underscores(form, field):
    if '__' in field.data:
        raise ValidationError("Emote name must not have consecutive underscores.")

class EmoteUploadForm(Form):
    emote  = FileField('Emote', validators=[DataRequired()])
    name   = StringField('Name', validators=[DataRequired(),
                                             Regexp(r'^([a-zA-Z0-9][a-zA-Z0-9_]{2,31})$',
                                                    message="Emote name must be alphanumeric with underscores and must "
                                                            "not start with an underscore."),
                                             no_consecutive_underscores])
    shared = BooleanField('Enable sharing')

