from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, SubmitField
from wtforms.validators import DataRequired, Email

class AuthForm(FlaskForm):
    username = StringField(label='Email', validators=[DataRequired(), Email()])
    password = PasswordField(label='Password', validators=[DataRequired()])
    submit = SubmitField(label="Log In")

class RowsPerPage(FlaskForm):
    rows_per_page = SelectField(u'Rows Per Page', choices=[(10, '10'), (25, '25'), (50, '50')], coerce=int)
    submit = SubmitField(label="Update")

class Query(FlaskForm):
    query = StringField()
