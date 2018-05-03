# from flask import Flask
# app = Flask(__name__)
# from flask.ext.sqlalchemy import SQLAlchemy
# app.config.from_object('config')
# db = SQLAlchemy(app)
# from app import views,models

from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.login import LoginManager
from .momentjs import momentsjs
from flask.ext.openid import OpenID
from config import basedir
import os
from flask.ext.mail import Mail
from flask.ext.babel import Babel
# 初始化flask应用
app = Flask(__name__)
app.config.from_object('config')
# 初始化数据库
db = SQLAlchemy(app)
# 初始化flask-Login
lm = LoginManager()
lm.init_app(app)
lm.login_view = "login"  # 指定登录视图
# # 初始化Flask-OpenID，存储临时文件夹的路径tmp
# oid = OpenID(app, os.path.join(basedir, 'tmp'))

# 初始化mail对象
mail = Mail(app)

# 封装好的类与jinja2 绑定
app.jinja_env.globals["momentjs"] = momentsjs

# 便于外国访问者
babel = Babel(app)

from app import Views, models
