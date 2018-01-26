from flask_wtf import Form
from wtforms import TextField, BooleanField, PasswordField, SubmitField
from wtforms.validators import Required, Length, Email


class LoginForm(Form):
    user_name =TextField('user name', validators=[
        Required(), Length(max=15)])
    # password = PasswordField('password', validators=[Required()])
    remember_me = BooleanField('Remember_me', default=False)
    submit = SubmitField("Login")


class SignUpForm(Form):
    user_name = TextField("user name", validators=[
        Required(), Length(max=15)
    ])
    user_email = TextField("user email", validators=[
        Email(), Required(), Length(max=128)
    ])
    submit = SubmitField("Sign up")


