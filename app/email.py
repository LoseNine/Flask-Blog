from flask_mail import Message
from . import mail
from threading import Thread
from . import create_app
from flask import render_template
app=create_app()

def send_sync(app,msg):
    with app.app_context():
        mail.send(msg)

def send_mail(to,subject,template,**kwargs):
    msg=Message(subject,sender=app.config['MAIL_USERNAME'],recipients=[to])
    msg.body=render_template(template+'.txt',**kwargs)
    msg.html=render_template(template+'.html',**kwargs)

    t=Thread(target=send_sync,args=(app,msg))
    t.start()
    return t