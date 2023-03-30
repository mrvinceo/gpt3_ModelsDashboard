# Python standard libraries
import json, os, sys, sqlite3, config, urllib.request, requests, openai, markdown

from gpt_index import SimpleDirectoryReader, GPTListIndex, GPTSimpleVectorIndex, LLMPredictor, PromptHelper
from langchain import OpenAI
from dotenv import load_dotenv
from os import environ

# Third party libraries
from flask import Flask, redirect, url_for, render_template, jsonify, request
from flask_login import (
    LoginManager,
    current_user,
    login_required,
    login_user,
    logout_user
)
from oauthlib.oauth2 import WebApplicationClient

# Local files
import aiapi
import gptguru

# Internal imports
#from db import init_db_command
from user import User

# Configuration - these are set at Gunicorn Initialisation, NOT via .env file.
GOOGLE_CLIENT_ID=os.environ.get("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET=os.environ.get("GOOGLE_CLIENT_SECRET")
GOOGLE_DISCOVERY_URL = (
    "https://accounts.google.com/.well-known/openid-configuration"
)

# Flask app setup
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY") or os.urandom(24)

# User session management setup
# https://flask-login.readthedocs.io/en/latest
login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.unauthorized_handler
def unauthorized():
    return "You must be logged in to access this content.", 403


# Database setup - run outside of Gunicorn then comment out for prod
#try:
#    init_db_command()
#except sqlite3.OperationalError:
    # Assume it's already been created
#    pass

# OAuth2 client setup
client = WebApplicationClient(GOOGLE_CLIENT_ID)

# Flask-Login helper to retrieve a user from our db
@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)

@app.route("/", methods = ['POST','GET'])
def index():
    if current_user.is_authenticated:
        profile=current_user.profile_pic
        name=current_user.name
        if request.method == 'POST':
            prompt = request.form['prompt']
            res = {}
            res['answer'] = aiapi.generateChatResponse(prompt)
            res['answer'] = markdown.markdown(res['answer'], extensions=['fenced_code'])
            
            return jsonify(res), 200

        return render_template('index.html', **locals())
    else:
        return render_template('loggedout.html')
        #return '<a class="button" href="/login">OCA Google Login</a>'


@app.route("/dalle", methods = ['POST','GET'])
def dalle():
    if current_user.is_authenticated:
        profile=current_user.profile_pic
        imgprompt = ''
        name=current_user.name
        if request.method == 'POST':
            imgprompt = request.form['imgprompt']
            res = {}
            res['file'] = aiapi.generateImageResponse(imgprompt)
            return jsonify(res), 200
        return render_template('dalle.html', **locals())
    else:
        return render_template('loggedout.html')
        #return '<a class="button" href="/login">OCA Google Login</a>'


@app.route("/guru", methods = ['POST','GET'])
def guru():
    if current_user.is_authenticated:
        profile=current_user.profile_pic
        query = ''
        name=current_user.name
        if request.method == 'POST':
            query = request.form['query']
            res = {}
            res['answer'] = gptguru.chatbot(query)
            return jsonify(res), 200
        return render_template('guru.html', **locals())
    else:
        return render_template('loggedout.html')
        #return '<a class="button" href="/login">OCA Google Login</a>'


@app.route("/login")
def login():
    # Find out what URL to be used for  Google login
    google_provider_cfg = get_google_provider_cfg()
    authorization_endpoint = google_provider_cfg["authorization_endpoint"]

    # Use library to construct the request for login and provide
    # scopes that let you retrieve user's profile from Google
    request_uri = client.prepare_request_uri(
        authorization_endpoint,
        redirect_uri=request.base_url + "/callback",
        scope=["openid", "email", "profile"],
    )
    print(request.base_url + "/callback")
    return redirect(request_uri)

@app.route("/login/callback")
def callback():
    # Get authorization code Google sent back to you
    code = request.args.get("code")

    # Find out what URL to hit to get tokens that allow you to ask for
    # things on behalf of a user
    google_provider_cfg = get_google_provider_cfg()
    token_endpoint = google_provider_cfg["token_endpoint"]

    # Prepare and send request to get tokens! Yay tokens!
    token_url, headers, body = client.prepare_token_request(
        token_endpoint,
        authorization_response=request.url,
        redirect_url=request.base_url,
        code=code,
    )
    token_response = requests.post(
        token_url,
        headers=headers,
        data=body,
        auth=(GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET),
    )

    # Parse them tokens!
    client.parse_request_body_response(json.dumps(token_response.json()))

    # We now have tokens, ready to use to get our user, 
    # including their Google Profile Image and Email
    userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
    uri, headers, body = client.add_token(userinfo_endpoint)
    userinfo_response = requests.get(uri, headers=headers, data=body)
    print(userinfo_response.json())

    # We want to make sure their email is verified.
    # The user authenticated with Google, authorized our
    # app, and now we've verified their email through Google!
    if userinfo_response.json().get("email_verified"):
        unique_id = userinfo_response.json()["sub"]
        users_email = userinfo_response.json()["email"]
        picture = userinfo_response.json()["picture"]
        users_name = userinfo_response.json()["given_name"]
    else:
        return "User email not available or not verified by Google.", 400

    # Create a user in our db with the information provided
    # by Google
    user = User(
        id_=unique_id, name=users_name, email=users_email, profile_pic=picture
    )

    # Doesn't exist? Add to database
    if not User.get(unique_id):
        User.create(unique_id, users_name, users_email, picture)

    # Begin user session by logging the user in
    login_user(user)

    # Send user back to homepage
    return redirect(url_for("index"))


def get_google_provider_cfg():
    return requests.get(GOOGLE_DISCOVERY_URL).json()

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("index"))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port='5000')
