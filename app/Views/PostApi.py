from flask import Blueprint, jsonify, request, g, abort
from app import app, db, lm
from ..models import User, login_required
from ..models import Post, FeedsComment, FeedsFav
from sqlalchemy.exc import IntegrityError
# from .qiniuApi import delete_key
import datetime
import uuid

# app = Blueprint('feedsApi', __name__)


@app.route('/post', methods=['POST'])
@login_required
def post():
    content = request.form.get('content')
    # print(content)
    # picture = request.form.getfile('picture')
    pic = request.files.get('image')
    # picture_ratio = float(request.form.get('picture_ratio'))
    picture = str(uuid.uuid4())
    if None in [content,pic]:
        return jsonify(success=False, msg='参数错误')

    pic.save('app/static/uploads/%s' % picture)
    new_feed = Post(g.user.uid, content, picture, )
    db.session.add(new_feed)
    db.session.commit()
    return jsonify(success=True, fid=new_feed.fid)


@app.route('/timeline')
# @login_required
def get_timeline():
    timestamp = request.args.get('timestamp')
    if not timestamp:
        timestamp = datetime.datetime.now()
    else:
        timestamp = datetime.datetime.fromtimestamp(int(timestamp))

    feeds = Post.query.filter(Post.create_time < timestamp).order_by(Post.create_time.desc()).limit(10).all()

    res =[]
    for each in feeds:
        res.append(each.general_info_dict_with_user)
        each.view_count += 1

    db.session.commit()
    # view_count = [(each.view_count+=1) for each in feeds]
    datetime.datetime.now().timestamp()

    if len(feeds) > 0:
        end = False
        early_time_stamp = feeds[-1].create_time.timestamp()
    else:
        end = True
        early_time_stamp = datetime.datetime.now().timestamp()
    return jsonify(feeds=res, earlyTimeStamp=int(early_time_stamp), end=end)


@app.route('/content/<fid>')
@login_required
def get_feed_detail(fid):
    res = Post.query.filter_by(fid=fid).first()
    if not res:
        abort(404)

    return jsonify(res.general_info_dict_with_user)


@app.route('/comment/<fid>')
@login_required
def get_timeline_comment(fid):
    # res = Feeds.query.filter_by(fid=fid).first().general_info_dict_with_user
    # if not res:
    #     abort(404)
    comments = FeedsComment.comments_dict_for_feed(fid)
    # res['comments'] = comments
    # return jsonify(res)
    return jsonify(comments=comments)


@app.route('/fav', methods=['POST'])
@login_required
def add_fav_feed():
    uid = g.user.uid
    fid = request.form.get('fid')
    if not fid:
        abort(400)
    try:
        if not FeedsFav.query.filter_by(fid=fid, uid=uid).first():
            new_fav = FeedsFav(fid, uid)
            db.session.add(new_fav)
            feed = Post.query.filter_by(fid=fid).first()
            feed.fav_count += 1
            db.session.commit()
        return jsonify(success=True)
    except IntegrityError:
        return jsonify(success=False)


@app.route('/unfav', methods=['POST'])
@login_required
def remove_fav_feed():
    uid = g.user.uid
    fid = request.form.get('fid')
    if not fid:
        abort(400)
    try:
        fav = FeedsFav.query.filter_by(fid=fid, uid=uid).first()
        if fav:
            feed = Post.query.filter_by(fid=fid).first()
            feed.fav_count -= 1
            db.session.delete(fav)
            db.session.commit()
        return jsonify(success=True)
    except IntegrityError:
        return jsonify(success=False)


@app.route('/fav_list')
@login_required
def get_fav_list():
    fav_list = FeedsFav.query.filter_by(uid=g.user.uid).all()
    fav_list_array = [each.fid for each in fav_list]
    return jsonify(data=fav_list_array)


@app.route('/favPost_list')
@login_required
def get_favpost_list():
    fav_list = FeedsFav.query.filter_by(uid=g.user.uid).all()
    res=[]
    for each in fav_list:
       item = Post.query.filter_by(fid=each.fid).first()
       res.append(item.general_info_dict_with_user)

    return jsonify(data=res)


@app.route('/myPost_list')
@login_required
def get_mypost_list():
    post_list = Post.query.filter_by(uid=g.user.uid).order_by(Post.create_time.desc()).all()
    res = [each.general_info_dict_with_user for each in post_list]
    return jsonify(data=res)


@app.route('/otherPost_list/<uid>')
@login_required
def get_otherpost_list(uid):
    post_list = Post.query.filter_by(uid=uid).order_by(Post.create_time.desc()).all()
    res = [each.general_info_dict_with_user for each in post_list]
    return jsonify(data=res)


@app.route('/favPeo_list/<fid>')
@login_required
def get_favPeo_list(fid):
    fav_list = FeedsFav.query.filter_by(fid=fid).all()
    fav_list_array = [{"uid": each.uid,
                       "nickname": User.query.filter_by(uid=each.uid).first().nickname,
                       "avatar": User.query.filter_by(uid=each.uid).first().avatar,
                       } for each in fav_list]
    return jsonify(data=fav_list_array)


@app.route('/comment', methods=['POST'])
@login_required
def add_comment_feed():
    uid = g.user.uid
    fid = request.form.get('fid')
    text = request.form.get('text')
    try:
        new_comment = FeedsComment(fid, uid, text)
        db.session.add(new_comment)
        feed = Post.query.filter_by(fid=fid).first()
        feed.comment_count += 1
        db.session.commit()
    except IntegrityError:
        return jsonify(success=False)
    return jsonify(success=True)


# @app.route('/delete/<fid>', methods=['POST'])
# @login_required
# def delete_feed(fid):
#     feed = Post.query.filter_by(fid=fid).first()
#     file_key = feed.picture
#     if not feed or feed.uid != g.user.uid:
#         abort(401)
#     db.session.delete(feed)
#     db.session.commit()
#     delete_key(file_key)
#     return jsonify(success=True)