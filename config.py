CSRF_ENABLED = True
SECRET_KEY = 'bawel'

#  每页显示blog数量
POSTS_PER_PAGE = 3

import os


basedir = os.path.abspath(os.path.dirname(__file__))

SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'app.db')
SQLALCHEMY_MIGRATE_REPO = os.path.join(basedir, 'db_repository')

# 全文搜索,配置地址
WHOOSH_BASE = os.path.join(basedir, "search.db")

# 搜素结果返回最大数量
MAX_SEARCH_RESULTS = 50
