# github-np
Github Now Playing - Display an SVG in your README for Spotify now playing!

Example (Not Playing would be replaced with currently playing song):

<img src="https://github.com/M4cs/github-np/blob/master/app/templates/assets/paused.svg">
<img src="https://github.com/M4cs/github-np/blob/master/app/templates/assets/output.svg">

# Requirements

- Python 3.6+
- A Server or Somewhere to Host

# Getting Started

Run `pip install -r requirements.txt`

Add a file in the root dir called `config.json` and get your tokens here: https://ssrp.maxbridgland.com/authorize **(OR MAKE YOUR OWN SPOTIFY APP/HOST SSRP YOURSELF. YOU CAN FIND IT ON MY GITHUB)**

```json
{
    "OAUTH_TOKEN": "",
    "REFRESH_TOKEN": ""
}
```

Make sure your config.json is setup correctly and then you can start the app. All you have to do is add an image tag to the domain it's hosted on!
