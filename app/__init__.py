from flask import Flask,render_template
from flask_mail import Mail
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from config import config
from flask_login import LoginManager
from flask_bootstrap import Bootstrap
from flask_pagedown import PageDown

bootstrap=Bootstrap()
mail = Mail()
moment = Moment()
db = SQLAlchemy()
pagedown=PageDown()

login_manager=LoginManager()
login_manager.session_protection='strong'
login_manager.login_view='auth.login'

def create_app():
    app=Flask(__name__)
    config_name='development'
    app.config.from_object(config[config_name])
    config[config_name].init_app()

    bootstrap.init_app(app)
    mail.init_app(app)
    moment.init_app(app)
    db.init_app(app)
    login_manager.init_app(app)
    pagedown.init_app(app)

    #蓝图
    from .main import main as main_blue#如果放在一开始话，这时候db换没有加载就会报错
    from .auth import auth as auth_blue
    app.register_blueprint(main_blue)
    app.register_blueprint(auth_blue,url_prefix='/auth')

    return app