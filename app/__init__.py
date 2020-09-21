from flask import Flask, send_file, make_response
import base64, requests, json
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger


app = Flask(__name__)


config = {}
with open('config.json', 'r') as f:
    c = json.load(f)
    config['OAUTH_TOKEN'] = c['OAUTH_TOKEN']
    config['REFRESH_TOKEN'] = c['REFRESH_TOKEN']


def replace_text(src, title, artist, album_name, progress, duration, percentage):
    if len(title) >= 23:
        title = title[0:20] + "..."
    if len(artist) >= 25:
        artist = artist[0:25] + "..."
    if len(album_name) >= 30:
        album_name = album_name[0:27] + "..."
    src = src.replace('Song Title', title.upper())
    src = src.replace('Artist Name', artist)
    src = src.replace('Album Title', album_name)
    src = src.replace('Progress', datetime.utcfromtimestamp(progress / 1000).strftime("%M:%S"))
    src = src.replace('Duration', datetime.utcfromtimestamp(duration / 1000).strftime("%M:%S"))
    src = src.replace('{prog_width}', str(int(9.54  * percentage))) 
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
            return (None, None, None, None, None, None, None, False)
        if res.json() == None:
            return (None, None, None, None, None, None, None, False)
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
            return (None, None, None, None, None, None, None, False)
        album_name = None
        artist = None
        title = None
        album_art = None
        duration = None
        progress = None
        is_playing = False
        if res.json() == None:
            return (None, None, None, None, None, None, None, False)
        resobj = res.json()
        if resobj.get('item'):
            is_playing = resobj['is_playing']
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
            percentage = (int(progress) / int(duration)) * 100
            return (title, artist, album_name, album_art, progress, duration, percentage, is_playing)
        else:
            return (None, None, None, None, None, None, False)

def update_songs(sd):
    sd.title, sd.artist, sd.album_name, sd.album_art, sd.progress, sd.duration, sd.percentage, sd.is_playing = get_now_playing(config['OAUTH_TOKEN'])
    if sd.is_playing:
        if "&" in sd.title:
            sd.title = sd.title.replace("&", "+")
        if "&" in sd.artist:
            sd.artist = sd.artist.replace("&", "+")
        if "&" in sd.album_name:
            sd.album_name = sd.album_name.replace("&", "+")
        src = ""
        with open('template-clean.svg', 'r') as f:
            src = f.read()
        src = replace_text(src, sd.title, sd.artist, sd.album_name, sd.progress, sd.duration, sd.percentage)
        src = replace_album_art(src, sd.album_art)
        with open('app/templates/assets/output.svg', 'w') as o:
            o.write(src)

class SongData:
    def __init__(self):
        self.title = None
        self.artist = None
        self.album_name = None
        self.album_art = None
        self.progress = None
        self.duration = None
        self.percentage = None
        self.is_playing = False

sd = SongData()
sd.title, sd.artist, sd.album_name, sd.album_art, sd.progress, sd.duration, sd.percentage, sd.is_playing = get_now_playing(config['OAUTH_TOKEN'])
if sd.is_playing:
    if "&" in sd.title:
        sd.title = sd.title.replace("&", "+")
    if "&" in sd.artist:
        sd.artist = sd.artist.replace("&", "+")
    if "&" in sd.album_name:
        sd.album_name = sd.album_name.replace("&", "+")
    src = ""
    with open('template-clean.svg', 'r') as f:
        src = f.read()
    src = replace_text(src, sd.title, sd.artist, sd.album_name, sd.progress, sd.duration, sd.percentage)
    src = replace_album_art(src, sd.album_art)
    with open('app/templates/assets/output.svg', 'w') as o:
        o.write(src)

@app.route('/')
def index():
    if sd.is_playing:
        res = make_response(send_file('templates/assets/output.svg', mimetype='image/svg+xml'))
        res.headers.set('Cache-Control', 'max-age=3')
        return res
    else:
        res = make_response(send_file('templates/assets/paused.svg', mimetype='image/svg+xml'))
        res.headers.set('Cache-Control', 'max-age=3')
        return res

sched = BackgroundScheduler()
trig = IntervalTrigger(seconds=3)
sched.add_job(update_songs, args=[sd], trigger=trig)
sched.start()