#-*- coding:utf-8 -*-

import functools
from datetime import datetime

from flask import request, jsonify, g
from flask_login import UserMixin
from flask_login._compat import unicode
from hashlib import md5

from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from itsdangerous import BadSignature, SignatureExpired
from werkzeug.security import generate_password_hash, check_password_hash

from app import app as parent_app
import sys
from app import db
import flask_whooshalchemyplus

ROLE_USER = 0
ROLE_ADMIN = 1


followers = db.Table('followers',
                     db.Column('follower_id', db.Integer, db.ForeignKey('user.uid')),
                     db.Column('followed_id', db.Integer, db.ForeignKey('user.uid'))
                     )


class User(db.Model, UserMixin):
    uid = db.Column(db.Integer,autoincrement=True, primary_key=True)
    nickname = db.Column(db.String(64), unique=True)
    mail = db.Column(db.String(120), unique=True)
    password = db.Column(db.Text)
    avatar = db.Column(db.Text)

    token_version = db.Column(db.Integer)
    role = db.Column(db.SmallInteger, default=ROLE_USER)
    posts = db.relationship('Post', backref='user', lazy='dynamic')  # 一对多的关系
    last_seen = db.Column(db.DateTime)
    introduce = db.Column(db.String(140))
    followed = db.relationship("User", secondary=followers,
                               primaryjoin=(followers.c.follower_id == uid),
                               secondaryjoin=(followers.c.followed_id == uid),
                               backref=db.backref("followers", lazy="dynamic"),
                               lazy="dynamic")  # 多对多
    name = db.Column(db.Text)
    stu_code = db.Column(db.Text)
    qq = db.Column(db.Text)
    phone = db.Column(db.Text)
    team = db.Column(db.Text)
    activity = db.Column(db.VARCHAR(10), db.ForeignKey('activities.aid'))

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
        return self.followed.filter(followers.c.followed_id == user.uid).count() > 0

    # 查询关注者所发布博客
    def followed_posts(self):
        return Post.query.join(followers,
                               (followers.c.followed_id == Post.uid)) \
            .filter(followers.c.follower_id == self.uid) \
            .order_by(Post.create_time.desc())

    def followed_acts(self):
        return Activities.query.join(followers,
                               (followers.c.followed_id == Activities.uid)) \
            .filter(followers.c.follower_id == self.uid) \
            .order_by(Activities.create_time.desc())

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
    def __init__(self, mail, password, nickname,name, stu_code, qq, phone, activity):
        self.mail = mail
        self.password = generate_password_hash(password)
        self.nickname = nickname
        self.introduce = ''
        self.token_version = 0
        self.name = name
        self.stu_code = stu_code
        self.qq = qq
        self.phone = phone
        self.activity = activity

        # self.avatar = 'avatar_default.png'

    def update_password(self, password):
        self.password = generate_password_hash(password)
        self.token_version = self.token_version + 1

    def generate_auth_token(self, expiration=4320000):
        s = Serializer(parent_app.config['SECRET_KEY'], expires_in=expiration)
        return (s.dumps({'id': self.uid, 'version': self.token_version})).decode()

    @property
    def team_str(self):
        if self.team is None:
            return ""
        return self.team

    @staticmethod
    def verify_auth_token(token):
        s = Serializer(parent_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except SignatureExpired:
            return None  # valid token, but expired
        except BadSignature:
            return None  # invalid token

        user = User.query.filter_by(uid=data['id']).first()
        if user and user.token_version == data['version']:
            return user
        return None

    @staticmethod
    def verify_user(mail, password):
        user = User.query.filter_by(mail=mail).first()
        if user:
            if check_password_hash(user.password, password):
                return user
        return None

    @property
    def general_info_dict(self):
        return {
            "nickname": self.nickname,
            "avatar": self.avatar,
            "introduce": self.introduce,
            "uid": self.uid
        }


def login_required(func):
    @functools.wraps(func)
    def wrapper(*args, **kw):
        token = request.headers.get('token')
        if not token:
            return jsonify(success=False, message='token no found'), 401
        user = User.verify_auth_token(token)
        if user:
            g.user = user
            return func(*args, **kw)
        return jsonify(success=False, message='token verify fail'), 401

    return wrapper


class Post(db.Model):
    __searchable__ = ["content"]
    fid = db.Column(db.Integer, primary_key=True,autoincrement=True)
    uid = db.Column(db.Integer, db.ForeignKey('user.uid'))
    content = db.Column(db.Text)
    picture = db.Column(db.Text, nullable=True)
    view_count=db.Column(db.Integer)
    # picture==save_name

    # picture_ratio = db.Column(db.Float)
    create_time = db.Column(db.DateTime)
    fav_count = db.Column(db.Integer)
    comment_count = db.Column(db.Integer)

    def __init__(self, uid, content, picture,):
        self.uid = uid
        self.content = content
        self.picture = picture
        # self.picture_ratio = picture_ratio
        self.create_time = datetime.now()
        self.view_count=0
        self.fav_count = 0
        self.comment_count = 0

    @property
    def create_time_str(self):
        return self.create_time.strftime('%Y/%m/%d %H:%M:%S')

    @property
    def user_model(self):
        return User.query.filter_by(uid=self.uid).first()

    @property
    def general_info_dict_with_user(self):
        return {
            "fid": self.fid,
            "content": self.content,
            "picture": self.picture,
            # "pictureRatio": round(self.picture_ratio, 2),
            "viewCount":self.view_count,
            "createTime": self.create_time_str,
            "favCount": self.fav_count,
            "commentCount": self.comment_count,
            "user": self.user_model.general_info_dict
        }


class FeedsFav(db.Model):
    fid = db.Column(db.Integer, db.ForeignKey('post.fid'), primary_key=True)
    uid = db.Column(db.Integer, db.ForeignKey('user.uid'), primary_key=True)
    time = db.Column(db.Integer)

    def __init__(self, fid, uid):
        self.fid = fid
        self.uid = uid
        self.time = int(datetime.now().timestamp())


class FeedsComment(db.Model):
    cid = db.Column(db.Integer, autoincrement=True, primary_key=True)
    fid = db.Column(db.Integer, db.ForeignKey('post.fid'))
    uid = db.Column(db.Integer, db.ForeignKey('user.uid'))
    text = db.Column(db.Text)
    create_time = db.Column(db.DateTime)

    def __init__(self, fid, uid, text):
        self.fid = fid
        self.uid = uid
        self.text = text
        self.create_time = datetime.now()

    @property
    def create_time_str(self):
        return self.create_time.strftime('%m/%d %H:%M')

    @property
    def general_info_dict(self):
        return {
            "cid": self.cid,
            "text": self.text,
            "createTime": self.create_time_str,
            "fid": self.fid,
            "picture": None
        }

    def info_dict_for_user(self, user, post=None):
        general_dict = self.general_info_dict
        general_dict['user'] = user.general_info_dict
        if post:
            general_dict['picture'] = post.picture
        return general_dict

    @classmethod
    def comments_dict_for_feed(cls, fid):
        comments_arr = db.session.query(FeedsComment, User).filter(FeedsComment.fid == fid,
                                                                   FeedsComment.uid == User.uid).all()
        return [each[0].info_dict_for_user(each[1]) for each in comments_arr]

    @classmethod
    def comments_dict_for_uid(cls, uid):
        comments_arr = db.session.query(FeedsComment, Post, User).filter(Post.uid == User.uid,
                                                                         FeedsComment.fid == Post.fid,
                                                                         Post.uid == uid).all()
        return [each[0].info_dict_for_user(each[2], post=each[1]) for each in comments_arr]


class Activities(db.Model):
    # __bind_key__ = 'activity'
    # activity_name = db.Column(db.VARCHAR(10), primary_key=True, unique=True)
    aid = db.Column(db.Integer, primary_key=True,autoincrement=True)
    uid = db.Column(db.Integer, db.ForeignKey('user.uid'))
    title = db.Column(db.Text)
    note = db.Column(db.Text)
    picture = db.Column(db.Text, nullable=True)
    address = db.Column(db.Text)
    start_time = db.Column(db.DateTime)
    phone = db.Column(db.Text)
    create_time = db.Column(db.DateTime)
    join_time = db.Column(db.DateTime)
    end_time = db.Column(db.DateTime)
    organization =db.Column(db.Text)
    activity_type = db.Column(db.Text)
    max_person = db.Column(db.Integer)
    award = db.Column(db.Integer)
    reg_enable = db.Column(db.Boolean, default=True)
    team_enable = db.Column(db.Boolean, default=False)
    upload_enable = db.Column(db.Boolean, default=False)
    view_count=db.Column(db.Integer)
    rank = db.Column(db.Integer,)
    hide = db.Column(db.Boolean, default=False)
    registered = db.Column(db.Integer)
    comment_count = db.Column(db.Integer)

    def __init__(self, uid, title, note, picture, address, start_time, phone, join_time,
                 end_time, activity_type, max_person, award, team_enable, upload_enable, organization,):
        self.uid = uid
        self.title = title
        self.note = note
        self.picture = picture
        self.address = address
        self.start_time = start_time
        self.phone = phone
        self.join_time = join_time
        self.end_time = end_time
        self.activity_type = activity_type
        self.max_person = max_person
        self.award = award
        self.team_enable = team_enable
        self.upload_enable = upload_enable
        self.organization = organization
        self.reg_enable = 1
        self.create_time = datetime.now()
        self.view_count = 0
        self.registered = 0
        self.comment_count = 0

        # self.rank = rank
        self.hide = False

    @property
    def create_time_str(self):
        return self.create_time.strftime('%Y.%m.%d')

    @property
    def user_model(self):
        return User.query.filter_by(uid=self.uid).first()

    @property
    def start_time_str(self):
        return self.start_time.strftime('%Y-%m-%d %a %H:%M')

    @property
    def end_time_str(self):
        return self.end_time.strftime('%Y-%m-%d %a %H:%M')

    @property
    def join_time_str(self):
        return self.join_time.strftime('%Y-%m-%d %a %H:%M')

    @property
    def general_info_act_with_user(self):
        return {
            "aid": self.aid,
            "title": self.title,
            "picture": self.picture,
            "award":self.award,
            "start_time": self.start_time_str,
            # "pictureRatio": round(self.picture_ratio, 2),
            "address": self.address,
            "createTime": self.create_time_str,
            "max_person": self.max_person,
            "registered": self.registered,
            "user": self.user_model.general_info_dict,
            "reg_enable":self.reg_enable
        }

    @property
    def detail_info_act_with_user(self):
        general_info = self.general_info_act_with_user
        general_info.update({
            "phone": self.phone,
            "join_time": self.join_time_str,
            "end_time": self.end_time_str,
            "organization": self.organization,
            "award": self.award,
            "note": self.note,
            "upload_enable":self.upload_enable,
            "view_count":self.view_count,
            "team_enable":self.team_enable
        })
        return general_info
    # def __repr__(self):
    #     return "{0} {1} {2}".format(self.activity_name, self.team_enable, self.upload_enable)


class ActivityFav(db.Model):
    aid = db.Column(db.Integer, db.ForeignKey('activities.aid'), primary_key=True)
    uid = db.Column(db.Integer, db.ForeignKey('user.uid'), primary_key=True)
    time = db.Column(db.Integer)

    def __init__(self, aid, uid):
        self.aid = aid
        self.uid = uid
        self.time = int(datetime.now().timestamp())


class ActivityComment(db.Model):
    cid = db.Column(db.Integer, autoincrement=True, primary_key=True)
    aid = db.Column(db.Integer, db.ForeignKey('activities.aid'))
    uid = db.Column(db.Integer, db.ForeignKey('user.uid'))
    text = db.Column(db.Text)
    create_time = db.Column(db.DateTime)

    def __init__(self, aid, uid, text):
        self.aid = aid
        self.uid = uid
        self.text = text
        self.create_time = datetime.now()

    @property
    def create_time_str(self):
        return self.create_time.strftime('%m/%d %H:%M')

    @property
    def general_info_dict(self):
        return {
            "cid": self.cid,
            "text": self.text,
            "createTime": self.create_time_str,
            "fid": self.aid,
            "picture": None
        }

    def info_dict_for_user(self, user, activities=None):
        general_dict = self.general_info_dict
        general_dict['user'] = user.general_info_dict
        if activities:
            general_dict['picture'] = activities.picture
        return general_dict

    @classmethod
    def comments_dict_for_activity(cls, aid):
        comments_arr = db.session.query(ActivityComment, User).filter(ActivityComment.aid == aid,
                                                                      ActivityComment.uid == User.uid).all()
        return [each[0].info_dict_for_user(each[1]) for each in comments_arr]

    @classmethod
    def comments_dict_for_uid(cls, uid):
        comments_arr = db.session.query(ActivityComment, Activities, User).filter(Activities.uid == User.uid,
                                                                                  ActivityComment.fid == Post.fid,
                                                                                  Activities.uid == uid).all()
        return [each[0].info_dict_for_user(each[2], post=each[1]) for each in comments_arr]


class UploadHistory(db.Model):
    __bind_key__ = 'activity'
    uid = db.Column(db.Integer, db.ForeignKey('user.uid'))
    activity = db.Column(db.VARCHAR, db.ForeignKey('activities.aid'))
    time = db.Column(db.DateTime)
    size = db.Column(db.Text)
    fid = db.Column(db.Integer, primary_key=True)

    def __init__(self, sid, activity, size):
        self.sid = sid
        self.size = size
        self.time = datetime.now()
        self.activity = activity


class Admins(db.Model):
    __bind_key__ = 'activity'
    user = db.Column(db.VARCHAR, primary_key=True)
    passwd = db.Column(db.Text)


flask_whooshalchemyplus.init_app(parent_app)

