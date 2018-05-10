# from flask import Flask
# app = Flask(__name__)
# from flask.ext.sqlalchemy import SQLAlchemy
# app.config.from_object('config')
# db = SQLAlchemy(app)
# from app import views,models

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

from config import basedir
import os

# 初始化flask应用
app = Flask(__name__)
app.config.from_object('config')
# 初始化数据库
db = SQLAlchemy(app)


from app import Views, models
