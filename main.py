import os
from flask import Flask, render_template, redirect, url_for, flash,request,abort
from flask_bootstrap import Bootstrap
from flask_ckeditor import CKEditor
from datetime import date
from werkzeug.security import generate_password_hash, check_password_hash
from flask_ckeditor import CKEditor,CKEditorField
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from wtforms import StringField, SubmitField,validators,PasswordField
from wtforms.validators import DataRequired, URL,Email
from forms import CreatePostForm,FlaskForm
import werkzeug.security
from functools import wraps
from sqlalchemy import Table, Column, Integer, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


from flask_gravatar import Gravatar

app = Flask(__name__)

app.config['SECRET_KEY']=os.environ.get("SECRET_KEY")



ckeditor = CKEditor(app)
Bootstrap(app)
login_manager = LoginManager()
login_manager.init_app(app)

##CONNECT TO DB

app.config['SQLALCHEMY_DATABASE_URI'] =os.environ.get("DATABASE_URL","sqlite:///blog.db")


app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
gravatar = Gravatar(app,
                    size=100,
                    rating='g',
                    default='retro',
                    force_default=False,
                    force_lower=False,
                    use_ssl=False,
                    base_url=None)

class RegisterForm(FlaskForm):
    name= StringField('name',validators=[DataRequired()])
    email=StringField('email',validators=[DataRequired(),Email()])
    password=PasswordField('password',validators=[DataRequired()])
    submit=SubmitField('submit')
class LoginForm(FlaskForm):
    email=StringField('Email',validators=[DataRequired(),Email()])
    password=PasswordField('Password',validators=[DataRequired()])
    submit=SubmitField('Submit')
class CommentForm(FlaskForm):
    comment= CKEditorField('Comment',validators=[DataRequired()])
    submit=SubmitField('Submit')
##CONFIGURE TABLES
class User(db.Model,UserMixin):
    __tablename__ = "user"
    id= db.Column(db.Integer, primary_key=True)

    email= db.Column(db.String(250),nullable=False,unique=True)
    password= db.Column(db.String(250),nullable=False)
    name = db.Column(db.String(250), nullable=False)
    posts=relationship('BlogPost',back_populates='author')
    comments= relationship('Comment',back_populates='comment_author')








class BlogPost(db.Model,UserMixin):
    __tablename__ = "blog_posts"
    id = db.Column(db.Integer, primary_key=True)
    parent_id = Column(db.Integer, ForeignKey('user.name'))
    author = relationship("User", back_populates="posts")
    title = db.Column(db.String(250), unique=True, nullable=False)
    subtitle = db.Column(db.String(250), nullable=False)
    date = db.Column(db.String(250), nullable=False)
    body = db.Column(db.Text, nullable=False)
    img_url = db.Column(db.String(250), nullable=False)

class Comment(db.Model,UserMixin):
    __tablename__="comments"
    id = db.Column(db.Integer, primary_key=True)
    author_name = db.Column(db.Integer, db.ForeignKey("user.name"))
    comment_author = relationship("User", back_populates="comments")
    text = db.Column(db.Text, nullable=False)












def admin_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.email!='giovannirainolfi@gmail.com':
            return abort(403)

        return f(*args, **kwargs)
    return decorated_function

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)


@app.route('/')
def get_all_posts():
    posts = BlogPost.query.all()
    alpha=current_user.is_authenticated
    try:
        if current_user.email=='giovannirainolfi@gmail.com':
            is_admin=True
        else:
            is_admin=False
    except:
        return render_template("index.html", all_posts=posts, alpha=alpha)

    return render_template("index.html", all_posts=posts,alpha=alpha,is_admin=is_admin)



@app.route('/register',methods=['POST','GET'])
def register():
    form= RegisterForm()
    all_user=User.query.all()
    if request.method=='POST':
        name=form.name.data
        email=form.email.data
        password = form.password.data
        for x  in all_user:
            if x.email==email:
                flash('you already register with this email,please log in instead!')
                return  redirect(url_for('login'))

        new_user = User(name=name, email=email,
                        password=werkzeug.security.generate_password_hash(password, method='pbkdf2:sha256',
                                                                          salt_length=8))
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return redirect(url_for('get_all_posts'))




    return render_template("register.html",form=form)


@app.route('/login',methods=['POST','GET'])
def login():
    form=LoginForm()

    if form.validate_on_submit():
        email=form.email.data
        password=form.password.data
        user_data=User.query.filter_by(email=email).first()

        if user_data:


            if werkzeug.security.check_password_hash(pwhash=user_data.password,password=password):
                login_user(user_data)
                return redirect(url_for('get_all_posts'))


            else:
                flash('the password is incorrect')
                return redirect(url_for('login'))
        else:
            flash('the email does not exist')
            return redirect(url_for('login'))


    return render_template("login.html",form=form)



@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('get_all_posts'))


@app.route("/post/<int:post_id>",methods=['GET','POST'])

def show_post(post_id):
    form=CommentForm()
    requested_post = BlogPost.query.get(post_id)
    all_comment=Comment.query.all()
    if current_user.is_authenticated:
        if current_user.email == 'giovannirainolfi@gmail.com':
            is_admin = True
        else:
            is_admin = False

        if form.validate_on_submit():
                new_comment = Comment( text=form.comment.data,
            author_name =current_user.name,


            )



                db.session.add(new_comment)
                db.session.commit()
                return render_template("post.html", post=requested_post, form=form,
                                       all_comments=all_comment,is_admin=is_admin)
    else:
        flash('you must log  in to comment !')
        return redirect(url_for('login'))

    return render_template("post.html", post=requested_post, form=form,
                           all_comments=all_comment, is_admin=is_admin)






@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/contact")
def contact():
    return render_template("contact.html")


@app.route("/new-post",methods=['POST','GET'])
@admin_only
def add_new_post():
    form = CreatePostForm()
    if form.validate_on_submit():
        new_post = BlogPost(
            title=form.title.data,
            subtitle=form.subtitle.data,
            body=form.body.data,
            img_url=form.img_url.data,
            author=current_user,
            date=date.today().strftime("%B %d, %Y")
        )
        db.session.add(new_post)
        db.session.commit()
        print(current_user.email)
        return redirect(url_for("get_all_posts"))
    return render_template("make-post.html", form=form, alpha=current_user.is_authenticated)


@app.route("/edit-post/<int:post_id>")
@admin_only
def edit_post(post_id):
    post = BlogPost.query.get(post_id)
    edit_form = CreatePostForm(
        title=post.title,
        subtitle=post.subtitle,
        img_url=post.img_url,
        author=post.author,
        body=post.body
    )
    if edit_form.validate_on_submit():
        post.title = edit_form.title.data
        post.subtitle = edit_form.subtitle.data
        post.img_url = edit_form.img_url.data
        post.author = edit_form.author.data
        post.body = edit_form.body.data
        db.session.commit()
        return redirect(url_for("show_post", post_id=post.id))

    return render_template("make-post.html", form=edit_form)


@app.route("/delete/<int:post_id>")
@admin_only
def delete_post(post_id):
    post_to_delete = BlogPost.query.get(post_id)
    db.session.delete(post_to_delete)
    db.session.commit()
    return redirect(url_for('get_all_posts'))


if __name__ == "__main__":
    app.run(host='0.0.0.0',port=5000)

