from flask import Flask, request, url_for, session, redirect
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import time
import sys


app = Flask(__name__)

clientID = '65d88f8d3c8d409da1893e3caa0c833f'
clientSecret = 'eb61ba04ff4f4ea3a921b8ed6c66b521'

app.secret_key = "abcdefg"
app.config['Session_Cookie_Name'] = "Ajai's Cookie"
TOKEN_INFO = "token_info"

@app.route('/')
def login():
    sp_oauth =  create_spotify_oauth()
    auth_url = sp_oauth.get_authorize_url()
    return redirect(auth_url)

@app.route('/redirect')
def redirectPage():
    sp_oauth =  create_spotify_oauth()
    session.clear()
    code = request.args.get('code')
    token_info = sp_oauth.get_access_token(code)
    session[TOKEN_INFO] = token_info
    return redirect(url_for('getTracks', _external=True))

@app.route('/getTracks')
def getTracks():
    try:
        token_info = get_token()
    except:
        print("user not logged in")
        return redirect("/")
    sp = spotipy.Spotify(auth=token_info['access_token'])
    
    current_playlists = sp.current_user_playlists()['items']
    playlists = []
    for playlist in current_playlists:
        playlists.append(playlist['id'])

    start=0
    song_uris=[]
    while True:
        items= sp.playlist_items(playlists[0], limit=100, offset=start*50)
        for song in items['items']:
            song_uri = song['track']['name']
            song_uris.append(song_uri)
        start += 1
        if (len((items['items'])) < 100):
            break
    '''
    items_of_first = sp.playlist_items(playlists[1], limit=100)
    song_uris = []

    for song in items_of_first['items']:
        song_uri = song['track']['name']
        song_uris.append(song_uri)
    '''
    return(song_uris)
    
    '''
    all_songs = []
    start = 0
    
    while True:
        items = sp.user_playlist(limit=50, offset=start*50)['items']
        start += 1
        all_songs += items
        if (len(items) < 50):
            break
    
    return str(all_songs)
    '''


def get_token():
    token_info = session.get(TOKEN_INFO, None)
    if not token_info:
        raise "exception"
    now = int(time.time())
    is_expired = token_info['expires_at'] - now <60
    if (is_expired):
        sp_oauth = create_spotify_oauth()
        token_info = sp_oauth.refresh_access_token(token_info['refresh_token'])
    return token_info

def create_spotify_oauth():
    return SpotifyOAuth(
            client_id='65d88f8d3c8d409da1893e3caa0c833f',
            client_secret='eb61ba04ff4f4ea3a921b8ed6c66b521',
            redirect_uri=url_for('redirectPage', _external=True),
            #scope = "playlist-read-private playlist-read-collaborative")
            scope = "user-library-read playlist-read-private playlist-read-collaborative")
    