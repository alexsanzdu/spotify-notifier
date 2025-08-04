# Introduction

A simple Python script which will routinely check your Liked Songs list, and email you summarizing any changes in your playlist.

# Spotify account setup

TBD

# Email account creation

TBD (include the 2FA setup)

# Secrets.py formatting

Rename `secrets_template.py` to `secrets.py`

TBD

# Getting tokens

```
import spotipy
from spotipy.oauth2 import SpotifyOAuth

sp_oauth = SpotifyOAuth(
    client_id=<CLIENT_ID>,
    client_secret=<CLIENT_SECRET>,
    redirect_uri="https://example.com/callback",
    scope="user-library-read"
)

###Prompt user to log in
auth_url = sp_oauth.get_authorize_url()
print(f"Please navigate here: {auth_url}")

###After login, Spotify redirects to a URL like http://example:8888/callback?code=XYZ
###Paste the entire redirected URL here
response = input("Paste the redirected URL: ")

###Extract token info
code = sp_oauth.parse_response_code(response)
token_info = sp_oauth.get_access_token(code, as_dict=True)

print("Access token:", token_info['access_token'])
print("Refresh token:", token_info['refresh_token'])  # Save this
```

# Service

1) Create the service
```
sudo nano /etc/systemd/system/spotify_backup.service
```
2) Paste these contents (adjusting the paths for the project and python3!)
```
[Unit]
Description=Spotify Liked Songs Backup

[Service]
Type=oneshot
ExecStart=<PYTHON_PATH> <REPOSITORY_PATH>/main.py
WorkingDirectory=<REPOSITORY_PATH>
```
# Timer

1) Create the timer
```
sudo nano /etc/systemd/system/spotify_backup.timer
```
2) Contents
```
[Unit]
Description=Run Spotify backup every 30 minutes

[Timer]
OnBootSec=5min
OnUnitActiveSec=30min
Persistent=true

[Install]
WantedBy=timers.target
```
# Enable and start timer

1) Commands
```
sudo systemctl daemon-reload
sudo systemctl enable spotify_backup.timer
sudo systemctl start spotify_backup.timer
```
2) Check status
```
systemctl list-timers | grep spotify
```
3) Test manually
```
sudo systemctl start spotify_backup.service
```
# Future improvements

Potential upgrades to be developed in the future:
- Running the service online (using a remote server) instead of locally.
- Better formatting for the email summary.
- Store song backups using a remote storage website (e.g. Google Drive, OneDrive).
- Allow the user to check additional playlists.
- Inform the user if the limit of 10 000 songs has been surpassed.

