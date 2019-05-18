from flask_wtf import FlaskForm
from wtforms import StringField,PasswordField,BooleanField,SubmitField
from wtforms.validators import EqualTo,Email
from ..models import User
from wtforms import ValidationError

class LoginForm(FlaskForm):
    email=StringField(label='邮箱',validators=[Email()])
    password=PasswordField(label='密码')
    remember_me=BooleanField('保持登录')
    submit=SubmitField('Login in')

class RegisterForm(FlaskForm):
    email=StringField(label='邮箱',validators=[Email()])
    username=StringField(label='账号名')
    password=PasswordField(label='密码',validators=[EqualTo('password2')])
    password2 = PasswordField(label='密码')
    submit = SubmitField('注册')

    def validate_email(self,email):
        print("validate email")
        if User.query.filter_by(email=email.data).first():
            raise ValidationError('email has been register')

    def validate_username(self,username):
        print("validate username")
        if User.query.filter_by(username=username.data).first():
            raise ValidationError('username has been register')