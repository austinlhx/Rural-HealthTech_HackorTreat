import json
import os
import pprint

from pymongo import MongoClient
from diseaseclf.diseaseclf import DiseaseClassifier

from flask import Flask, redirect, request, url_for
from flask_login import (
    LoginManager,
    current_user,
    login_required,
    login_user,
    logout_user,
)
from flask_login import UserMixin
from flask import render_template
from flask_wtf import FlaskForm
from radar import RadarClient


from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired

from oauthlib.oauth2 import WebApplicationClient
import requests



GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", None)
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", None)
RADAR_SECRET_KEY = os.environ.get("RADAR_SECRET_KEY", None)
GOOGLE_DISCOVERY_URL = (
    "https://accounts.google.com/.well-known/openid-configuration"
)

radar = RadarClient(RADAR_SECRET_KEY)
app = Flask(__name__, template_folder='html')
app.secret_key = os.environ.get("SECRET_KEY") or os.urandom(24)

login_manager = LoginManager()
login_manager.init_app(app)

client = WebApplicationClient(GOOGLE_CLIENT_ID)
database_client = MongoClient("mongodb+srv://austinhx:helloworld@medicaldb.scqt4.mongodb.net/MedicalDB?retryWrites=true&w=majority")
#os.environ.get("MONGO_CLIENT", None))
database = database_client.User
user_database = database.user_info
doctor_database = database.doctor_info



#collection = database.test_collection

def get_google_provider_cfg():
    return requests.get(GOOGLE_DISCOVERY_URL).json()

@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)
    
@app.route("/")
def landing():
    return render_template('index.html')

@app.route("/dashboard", methods=['GET', 'POST'])
def index():
    if current_user.is_authenticated:
        user_info = user_database.find_one({'unique_id': current_user.id})
        user_history = user_info['history'] 
        return render_template('dashboard.html', user=current_user.name, history=user_history)
        #return( 
            # This is where the html for the form will go
            #"<p>Hello, {}! You're logged in! Email: {}</p>"
            #"<div>"
            #'<img src="{}" alt="Google profile pic"></img></div>'
            #'<a class="button" href="/logout">Logout</a>'.format(
            #    current_user.name, current_user.email, current_user.profile_pic
            #)
        #)
    else:
        return render_template('index.html')

@app.route("/login")
def login():
    google_provider_cfg = get_google_provider_cfg()
    authorization_endpoint = google_provider_cfg["authorization_endpoint"]
    request_uri = client.prepare_request_uri(
        authorization_endpoint,
        redirect_uri=request.base_url + "/callback",
        scope=["openid", "email", "profile"],
    )
    return redirect(request_uri)


class User(UserMixin):
    def __init__(self, id_, name, email, profile_pic):
        self.id = id_
        self.name = name
        self.email = email
        self.profile_pic = profile_pic

    @staticmethod
    def get(user_id):
        #user_id = unique_id
        try:
            user = user_database.find_one({'unique_id': user_id})
            user = User(
                id_=user['unique_id'], name=user['users_name'], email=user['users_email'], profile_pic=user['users_picture']
            )
        
            return user
        except:
            return None

    @staticmethod
    def create(id_, name, email, profile_pic):
        userdict = {
                "unique_id": id_,
                "users_name": name,
                "users_email": email,
                "users_picture": profile_pic,
                "history": [],
            }
        user_database.insert_one(userdict)
    
    
@app.route("/login/callback")
def callback():
    code = request.args.get("code")
    # Find out what URL to hit to get tokens that allow you to ask for
    # things on behalf of a user
    google_provider_cfg = get_google_provider_cfg()
    token_endpoint = google_provider_cfg["token_endpoint"]

    token_url, headers, body = client.prepare_token_request(
        token_endpoint,
        authorization_response=request.url,
        redirect_url=request.base_url,
        code=code
    )
    token_response = requests.post(
        token_url,
        headers=headers,
        data=body,
        auth=(GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET),
    )

    # Parse the tokens!
    client.parse_request_body_response(json.dumps(token_response.json()))

    userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
    uri, headers, body = client.add_token(userinfo_endpoint)
    userinfo_response = requests.get(uri, headers=headers, data=body)

    # You want to make sure their email is verified.
    # The user authenticated with Google, authorized your
    # app, and now you've verified their email through Google!
    if userinfo_response.json().get("email_verified"):
        unique_id = userinfo_response.json()["sub"]
        users_email = userinfo_response.json()["email"]
        picture = userinfo_response.json()["picture"]
        users_name = userinfo_response.json()["given_name"]
    else:
        return "User email not available or not verified by Google.", 400

    # Create a user in your db with the information provided
    # by Google
    user = User(
        id_=unique_id, name=users_name, email=users_email, profile_pic=picture
    )
        
    #pprint.pprint(user_database.find_one())
    



    # Begin user session by logging the user in
    login_user(user)

    # Send user back to homepage
    return redirect(url_for("index"))



class LoginForm(FlaskForm):
    name = StringField('Name', [DataRequired()])
    #Add more conditions
    submit = SubmitField('Submit')

@app.route('/form', methods=['GET', 'POST'])
@login_required
def symptomForm():
    
    form = LoginForm()
    
    
    if request.method == 'POST' and form.submit():

        print(form.name.data)
        print(request.remote_addr)
        print(current_user.id)
        
        '''age = form.age.data
        tempe = form.temperature.data
        fatig = form.fatigue.data
        sore = form.sore_throat.data
        eye = form.eye_color.data
        hache = form.headache.data
        cough = form.cough.data
        #send data to the db
        #Apply ML model here
        #send back nearest doctors within a certain radius, 
        #user_ip = request.remote_addr
        #ip_location = radar.geocode.ip(ip=user_ip)
        disease = DiseaseClassifier( [  age, tempe, fatig, sore, eye, hache, cough  ]  )
        disease_result = disease.predict(proba=False)'''

        query = {"unique_id": current_user.id}
        #this updates our history
        #TODO: Add disease result
        value = {"$push": {"history" : form.name.data}}
        user_database.update_one(query, value)
        ip_location = ('40.7832', '73.9700')

        all_doctors = doctor_database.find({})
        for doctor in all_doctors:
            longitude = doctor['longitude']
            latitude = doctor['latitude']
            location = (latitude, longitude)
            print(location)
            #routes = radar.route.distance(origin=ip_location, destination=location, modes="foot", units="metric")
            origin = (40.7041029, -73.98706)
            destination = (40.7141029, -73.99706)
            routes = radar.route.distance(origin, destination, modes="bike,foot")
            #radar.route.distance(origin=[lat,lng], destination=[lat,lng], modes=’car’, units=’metric’)
            print(routes.foot)


        return redirect('/dashboard')
    
    return render_template('form.html', form=form)
#longitude:73.9700, latitude: 40.7832

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(ssl_context="adhoc")