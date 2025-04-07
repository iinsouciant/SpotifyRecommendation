from dotenv import load_dotenv
import os

import requests
from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth
from spotipy.cache_handler import FlaskSessionCacheHandler

# for webapps, microframework
import flask
from markupsafe import escape

from SinglyLinkedList import LinkedList
from Stack import LinkedStack

from typing import Any, Generator

# scopes of app https://developer.spotify.com/documentation/web-api/concepts/scopes
SCOPES = [
    "playlist-read-private",
    "playlist-read-collaborative",
    "playlist-modify-private",
    "playlist-modify-public",
    "user-library-read",
]

# used for type hints for readability
type Album = dict[str, str]
type Song = dict[str, Album]
type Songs = list[Song]
type Playlists = list[str]


class PlaylistLinkedList(LinkedList):
    # def append(self, val) -> None:
    #     if (type(val) is Node):

    #     return super().append(val)

    def __repr__(self) -> str:
        output = ""
        nextNode = self.head
        while nextNode is not None:
            output += f"{nextNode.value['name']} -> "
            nextNode = nextNode.next
        output += "None"
        return output

    def msort_pls_key(self, key) -> None:
        """Merge Sort algorithm adapted to Linked Lists according to the given key for each dict element"""
        # split then sort
        # split array in two until 1 element arrays, then compare first element of one array to another then merge
        # base case is if only one element, then we compare
        if len(self) <= 1:
            return
        else:
            mid = len(self) // 2
            left = PlaylistLinkedList()
            left.head = self.head
            current = self.head
            prev = None
            i = 0
            while i < mid and current:
                prev = current
                current = current.next
                i += 1

            # get left and right sections of list
            right = PlaylistLinkedList()
            right.head = current
            prev.next = None

            # sort sections
            left.msort_pls_key(key)
            right.msort_pls_key(key)

            result = PlaylistLinkedList()
            left_current = left.head
            right_current = right.head
            while left_current and right_current:
                # compare first element, append, then increment
                if left_current.value[key].lower() <= right_current.value[key].lower():
                    result.append(left_current.value)
                    left_current = left_current.next
                else:
                    result.append(right_current.value)
                    right_current = right_current.next
            # when one runs out of elements, need to add the rest of the other
            while left_current:
                result.append(left_current.value)
                left_current = left_current.next
            while right_current:
                result.append(right_current.value)
                right_current = right_current.next

            self.head = result.head


class SongStack(LinkedStack):
    def __init__(self, songs: Songs = []):
        super().__init__()

        if len(songs) > 0:
            for song in songs:
                self.push(song)


def get_secret_key() -> str | None:
    if load_dotenv() and (os.getenv("SECRET_KEY") is not None):
        return os.getenv("SECRET_KEY")
    raise FileNotFoundError("Missing .env file with SECRET_KEY variable")


def get_oauth(cache_handler) -> SpotifyOAuth:
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

def get_songs(pl_id) -> Generator[Song]:
    """ Generator to get each song from a playlist so that it can be put into different data structures"""
    offset = 0
    lim = 100
    while offset < 501:
        temp = sp.playlist_tracks(
            pl_id,
            fields="items(track(id, name, artists, album(id, name)))",
            offset=offset,
            limit=lim
        )

        # if there are no more songs to get, items will be empty list
        if len(temp["items"]) == 0:
            offset = 502
            break

        for song in temp["items"]:
            song = song['track']
            if len(song["name"]) == 0:
                song["name"] = "blank"
            songDict: Song = {
                    "name": song["name"],
                    "artists": song["artists"],
                    "id": song["id"],
                    "album": song["album"],
                }
            # optional song data shown from https://github.com/obielin/Music-recommendation-System/blob/main/spotify_recommendation_system.py
            # maybe build off of later? NVM this is deprecated along with getting recommendations()
            """
            try:
                # Get audio features for the track
                audio_features = sp.audio_features(track_id)[0] if track_id != 'Not available' else None

                # Get release date of the album
                try:
                    album_info = sp.album(album_id) if album_id != 'Not available' else None
                    release_date = album_info['release_date'] if album_info else None
                except:
                    release_date = None

                # Get popularity of the track
                try:
                    track_info = sp.track(track_id) if track_id != 'Not available' else None
                    popularity = track_info['popularity'] if track_info else None
                except:
                    popularity = None

                # Add additional track information to the track data
                track_data = {
                    'Track Name': track_name,
                    'Artists': artists,
                    'Album Name': album_name,
                    'Album ID': album_id,
                    'Track ID': track_id,
                    'Popularity': popularity,
                    'Release Date': release_date,
                    'Duration (ms)': audio_features['duration_ms'] if audio_features else None,
                    'Explicit': track_info.get('explicit', None),
                    'External URLs': track_info.get('external_urls', {}).get('spotify', None),
                    'Danceability': audio_features['danceability'] if audio_features else None,
                    'Energy': audio_features['energy'] if audio_features else None,
                    'Key': audio_features['key'] if audio_features else None,
                    'Loudness': audio_features['loudness'] if audio_features else None,
                    'Mode': audio_features['mode'] if audio_features else None,
                    'Speechiness': audio_features['speechiness'] if audio_features else None,
                    'Acousticness': audio_features['acousticness'] if audio_features else None,
                    'Instrumentalness': audio_features['instrumentalness'] if audio_features else None,
                    'Liveness': audio_features['liveness'] if audio_features else None,
                    'Valence': audio_features['valence'] if audio_features else None,
                    'Tempo': audio_features['tempo'] if audio_features else None,
                    # Add more attributes as needed
                }
                songDict['data'] = track_data
            """
            yield songDict
        offset += lim


def get_pl_stack(pl_id) -> SongStack:
    " For feeding last in to the recommendation system"
    songs = SongStack()
    for song in get_songs(pl_id):
        songs.push(song)
    return songs


def get_pl_list(pl_id) -> Songs:
    """ For compiling song data into large set to get recommendations from"""
    return [song for song in get_songs(pl_id)]


def get_ft_pls(n: int =  20) -> Playlists:
    """ Get n featured playlist IDs to be used with get_pl_list() 
    This approach will not work as the get-featured-playlists endpoint is now
    deprecated and cannot be accessed. Always gives 404 Error"""
    pls = []
    offset = 0
    lim = 50
    while offset < n:
        # gives 404 error. deprecated? https://developer.spotify.com/documentation/web-api/reference/get-featured-playlists
        # temp = sp.featured_playlists(
        #     limit=lim,
        #     offset=offset,
        #     timestamp=None
        # )
        # 100% deprecated, not able to access https://developer.spotify.com/blog/2024-11-27-changes-to-the-web-api
        # a = requests.get(
        #     url='https://api.spotify.com/v1/browse/featured-playlists',
        #     headers={'Authorization': f"Bearer {cache_handler.get_cached_token()['access_token']}"}
        # )

        # if there are no more playlists to get, items will be empty list
        if len(temp["items"]) == 0:
            return pls
        
        for pl in temp:
            pls.append(pl['id'])

        offset += lim

    return pls


def get_top_pls(n: int =  20) -> Playlists:
    """ Get n featured playlist IDs to be used with get_pl_list() 
    This approach will not work as the get-featured-playlists endpoint is now
    deprecated and cannot be accessed. Always gives 404 Error"""
    pls = []
    offset = 0
    lim = 50
    while offset < n:
        # gives 404 error. deprecated? https://developer.spotify.com/documentation/web-api/reference/get-featured-playlists
        # temp = sp.featured_playlists(
        #     limit=lim,
        #     offset=offset,
        #     timestamp=None
        # )
        # 100% deprecated, not able to access https://developer.spotify.com/blog/2024-11-27-changes-to-the-web-api
        # a = requests.get(
        #     url='https://api.spotify.com/v1/browse/featured-playlists',
        #     headers={'Authorization': f"Bearer {cache_handler.get_cached_token()['access_token']}"}
        # )

        # if there are no more playlists to get, items will be empty list
        if len(temp["items"]) == 0:
            return pls
        
        for pl in temp:
            pls.append(pl['id'])

        offset += lim

    return pls


app = flask.Flask(__name__)
# store user access token in app session, encrypted with secret key
app.config["SECRET_KEY"] = get_secret_key()
# session stores data for user as they move from page to page
cache_handler = FlaskSessionCacheHandler(flask.session)
sp_oauth = get_oauth(cache_handler)
sp = Spotify(auth_manager=sp_oauth)


# first endpoint. want user to see this when they access
@app.route("/")
def home():
    return flask.render_template("index.html")


@app.route("/login")
def login():
    if not sp_oauth.validate_token(cache_handler.get_cached_token()):
        auth_url = sp_oauth.get_authorize_url()
        return flask.redirect(auth_url)
    # if valid, redirect to endpoint for method to user selecting playlists
    user = sp.current_user()
    return flask.redirect(flask.url_for("user_select_playlist", username=user["id"]))


@app.route("/callback")
def callback():
    # get 'code' once the authorization is done to store access token in authentication manager
    sp_oauth.get_access_token(flask.request.args["code"])
    # return flask.redirect(flask.url_for("get_playlists"))
    user = sp.current_user()
    return flask.redirect(flask.url_for("user_select_playlist", username=user["id"]))


"""
@app.route("/get_playlists")
def get_playlists():
    # https://www.youtube.com/watch?v=2if5xSaZJlg for getting user playlists
    # need to use authorization code flow to allow user to log in once and refresh token https://spotipy.readthedocs.io/en/2.25.1/#authorization-code-flow
    # flasksessioncachehandler
    # make sure token is still valid
    if not sp_oauth.validate_token(cache_handler.get_cached_token()):
        auth_url = sp_oauth.get_authorize_url()
        return flask.redirect(auth_url)

    playlists = sp.current_user_playlists()
    
    if playlists:
        playlists_info = [
            (pl["name"], pl["external_urls"]["spotify"]) for pl in playlists["items"]
        ]
        playlists_html = "<br>".join([f"{name}: {url}" for name, url in playlists_info])

        return playlists_html"""

"""
user clicks on a playlist to get recommendations and it sends them to
'/playlist/recommendations
sp.current_user() returns dict with keys https://developer.spotify.com/documentation/web-api/reference/get-track
  'display_name'
  'external_urls' e.g. {'spotify': 'https://open.spotify.com/user/insouciiant'}
  'followers' with dict of follower data
  'href' for api? e.g. 'https://api.spotify.com/v1/users/insouciiant'
  'id' 
  'images' for pfp data
  'type' for account type?
  'uri'
"""


@app.route("/<username>/playlists")
def user_select_playlist(username):
    # make sure token is still valid
    if not sp_oauth.validate_token(cache_handler.get_cached_token()):
        return flask.redirect(flask.url_for("login"))

    # if this is not user's profile, redirect them
    user = sp.current_user()
    if not user or user["id"] != username:
        # redirect to correct profile
        return flask.redirect(flask.url_for("user_select_playlist", username=user["id"]))
    

    offset = 0
    lim = 50
    pls = PlaylistLinkedList()
    while True:
        playlists = sp.current_user_playlists(offset=offset, limit=lim)
        if len(playlists["items"]) == 0:
            break
        for pl in playlists["items"]:
            if len(pl["name"]) == 0:
                pl["name"] = "blank"
            pls.append(
                {
                    "name": pl["name"],
                    "url": pl["external_urls"]["spotify"],
                    "id": pl["id"],
                }
            )
        offset += lim

    pls.msort_pls_key(key="name")

    return flask.render_template("playlist_select.html", user=user, playlists=pls)



@app.route("/<username>/<pl_id>/recommendations")
def display_playlist_recommendations(username, pl_id):
    # make sure token is still valid
    if not sp_oauth.validate_token(cache_handler.get_cached_token()):
        return flask.redirect(flask.url_for("login"))

    # songs to feed in to recommendation system
    selected_songs = get_pl_stack(pl_id)
    # pull from ?? featured playlists and start getting scores for each track
    """ note for final report: debated with how to quickly get a bunch of potentially viable songs
     while considering difficulty and memory space. 
     considered pulling daily and adding to SQL db but would increase complexity and running out of time
     even if it may save time trying to pull from API each time.
     Looking through available methods, will be easier to pull from some featured playlists.
    """
    dataset = []
    for pl_id in get_ft_pls():
        for song in get_songs(pl_id):
            dataset.append(song)
    #looking at the approach by Linda, they had a playlist of songs (presumably some trending playlist)
    # then the user would feed in a song name in that playlist and get out n most similar songs weighted by recency
    # I will adapt this approac by making a large list of songs from a handful of featured playlists and pulling them into one large list
    return flask.render_template("index.html")


@app.route("/logout")
def logout():
    flask.session.clear()
    return flask.redirect(flask.url_for("home"))


def main():
    app.run(debug=True)


if __name__ == "__main__":
    main()
