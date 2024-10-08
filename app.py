from flask import Flask, render_template, redirect, url_for, request, session, flash, jsonify
from flask_pymongo import PyMongo
from flask_bcrypt import Bcrypt
from bson.objectid import ObjectId
from datetime import datetime


app = Flask(__name__)
app.secret_key = 'J3wL9kzF7vYqXgH6!@$BzP9rT2lQmN'

# MongoDB configuration
app.config['MONGO_URI'] = "mongodb+srv://IRWA:Irwa%40123@cluster0.mgts3.mongodb.net/Text_Summarization"  
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
        user_id = users.insert_one({
            'username': username,
            'email': email,
            'password': hashed_password
        }).inserted_id  # Get the user ID

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
            session['user_id'] = str(user['_id'])  # Store user ID in session
            flash(f'Welcome back, {user["username"]}!', 'success')
            return redirect(url_for('summarize'))
        else:
            flash('Invalid login credentials', 'danger')
            return redirect(url_for('login'))

    return render_template('login.html')


@app.route('/summarize', methods=['GET', 'POST'])
def summarize():
    if 'username' in session:
        if request.method == 'POST':
            user_input = request.form.get('user_input')  # Get the text input
            user_link = request.form.get('user_link')    # Get the link input
            
            # Check which input was provided and save accordingly
            if user_input:
                mongo.db.user_inputs.insert_one({
                    'user_id': session['user_id'],  # Save user ID
                    'input_type': 'text',
                    'input_value': user_input
                })
            elif user_link:
                mongo.db.user_inputs.insert_one({
                    'user_id': session['user_id'],  # Save user ID
                    'input_type': 'link',
                    'input_value': user_link
                })

            flash('Input saved successfully!', 'success')
            return render_template('summerization.html')

        return render_template('summerization.html')
    else:
        return redirect(url_for('login'))




@app.route('/logout')
def logout():
    session.pop('username', None)
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))

    
# Route to fetch user inputs
@app.route('/get_user_inputs', methods=['GET'])
def get_user_inputs():
    user_id = session.get('user_id')  # Assuming you store user_id in session after login
    if user_id:
        # Retrieve input values without the date
        inputs = list(mongo.db.user_inputs.find({"user_id": user_id}, {"_id": 0, "input_value": 1, "input_type": 1}))
        return jsonify({'inputs': [{'input_value': input['input_value'], 'input_type': input['input_type']} for input in inputs]})
    return jsonify({'inputs': []})


    
@app.route('/history')
def history():
    if 'user_id' in session:
        user_id = session['user_id']
        user_summaries = mongo.db.summaries.find({'user_id': ObjectId(user_id)})
        return render_template('history.html', summaries=user_summaries)
    else:
        flash('You must be logged in to view history.')
        return redirect(url_for('login'))

@app.errorhandler(404)
def not_found(error):
    return "Not Found", 404

if __name__ == '__main__':
    app.run(debug=True)