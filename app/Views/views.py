import uuid
from io import BytesIO as StringIO

# from flask import Response, Flask
import xlwt as xlwt
from flask import flash, send_file, abort
from flask import jsonify, request, g
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer

from app import app, db
from ..models import Post, FeedsFav, FeedsComment
from ..models import User, login_required, followers, Activities, ActivityFav


# app = Blueprint('userApi', __name__)


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


# 注册
@app.route('/register', methods=['POST'])
def register():
    pwd = request.form['pwd']
    nickname = request.form['nickname']
    mail = request.form['mail']
    s = {"success": False, "Msg": "注册成功"}

    # Check mail available
    if User.query.filter_by(mail=mail).first() is not None:
        s['msg'] = '邮箱已被使用'
        return jsonify(s)

    # Add User
    new_user = User(mail, pwd, nickname)
    db.session.add(new_user)
    db.session.commit()
    s['success'] = True
    s['token'] = new_user.generate_auth_token()
    profile = {
        "nickname": new_user.nickname,
        "avatar": new_user.avatar,
        "introduce": new_user.introduce,
        "mail": new_user.mail,
        "uid": new_user.uid,
    }
    s["profile"] = profile
    return jsonify(s)



@app.route("/follow/<int:user_id>")
@login_required
def follow(user_id):
    user = User.query.filter_by(uid=user_id).first()
    if user is None:
        flash("User %d not found." % user_id)
        meg = str(user_id) + '未找到'
        return jsonify(success=False, meg=meg)
    if user.uid == g.user.uid:
        return jsonify(success=False, meg="You can\'t follow yourself!")
    u = g.user.follow(user)
    if u is None:
        meg = "Cannot follow" + user.nickname + '.'
        return jsonify(success=False, meg=meg)
    db.session.add(u)
    db.session.commit()
    # flash("You are now following" + user.nickname + "!")
    # 发邮件功能
    # follower_notification(user, g.user)
    return jsonify(success=True, meg="关注成功")


@app.route('/unfollow/<int:user_id>')
@login_required
def unfollow(user_id):
    user = User.query.filter_by(uid=user_id).first()
    if user is None:
        meg = 'User %d not found.' % user_id
        return jsonify(success=False, meg=meg)
    if user.uid == g.user.uid:
        meg = 'You can\'t unfollow yourself!'
        return jsonify(success=False, meg=meg)
    u = g.user.unfollow(user)
    if u is None:
        meg = 'Cannot unfollow ' + user.nickname + '.'
        return jsonify(success=False, meg=meg)
    db.session.add(u)
    db.session.commit()
    # flash('You have stopped following ' + user.nickname + '.')
    return jsonify(success=True, meg="取消关注")


@app.route("/search_results")
@login_required
def search_results():
    find = request.args.get('find')
    if not find:
        return jsonify(success=False, msg='请输入需要查找的活动名称或博客内容')
    post_results = Post.query.filter(Post.content.like('%{}%'.format(find))).order_by(Post.create_time.desc()).limit(
        10).all()
    act_results = Activities.query.filter(Activities.title.like('%{}%'.format(find))).order_by(
        Activities.create_time.desc()).limit(10).all()
    if not post_results and not act_results:
        return jsonify(success=False, msg='未找到')

    act_res = []
    if act_results:
        act_res = []

        for each in act_results:
            act_res.append(each.general_info_act_with_user)
            each.view_count += 1
    post_res = []
    if post_results:
        post_res = [each.general_info_dict_with_user for each in post_results]
        act_res.extend(post_res)
        # return render_template("search_results.html",
        #                        results=results,
        #                        find=find
        #                        )

    return jsonify(success=True, find=find, results=act_res, )


# @babel.localeselector
# def get_locale():
#     return request.accept_languages.best_match(LANGUAGES.keys())


# 更新个人资料
@app.route('/update_profile', methods=['POST'])
@login_required
def update_profile():
    # print(request.files)
    nickname = request.form.get('nickname')
    introduce = request.form.get('introduce')
    pic = request.files.get('image')
    if pic:
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
        "name": user.name,
        "stu_code": user.stu_code,
        "phone": user.phone,
        "qq": user.qq,
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
    followothe_count = User.query.join(followers, (followers.c.followed_id == User.uid)).filter(
        followers.c.follower_id == user.uid).count()
    follow_me = User.query.join(followers, (followers.c.follower_id == User.uid)).filter(
        followers.c.followed_id == g.user.uid).count()
    Activities_list = Activities.query.filter_by(uid=user.uid).count()
    profile = {
        "favCount": fav_count,
        "commentCount": comment_count,
        "feeds": posts_list,
        "follow_count": followothe_count,
        "follow_me": follow_me,
        "Activities_list": Activities_list
    }
    return jsonify(profile)


@app.route('/followother_list/<int:uid>')
@login_required
def get_followother_list(uid):
    follow_me = User.query.join(followers, (followers.c.followed_id == User.uid)).filter(
        followers.c.follower_id == uid)
    res = [each.general_info_dict for each in follow_me]
    return jsonify(data=res)


@app.route('/followme_list/<int:uid>')
@login_required
def get_followme_list(uid):
    follow_me = User.query.join(followers, (followers.c.follower_id == User.uid)).filter(
        followers.c.followed_id == uid)
    res = [each.general_info_dict for each in follow_me]
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
             "creat_time": each[0].create_time_str,
             } for each in arr]

    return jsonify(data=data, )


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
        "profile": {
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
        'Activities_list': Activities_list,
    }
    return jsonify(profile)


@app.route('/followedposts')
@login_required
def get_followedposts():
    page = int(request.args.get('page', '0'))
    post = g.user.followed_posts(page)
    res = [each.general_info_dict_with_user for each in post]
    if len(post) > 0:
        end = False

    else:
        end = True

    return jsonify(data=res, end=end)


@app.route('/followedacts')
@login_required
def get_followedacts():
    page = int(request.args.get('page', '0'))
    act = g.user.followed_acts(page)
    res = [each.general_info_act_with_user for each in act]
    return jsonify(data=res)


@app.route('/admin/export')
def generate_excel():
    # act_name = request.args.get('act')
    file_token = request.args.get('filetoken')

    if not file_token:
        abort(401)
    s = Serializer("zmfang")
    try:
        data = s.loads(file_token)
    except Exception as err:

        abort(401)  # valid token, but expired

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
