from flask import Blueprint, jsonify, request, g, abort
from app import app, db, lm
import time
from ..models import User, login_required, Activities
from ..models import Activities, ActivityComment, ActivityFav
from sqlalchemy.exc import IntegrityError
# from .qiniuApi import delete_key
import datetime
import uuid

# app = Blueprint('activitysApi', __name__)


@app.route('/sendActivity', methods=['POST'])
@login_required
def sendActivity():
    title = request.form.get('title')
    note = request.form.get('note')
    pic = request.files.get('image')
    address = request.form.get('address')
    start_time = datetime.datetime.fromtimestamp(int(request.form.get('start_time'))//1000)
    phone = request.form.get('phone')
    join_time =datetime.datetime.fromtimestamp(int(request.form.get('join_time'))//1000)
    end_time = datetime.datetime.fromtimestamp(int(request.form.get('end_time'))//1000)
    activity_type = request.form.get('activity_type')
    team_enable =request.form.get('team_enable')
    upload_enable = request.form.get('upload_enable')
    organization = request.form.get('organization')
    # print(content)
    # picture = request.form.getfile('picture')
    try:
        max_person =int(request.form.get('max_person'))

    except:
        return jsonify(success=False, msg='最大人数必须为数字')
    # picture_ratio = float(request.form.get('picture_ratio'))
    try:
        award = int(request.form.get('award'))
    except:
        return jsonify(success=False, msg='综测必须为数字')

    picture = str(uuid.uuid4())
    if join_time>start_time:
        return jsonify(success=False, msg='报名开始时间不得小于活动开始时间')

    if end_time>start_time:
        return jsonify(success=False, msg='报名结束时间不得大于活动开始时间')

    pic.save('app/static/uploads/%s' % picture)
    new_act = Activities(g.user.uid,title, note,picture, address,start_time, phone,
                          join_time,end_time,activity_type, max_person,award,team_enable,upload_enable,organization)
    db.session.add(new_act)
    db.session.commit()
    return jsonify(success=True,aid=new_act.aid)


@app.route('/activityHotlist')
# @login_required
def get_activityHotlist():
    timestamp = request.args.get('timestamp')
    if not timestamp:
        timestamp = datetime.datetime.now()
    else:
        timestamp = datetime.datetime.fromtimestamp(int(timestamp))

    activities = Activities.query.filter(Activities.create_time < timestamp).order_by(Activities.create_time.desc()).limit(4).all()

    res =[]
    for each in activities:
        res.append(each.general_info_act_with_user)
        each.view_count += 1

    db.session.commit()
    # view_count = [(each.view_count+=1) for each in activitys]

    if len(activities) > 0:
        end = False
        early_time_stamp = activities[-1].create_time.timestamp()
    else:
        end = True
        early_time_stamp = datetime.datetime.now().timestamp()
    return jsonify(activities=res, earlyTimeStamp=int(early_time_stamp), end=end)


@app.route('/activitylist')
# @login_required
def get_activitylist():
    timestamp = request.args.get('timestamp')
    activity_type = request.args.get('activity_type')
    page = int(request.args.get('page','0'))
    orderby = request.args.get('orderby')
    if not orderby:

        if not timestamp:
            timestamp = datetime.datetime.now()
        else:
            timestamp = datetime.datetime.fromtimestamp(int(timestamp))
        if  activity_type=='综合':
            activities = Activities.query.filter(Activities.create_time < timestamp).order_by(
                Activities.create_time.desc()).limit(4).all()
        else:
            activities = Activities.query.filter(Activities.activity_type == activity_type,Activities.create_time < timestamp).order_by(Activities.create_time.desc()).limit(4).all()
    elif orderby=='发布时间':

        if not timestamp:
            timestamp = datetime.datetime.now()
        else:
            timestamp = datetime.datetime.fromtimestamp(int(timestamp))
        if activity_type=='综合':
            activities = Activities.query.order_by(
                Activities.create_time.desc()).offset(page*5).limit(5).all()
        else:
            activities = Activities.query.filter(Activities.activity_type == activity_type,
                                             Activities.create_time < timestamp).order_by(
            Activities.create_time.desc()).limit(4).all()
    elif orderby=='报名截至时间':
        if activity_type=='综合':
            activities = Activities.query.order_by(
                Activities.end_time.asc()).offset(page*5).limit(5).all()
            print(activities)
        else:
            activities = Activities.query.filter(Activities.activity_type == activity_type,
                                             ).order_by(
            Activities.end_time.asc()).offset(page * 5).limit(5).all()

    elif orderby == '活动开始时间':

        if activity_type=='综合':
            activities = Activities.query.order_by(
                Activities.start_time.asc()).offset(page*5).limit(5).all()
            print(activities)
        else:
            activities = Activities.query.filter(Activities.activity_type == activity_type,
                                             ).order_by(
            Activities.start_time.asc()).offset(page * 5).limit(5).all()

    res =[]
    for each in activities:
        res.append(each.general_info_act_with_user)
        each.view_count += 1

    db.session.commit()
    # view_count = [(each.view_count+=1) for each in activitys]


    if len(activities) > 0:
        end = False
        early_time_stamp = activities[-1].create_time.timestamp()
    else:
        end = True
        early_time_stamp = datetime.datetime.now().timestamp()
    return jsonify(activities=res, earlyTimeStamp=int(early_time_stamp), end=end)


@app.route('/contentact/<aid>')
@login_required
def get_activity_detail(aid):
    res = Activities.query.filter_by(aid=aid).first()

    if not res:
        abort(404)
    if res.end_time<datetime.datetime.now() or res.join_time>datetime.datetime.now():
        res_able=False
        res.reg_enable=False
        db.session.commit()
    else:
        res_able=True
    return jsonify(detail=res.detail_info_act_with_user,res_able=res_able)


@app.route('/commentAct/<aid>')
@login_required
def get_timeline_comment_act(aid):
    # res = activitys.query.filter_by(aid=aid).first().general_info_dict_with_user
    # if not res:
    #     abort(404)
    comments = ActivityComment.comments_dict_for_activity(aid)
    # res['comments'] = comments
    # return jsonify(res)
    return jsonify(comments=comments)


@app.route('/favAct', methods=['POST'])
@login_required
def add_fav_activity():
    uid = g.user.uid
    aid = request.form.get('aid')
    if not aid:
        abort(400)
    try:
        if not ActivityFav.query.filter_by(aid=aid, uid=uid).first():
            new_fav = ActivityFav(aid, uid)
            db.session.add(new_fav)
            activity = Activities.query.filter_by(aid=aid).first()
            activity.registered += 1
            db.session.commit()
        return jsonify(success=True)
    except IntegrityError:
        return jsonify(success=False)


@app.route('/unfavact', methods=['POST'])
@login_required
def remove_fav_activity():
    uid = g.user.uid
    aid = request.form.get('aid')
    if not aid:
        abort(400)
    try:
        fav = ActivityFav.query.filter_by(aid=aid, uid=uid).first()
        if fav:
            activity = Activities.query.filter_by(aid=aid).first()
            activity.registered -= 1
            db.session.delete(fav)
            db.session.commit()
        return jsonify(success=True)
    except IntegrityError:
        return jsonify(success=False)


@app.route('/favact_list')
@login_required
def get_favact_list():
    fav_list = ActivityFav.query.filter_by(uid=g.user.uid).all()
    fav_list_array = [each.aid for each in fav_list]
    return jsonify(data=fav_list_array)


@app.route('/favActivities_list')
@login_required
def get_favActivities_list():
    fav_list = ActivityFav.query.filter_by(uid=g.user.uid).all()
    res = []
    for each in fav_list:
        item = Activities.query.filter_by(aid=each.aid).first()
        res.append(item.general_info_act_with_user)

    return jsonify(data=res)


@app.route('/myActivities_list')
@login_required
def get_myActivities_list():
    Activities_list = Activities.query.filter_by(uid=g.user.uid).all()
    res = [each.general_info_dict_with_user for each in Activities_list]
    return jsonify(data=res)


@app.route('/otherActivities_list/<uid>')
@login_required
def get_otherActivities_list(uid):
    Activities_list = Activities.query.filter_by(uid=uid).all()
    res = [each.general_info_dict_with_user for each in Activities_list]
    return jsonify(data=res)


@app.route('/favPeoAct_list/<aid>')
@login_required
def get_favPeo_list_act(aid):
    fav_list = ActivityFav.query.filter_by(aid=aid).all()
    fav_list_array = [{"uid": each.uid,
                       "nickname": User.query.filter_by(uid=each.uid).first().nickname,
                       "avatar": User.query.filter_by(uid=each.uid).first().avatar,
                       } for each in fav_list]
    return jsonify(data=fav_list_array)


@app.route('/commentact', methods=['POST'])
@login_required
def add_comment_activity():
    uid = g.user.uid
    aid = request.form.get('aid')
    text = request.form.get('text')
    if not text:
        return jsonify(success=False,msg="评论不能为空")
    try:
        new_comment = ActivityComment(aid, uid, text)
        db.session.add(new_comment)
        activity = Activities.query.filter_by(aid=aid).first()
        activity.comment_count += 1
        db.session.commit()
    except IntegrityError:
        return jsonify(success=False)
    return jsonify(success=True)


# @app.route('/delete/<aid>', methods=['Activities'])
# @login_required
# def delete_activity(aid):
#     activity = Activities.query.filter_by(aid=aid).first()
#     file_key = activity.picture
#     if not activity or activity.uid != g.user.uid:
#         abort(401)
#     db.session.delete(activity)
#     db.session.commit()
#     delete_key(file_key)
#     return jsonify(success=True)