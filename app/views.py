from flask import render_template,flash,redirect,session,url_for,request,g
from flask.ext.login import login_user,logout_user,current_user,login_required
from .forms import LoginForm
from .models import User

from app import app,db,lm,oid


@app.route('/')
@app.route('/index')
def index():
    user = {'nickname': 'Miguel'}  # 用户名
    posts = [  # 提交内容
        {
            'author': {'nickname': 'John'},
            'body': 'Beautiful day in Portland!'
        },
        {
            'author': {'nickname': 'Susan'},
            'body': 'The Avengers movie was so cool!'
        }
    ]

    return render_template("index.html",
                           title='Home',
                           user=user,
                           posts=posts)


@lm.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/login', methods = ['GET', 'POST'])
@oid.loginhandler   # 告诉 Flask-OpenID 这是我们的登录视图函数。
def login():
    # form = LoginForm()
    # if form.validate_on_submit():  # flash函数是一种快速的方式下呈现给用户的页面上显示一个消息。
    #     flash('Login requested for Name: ' + form.name.data)
    #     flash('passwd: ' + str(form.password.data))
    #     flash('remember_me: ' + str(form.remember_me.data))
    #     return redirect('/index')
    # return render_template('login.html',
    #                        title='Sign In',
    #                        form=form)

    #  g 全局变量是一个在请求生命周期中用来存储和共享数据
    if g.user is not None and g.user.is_authenticated():
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        session['remember_me']=form.remember_me.data
        return oid.try_login(form.openid.data, ask_for=["nickname", "email"])

    return render_template('login.html',
                           title='Sign In',
                           form=form,
                           providers=app.config['OPENID_PROVIDERS'])
