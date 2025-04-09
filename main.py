from dotenv import load_dotenv
import os
from time import time

import requests
from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth
from spotipy.cache_handler import FlaskSessionCacheHandler

# for webapps, microframework
import flask
from urllib.parse import quote_plus

from SinglyLinkedList import LinkedList
from Stack import Stack
from lyricDB import LyricDB

from typing import Any, Generator

# scopes of app https://developer.spotify.com/documentation/web-api/concepts/scopes
SCOPES = [
    "playlist-read-private",
    "playlist-read-collaborative",
    "playlist-modify-private",
    "playlist-modify-public",
    "user-library-read",
]

database = LyricDB()

# used for type hints for readability
type Album = dict[str, str]
type AlbumName = str
type Songs = list[Song]
type Playlists = list[str]
type Albums = list[tuple[Album, AlbumName]]
type Artist = dict[str, str]
type Artists = list[Artist]


class Song():
    """ 
    A simple object to hold 6 different standard text fields. This is essentially a dict
    with a couple helpful methods.

    self.NAME : Song name
    self.artists : list of artist dictionaries from Spotify API
    self.ID : Spotify ID
    self.ALBUM : Album name
    self.DURATION_MS : Song duration in ms
    self.LYRICS : Plain text lyrics
    self.database : reference to initialized sqlite3 handler to retrieve lyrics when needed.
    """

    def __init__(self, name:str, artists:Artists, id:str, album:str, duration_ms:int, database:LyricDB, lyrics:str|None = None) -> None:
        self.name = name
        self.artists = artists
        self.id = id
        self.album = album
        self.duration_ms = duration_ms
        self.lyrics = lyrics
        self.database = database

    def __getitem__(self, key) -> Any:
        return getattr(self, key)

    def __setitem__(self, key, val) -> Any:
        return setattr(self, key, val)

    def get_lyrics(self) -> str | None:
        """
        Check local database for lyrics. If not there, insert into database
        Use spotify song data to look up lyrics from LRCLIB API.
        This API takes up most of the time required to get response back to user.
        Instead of using Spotify's deprecated song features endpoint,
        pivoting to semantic search lyrics. If time allows, try to pull in tempo and give score for closeness.
        https://lrclib.net/docs

        "Attempt to find the best match of lyrics for the track. You must provide the exact signature of the track, including the track title, artist name, album name, and the track's duration in seconds."

        Example GET:
        GET /api/get?artist_name=Borislav+Slavov&track_name=I+Want+to+Live&album_name=Baldur%27s+Gate+3+(Original+Game+Soundtrack)&duration=233

        """
        # Check local lyric database first
        db_response = database.search_lyric(self)
        if db_response == "":
            return
        if db_response:
            return db_response

        artist = quote_plus(self["artists"][0]["name"])
        track = quote_plus(self["name"])
        album = quote_plus(self["album"])
        dur = self["duration_ms"] // 1000
        url = f"https://lrclib.net/api/get?artist_name={artist}&track_name={track}&album_name={album}&duration={dur}"
        # artist['name'] can be empty if spotify attributes an album to "Various Artists"
        # skip for now since it doesn't include any other artist data
        if len(artist) == 0:
            return
        # "...If you are developing an application to interact with LRCLIB, we encourage you to include the User-Agent header in your requests, specifying your application's name, version, and a link to its homepage or project page. For example: LRCGET v0.2.0 (https://github.com/tranxuanthang/lrcget)."
        try:
            lrc_response = requests.get(
                url=url,
                headers={
                    "LRCGET": "v0.1.0 (https://github.com/iinsouciant/SpotifyRecommendation)"
                },
            )
            # if invalid response, can't find song
            if lrc_response.status_code == 404:
                database.insert_lyric(self["id"], "")
                return
            lyrics = lrc_response.json()["plainLyrics"]
            database.insert_lyric(self["id"], lyrics)
            print(f"Lyrics for {self['name']} by ({self["artists"][0]["name"]}) not found in database. Retrieved from API.")
            self['lyrics'] = lyrics
            return lyrics
        except Exception as e:
            print(f"Error occurred during lyric retrieval: {e}")
            return



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


class SongStack(Stack):
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


def get_songs_pl(pl_id) -> Generator[Song]:
    """Generator to get each song from a playlist so that it can be put into different data structures"""
    offset = 0
    lim = 100
    while offset < 501:
        temp = sp.playlist_tracks(
            pl_id,
            fields="items(track(id, name, artists, album(name), duration_ms))",
            offset=offset,
            limit=lim,
        )

        # if there are no more songs to get, items will be empty list
        if len(temp["items"]) == 0:
            offset = 502
            break

        for track in temp["items"]:
            songDict = track["track"]
            if len(songDict["name"]) == 0:
                songDict["name"] = "blank"
            song = Song(
                name = songDict["name"],
                artists = songDict["artists"],
                id = songDict["id"],
                album = songDict["album"]["name"],
                duration_ms = songDict["duration_ms"],
                database=database
            )
            # song.get_lyrics()

            yield song
        offset += lim


def get_songs_album(al_id) -> Generator[Song]:
    """Generator to get each song from an album so that it can be put into different data structures.
    Assumed that all albums num songs < default limit (50)"""
    album = sp.album(
        al_id,
        # offset=offset,
        # limit=lim
    )

    temp = album["tracks"]["items"]
    for songDict in temp:
        if len(songDict["name"]) == 0:
            songDict["name"] = "blank"
        song = Song(
            name = songDict["name"],
            artists = songDict["artists"],
            id = songDict["id"],
            album = album["name"],
            duration_ms = songDict["duration_ms"],
            database=database
        )
        # song.get_lyrics()

        yield song


def get_pl_stack(pl_id) -> SongStack:
    "For feeding last in to the recommendation system"
    songs = SongStack()
    for song in get_songs_pl(pl_id):
        songs.push(song)
    return songs


def get_pl_list(pl_id) -> Songs:
    """For compiling song data into large set to get recommendations from"""
    return [song for song in get_songs_pl(pl_id)]


def get_ft_pls(n: int = 20) -> Playlists:
    """Get n featured playlist IDs to be used with get_pl_list()
    This approach will not work as the get-featured-playlists endpoint is now
    deprecated and cannot be accessed. Always gives 404 Error.
    https://developer.spotify.com/blog/2024-11-27-changes-to-the-web-api
    """
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
            pls.append(pl["id"])

        offset += lim

    return pls


def get_new_releases(n: int = 25) -> Albums:
    """Get n few albums IDs to be used with get_pl_list()
    This approach will not work as the get-featured-playlists endpoint is now
    deprecated and cannot be accessed. Always gives 404 Error"""
    albums = []
    offset = 0
    lim = min(50, n)
    while offset < n:
        temp = sp.new_releases(limit=lim, offset=offset, country="US")
        temp = temp["albums"]

        # if there are no more releases to get, items will be empty list
        if len(temp["items"]) == 0:
            return albums

        for album in temp["items"]:
            albums.append(album["id"])

        offset += lim

    return albums


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
        return flask.redirect(
            flask.url_for("user_select_playlist", username=user["id"])
        )

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
    #   make it so user selects number of new releases to check for sinmilarity
    dataset = []
    startTime = time()
    for pl_id in get_new_releases(100):
        for song in get_songs_album(pl_id):
            song.get_lyrics()
            dataset.append(song)
            print(f"Got lyrics for: ({song['name']}) by ({song["artists"][0]["name"]})")
    linearDur = time() - startTime
    print(f"\nData set size: {len(dataset)}")
    print(f"Lyric get time: {linearDur:.9f} seconds\n")

    # semantic search and get song distance to nearest neighbors + a weighted factor for bpm difference,
    # sum distance score in dataset for n songs in selected_songs
    # output html page with links to m songs with the lowest score
    # use this to get similarity? https://whoosh.readthedocs.io/en/latest/intro.html
    return flask.render_template("index.html")


@app.route("/logout")
def logout():
    flask.session.clear()
    return flask.redirect(flask.url_for("home"))


def main():
    app.run(debug=True)


if __name__ == "__main__":
    main()
