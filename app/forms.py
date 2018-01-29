from flask_wtf import Form
from wtforms import TextField, BooleanField, PasswordField, SubmitField, TextAreaField
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


class AboutMeForm(Form):
    describe = TextAreaField('about me', validators=[
        Required(), Length(max=140)
    ])
    submit = SubmitField('YES')


class PublishBlogForm(Form):
    body = TextAreaField('blog content', validators=[Required()])
    submit = SubmitField('Submit')

