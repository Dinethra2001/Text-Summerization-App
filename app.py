from flask import Flask, render_template, redirect, url_for, request, session, flash
from flask_pymongo import PyMongo
from flask_bcrypt import Bcrypt
from bson.objectid import ObjectId

app = Flask(__name__)
app.secret_key = 'J3wL9kzF7vYqXgH6!@$BzP9rT2lQmN'

# MongoDB configuration
app.config['MONGO_URI'] = "mongodb+srv://IRWA:Irwa%40123@cluster1.71el3.mongodb.net/Text_Summarization"  
mongo = PyMongo(app)
bcrypt = Bcrypt(app)

# Collection (table) reference
users = mongo.db.signup

@app.route('/')
def home():
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        # Password validation
        if password != confirm_password:
            flash('Passwords do not match', 'danger')
            return redirect(url_for('signup'))

        # Hash the password
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        # Insert user into MongoDB
        users.insert_one({
            'username': username,
            'email': email,
            'password': hashed_password
        })

        flash('Account created successfully! You can log in now.', 'success')
        return redirect(url_for('login'))

    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = users.find_one({'email': email})

        # Check if user exists and password is correct
        if user and bcrypt.check_password_hash(user['password'], password):
            session['username'] = user['username']
            flash(f'Welcome back, {user["username"]}!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid login credentials', 'danger')
            return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'username' in session:
        return f"Hello, {session['username']}! Welcome to your dashboard."
    else:
        return redirect(url_for('login'))

@app.route('/logout')
def logout():
    session.pop('username', None)
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
