import datetime

# from flask import Response, Flask
from flask import render_template, flash, redirect, session, url_for, request, g
from flask.ext.login import login_user, logout_user, current_user, login_required
from lxml.doctestcompare import strip

from .forms import LoginForm, SignUpForm, AboutMeForm, PublishBlogForm
from .models import User, ROLE_USER, Post

from app import app, db, lm


@app.route('/')
@app.route('/index')
def index():
    # user = "Man"  # 用户名
    # # posts = [  # 提交内容
    # #     {
    # #         'author': {'nickname': 'John'},
    # #         'body': 'Beautiful day in Portland!'
    # #     },
    #     {
    #         'author': {'nickname': 'Susan'},
    #         'body': 'The Avengers movie was so cool!'
    #     }
    # ]

    return render_template("index.html",
                           title='Home',
                           )


# 用于从数据库加载用户，这个函数将会被 Flask-Login 使用
@lm.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/login', methods=['GET', 'POST'])
# @oid.loginhandler   # 告诉 Flask-OpenID 这是我们的登录视图函数。
def login():
    # 3
    # 验证用户是否被验证
    if g.user.is_authenticated:
        return redirect("index")
    # 注册验证
    form = LoginForm()
    if form.validate_on_submit():
        user = User.login_check(request.form.get("user_name"))

        if user:
            login_user(user)
            user.last_seen = datetime.datetime.now()

            try:
                db.session.add(user)
                db.session.commit()
            except():
                flash("错误：The Database error!")
                return redirect("/login")

            flash('Your name: ' + request.form.get('user_name'))
            flash('remember me? ' + str(request.form.get('remember_me')))
            session['remember_me'] = form.remember_me.data
            # return redirect(url_for("users", user_id=current_user.id))
            return redirect(url_for("index"))
            # url_for为一个给定的视图函数获取 URL
        else:
            flash("Login failed,Your name is not exist!")
            return redirect("/login")

    return render_template("login.html",
                           title="Sign In",
                           form=form
                           )
    # 1.1

    # form = LoginForm()
    # if form.validate_on_submit():  # flash函数是一种快速的方式下呈现给用户的页面上显示一个消息。
    #     flash('Login requested for Name: ' + form.name.data)
    #     flash('passwd: ' + str(form.password.data))
    #     flash('remember_me: ' + str(form.remember_me.data))
    #     return redirect('/index')
    # return render_template('login.html',
    #                        title='Sign In',
    #                        form=form)
# 2
#  g 全局变量是一个在请求生命周期中用来存储和共享数据
# if g.user is not None and g.user.is_authenticated():
#     return redirect(url_for('index'))
# form = LoginForm()
# if form.validate_on_submit():
#     # flask.session提供了一个更加复杂的服务对于存储和共享数据。
#     # 一旦数据存储在会话对象中，在来自同一客户端的现在和任何以后的请求都是可用的。数据保持在会话中直到会话被明确地删除。
#     session['remember_me'] = form.remember_me.data
#     # 触发用户使用 Flask-OpenID 认证。
#
#     return oid.try_login(form.openid.data, ask_for=["nickname", "email"])
#
# return render_template('login.html',
#                        title='Sign In',
#                        form=form,
#                        providers=app.config['OPENID_PROVIDERS'])


@app.route("/logout")
@login_required  # 验证用户必须是以登录为前提
def logout():
    logout_user()
    return redirect(url_for("index"))


@app.route("/sign-up", methods=['Get', 'Post'])
def sign_up():
    form = SignUpForm()
    user = User()
    if form.validate_on_submit():
        user_name = request.form.get('user_name')
        user_email = request.form.get('user_email')

        register_check = User.query.filter(db.or_(
            User.nickname == user_name, User.email == user_email
        )).first()
        if register_check:
            flash("error:The user's name or email already exits!")
            return redirect("/sign-up")

        if len(user_name) and len(user_email):
            user.nickname = user_name
            user.email = user_email
            user.role = ROLE_USER
            user.last_seen = datetime.datetime.now()
        try:
            db.session.add(user)
            db.session.commit()
        except():
            flash("The Database error!")
            return redirect('/sign-up')

        flash("Sign up successful!")
        return redirect('/index')

    return render_template("sign_up.html", form=form)


@app.before_request
def before_request():
    g.user = current_user


@app.route('/user/<int:user_id>', methods=["POST","GET"])
@login_required
def users(user_id):
    form = AboutMeForm()
    user = User.query.filter(User.id == user_id).first()
    if not user:
        flash("The user is not exist.")
        redirect("/index")

    blogs = user.posts.all()

    return render_template("user.html",
                           form=form,
                           user=user,
                           blogs=blogs
                           )


@app.route("/publish/<int:user_id>", methods=["POST", "GET"])
@login_required
def publish(user_id):
    form = PublishBlogForm()
    posts = Post()
    if form.validate_on_submit():
        blog_body = request.form.get("body")
        if not len(strip(blog_body)):
            flash("The content is necessary!")
            return redirect(url_for("publish", user_id=user_id))

        posts.body = blog_body
        posts.timestamp = datetime.datetime.now()
        posts.user_id = user_id

        try:
            db.session.add(posts)
            db.session.commit()
        except():
            flash("Database error")
            return redirect(url_for("publish", user_id=user_id))

        flash("Publish Successful!")
        return redirect(url_for("publish", user_id=user_id))

    return render_template("publish.html",
                           form=form
                           )


@app.route('/user/about-me/<int:user_id>', methods=["POST", "GET"])
@login_required
def about_me(user_id):
    user = User.query.filter(User.id == user_id).first()
    if request.method == "POST":
        content = request.form.get("describe")
        if len(content) and len(content) <= 140:
            user.about_me = content
            try:
                db.session.add(user)
                db.session.commit()
            except:
                flash("Database error!")
                return redirect(url_for("users", user_id=user_id))
        else:
            flash("Sorry, May be your data have some error.")
    return redirect(url_for("users", user_id=user_id))


# @app.router("/image/<image_id>")
# def index(image_id):
#     image = file ()
