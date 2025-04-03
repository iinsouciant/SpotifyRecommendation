from dotenv import load_dotenv
import os

import base64

import requests
from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth
from spotipy.cache_handler import FlaskSessionCacheHandler

# for webapps, microframework
import flask

# https://www.youtube.com/watch?v=2if5xSaZJlg for getting user playlists
# need to use authorization code flow to allow user to log in once and refresh token https://spotipy.readthedocs.io/en/2.25.1/#authorization-code-flow
# flasksessioncachehandler

# scopes of app https://developer.spotify.com/documentation/web-api/concepts/scopes
SCOPES = [
    "playlist-read-private",
    "playlist-read-collaborative",
    "playlist-modify-private",
    "playlist-modify-public",
    "user-library-read",
]


def getEncodedSKey() -> bytes:
    load_dotenv()
    return base64.b64encode(os.getenv("SECRET_KEY").encode())


def getOAuth(cache_handler) -> SpotifyOAuth:
    # Create authentication manager for API with Authorization Code Flow
    load_dotenv()
    REDIRECT: str = "http://127.0.0.1:5000/callback"
    auth = SpotifyOAuth(
        scope=SCOPES,
        client_id=os.getenv("CLIENT_ID"),
        client_secret=os.getenv("CLIENT_SECRET"),
        redirect_uri=REDIRECT,
        cache_handler=cache_handler,
        show_dialog=True,
    )

    return auth


app = flask.Flask(__name__)
# store user access token in app session
app.config["SECRET_KEY"] = getEncodedSKey().decode()
cache_handler = FlaskSessionCacheHandler(flask.session)
sp_oauth = getOAuth(cache_handler)
sp = Spotify(auth_manager=sp_oauth)


# first endpoint. want user to see this when they access
@app.route("/")
def home():
    # is_valid_token()
    if not sp_oauth.validate_token(cache_handler.get_cached_token()):
        auth_url = sp_oauth.get_authorize_url()
        return flask.redirect(auth_url)
    # if valid, redirect to endpoint for method get_playlists
    return flask.redirect(flask.url_for("get_playlists"))


@app.route("/callback")
def callback():
    # get 'code' once the authorization is done to store access token in authentication manager
    sp_oauth.get_access_token(flask.request.args["code"])
    return flask.redirect(flask.url_for("get_playlists"))


@app.route("/get_playlists")
def get_playlists():
    # make sure token is still valid
    if not sp_oauth.validate_token(cache_handler.get_cached_token()):
        auth_url = sp_oauth.get_authorize_url()
        return flask.redirect(auth_url)

    playlists = sp.current_user_playlists()

    playlists_info = [
        (pl["name"], pl["external_urls"]["spotify"]) for pl in playlists["items"]
    ]
    playlists_html = "<br>".join([f"{name}: {url}" for name, url in playlists_info])

    return playlists_html


@app.route("/logout")
def logout():
    flask.session.clear()
    return flask.redirect(flask.url_for("home"))


def main():
    app.run(debug=True)


if __name__ == "__main__":
    main()
