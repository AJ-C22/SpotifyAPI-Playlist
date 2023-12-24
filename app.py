from flask import Flask, request, url_for, session, redirect
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import time
import sys
import pandas as pd
import math


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

    filename = 'songs.csv'
    f = open(filename, 'a')
    headers = 'Name,Artist,Genre,Populatrity,Length,\n'
    f.write(headers)

    def msToMin(ms):
        ms/60000
        minutes= math.floor(ms/60000)
        seconds = round(60*((ms/60000)-minutes))
        return(str(minutes)+'min '+str(seconds)+'sec')
        
    song_uris=[]

    def allPlaylistSongs(playlist_id):
        start=0
        while True:
            items= sp.playlist_items(playlist_id, limit=100, offset=start*50)
            for song in items['items']:
                name = song['track']['name']
                artist = song['track']['artists'][0]['name']
                #genre = song['track']['artists'][0]['genres']
                '''
                result = sp.search(artist)
                track = result['tracks']['items'][0]
                artist_help = sp.artist(track["artists"][0]["external_urls"]["spotify"])
                genre = artist_help["genres"]
                '''

                popularity = song['track']['popularity']
                length = song['track']['duration_ms']
                #f.write(name+', '+ artist+', '+str(genre)+', '+str(popularity)+', '+ msToMin(length))
                f.write(name+', '+artist+', '+str(popularity)+', '+msToMin(length)+'\n')
                song_uris.extend([name, popularity])
                
            start += 1
            if (len((items['items'])) < 100):
                break

    #for playlist_id in playlists:
    #allPlaylistSongs(playlist_id)
    allPlaylistSongs(playlists[9])
    f.close()   
    return(filename)


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
            scope = "user-library-read playlist-read-private playlist-read-collaborative")
    