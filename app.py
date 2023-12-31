from flask import Flask, request, url_for, session, redirect, render_template
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import time
import sys
import pandas as pd
import math
import matplotlib.pyplot as plt 
import seaborn as sns 
from io import BytesIO
import base64


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
    return redirect(url_for('homePage', _external=True))

@app.route('/homePage')
def homePage():
    return(render_template('index.html'))

@app.route('/critiquePage')
def critiquePage():
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

    popularity_scores = []
    artists = []
    def getPopularity():
        start=0
        while True:
            items= sp.current_user_saved_tracks(limit=50, offset=start*50)
            for song in items['items']:
                popularity = song['track']['popularity']
                artist = song['track']['artists'][0]['name']
                if artist in artists:
                    None
                else:
                    artists.append(artist)

                if popularity == 0 or popularity == 1:
                    None
                else:
                    popularity_scores.append(popularity)

            start += 1
            if (len((items['items'])) < 50):
                break

    global_artists = []
    def getArtists(playlist_id):
        start=0
        while True:
            items= sp.playlist_items(playlist_id, limit=100, offset=start*50)
            for song in items['items']:
                artist = song['track']['artists'][0]['name']
                global_artists.append(artist)
            start += 1
            if (len((items['items'])) < 100):
                break

    def compare_intersect(x, y):
        return frozenset(x).intersection(y)
    
 
    getPopularity()
    getArtists('spotify:playlist:6UeSakyzhiEt4NB3UAd6NQ')

    avg_pop = round(sum(popularity_scores) / len(popularity_scores))
    same_artists = len(compare_intersect(artists, global_artists))
    num_artists = len(artists)

    return(render_template('critique.html', **locals()))

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

    def msToMin(ms):
        return(str(round(ms/60000, 2)))
        
    song_uris=[]
    #Use this: https://medium.com/analytics-vidhya/your-top-100-songs-2020-in-python-and-plotly-2e803d7e2990

    def allPlaylistSongs():

        f = open('songs.csv', 'r+')
        f.truncate(0)

        filename = 'songs.csv'
        f = open(filename, 'a', encoding="utf-8")
        headers = 'Name,Artist,Popularity,Length,Release,Date_Added\n'
        f.write(headers)

        start=0
        while True:
            items= sp.current_user_saved_tracks(limit=50, offset=start*50)
            for song in items['items']:
                name = song['track']['name']
                name = name.replace(",", "")
                artist = song['track']['artists'][0]['name']
                popularity = song['track']['popularity']
                length = song['track']['duration_ms']
                release = song['track']['album']['release_date']
                added = song['added_at']
                #maybe add followers
                f.write(name+', '+artist+', '+str(popularity)+', '+msToMin(length)+', '+release[:4]+', '
                        +added[:7]+'\n')
                
            start += 1
            if (len((items['items'])) < 50):
                break       

        f.close()       
        
    allPlaylistSongs()
    df = pd.read_csv('songs.csv', encoding="ISO-8859-1")

    top_10_artists = df['Artist'].value_counts().nlargest(10)
    bottom_10_artists = df['Artist'].value_counts().nsmallest(10)
    top_10_pop = df.nlargest(10, 'Popularity')
    top_10_length = df.nlargest(10, 'Length')

    sns.histplot( data=df, x='Popularity')
    plt.xlabel('Popularity')
    plt.ylabel('Count')
    plt.title('Sample Seaborn Plot')

    # Save the Seaborn plot to a BytesIO object
    popularity_hist_buf = BytesIO()
    plt.savefig(popularity_hist_buf, format='png')
    popularity_hist_buf.seek(0)
    popularity_hist_base64 = base64.b64encode(popularity_hist_buf.read()).decode('utf-8')
    plt.clf()

    sns.histplot(df[df['Artist'].isin(top_10_artists.index)], x='Artist')
    plt.xlabel('Artists')
    plt.ylabel('Count')
    plt.title('Top Artist Seaborn Plot')

    artists_buf = BytesIO()
    plt.savefig(artists_buf, format='png')
    artists_buf.seek(0)
    artists_base64 = base64.b64encode(artists_buf.read()).decode('utf-8')
    plt.clf()

    sns.histplot(df[df['Artist'].isin(bottom_10_artists.index)], x='Artist')
    plt.xlabel('Artists')
    plt.ylabel('Count')
    plt.title('Bottom Artist Seaborn Plot')

    bot_artists_buf = BytesIO()
    plt.savefig(bot_artists_buf, format='png')
    bot_artists_buf.seek(0)
    bot_artists_base64 = base64.b64encode(bot_artists_buf.read()).decode('utf-8')
    plt.clf()

    sns.histplot(data=df, x='Release')
    plt.xlabel('Years')
    plt.ylabel('Count')
    plt.title('Release Seaborn Plot')
    
    release_date_buf = BytesIO()
    plt.savefig(release_date_buf, format='png')
    release_date_buf.seek(0)
    release_date_base64 = base64.b64encode(release_date_buf.read()).decode('utf-8')
    plt.clf()

    sns.scatterplot(data=df, x='Length', y='Popularity')
    plt.xlabel('Song Length')
    plt.ylabel('Popularity')
    plt.title('Length vs Popularity Seaborn Plot')
    
    length_v_pop_buf = BytesIO()
    plt.savefig(length_v_pop_buf, format='png')
    length_v_pop_buf.seek(0)
    length_v_pop_base64 = base64.b64encode(length_v_pop_buf.read()).decode('utf-8')
    plt.clf()

    sns.barplot(data=df[df['Artist'].isin(top_10_artists.index)], x='Artist', y='Length')
    plt.xlabel('Artist')
    plt.ylabel('Song Length')
    plt.title('Length vs Popularity Seaborn Plot')
    
    artist_len_buf = BytesIO()
    plt.savefig(artist_len_buf, format='png')
    artist_len_buf.seek(0)
    artist_len_base64 = base64.b64encode(artist_len_buf.read()).decode('utf-8')
    plt.clf()

    sns.histplot(data=df, x="Date_Added")
    plt.xlabel('Date Added')
    plt.ylabel('Count')
    plt.title('How Many Songs Added Per Month')
    
    songs_added_buf = BytesIO()
    plt.savefig(songs_added_buf, format='png')
    songs_added_buf.seek(0)
    songs_added_base64 = base64.b64encode(songs_added_buf.read()).decode('utf-8')
    plt.clf()

    sns.barplot(data=top_10_pop, x='Popularity', y='Name')
    plt.xlabel('Song Name')
    plt.ylabel('Popularity')
    plt.title('Top 10 Most Popular Songs')
    
    song_pop_buf = BytesIO()
    plt.savefig(song_pop_buf, format='png')
    song_pop_buf.seek(0)
    song_pop_base64 = base64.b64encode(song_pop_buf.read()).decode('utf-8')
    plt.clf()

    sns.barplot(data=top_10_length, x='Name', y='Length')
    plt.xlabel('Song Name')
    plt.ylabel('Length')
    plt.title('Top 10 Longest Songs')
    
    song_len_buf = BytesIO()
    plt.savefig(song_len_buf, format='png')
    song_len_buf.seek(0)
    song_len_base64 = base64.b64encode(song_len_buf.read()).decode('utf-8')
    plt.clf()

    return render_template('data.html', popularity_hist_base64=popularity_hist_base64 ,artists_base64=artists_base64, 
                           release_date_base64=release_date_base64, length_v_pop_base64=length_v_pop_base64,
                           artist_len_base64=artist_len_base64, songs_added_base64=songs_added_base64, song_pop_base64=song_pop_base64,
                           bot_artists_base64=bot_artists_base64, song_len_base64=song_len_base64,)
    
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



@app.route('/getGenres')
   
def getGenres():
    try:
        token_info = get_token()
    except:
        print("user not logged in")
        return redirect("/")
    sp = spotipy.Spotify(auth=token_info['access_token'])
    
    start = 0
    def allPlaylistGenres():
        f = open('genres.csv', 'r+')
        f.truncate(0)

        filename = 'genres.csv'
        f = open(filename, 'a', encoding="utf-8")
        headers = 'Genre,Popularity,Length,Release\n'
        f.write(headers)
        
        start = 0

        while True:
            items = sp.current_user_saved_tracks(limit=50, offset=start*50)
            for song in items['items']:
                artist_id= song['track']['artists'][0]['id']
                artist = sp.artist(artist_id)
                try:
                    genre= artist['genres'][0]
                except:
                    None

                popularity = song['track']['popularity']
                length = song['track']['duration_ms']
                release = song['track']['album']['release_date']

                f.write(genre+','+str(popularity)+','+str(length)+','+str(release[:4])+'\n')
            
            start += 1
            if (len((items['items'])) < 50):
                break

        f.close()      

    allPlaylistGenres()
    df = pd.read_csv('genres.csv', encoding="ISO-8859-1")
    return (render_template('genre.html'))
