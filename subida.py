"""Don Doblon - complete upload script (used by the owner's private GitHub Actions job).
Uploads one finished Short to the OWNER'S OWN channel as private, with the AI disclosure,
and after the owner approves it in Telegram, schedules it to go public.
Credentials come from environment variables (encrypted GitHub Secrets)."""
import os
import sys

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload


def youtube():
    cred = Credentials(None, refresh_token=os.environ["YT_REFRESH_TOKEN"],
                       client_id=os.environ["YT_CLIENT_ID"], client_secret=os.environ["YT_CLIENT_SECRET"],
                       token_uri="https://oauth2.googleapis.com/token")
    return build("youtube", "v3", credentials=cred, cache_discovery=False)


def upload_private(path, title, description, tags):
    body = {
        "snippet": {"title": title[:100], "description": description[:4900], "tags": tags[:30],
                    "categoryId": "27", "defaultLanguage": "es", "defaultAudioLanguage": "es"},
        "status": {"privacyStatus": "private", "selfDeclaredMadeForKids": False,
                   "containsSyntheticMedia": True},   # "altered or synthetic content" disclosure
    }
    req = youtube().videos().insert(part="snippet,status", body=body,
                                    media_body=MediaFileUpload(path, chunksize=-1, resumable=True))
    resp = None
    while resp is None:
        _, resp = req.next_chunk()
    return resp["id"]


def schedule(video_id, publish_at_utc):
    """Called only after the owner presses Approve in Telegram."""
    status = {"privacyStatus": "private", "publishAt": publish_at_utc,
              "selfDeclaredMadeForKids": False, "containsSyntheticMedia": True}
    youtube().videos().update(part="status", body={"id": video_id, "status": status}).execute()


def discard(video_id):
    """Called when the owner presses Discard in Telegram."""
    youtube().videos().delete(id=video_id).execute()


if __name__ == "__main__":
    # usage: python upload.py video.mp4 "Title" "Description" [2026-11-13T18:00:00Z]
    vid = upload_private(sys.argv[1], sys.argv[2], sys.argv[3], ["historias de negocios", "shorts"])
    print("uploaded (private):", vid)
    if len(sys.argv) > 4:
        schedule(vid, sys.argv[4])
        print("scheduled for", sys.argv[4])
