from flask import render_template,redirect,url_for,flash,request
from . import auth
from .forms import LoginForm,RegisterForm
from ..models import User
from flask_login import login_user,login_required,logout_user
from ..email import send_mail
from flask_login import current_user
from ..decorators import admin_required
from .. import db

@auth.route("/login",methods=['GET','POST'])
def login():
    form=LoginForm()
    if form.validate_on_submit():
        user=User.query.filter_by(email=form.email.data).first()
        if user:
            login_user(user,form.remember_me.data)
            return redirect(url_for('main.index'))
        else:
            flash("Invalid username or password")
    return render_template('login.html',form=form,title='Login')

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash("You have been log out")
    return redirect(url_for('main.index'))

@auth.route('/register',methods=['GET','POST'])
def register():
    form=RegisterForm()
    user=User()
    print('resgister')
    if form.validate_on_submit():
        print('submit')
        email=form.email.data
        username=form.username.data
        password=form.password.data
        user=User(email=email,username=username,password=password)
        db.session.add(user)
        db.session.commit()
        token=user.generate_confirmation_token()
        send_mail(email,'confirm your account','email/confirm',user=username,
                  token=token)
        flash("A confirm has been send to you mail")
        return redirect(url_for('main.index'))
    print('no submit')
    return render_template('login.html',form=form,title='Register')

@auth.route('/confirm/<token>')
@login_required
def confirm(token):
    if current_user.confirmed:
        return redirect(url_for('main.index'))
    if current_user.confirm(token):
        flash("You have confirmed your account")
    else:
        flash("The confirmation link is invaild or expired")
    return redirect(url_for('main.index'))

@auth.before_app_request
def before_request():
    if current_user.is_authenticated:
        current_user.ping()

    if current_user.is_authenticated\
        and not current_user.confirmed \
        and request.endpoint[:4] !='auth'\
        and request.endpoint !='static':
        return redirect(url_for('auth.unconfirmed'))

@auth.route('/unconfirmed')
def unconfirmed():
    if current_user.is_anonymous or current_user.confirmed:
        return redirect(url_for('main.index'))

    return render_template('unconfirmed.html')

@auth.route('/confirm')
@login_required
def resend_confirmation():
    token=current_user.generate_confirmation_token()
    send_mail(current_user.email,'Confirm your ccount',
              'email/confirm',token=token,user=current_user.username)
    return "ok"

