from flask import Flask, send_file, make_response
import base64, requests, json
from datetime import date, datetime, time
from flask.templating import render_template


app = Flask(__name__)


config = {}
with open('config.json', 'r') as f:
    c = json.load(f)
    config['OAUTH_TOKEN'] = c['OAUTH_TOKEN']
    config['REFRESH_TOKEN'] = c['REFRESH_TOKEN']

class SongData:
    def __init__(self):
        self.current_song = None
        self.current_artist = None
        self.current_album = None
        self.is_playing = False

def replace_text(src, title, artist, album_name, progress, duration):
    if len(title) >= 20:
        title = title[0:17] + "..."
    if len(artist) >= 20:
        artist = artist[0:20] + "..."
    if len(album_name) >= 25:
        album_name = album_name[0:22] + "..."
    src = src.replace('Song Title', title)
    src = src.replace('Artist Name', artist)
    src = src.replace('Album Title', album_name)
    src = src.replace('Progress', datetime.utcfromtimestamp(progress / 1000).strftime("%M:%S"))
    src = src.replace('Duration', datetime.utcfromtimestamp(duration / 1000).strftime("%M:%S"))
    return src

def replace_album_art(src, image):
    if image == "N/A":
        image = "https://cdn.pixabay.com/photo/2015/10/05/22/37/blank-profile-picture-973460_960_720.png"
    res = requests.get(image).content
    b64_str = base64.b64encode(res)
    b64_msg = b64_str.decode('utf-8')
    src = src.replace('{album_art}', b64_msg)
    return src

def get_now_playing(oauth_token):
    headers = {'Authorization': 'Bearer ' + oauth_token}
    while True:
        url = "https://api.spotify.com/v1/me/player/currently-playing"
        res = requests.get(url, headers=headers)
        if res.status_code == 204:
            return (None, None, None, None, None, None)
        if res.json() == None:
            return (None, None, None, None, None, None)
        if res.json().get('error') != None:
            err = res.json()
            if err['error']['status'] == 401:
                res = requests.get("https://ssrp.maxbridgland.com/getRefreshForSpotify/" + config['REFRESH_TOKEN'])
                if res.status_code == 200:
                    resobj = res.json()
                    if resobj.get("access_token"):
                        config['OAUTH_TOKEN'] = resobj['access_token']
                        with open("config.json", "r+") as jf:
                            confObj = json.load(jf)
                            confObj['OAUTH_TOKEN'] = resobj['access_token']
                            if resobj.get('refresh_token'):
                                config['OAUTH_TOKEN'] = resobj['refresh_token']
                            jf.seek(0)
                            json.dump(confObj, jf, indent=4)
                            jf.truncate()
        if res.status_code != 200:
            return (None, None, None, None, None, None)
        album_name = None
        artist = None
        title = None
        album_art = None
        duration = None
        progress = None
        if res.json() == None:
            return (None, None, None, None, None, None)
        resobj = res.json()
        if resobj.get('item'):
            if resobj['item'].get('album'):
                album_name = resobj['item']['album']['name']
            if resobj['item'].get('artists'):
                artist = resobj['item']['artists'][0]['name']
            if resobj['item'].get('name'):
                title = resobj['item']['name']
            if resobj['item'].get('album'):
                album_art = resobj['item']['album']['images'][0]['url']
            if resobj.get('progress_ms'):
                progress = resobj['progress_ms']
            if resobj['item'].get('duration_ms'):
                duration = resobj['item']['duration_ms']
            return (title, artist, album_name, album_art, progress, duration)
    else:
        return (None, None, None, None, None, None)

@app.before_first_request
def setup():
    print('In First Request')
    title, artist, album_name, album_art, progress, duration = get_now_playing(config['OAUTH_TOKEN'])
    if None in [title, artist, album_art, album_name, progress, duration]:
        title = "Not Playing"
        artist = "N/A"
        album_art = "N/A"
        album_name = "N/A"
        progress = 0
        duration = 0
    if "&" in title:
        title = title.replace("&", "+")
    if "&" in artist:
        artist = artist.replace("&", "+")
    if "&" in album_name:
        album_name = album_name.replace("&", "+")
    src = ""
    with open('template-clean.svg', 'r') as f:
        src = f.read()
    src = replace_text(src, title, artist, album_name, progress, duration)
    src = replace_album_art(src, album_art)
    with open('app/templates/assets/output.svg', 'w') as o:
        o.write(src)

@app.route('/')
def index():
    title, artist, album_name, album_art, progress, duration = get_now_playing(config['OAUTH_TOKEN'])
    if None in [title, artist, album_art, album_name, progress, duration]:
        title = "Not Playing"
        artist = "N/A"
        album_art = "N/A"
        album_name = "N/A"
        progress = 0
        duration = 0
    if "&" in title:
        title = title.replace("&", "+")
    if "&" in artist:
        artist = artist.replace("&", "+")
    if "&" in album_name:
        album_name = album_name.replace("&", "+")
    if artist != "N/A" and album_name != "N/A":
        src = ""
        with open('template-clean.svg', 'r') as f:
            src = f.read()
        src = replace_text(src, title, artist, album_name, progress, duration)
        src = replace_album_art(src, album_art)
        with open('app/templates/assets/output.svg', 'w') as o:
            o.write(src)
        res = make_response(send_file('templates/assets/output.svg', mimetype='image/svg+xml'))
        res.headers.set('Cache-Control', 'max-age=5')
        return res
    else:
        res = make_response(send_file('templates/assets/paused.svg', mimetype='image/svg+xml'))
        res.headers.set('Cache-Control', 'max-age=5')
        return res