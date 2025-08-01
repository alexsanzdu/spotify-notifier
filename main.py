import os
import csv
import smtplib
import datetime
# from deepdiff import DeepDiff
import difflib

from email.message import EmailMessage
from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth
from spotipy.cache_handler import MemoryCacheHandler
from secrets import (
    SPOTIPY_CLIENT_ID, SPOTIPY_CLIENT_SECRET, SPOTIPY_REDIRECT_URL, SPOTIPY_REFRESH_TOKEN,
    EMAIL_SENDER, EMAIL_PASSWORD, EMAIL_RECEIVER
)

BACKUP_DIR = "backups"
LAST_RUN_FILE = "last_run.txt"
CSV_DATE_FORMAT = "%Y-%m-%d"

EXEC_FREQUENCY = 1 # allow the script to run after X days have passed

def create_spotify_client():
    auth = SpotifyOAuth(
        client_id=SPOTIPY_CLIENT_ID,
        client_secret=SPOTIPY_CLIENT_SECRET,
        redirect_uri=SPOTIPY_REDIRECT_URL,
        scope="user-library-read",
        #cache_handler=MemoryCacheHandler(token_info={"refresh_token": SPOTIPY_REFRESH_TOKEN})
    )
    # return Spotify(auth_manager=auth)
    token_info = auth.refresh_access_token(SPOTIPY_REFRESH_TOKEN)
    return Spotify(auth=token_info['access_token'])

def get_liked_songs(sp):
    results = []
    offset = 0
    while True:
        batch = sp.current_user_saved_tracks(limit=50, offset=offset)
        if not batch["items"]:
            break
        for item in batch["items"]:
            track = item["track"]
            results.append((track["id"], track["name"], track["artists"][0]["name"]))
        offset += 50
    # Convert to list of lists
    return [list(t) for t in results]

def save_csv(songs, date_str):
    os.makedirs(BACKUP_DIR, exist_ok=True)
    path = os.path.join(BACKUP_DIR, f"{date_str}.csv")
    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["ID", "Name", "Artist"])
        writer.writerows(songs)
    return path

def load_last_backup():
    files = sorted(os.listdir(BACKUP_DIR))
    if not files:
        return []
    with open(os.path.join(BACKUP_DIR, files[-1]), "r") as f:
        ###Convert each sublist into a tuple
        ###all_items = list(csv.reader(f))[1:]
        ###return [tuple(l) for l in all_items]
        return list(csv.reader(f))[1:]

def songs_changed(old, new):
    if old == new:
        return []
    ###return DeepDiff(old, new)
    ###diff = difflib.ndiff(old, new)

    # Use difflib.ndiff to get a human-readable difference
    diff = difflib.unified_diff(["\t".join(row) for row in old], ["\t".join(row) for row in new], lineterm='', n=3)
    return '\n'.join(diff)

def send_email(subject, message):
    msg = EmailMessage()
    msg.set_content(message)
    msg["Subject"] = subject
    msg["From"] = EMAIL_SENDER
    msg["To"] = EMAIL_RECEIVER
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(EMAIL_SENDER, EMAIL_PASSWORD)
        smtp.send_message(msg)

def last_run_exceeds_days(days):
    if not os.path.exists(LAST_RUN_FILE):
        return True
    with open(LAST_RUN_FILE) as f:
        last_run = datetime.datetime.fromisoformat(f.read().strip())
    return (datetime.datetime.now() - last_run).total_seconds() > (86400 * days)

def update_last_run():
    with open(LAST_RUN_FILE, "w") as f:
        f.write(datetime.datetime.now().isoformat())

def main():
    if not last_run_exceeds_days(EXEC_FREQUENCY):
       return

    # Define today's date
    today_str = datetime.datetime.now().strftime(CSV_DATE_FORMAT)

    # Create client
    sp = create_spotify_client()

    # Read current and backup songs
    current_songs = get_liked_songs(sp) 
    previous_songs = load_last_backup()

    # Compare songs and send email
    songs_diff = songs_changed(previous_songs, current_songs)
    msg = ""
    if songs_diff:
        subject = f"Spotify Liked Songs - Change Detected ({today_str})"
        if len(previous_songs) > len(current_songs):
            msg += f"\n\nWARNING! Current playlist is shorter than before (current = {len(current_songs)}, old = {len(previous_songs)})"
        msg += f"\n\nHere are the changes:\n\n{songs_diff}"
    else:
        subject = f"Spotify Liked Songs - No Changes Detected ({today_str})"
    send_email(subject, msg)

    # Backup songs
    save_csv(current_songs, today_str)

    # Update last run with today's date
    update_last_run()

if __name__ == "__main__":
    main()
