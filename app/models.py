#-*- coding:utf-8 -*-
from flask_login import UserMixin
from flask_login._compat import unicode
from hashlib import md5

from app import db

ROLE_USER = 0
ROLE_ADMIN = 1


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    nickname = db.Column(db.String(64), unique=True)
    email = db.Column(db.String(120), unique=True)
    role = db.Column(db.SmallInteger, default=ROLE_USER)
    posts = db.relationship('Post', backref='author', lazy='dynamic')
    last_seen = db.Column(db.String(120), unique=True)
    about_me = db.Column(db.String(140))

    # def is_authenticated(self):
    #     return True  # 除非表示用户的对象因为某些原因不允许被认证。
    #
    # def is_active(self):
    #     return False  # 除非是用户是无效的，比如因为他们的账号是被禁止。
    #
    # def is_anonymous(self):
    #     return False  # 如果是匿名的用户不允许登录系统。

    # def get_id(self):
    #     try:
    #         return unicode(self.id)
    #     except NameError:
    #         return str(self.id)

    # cls为类，self为类的实例，相当于this
    @classmethod
    def login_check(cls, user_name):
        user = cls.query.filter(db.or_(
            User.nickname == user_name, User.email == user_name
        )).first()

        if not user:
            return None

        return user



    # 调试输出 __repr__
    def __repr__(self):
        return '<User %r>' % self.nickname


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.String(140))
    timestamp = db.Column(db.DateTime)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        return '<Post %r>' % self.body


