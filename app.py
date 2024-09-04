import math
from flask import Flask ,render_template ,redirect ,request ,flash ,url_for ,session
from flask_pymongo import PyMongo
from flask_bcrypt import Bcrypt 
from werkzeug.utils import secure_filename
from functools import wraps
import os 
import random
import datetime







app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = "A:\Programs\Post\static\images"
app.config["MONGO_URI"] = "mongodb://localhost:27017/og_gram"
mongo = PyMongo(app)
bcrypt = Bcrypt(app)


def login_required(f):
    @wraps(f)
    def decorated_function(*args,**kwargs):
        if "email" in session:
            return f(*args,**kwargs)
        else:
            flash("You have to login first","warning")
            return redirect(url_for('login'))
    return decorated_function


@app.route('/')
def home():
    return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.method == 'POST':
            email= request.form['email']
            password= request.form['password']
            found_user = mongo.db.users.find_one({'email':email})
            if found_user:
                if bcrypt.check_password_hash(found_user['password'], password):
                    session['is_logged_in'] = True
                    session['email'] = found_user['email']
                    session['fname'] = found_user['fname']
                    session['lname'] = found_user['lname']
                    session['pro_pic'] = found_user['pro_pic']
                    
                    flash('You were successfully logged in','success')
                    return redirect(url_for('home'))
                else:
                    flash('Incorrect password, please try again!','danger')
                    print("incorrect password")
                    return redirect(url_for('login'))
            else:
                print("user not found")
                flash('User not found!, create an account','danger')
                return redirect(url_for('signup'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out outsuccessfully!','success')
    return redirect(url_for('login'))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        pw_hash = bcrypt.generate_password_hash(request.form['password'])
        file= request.files['pro_pic']
        filename = secure_filename(file.filename) 
        file.save(os.path.join(app.config['UPLOAD_FOLDER'],filename))
        user = {
        'fname':request.form['fname'],
        'lname':request.form['lname'],
        'email':request.form['email'],
        'password':pw_hash,
        'pro_pic':'images/'+filename
        }
        done = mongo.db.users.insert_one(user)
        if done.acknowledged:
            flash('Account  created successfully','success')
            return redirect(url_for('login'))
        else:
            print("Something went Wrong ...")

    return render_template('signup.html')


@app.route('/post')
def post():
    page = request.args.get('page')
    if page and page.isdigit():
        page=int(page)
    else:
        page=0

    
    total_count = mongo.db.posts.count_documents({})
    limit = 6 if total_count % 2 == 0 else 9 
    skip=page*limit
    posts_cursor = mongo.db.posts.find().limit(limit).skip(skip)
    posts_list= list(posts_cursor)
    # records_cursor = mongo.db.posts.find()
    # records_list=list(records_cursor)
    # length =len(records_list)
    print(total_count)
    print(limit)
    pages = math.floor(total_count/limit)
    return render_template('post.html', posts=posts_list,pages=pages)


@app.route('/dashboard')
@login_required
def dashboard():
    posts_cursor = mongo.db.posts.find({'owner.email':session['email']})
    posts_list= list(posts_cursor)
    return render_template('dashboard.html', posts = posts_list)


@app.route('/profile', methods = ['POST','GET'])
@login_required 
def profile():
    if request.method == 'POST':
        mongo.db.users.update_one({'email': session['email']},{'$set':{
            'fname':request.form['fname'],
            'lname':request.form['lname'],
            'email':request.form['email']
            }})
        session['fname'] = request.form['fname']
        session['lname'] = request.form['lname']
        session['email'] = request.form['email']
        flash("Updated profile successfully","success")
    return render_template('profile.html')



@app.route('/update_picture', methods=['GET', 'POST'])
@login_required 
def update_picture():
   if request.method == "POST":
        if 'pro_pic'  not in request.files:
            flash("Select an Image","warning")
            return redirect(request.url)
        
        file= request.files['pro_pic']
        filename = secure_filename(file.filename) 
        file.save(os.path.join(app.config['UPLOAD_FOLDER'],filename))
        mongo.db.users.update_one({'email':session['email']},{'$set':{
            'pro_pic':'images/'+filename
        }})
        session['pro_pic']= 'images/'+filename
        flash("Upload Successful","success")

        return redirect(url_for('profile'))
            

@app.route('/add_post', methods=['GET', 'POST'])
@login_required 
def add_post():
    if request.method == "POST":
        title = request.form['title']
        content = request.form['content']
        description = request.form['des']
        file = request.files['post']
        filename = secure_filename(file.filename) 
        file.save(os.path.join(app.config['UPLOAD_FOLDER'],filename))
        session['post']= 'images/'+filename
        mongo.db.posts.insert_one({
            'title':title,
            'content':content,
            'description':description,
            'post':session['post'],
            'post_id':random.randint(1111,9999),
            'created_at':datetime.datetime.now(),
            'owner':{
                'name':session['fname']+' '+ session['lname'],
                'email':session['email'],
                'pro_pic':session['pro_pic']
            }
        })

    flash('Posted','success')
    return render_template('add_post.html')

@app.route('/edit_post/<int:post_id>', methods=['GET', 'POST'])
@login_required 
def edit_post(post_id):
   
    post = mongo.db.posts.find_one({'post_id':post_id , 'owner.email':session['email']})
    if post is None:
        flash("Post not found , Not Allowed!", "warning")
        return redirect(url_for('dashboard'))

    if request.method == "POST":
        file = request.files['post']
        filename = secure_filename(file.filename) 
        file.save(os.path.join(app.config['UPLOAD_FOLDER'],filename))
        mongo.db.posts.update_one({'post_id':post_id} , {'$set':{'title':request.form['title'], 
                                                                 'content':request.form['content'],
                                                                 'description':request.form['des'],
                                                                 'post':'images/'+filename}} ,upsert = False)
        flash("Post updated successfully","success")
        return redirect(url_for("edit_post",post_id = post_id))
    return render_template('edit_post.html',post=post)


@app.route('/delete/<int:post_id>', methods=['GET','POST'])
@login_required 
def delete_post(post_id):
    mongo.db.posts.delete_one({'post_id': post_id , 'owner.email':session['email']})
    flash("Post deleted successfully", "success")
    return redirect(url_for('dashboard'))


@app.route('/view_post/<int:post_id>')
@login_required
def view_post(post_id):
    found_post = mongo.db.posts.find_one({'post_id':post_id})
    return render_template("view_post.html",post=found_post)


@app.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == "POST":
        search_query = request.form['search_query']
        search_result = mongo.db.posts.find({'$text':{'$search': search_query}})

    return render_template('search.html',search_results=search_result, search_query=search_query)

if __name__ == '__main__':
    app.secret_key = "super secret key"
    app.run(debug=True)