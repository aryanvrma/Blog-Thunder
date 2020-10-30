from flask import Flask,render_template,request,session,redirect,logging
from flask_mail import Mail
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.utils import secure_filename
import json
import math
import os


with open('config.json','r') as c:
    params=json.load(c)["params"]

local_server = True

app = Flask(__name__)
app.secret_key = 'super-secret-key'
app.config.update(
    MAIL_SERVER = 'smtp.gmail.com',
    MAIL_PORT = '465',
    MAIL_USE_SSL = True,
    MAIL_USERNAME = params['user-gmail'],
    MAIL_PASSWORD = params['user-password']
    )

app.config['UPLOAD_FOLDER'] = params['upload_location']

mail = Mail(app)

if (local_server):
    app.config['SQLALCHEMY_DATABASE_URI'] =  params['local_uri']
else:
    app.config['SQLALCHEMY_DATABASE_URI'] =  params['prod_uri']

db = SQLAlchemy(app)

class Contacts(db.Model):
    s_num = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80),  nullable=False)
    email = db.Column(db.String(20), nullable=False)
    phone_num = db.Column(db.String(12), nullable=False)
    msg = db.Column(db.String(12), nullable=True)
    date = db.Column(db.String(12), nullable=True)


class Posts(db.Model):
    s_num = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80),  nullable=False)
    slug = db.Column(db.String(21), nullable=False)
    content = db.Column(db.String(120),  nullable=False)
    img = db.Column(db.String(25), nullable=True)
    date = db.Column(db.String(12), nullable=True)
    subhead = db.Column(db.String(25), nullable=True)
class Register(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    gmail = db.Column(db.String(80), nullable=False)
    username = db.Column(db.String(80),  nullable=False)
    password =  db.Column(db.String(80),  nullable=False)


@app.route("/")
def home():

    posts=Posts.query.filter_by().all()
    last = math.ceil(len(posts)/int(params['post_index']))
    page = request.args.get('page')
    
    if  not (str(page).isnumeric()):
    
        page= 1
    page=int(page)
    posts = posts[(page-1)*int(params['post_index']):(page-1)*int(params['post_index'])+int(params['post_index'])]
    if (page==1):
        prev="#"
        next="/?page="+str(page+1)
    elif (page==last):
        prev="/?page="+str(page-1)
        next="#"
    else:
        prev="/?page="+str(page-1)
        next="/?page="+str(page+1)



    
    return render_template('home.html', params=params,posts=posts,prev=prev,next=next)




@app.route("/about")
def about():
    return render_template('about.html', params=params,posts=post)
    

@app.route("/dashboard", methods=['GET','POST'])
def dashboard():
    username=request.form.get('uname')
    userpass=request.form.get('pass')        
    user = Register(username)
    passw= Register(userpass)     
    if (username==user and password==passw):
        post = Posts.query.all()
        return render_template('dashboard.html',params=params,posts=post)


    if request.method == 'POST':
        username=request.form.get('uname')
        userpass=request.form.get('pass')        
        user = Register('username')
        passw= Register('passwrod')

        if ('user' in session and session['user']==params['admin_user']):

            post = Posts.query.all()
            return render_template('dashboard.html',params=params,posts=post)
    
    return render_template('index.html', params=params)


@app.route("/logout")
def logout():
    session.pop('user')
    return redirect('/dashboard')


@app.route("/contact", methods = ('GET','POST'))
def contact():
    if (request.method=='POST'):
        name = request.form.get('name')
        email = request.form.get('email')
        number = request.form.get('number')
        msg = request.form.get('msg')
        entry = Contacts(name = name , phone_num = number , msg = msg ,date=datetime.now(), email = email)
        db.session.add(entry)
        db.session.commit()
        mail.send_message('New message from ' + name,sender=email,recipients = [params['user-gmail']]+'/n', body= msg + number)


    return render_template('contact.html', params=params,posts=post)
@app.route("/post/<string:post_slug>",methods=['GET'])
def post(post_slug):
    post = Posts.query.filter_by(slug = post_slug).first()

    return render_template('post.html', params=params,posts=post)

@app.route("/edit/<string:s_num>", methods=['GET','post'])
def edit(s_num):

    if ('user' in session and session['user']==params['admin_user']):
        if request.method == 'POST':        
            title = request.form.get('title')
            tagline= request.form.get('tagline')
            slug= request.form.get('slug')
            content = request.form.get('content')
            img= request.form.get('img')
            if s_num=='0':
                post = Posts(title=title,subhead=tagline,slug=slug,content=content,img=img,date=datetime.now())
                db.session.add(post)
                db.session.commit()
            else:
                post=Posts.query.filter_by(s_num=s_num).first()
                post.title = title
                post.slug = slug
                post.subhead= tagline
                post.img=img
                post.content = content
                post.date = datetime.now()
                db.session.commit()
                return redirect('/edit/'+s_num)
    post= Posts.query.filter_by(s_num=s_num).first()           
    return render_template('edit.html',params=params,posts=post,s_num = s_num)
@app.route("/uploader", methods=['GET','POST'])
def uploader():
    if ('user' in session and session['user']==params['admin_user']):

        if request.method == 'POST':  
            f=request.files['file1']
            f.save(os.path.join(app.config['UPLOAD_FOLDER'] ,secure_filename(f.filename)))
        return "uploaded successfully"
        
@app.route("/delete/<string:s_num>", methods=['GET','post'])
def delete(s_num):

    if ('user' in session and session['user']==params['admin_user']):
        post=Posts.query.filter_by(s_num=s_num).first()
        db.session.delete(post)
        db.session.commit()

    return redirect('/dashboard')

@app.route("/register", methods=['GET','POST'])
def register():
    if (request.method == 'POST'):
        gmail = request.form.get('gmail')
        username = request.form.get('username')
        password = request.form.get('password')
        entry = Register(gmail=gmail,username=username,password=password)
        db.session.add(entry)
        db.session.commit()

    return render_template('register.html',Register=register,gmail=gmail)





app.run(debug=True)


