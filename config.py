# -*- coding: utf-8 -*-
# ...
# available languages
CSRF_ENABLED = True
SECRET_KEY = 'bawel'

#  每页显示blog数量
POSTS_PER_PAGE = 3

import os


basedir = os.path.abspath(os.path.dirname(__file__))

SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'app.db')
SQLALCHEMY_MIGRATE_REPO = os.path.join(basedir, 'db_repository')
SQLALCHEMY_TRACK_MODIFICATIONS=True

