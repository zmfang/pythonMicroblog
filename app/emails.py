from flask.ext.mail import Message
from app import mail
from flask import render_template
from config import ADMINS
from threading import Thread
from app import app
from .decorators import async


# 创建一个 app_context 来发送邮件。
# Flask-Mail 最近的版本需要这个。当 Flask 处理请求的时候，应用内容就被自动地创建
@async
def send_async_email(app, msg):
    with app.app_context():
        mail.send(msg)


def send_mail(subject, sender, recipients, text_body, html_body):
    msg = Message(subject, sender=sender, recipients=recipients)
    msg.body = text_body
    msg.html = html_body
    send_async_email(app, msg)


def follower_notification(followed, follower):
    send_mail("[Microblog] %s is now following you !" % follower.nickname,
              sender=ADMINS[0],
              recipients=[followed.email],
              text_body=render_template("follower_email.txt",
                                        user=followed, follower=follower
                                        ),
              html_body=render_template("follower_email.html",
                                        user=followed, follower=follower
                                        )
              )

