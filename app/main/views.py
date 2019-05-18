from datetime import datetime
from flask import render_template,make_response,redirect,url_for,abort,flash,request
from flask_login import login_required,current_user
from ..decorators import permission_required,admin_required
from ..models import Permission,User,Role,Post
from . import main
from .forms import EditProfileForm,EditProfileAdminForm,PostForm
from .. import db
from flask import current_app


@main.route("/",methods=['GET','POST'])
def index():
    form=PostForm()
    if current_user.can(Permission.WRITE_ARTICLES) and \
        form.validate_on_submit():
        post=Post(body=form.body.data,
                  author=current_user._get_current_object())
        db.session.add(post)
        db.session.commit()
        return redirect(url_for('main.index'))
    posts=Post.query.order_by(Post.timestamp.desc()).all()
    
    show_followed=False
    if current_user.is_authenticated:
        show_followed=bool(request.cookies.get('show_followed',''))
    if show_followed:
        query=current_user.followed_posts
    else:
        query=Post.query
    
    page=request.args.get('page',1,type=int)
    pagination=query.order_by(Post.timestamp.desc()).paginate(
        page,per_page=current_app.config['FLASK_PER_PAGE'],
        error_out=False
    )
    posts=pagination.items
    return render_template('index.html',form=form,posts=posts,pagination=pagination,
                           show_followed=show_followed)

@main.route('/all')
@login_required
def show_all():
    resp=make_response(redirect(url_for('.index')))
    resp.set_cookie('show_followed','',max_age=30*24*60*60)
    return resp

@main.route('/followed')
@login_required
def show_followed():
    resp=make_response(redirect(url_for('.index')))
    resp.set_cookie('show_followed','1',max_age=30*24*60*60)
    return resp

@main.route('/admin')
@login_required
@admin_required
def for_admin_only():
    return "For administrators"

@main.route('/moderator')
@login_required
@permission_required(Permission.MODERATE_COMMITS)
def for_moderators_only():
    return "For moderators"

@main.route('/user/<username>')
def user(username):
    user=User.query.filter_by(username=username).first()
    if user is None:
        abort(404)
    posts=user.posts.order_by(Post.timestamp.desc()).all()
    return render_template('user.html',user=user,posts=posts)

@main.route('/edit-profile',methods=['GET','POST'])
@login_required
def edit_profile():
    form=EditProfileForm()
    if form.validate_on_submit():
        current_user.username=form.username.data
        current_user.location=form.location.data
        current_user.about_me=form.about_me.data
        db.session.add(current_user)
        flash("Your profile has been updated")
        return redirect(url_for('main.user',username=current_user.username))
    form.username.date=current_user.username
    # form.location.data=current_user.locationn
    # form.about_me.date=current_user.about_me
    return render_template('edit_profile.html',form=form)

@main.route('/edit-profile/<int:id>',methods=['GET','POST'])
@login_required
@admin_required
def edit_profile_admin(id):
    user=User.query.get_or_404(id)
    form=EditProfileAdminForm(user=user)
    if form.validate_on_submit():
        user.email=form.email.data
        user.username=form.username.data
        user.confirmed=form.confirmed.data
        user.role=Role.query.get(form.role.data)
        user.location=form.location.data
        user.about_me=form.about_me.data
        db.session.add(user)
        flash("profile has been updated")
        return redirect(url_for('main.user',username=user.username))
    return render_template('edit_profile.html',form=form,user=user)

@main.route('/post/<int:id>')
def post(id):
    post=Post.query.get_or_404(id)
    return render_template('post.html',posts=[post])

@main.route('/edit/<int:id>',methods=['GET','POST'])
@login_required
def edit(id):
    post=Post.query.get_or_404(id)
    if current_user!=post.author and \
        not current_user.can(Permission.ADMINISTER):
        abort(403)
    form=PostForm()
    if form.validate_on_submit():
        post.body=form.body.data
        db.session.add(post)
        flash("ths post has been updated")
        return redirect(url_for('main.post',id=post.id))
    form.body.data=post.body
    return render_template('edit_post.html',form=form)

@main.route('/follow/<username>')
@login_required
@permission_required(Permission.FOLLOE)
def follow(username):
    user=User.query.filter_by(username=username).first()
    if user is None:
        flash("Invalid user")
        return redirect(url_for('main.index'))
    if current_user.is_following(user):
        flash("You have already followed this user")
        return redirect(url_for('main.user',username=username))
    current_user.follow(user)
    flash('You following %s'%username)
    return redirect(url_for('main.user',username=username))

@main.route('/followers/<username>')
def followers(username):
    user=User.query.filter_by(username=username).first()
    if user is None:
        flash("Invalid user")
        return redirect(url_for('.index'))
    page=request.args.get('page',1,type=int)
    pagination=user.followers.pagination(
        page,per_page=1,error_out=False
    )
    follows=[{
        'user':item.follower,'timestamp':item.timestamp
    } for item in pagination.items]
    return render_template('followers.html',user=user,endpoint='.followers',pagination=pagination,
                           follows=follows)

@main.route('/followed_by')
@login_required
def followed_by(user):
    return 'followed_by'

@main.route('/unfollow')
@login_required
def unfollow(user):
    return 'unfollow'