import datetime
import random
from flask import request, Flask, render_template, jsonify, redirect, session , flash
from spotipy.oauth2 import SpotifyClientCredentials
import spotipy
import spotipy.util as util
import os

from models import db ,connect_db, User , PlayedSong
from forms import LoginForm , Signupform
from datetime import timedelta
from flask_debugtoolbar import DebugToolbarExtension
from dotenv import load_dotenv

from flask_login import (
    login_user,
    LoginManager,
    current_user,
    logout_user,
    login_required,
)
load_dotenv()

login_manager = LoginManager()
login_manager.session_protection = "strong"
login_manager.login_view = "login"
login_manager.login_message_category = "info"

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL_') 
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = True
app.config["DEBUG_TB_INTERCEPT_REDIRECTS"] = False


connect_db(app)
db.create_all()

app.config['SECRET_KEY'] = os.getenv("SECRET_KEY")
client_id = os.getenv("Client_id")
client_secret = os.getenv("Client_secret") 
login_manager.init_app(app)
debug = DebugToolbarExtension(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.before_request
def session_handler():
    session.permanent = True
    app.permanent_session_lifetime = timedelta(minutes=1)


def getAllSongsDataFromSpotify():
    final_list = []
    client_credentials_manager = SpotifyClientCredentials(client_id=client_id,
                                                          client_secret=client_secret)
    sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)
    data = sp.user_playlists('spotify')

    Playlists = []
    for item in data['items']:
        Playlists.append(item['id'])

    playLists = Playlists
    count = 1

    for l in random.sample(playLists , 4):
        data = sp.playlist_tracks(playlist_id=l)['items']

        cat_song = []

        for row in data:
            try:
                cat_song.append({'name': row['track']['name'],
                             'artistname': row['track']['artists'][0]['name'],
                             'images': row['track']['album']['images']})
            except:
                pass

        final_list.append({'categoryName': f'category {count}', 'data': cat_song})
        count += 1
        
    return final_list


def getSearchResult(query):
    client_credentials_manager = SpotifyClientCredentials(client_id=client_id,
                                                          client_secret=client_secret)
    sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)
    search_result = sp.search(query)
    cat_song = []

    for data in search_result['tracks']['items']:
        try:
            artists = []
            for artist in data['artists']:
                artists.append(artist['name'])

            dic  = {'name': data['name'],
                         'artistname': ",".join(artists),
                         'images': data['album']['images']}

            cat_song.append(dic)

        except:
            pass


    return [{'categoryName': f'Search Result for {query}', 'data': cat_song}]


@app.route("/")
def homepage():
    """Show homepage."""

    if current_user.is_authenticated:
        data = getAllSongsDataFromSpotify()

        return render_template("index.html", songs=data , user=current_user)
    else:
        return redirect('/login')


@app.route("/login", methods=["GET", "POST"])
def login():
    """Show login page."""

    loginForm = LoginForm()

    if current_user.is_authenticated:
        return redirect('/')

    if request.method == 'POST':
        loginForm.email.data = request.form.get('email')
        loginForm.password.data = request.form.get('password')
        user = User.query.filter_by(email=loginForm.email.data).first()
        
        if user and user.password == loginForm.password.data:
            user.authenticated = True
            user.is_active = True
            login_user(user)
        else:
            flash('Email or password is incorrect' , "danger")

            return render_template("login.html", error="Email or password is wrong")

        flash('Login success', "success")

        return redirect('/')

    return render_template("login.html")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    """Show signup page."""

    signup_form = Signupform()

    if current_user.is_authenticated:
        return redirect('/')

    if request.method == 'POST':
        signup_form.username.data = request.form.get('username')
        signup_form.email.data = request.form.get('email')
        signup_form.password.data = request.form.get('password')
        signup_form.confirmPassword.data = request.form.get('confirm-password')

        data = User.query.filter_by(email=signup_form.email.data).first()
        if data:
            flash('Email already registered in data kindly provide another email', "danger")

            return render_template("signup.html", msg="Email already registered!")

        user = User()
        user.name = signup_form.username.data
        user.password = signup_form.password.data
        user.email = signup_form.email.data

        db.session.add(user)
        db.session.commit()

        flash('Signup Success Kindly Login', "success")

        return redirect('/login')

    return render_template("signup.html")


@app.route("/logout")
@login_required
def logout():
    """Show homepage."""

    logout_user()

    flash('Logout success', "success")

    return redirect('/login')


@app.route("/playlists")
def playlists():

    if current_user.is_authenticated:
        data = PlayedSong.query.filter_by(user_id=current_user.id).all()

        return render_template('playlist.html', data=data , user=current_user , count=len(data))
    else:
        return redirect('/login')


@app.route("/addToPlayList", methods=["GET", "POST"])
def addToPlayList():
    play_song = PlayedSong()

    if current_user.is_authenticated:
        play_song.song_name = request.form.get('name')
        play_song.url = request.form.get('url')
        play_song.time = "4:30"
        play_song.addedAt = str(datetime.date.today())
        play_song.user_id = current_user.id

        db.session.add(play_song)
        db.session.commit()

        flash('song added to Playlist successfully', "success")

        return redirect('/playlists')
    else:
        return redirect('/login')

@app.route("/playlists/<int:playlist_id>/delete")
def deleteById(playlist_id):
    if current_user.is_authenticated:
        data = PlayedSong.query.filter_by(id=playlist_id).one()

        db.session.delete(data)
        db.session.commit()

        flash('song remove from Playlist successfully', "success")
        
        return redirect("/playlists")
    else:
        return redirect('/login')


@app.route("/api/playlists", methods=["Get"])
def get_playlist():
    return (jsonify(data= getAllSongsDataFromSpotify()), 201)

@app.route("/search", methods=["GET", "POST"])
def search():
    if current_user.is_authenticated:
        if request.method == 'POST':
            query  = request.form.get('search')
            if len(query) > 0:
                data = getSearchResult(query=query)
                return render_template("index.html", songs=data , user=current_user)
            else:
                return redirect('/')
        else:
            return redirect('/')
    else:
        return redirect('/login')


@app.route("/api/search", methods=["Get"])
def search_spotify():
    query = request.args.get('query')
    if len(query) > 0:
        return (jsonify(data= getSearchResult(query=query)), 201)
    else:
        return (jsonify(data = []) , 201)

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

