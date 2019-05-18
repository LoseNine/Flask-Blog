from flask_wtf import FlaskForm
from wtforms import StringField,SubmitField,TextAreaField,BooleanField,SelectField
from wtforms.validators import Length,email
from ..models import Role,User,Post
from wtforms import ValidationError
from flask_pagedown.fields import PageDownField

class EditProfileForm(FlaskForm):
    username=StringField(label="姓名",validators=[Length(0,10)])
    location=StringField(label='住址',validators=[Length(0,64)])
    about_me=TextAreaField(label='关于我')
    submit=SubmitField('保存修改')

class EditProfileAdminForm(FlaskForm):
    email=StringField(label='邮箱',validators=[email()])
    username=StringField(label="姓名",validators=[Length(0,10)])
    location=StringField(label='住址',validators=[Length(0,64)])
    about_me=TextAreaField(label='关于我')
    confirmed=BooleanField('Confirmed')
    role=SelectField('Role',coerce=int)
    submit = SubmitField('保存修改')
    
    def __init__(self,user):
        super(EditProfileAdminForm, self).__init__()
        self.role.choices=[(role.id,role.role)
                           for role in Role.query.order_by(Role.role).all()]
        self.user=user
    
    def validate_email(self,email):
        if email.data!=self.user.email and User.query.filter_by(email=email.data).first():
            raise ValidationError('Email already registered')
    
    def validate_username(self,username):
        if username.data!=self.user.username and User.query.filter_by(username=username.data).first():
            raise ValidationError('Username already in use')

class PostForm(FlaskForm):
    body=PageDownField('What is on your mind?')
    submit=SubmitField('submit')

class CommentForm(FlaskForm):
    body=StringField('What is on your mind?')
    submit=SubmitField('submit')