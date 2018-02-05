from flask.ext.mail import Message
from app import mail
from flask import render_template
from config import ADMINS, MAIL_USERNAME


def send_mail(subject, sender, recipients, text_body, html_body):
    msg = Message(subject, sender=sender, recipients=recipients)
    msg.body = text_body
    msg.html = html_body
    mail.send(msg)


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

