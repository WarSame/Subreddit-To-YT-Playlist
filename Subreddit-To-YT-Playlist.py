# Subreddit To Youtube Playlist Bot
# V 1.1
# This bot will repeatedly cycle through the top list of a subreddit, to a set depth
# It will then take all top youtube links and add them to the Youtube playlist if they
# Haven't been added already
# Then it will sleep until it wants to cycle through the list again


import praw
import time
import httplib2
import os
import sys
import urllib.parse
import json
from googleapiclient.discovery import build
from oauth2client.client import flow_from_clientsecrets
from googleapiclient.errors import HttpError
from oauth2client.file import Storage
from oauth2client.tools import argparser, run_flow


# User-defined variables

# The maximum the bot will search is the top [depthLimit] posts
depth_limit = 10

# The subreddit it will search for videos
search_subreddit = "listentothis"

# The text it will match. Can have more than one option
text_to_match = ["youtube.com/", "youtu.be/"]

# The playlist it will add to by ID
default_playlist_id = 'PL0123Jmy2GdkAROYNrbti51KtYSohr-R0'

# The text file it will search and store IDs with
id_file_name = 'alreadyAdded'


def add_link(text):
    # When a link is first added to the youtube playlist, store the link in a local ID text file
    f = open(id_file_name, 'a')
    f.write(text + "\n")
    return


def already_added(link):
    # If the link is in the local ID text file return true. If not, false. Also check the file exists.
    try:
        if link in open(id_file_name, 'r').read():
            return True
        else:
            return False
    except IOError:
        open(id_file_name, 'a')
        return False


def add_to_playlist(url, youtube, playlist_id):
    # Strip the id from the link to use in YT API
    video_id = extract_id(url)

    if video_id is None:
        print("=========")
        print("Can not extract the id from {}".format(url))
        print("=========")
    else:
        # Login to YT and add the linked video to the playlist
        print("Adding {} to your playlist.".format(url))
        try:
            add_to_yt_playlist(youtube, video_id, playlist_id)
            add_link(url)
        except IOError:
            print("Problem adding video url to url list file.")
        except HttpError:
            print("Problem finding playlist.")
    return


def bot_cycle(r, youtube):
    # Runs the bot's logic. Scans top posts for unadded posts, then adds them to the YT playlist.
    while True:
        playlist_id = default_playlist_id
        subreddit = r.subreddit(search_subreddit)

        # Search depthLimit links and round them up if they're youtube
        for link in subreddit.hot(limit=depth_limit):
            url = link.url

            # Filter out non YT links, such as self-posts/announcements
            is_match = any(string in url for string in text_to_match)
            if is_match and not already_added(url):
                add_to_playlist(url, youtube, playlist_id)
            if not is_match:
                print("Not adding {}. Wrong form/site.".format(url))

        print("Cycled through top posts, all done.\n\n")
        # write_playlist_id(playlistID)
        time.sleep(1800)


def extract_id(url):
    # Given a youtube URL, extracts the id for the video and returns it.
    try:
        url_parsed = urllib.parse.urlparse(url)
        if url_parsed.netloc == "youtu.be":
            # Get path of mobile video, remove the leading slash
            print("Video ID is " + url_parsed.path[1:])
            return url_parsed.path[1:]
        else:
            query = urllib.parse.parse_qs(url_parsed.query)
            video_id = query["v"][0]
            return video_id
    except HttpError:
        print("Error retrieving the video id.")
        return None


def add_to_yt_playlist(youtube, video_id, playlist_id):
    # Given video and playlist, adds the video to the playlist
    youtube.playlistItems().insert(
        part="snippet",
        body={
            'snippet': {
                'playlistId': playlist_id,
                'resourceId': {
                    'kind': 'youtube#video',
                    'videoId': video_id
                }
            }
        }
    ).execute()


def get_authenticated_service(args):
    youtube_client_secrets_file = "youtube_client_secrets.json"
    youtube_read_write_scope = "https://www.googleapis.com/auth/youtube"
    youtube_api_service_name = "youtube"
    youtube_api_version = "v3"
    flow = flow_from_clientsecrets(youtube_client_secrets_file,
                                   scope=youtube_read_write_scope)

    storage = Storage("%s-oauth2.json" % sys.argv[0])
    credentials = storage.get()

    if credentials is None or credentials.invalid:
        credentials = run_flow(flow, storage, args)

    return build(youtube_api_service_name, youtube_api_version,
                 http=credentials.authorize(httplib2.Http()))


def obtain_praw_secrets():
    # Load PRAW secrets from file
    praw_client_secrets_file = "praw_client_secrets.json"
    praw_client_secrets = json.load(open(praw_client_secrets_file))
    praw_client_id = praw_client_secrets["CLIENT_ID"]
    praw_client_secret = praw_client_secrets["CLIENT_SECRET"]
    return praw_client_id, praw_client_secret


def main():
    # Start youtube and reddit apis, and runs the bot.
    youtube = get_authenticated_service(argparser.parse_args())
    praw_secrets = obtain_praw_secrets()
    r = praw.Reddit(client_id=praw_secrets[0],
                    client_secret=praw_secrets[1],
                    user_agent="LTT To YT Playlist v 1.2 /u/BlueFireAt")
    bot_cycle(r, youtube)


main()
