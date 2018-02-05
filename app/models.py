#-*- coding:utf-8 -*-
from flask_login import UserMixin
from flask_login._compat import unicode
from hashlib import md5
from app import app
import sys
from app import db
import flask_whooshalchemyplus

ROLE_USER = 0
ROLE_ADMIN = 1


followers = db.Table('followers',
                     db.Column('follower_id', db.Integer, db.ForeignKey('user.id')),
                     db.Column('followed_id', db.Integer, db.ForeignKey('user.id'))
                     )


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    nickname = db.Column(db.String(64), unique=True)
    email = db.Column(db.String(120), unique=True)
    role = db.Column(db.SmallInteger, default=ROLE_USER)
    posts = db.relationship('Post', backref='user', lazy='dynamic')  # 一对多的关系
    last_seen = db.Column(db.String(120), unique=True)
    about_me = db.Column(db.String(140))
    followed = db.relationship("User", secondary=followers,
                               primaryjoin=(followers.c.follower_id == id),
                               secondaryjoin=(followers.c.followed_id == id),
                               backref=db.backref("followers", lazy="dynamic"),
                               lazy="dynamic")  # 多对多

    #  添加和移除“关注者”功能
    def follow(self, user):
        if not self.is_following(user):
            self.followed.append(user)
            return self

    def unfollow(self, user):
        if self.is_following(user):
            self.followed.remove(user)
            return self

    def is_following(self, user):
        return self.followed.filter(followers.c.followed_id == user.id).count() > 0

    # 查询关注者所发布博客
    def followed_posts(self):
        return Post.query.join(followers,
                               (followers.c.followed_id == Post.user_id)) \
            .filter(followers.c.follower_id == self.id) \
            .order_by(Post.timestamp.desc())

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
    __searchable__ = ["body"]
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.String(140))
    timestamp = db.Column(db.DateTime)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        return '<Post %r>' % self.body


flask_whooshalchemyplus.init_app(app)

