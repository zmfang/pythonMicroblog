from flask import Blueprint, jsonify, request, g, abort
from app import app, db, lm
import time
from ..models import User, login_required, Activities
from ..models import Post, FeedsComment, FeedsFav
from sqlalchemy.exc import IntegrityError
# from .qiniuApi import delete_key
import datetime
import uuid

# app = Blueprint('feedsApi', __name__)


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


@app.route('/activitylist')
# @login_required
def get_activitylist():
    timestamp = request.args.get('timestamp')
    activity_type = request.args.get('activity_type')
    if not timestamp:
        timestamp = datetime.datetime.now()
    else:
        timestamp = datetime.datetime.fromtimestamp(int(timestamp))

    activities = Activities.query.filter(Activities.activity_type==activity_type,Activities.create_time < timestamp).order_by(Activities.start_time.desc()).limit(10).all()

    res =[]
    for each in activities:
        res.append(each.general_info_act_with_user)
        each.view_count += 1

    db.session.commit()
    # view_count = [(each.view_count+=1) for each in feeds]
    datetime.datetime.now().timestamp()

    if len(activities) > 0:
        end = False
        early_time_stamp = activities[-1].create_time.timestamp()
    else:
        end = True
        early_time_stamp = datetime.datetime.now().timestamp()
    return jsonify(activities=res, earlyTimeStamp=int(early_time_stamp), end=end)
