from flask import Flask, render_template, redirect, url_for, request, session, flash, jsonify
from flask_pymongo import PyMongo
from flask_bcrypt import Bcrypt
from bson.objectid import ObjectId
from datetime import datetime
from copy_of_irwa_orginal import summarize_text, predict_sentiment_hf, extract_keywords, topic_modeling, fetch_text_from_url  # Adjust the import as necessary

app = Flask(__name__)
app.secret_key = 'J3wL9kzF7vYqXgH6!@$BzP9rT2lQmN'

import os
os.environ["TOKENIZERS_PARALLELISM"] = "false"

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
            max_length = int(request.form.get('max_length'))  # Get the max length input

            # Determine which input to process
            if user_input and not user_link:  # Ensure user_input is provided and user_link is empty
                input_val = user_input
                pval = 1  # Indicates text 
                input_type = 'Text'
            elif user_link and not user_input:  # Ensure user_link is provided and user_input is empty                 #
                input_val = user_link
                pval = 0  # Indicates link input
                input_type = 'Link'
            else:
                return jsonify({"error": "Invalid input."}), 400  # Handle error gracefully

            if not input_val.strip():
                return jsonify({"error": "No valid text provided."}), 400  # Handle error gracefully

            # Summarization
            pre_proccessed_txt, summary = summarize_text(input_val, max_length, pval)

            # Sentiment Analysis
            sentiment = predict_sentiment_hf(summary)
            print(f"sentiment :" ,sentiment)

            if isinstance(sentiment, tuple) and len(sentiment) == 2:
                sentiment_label = sentiment[0]  # The first element is the label
                sentiment_score = sentiment[1]   # The second element is the score
            else:
                sentiment_label = "No sentiment detected"
                sentiment_score = 0

            # Keyword Extraction
            keywords = extract_keywords(pre_proccessed_txt)

            # Topic Modeling
            topics = topic_modeling(pre_proccessed_txt)

            document = {
                'user_id': session['user_id'],
                'input_type': input_type,
                'input': input_val,
                'summary': summary,
                'sentiment': {
                    'label': sentiment_label,
                    'score': sentiment_score
                },
                'keywords': keywords,          
                'topics': topics,               
                'timestamp': datetime.now()     
            }

            # Insert the document into the MongoDB collection
            mongo.db.user_input_tble.insert_one(document)

            return jsonify({
                'summary': summary,
                'sentiment': f"{sentiment_label}: {sentiment_score}",
                'keywords': keywords,
                'topics': topics
            })
        
        return render_template('summerization.html')
    else:
        return redirect(url_for('login'))   

@app.route('/logout')
def logout():
    session.pop('username', None)
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))

@app.route('/get_user_inputs', methods=['GET'])
def get_user_inputs():
    if 'username' in session:
        # Fetch user inputs from MongoDB for the logged-in user
        user_id = session['user_id']
        user_inputs = mongo.db.user_input_tble.find({'user_id': user_id}).sort('timestamp', -1)  # Sorting by timestamp in descending order

        # Prepare a list of inputs to send as a response
        inputs = []
        for input_doc in user_inputs:
            input_data = {
                'input': input_doc['input'],
                'summary': input_doc['summary'],
                'sentiment': f"{input_doc['sentiment']['label']}: {input_doc['sentiment']['score']}",
                'keywords': input_doc['keywords'],
                'topics': input_doc['topics']
            }
            inputs.append(input_data)

        return jsonify({'inputs': inputs})

    else:
        return jsonify({'error': 'User not logged in.'}), 401

# Render history page with username
@app.route('/history')
def history():
    username = session.get('username')  # Assuming username is stored in session
    return render_template('history.html', username=username)

@app.errorhandler(404)
def not_found(error):
    return "Not Found", 404

if __name__ == '__main__':
    app.run(debug=True)