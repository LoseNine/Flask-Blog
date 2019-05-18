from . import db
from werkzeug.security import generate_password_hash,check_password_hash
from flask_login import UserMixin,AnonymousUserMixin
from . import login_manager
from itsdangerous import TimedJSONWebSignatureSerializer
from flask import current_app
from datetime import datetime
import hashlib
from flask import request
from markdown import markdown
import bleach

class Permission:
    FOLLOE=0X01
    COMMIT=0X02
    WRITE_ARTICLES=0X04
    MODERATE_COMMITS=0X08
    ADMINISTER=0X80

class Role(db.Model):
    __tablename__='roles'
    id=db.Column(db.Integer,autoincrement=True,primary_key=True)
    role=db.Column(db.String(64),nullable=False)
    users=db.relationship('User',backref='role')

    default=db.Column(db.Boolean,default=False,index=True)
    permissions=db.Column(db.Integer)

    def __str__(self):
        return str(self.role)

    #创建role
    @staticmethod
    def insert_roles():
        roles={
            'User':(Permission.FOLLOE|
                    Permission.COMMIT|
                    Permission.WRITE_ARTICLES,True),
            "Moderator":(Permission.FOLLOE|
                        Permission.COMMIT|
                         Permission.WRITE_ARTICLES|
                         Permission.MODERATE_COMMITS,False),
            "Administrator":(0XFF,False)
        }
        for r in roles:
            role=Role.query.filter_by(role=r).first()
            if role is None:
                role=Role(role=r)
            role.permissions=roles[r][0]
            role.default=roles[r][1]
            db.session.add(role)
        db.session.commit()

class Follow(db.Model):
    __tablename__='follows'
    follower_id=db.Column(db.Integer,db.ForeignKey('user.id'))
    followed_id=db.Column(db.Integer,db.ForeignKey('user.id'))
    timestamp=db.Column(db.DateTime(),default=datetime.now)

class User(UserMixin,db.Model):
    __tabelename__='users'
    id=db.Column(db.Integer,autoincrement=True,primary_key=True)
    email=db.Column(db.String(64),nullable=True,index=True)
    username=db.Column(db.String(64))
    password_hash=db.Column(db.String(128))
    role_id=db.Column(db.Integer,db.ForeignKey('roles.id'))
    confirmed=db.Column(db.Boolean,default=False)

    location=db.Column(db.String(64))
    about_me=db.Column(db.Text())
    member_since=db.Column(db.DateTime(),default=datetime.utcnow)
    last_seen=db.Column(db.DateTime(),default=datetime.utcnow)

    avatar_hash=db.Column(db.String(256))

    posts=db.relationship('Post',backref='author',lazy='dynamic')

    followed=db.relationship('Follow',foreign_keys=[Follow.follower_id],
                             backref=db.backref('follower',lazy='joined'),
                             lazy='dynamic',
                             cascade='all,delete-orphan')
    followers=db.relationship('Follow',foreign_keys=[Follow.follower_id],
                             backref=db.backref('follower',lazy='joined'),
                             lazy='dynamic',
                             cascade='all,delete-orphan')

    def __str__(self):
        return str(self.username)

    def __init__(self,**kwargs):
        super(User, self).__init__(**kwargs)

        if self.email is not None and self.avatar_hash is None:
            self.avatar_hash=hashlib.md5(self.email.encode('utf-8')).hexdigest()

        if self.role is None:
            if self.email==current_app.config['MAIL_DEFAULT_SENDER']:
                self.role=Role.query.filter_by(permissions=0XFF).first()
            if self.role is None:
                self.role=Role.query.filter_by(default=True).first()

    def follow(self,user):
        if not self.is_following(user):
            f=Follow(follower=self,followed=user)
            db.session.add(f)

    def is_following(self,user):
        return self.followed.filter_by(followed_id=user.id).first() is not None

    def unfollow(self,user):
        f=self.followed.filter_by(followed_id=user.id).first()
        if f:
            db.session.delete(f)

    def is_followed_by(self,user):
        return self.followers.filter_by(
            follower_id=user.id
        ).first() is not None

    def ping(self):
        self.last_seen=datetime.utcnow()
        db.session.add(self)

    @property
    def password(self):
        raise AttributeError("password is not a readable column,Do u mean password_hash?")

    @password.setter
    def password(self,password):
        self.password_hash=generate_password_hash(password)

    def verify_password(self,password):
        return check_password_hash(self.password_hash,password)
    
    def add_user(self,email,username,password):
        user=User(email=email,username=username,password=password,role_id=1)
        db.session.add(user)
        db.session.commit()

    def generate_confirmation_token(self,expire=3600):
        s=TimedJSONWebSignatureSerializer(current_app.config['SECRET_KEY'],expires_in=expire)
        return s.dumps({'confirm':self.id})

    def confirm(self,token):
        s=TimedJSONWebSignatureSerializer(current_app.config['SECRET_KEY'])
        try:
            data=s.loads(token)
        except:
            return False
        if data.get('confirm')!=self.id:
            print('not ciformed')
            return False

        self.confirmed=True
        db.session.add(self)
        db.session.commit()
        return True

    def can(self,permission):
        #如果用户有了权限，而且权限
        return self.role is not None and (self.role.permissions & permission)==permission

    def is_administrator(self):
        return self.can(Permission.ADMINISTER)
    
    def gravatar(self,size=100,default='identicon',rating='g'):
        if request.is_secure:
            url='https://secure.gravator.com/avator'
        else:
            url='http://www.gravator.com/avator'
        hash=hashlib.md5(self.email.encode('utf-8')).hexdigest()
        return '{url}/{hash}?s={size}&d={default}&r={rating}'.format(
            url=url,
            hash=hash,
            size=size,
            default=default,
            rating=rating
        )

class Post(db.Model):
    __tablename__='posts'
    id=db.Column(db.Integer,primary_key=True,autoincrement=True)
    body=db.Column(db.Text())
    timestamp=db.Column(db.DateTime(),index=True,default=datetime.utcnow)
    author_id=db.Column(db.Integer,db.ForeignKey('user.id'))

    body_html=db.Column(db.Text())

    @staticmethod
    def on_changed_body(target,value,oldvalue,initiator):
        allowed_tags=['a','abbr','acronym','b','blockquote','code',
                      'em','i','li','ol','pre','strong','ul',
                      'h1','h2','h3','p']
        target.body_html=bleach.linkify(bleach.clean(
            markdown(value,output_format='html'),
            tags=allowed_tags,strip=True
        ))
        
class AnonymousUser(AnonymousUserMixin):

    def can(self,permissions):
        return False

    def is_administrator(self):
        return False



@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))



login_manager.anonymous_user=AnonymousUser
db.event.listen(Post.body,'set',Post.on_changed_body)