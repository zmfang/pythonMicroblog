import uuid
from datetime import datetime

# from flask import Response, Flask
import xlwt as xlwt
from flask import render_template, flash, redirect, session, url_for, request, g, send_file, abort
from flask.ext.login import login_user, logout_user, current_user, login_required
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from lxml.doctestcompare import strip

from app.emails import follower_notification
from config import POSTS_PER_PAGE, MAX_SEARCH_RESULTS
from ..forms import LoginForm, SignUpForm, PublishBlogForm, AboutMeForm, SearchForm
from ..models import User, ROLE_USER, login_required, followers, Activities, ActivityFav
from app import babel
from config import LANGUAGES
from flask import Blueprint, jsonify, request, g
from ..models import Post, FeedsFav, FeedsComment
from io import BytesIO as StringIO

# app = Blueprint('userApi', __name__)

from app import app, db, lm


# @app.route('/', methods=["GET", "POST"])
# @app.route('/index', methods=["POST", "GET"])
# @app.route('/index/<int:page>', methods=["POST", "GET"])
# @login_required
# def index(page = 1):
#     # user = "Man"  # 用户名
#     # # posts = [  # 提交内容
#     # #     {
#     # #         'author': {'nickname': 'John'},
#     # #         'body': 'Beautiful day in Portland!'
#     # #     },
#     #     {
#     #         'author': {'nickname': 'Susan'},
#     #         'body': 'The Avengers movie was so cool!'
#     #     }
#     # ]
#     form = PublishBlogForm()
#     if form.validate_on_submit():
#         post = Post(body=form.body.data, timestamp=datetime.datetime.utcnow(), user=g.user)
#         db.session.add(post)
#         db.session.commit()
#         flash('Your post is now live!')
#         # 重定向，避免了用户在提交 blog 后不小心触发刷新的动作而导致插入重复的 blog。
#         return redirect(url_for('index'))
#
#     # 查询关注者的博客，并分页显示
#     posts = g.user.followed_posts().paginate(page, POSTS_PER_PAGE, False)
#
#     return render_template("index.html",
#                            title='Home',
#                            form=form,
#                            posts=posts,
#                            )


# 用于从数据库加载用户，这个函数将会被 Flask-Login 使用
# @lm.user_loader
# def load_user(user_id):
#     return User.query.get(int(user_id))


@app.route('/login', methods=['POST'])
def login():
    mail = request.form.get('mail')
    pwd = request.form.get('password')
    if not mail or not pwd:
        return jsonify(success=False, msg='参数错误')
    user = User.verify_user(mail, pwd)
    if user:
        profile = {
            "nickname": user.nickname,
            "avatar": user.avatar,
            "introduce": user.introduce,
            "mail": user.mail,
            "uid": user.uid,
            "name": user.name,
            "stu_code": user.stu_code,
            "phone": user.phone,
            "qq": user.qq,
        }
        return jsonify(success=True, token=user.generate_auth_token(), profile=profile)
    return jsonify(success=False, msg='用户名或密码错误')

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


# 注册
@app.route('/register', methods=['POST'])
def register():
    pwd = request.form['pwd']
    nickname = request.form['nickname']
    mail = request.form['mail']
    s = {"success": False, "Msg": "注册成功"}

    # Check mail available
    if User.query.filter_by(mail=mail).first() is not None:
        s['Msg'] = '邮箱已被使用'
        return jsonify(s)

    # Add User
    new_user = User(mail, pwd, nickname)
    db.session.add(new_user)
    db.session.commit()
    s['success'] = True
    s['token'] = new_user.generate_auth_token()
    return jsonify(s)

#
# @app.before_request
# def before_request():
#     g.user = current_user
#     if g.user.is_authenticated:
#         g.user.last_seen = datetime.datetime.utcnow()
#         db.session.add(g.user)
#         db.session.commit()
#         g.search_form = SearchForm()
#     g.locale = get_locale()


@app.route('/user/<int:user_id>', methods=["POST", "GET"])
@app.route('/user/<int:user_id>/<int:page>', methods=["POST", "GET"])
@login_required
def users(user_id, page=1):
    form = AboutMeForm()
    user = User.query.filter(User.id == user_id).first()
    if not user:
        flash("The user is not exist.")
        redirect("/index")

    posts = user.posts.paginate(page, POSTS_PER_PAGE, False)

    return render_template("user.html",
                           form=form,
                           user=user,
                           posts=posts
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
            except():
                flash("Database error!")
                return redirect(url_for("users", user_id=user_id))
        else:
            flash("Sorry, May be your data have some error.")
    return redirect(url_for("users", user_id=user_id))


@app.route("/follow/<int:user_id>")
@login_required
def follow(user_id):
    user = User.query.filter_by(uid=user_id).first()
    if user is None:
        flash("User %d not found." % user_id)
        meg=str(user_id)+'未找到'
        return jsonify(success=False,meg=meg)
    if user.uid == g.user.uid:
        return jsonify(success=False,meg="You can\'t follow yourself!")
    u = g.user.follow(user)
    if u is None:
        meg="Cannot follow" + user.nickname + '.'
        return jsonify(success=False,meg=meg)
    db.session.add(u)
    db.session.commit()
    # flash("You are now following" + user.nickname + "!")
    # 发邮件功能
    # follower_notification(user, g.user)
    return jsonify(success=True,meg="关注成功")


@app.route('/unfollow/<int:user_id>')
@login_required
def unfollow(user_id):
    user = User.query.filter_by(uid=user_id).first()
    if user is None:
        meg='User %d not found.' % user_id
        return jsonify(success=False,meg=meg)
    if user.uid == g.user.uid:
        meg='You can\'t unfollow yourself!'
        return jsonify(success=False,meg=meg)
    u = g.user.unfollow(user)
    if u is None:
        meg='Cannot unfollow ' + user.nickname + '.'
        return jsonify(success=False,meg=meg)
    db.session.add(u)
    db.session.commit()
    # flash('You have stopped following ' + user.nickname + '.')
    return jsonify(success=True,meg="取消关注")


@app.route('/search', methods=['POST'])
@login_required
def search():
    if not g.search_form.validate_on_submit():
        return redirect(url_for('index'))
    return redirect(url_for('search_results',
                            find=g.search_form.searchString.data))


@app.route("/search_results/<find>")
@login_required
def search_results(find):
    print(find)
    results = Post.query.whoosh_search('2',)
    # return render_template("search_results.html",
    #                        results=results,
    #                        find=find
    #                        )
    return jsonify(find=find,results=results)


# @babel.localeselector
# def get_locale():
#     return request.accept_languages.best_match(LANGUAGES.keys())


# 更新个人资料
@app.route('/update_profile', methods=['POST'])
@login_required
def update_profile():
    print(request.form)
    # print(request.files)
    nickname = request.form.get('nickname')
    introduce = request.form.get('introduce')
    pic = request.files.get('image')
    if pic :
        picture = str(uuid.uuid4())
        pic.save('app/static/uploads/%s' % picture)
        g.user.avatar = picture
    # avatar = request.form.get('avatar')
    # print(avatar)
    g.user.nickname = nickname
    g.user.introduce = introduce

    db.session.commit()
    return jsonify(success=True)


@app.route('/update_detail', methods=['POST'])
@login_required
def update_detail():

    # print(request.files)
    name = request.form.get('name')
    phone = request.form.get('phone')
    stu_code = request.form.get('stu_code')
    qq = request.form.get('qq')

    # avatar = request.form.get('avatar')
    # print(avatar)
    g.user.name = name
    g.user.phone = phone
    g.user.stu_code = stu_code
    g.user.qq = qq

    db.session.commit()
    return jsonify(success=True)


# 更改密码
@app.route('/update_password', methods=['POST'])
@login_required
def update_password():
    new_password = request.form.get('password')
    g.user.update_password(new_password)
    db.session.commit()
    new_token = g.user.generate_auth_token()
    return jsonify(success=True, token=new_token)


@app.route('/profile')
@login_required
def get_profile():
    user = g.user
    profile = {
        "nickname": user.nickname,
         "avatar": user.avatar,
        "introduce": user.introduce,
        "mail": user.mail,
        "uid": user.uid,
        "token": user.generate_auth_token(),
        "name":user.name,
        "stu_code":user.stu_code,
        "phone":user.phone,
        "qq":user.qq,
    }
    return jsonify(profile)


@app.route('/personal_center')
@login_required
def get_person_center():
    user = g.user
    posts = Post.query.filter_by(uid=user.uid).order_by(Post.fid.desc()).all()
    fav_count = FeedsFav.query.join(Post).filter(Post.uid == user.uid).count()
    comment_count = FeedsComment.query.join(Post).filter(Post.uid == user.uid).count()
    posts_list = [{"fid": each.fid, "imgKey": each.picture} for each in posts]
    followothe_count = User.query.join(followers,(followers.c.followed_id == User.uid)).filter(followers.c.follower_id == user.uid).count()
    follow_me = User.query.join(followers, (followers.c.follower_id == User.uid)).filter(
        followers.c.followed_id == g.user.uid).count()
    Activities_list = Activities.query.filter_by(uid=user.uid).count()
    profile = {
        "favCount": fav_count,
        "commentCount": comment_count,
        "feeds": posts_list,
        "follow_count":followothe_count,
        "follow_me":follow_me,
        "Activities_list":Activities_list
    }
    return jsonify(profile)


@app.route('/followother_list/<int:uid>')
@login_required
def get_followother_list(uid):

    follow_me = User.query.join(followers, (followers.c.followed_id == User.uid)).filter(
        followers.c.follower_id == uid)
    res=[each.general_info_dict for each in follow_me]
    return jsonify(data=res)


@app.route('/followme_list/<int:uid>')
@login_required
def get_followme_list(uid):
    follow_me = User.query.join(followers, (followers.c.follower_id == User.uid)).filter(
        followers.c.followed_id == uid)
    res=[each.general_info_dict for each in follow_me]
    return jsonify(data=res)


@app.route('/comments_me')
@login_required
def get_comments_me():
    user = g.user
    return jsonify(data=FeedsComment.comments_dict_for_uid(user.uid))


@app.route('/like_me')
@login_required
def get_like_me():
    user = g.user

    arr = db.session.query(FeedsFav, Post, User).filter(FeedsFav.uid == User.uid,
                                                        Post.fid == FeedsFav.fid,
                                                        Post.uid == user.uid
                                                        ).order_by(FeedsFav.time.desc()).all()
    data = [{"fid": each[1].fid,
             "content": each[1].content,
             "picture": each[1].picture,
             "user": each[2].general_info_dict,
             "creat_time":each[0].create_time_str,
             } for each in arr]

    return jsonify(data=data,)


@app.route('/stranger_center/<uid>')
@login_required
def get_stranger_center(uid):
    user = User.query.filter_by(uid=uid).first()
    posts = Post.query.filter_by(uid=user.uid).order_by(Post.fid.desc()).all()
    fav_count = FeedsFav.query.join(Post).filter(Post.uid == user.uid).count()
    comment_count = FeedsComment.query.join(Post).filter(Post.uid == user.uid).count()
    posts_list = [{"fid": each.fid, "imgKey": each.picture} for each in posts]
    followothe_count = User.query.join(followers, (followers.c.followed_id == User.uid)).filter(
        followers.c.follower_id == uid).count()
    follow_me = User.query.join(followers, (followers.c.follower_id == User.uid)).filter(
        followers.c.followed_id == uid).count()
    Activities_list = Activities.query.filter_by(uid=uid).count()
    profile = {
        "profile":{
            "nickname": user.nickname,
            "avatar": user.avatar,
            "introduce": user.introduce,
            "mail": user.mail,

            "uid": user.uid,
            # "token": user.generate_auth_token()
        },
        "favCount": fav_count,
        "commentCount": comment_count,
        "feeds": posts_list,
        "isfollowing": g.user.is_following(user),
        "follow_count": followothe_count,
        "follow_me": follow_me,
        'Activities_list':Activities_list,
    }
    return jsonify(profile)


@app.route('/followedposts')
@login_required
def get_followedposts():

    page = int(request.args.get('page', '0'))
    post=g.user.followed_posts(page)
    res = [each.general_info_dict_with_user for each in post]
    if len(post) > 0:
        end = False

    else:
        end = True

    return jsonify(data=res,end=end)


@app.route('/followedacts')
@login_required
def get_followedacts():
    page = int(request.args.get('page', '0'))
    act=g.user.followed_acts(page)
    res = [each.general_info_act_with_user for each in act]
    return jsonify(data=res)


@app.route('/admin/export')
def generate_excel():
    # act_name = request.args.get('act')
    file_token=request.args.get('filetoken')

    if not file_token:
        abort(401)
    s = Serializer("zmfang")
    try:
        data = s.loads(file_token)
    except Exception as err:

        abort(401) # valid token, but expired

    aid = data['id']
    # members = User.query.filter_by(activity=aid).all()
    fav_list = ActivityFav.query.filter_by(aid=aid).all()
    # activity = Activities.query.filter_by(aid=aid).first().title
    # print(activity)
    file = xlwt.Workbook()
    table = file.add_sheet("sheet")
    title_row = ['姓名', '学号', 'qq', 'phone', '团队', '昵称']
    for col in range(0, len(title_row)):
        table.write(0, col, title_row[col])
    row = 0
    for each in fav_list:
        row += 1
        person = User.query.filter_by(uid=each.uid).first()
        # activity= Activities.query.filter_by(activity=person.aid).first().title
        table.write(row, 0, person.name)
        table.write(row, 1, person.stu_code)
        table.write(row, 2, person.qq)
        table.write(row, 3, person.phone)
        table.write(row, 4, person.team)
        table.write(row, 5, person.nickname)
        # if person.has_submit:
        #     table.write(row, 6, "YES")

    sio = StringIO()
    file.save(sio)
    sio.seek(0)
    return send_file(sio,
                     attachment_filename="act.xls",
                     as_attachment=True)