from flask_wtf import Form
from flask_wtf.file import FileField
from wtforms import StringField, BooleanField
from wtforms.validators import DataRequired, Length

class EmoteUploadForm(Form):
    emote = FileField('Emote', validators=[DataRequired()])
    name  = StringField('Name', validators=[DataRequired(), Length(min=3, max=32)])
    shared = BooleanField('Enable sharing')

