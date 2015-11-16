#!/usr/bin/python
# ListenToThis Subreddit To Youtube Playlist Bot
# V 1.1
# /u/BlueFireAt or /u/WarSame
# This bot will repeatedly cycle through the top list of /r/listentothis, to a set depth
# It will then take all top youtube links and add them to the Youtube playlist if they
# Haven't been added already
# Then it will sleep until it wants to cycle through the list again


import praw
import time
import httplib2
import os
import sys
import urlparse
from googleapiclient.discovery import build
from oauth2client.client import flow_from_clientsecrets
from googleapiclient.errors import HttpError
from oauth2client.file import Storage
from oauth2client.tools import argparser, run_flow

# The CLIENT_SECRETS_FILE variable specifies the name of a file that contains
# the OAuth 2.0 information for this application, including its client_id and
# client_secret. You can acquire an OAuth 2.0 client ID and client secret from
# the Google Developers Console at
# https://console.developers.google.com/.
# Please ensure that you have enabled the YouTube Data API for your project.
# For more information about using OAuth2 to access the YouTube Data API, see:
#   https://developers.google.com/youtube/v3/guides/authentication
# For more information about the client_secrets.json file format, see:
#   https://developers.google.com/api-client-library/python/guide/aaa_client_secrets
CLIENT_SECRETS_FILE = "client_secrets.json"

# This variable defines a message to display if the CLIENT_SECRETS_FILE is
# missing.
MISSING_CLIENT_SECRETS_MESSAGE = """
WARNING: Please configure OAuth 2.0

To make this sample run you will need to populate the client_secrets.json file
found at:

   %s

with information from the Developers Console
https://console.developers.google.com/

For more information about the client_secrets.json file format, please visit:
https://developers.google.com/api-client-library/python/guide/aaa_client_secrets
""" % os.path.abspath(os.path.join(os.path.dirname(__file__),
                                   CLIENT_SECRETS_FILE))

# This OAuth 2.0 access scope allows for full read/write access to the
# authenticated user's account.
YOUTUBE_READ_WRITE_SCOPE = "https://www.googleapis.com/auth/youtube"
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"


def get_authenticated_service(args):
    flow = flow_from_clientsecrets(CLIENT_SECRETS_FILE,
                                   scope=YOUTUBE_READ_WRITE_SCOPE,
                                   message=MISSING_CLIENT_SECRETS_MESSAGE)

    storage = Storage("%s-oauth2.json" % sys.argv[0])
    credentials = storage.get()

    if credentials is None or credentials.invalid:
        credentials = run_flow(flow, storage, args)

    return build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION,
                 http=credentials.authorize(httplib2.Http()))


# User-defined variables

# The maximum the bot will search is the top [depthLimit] posts. Default is 25
depth_limit = 25

# The subreddit it will search for videos. Default is /r/listentothis
search_subreddit = "listentothis"

# The text it will match. Default is *youtube.com/*. Can have more than one option.
text_to_match = ["youtube.com/", "youtu.be/"]

# The playlist it will add to by ID.
default_playlist_id = 'PL0123Jmy2GdkAROYNrbti51KtYSohr-R0'


def add_link(text):
    # When a link is first added to the youtube playlist, store the link in a local text file, "alreadyAdded".
    f = open('alreadyAdded', 'a')
    f.write(text + "\n")
    return


def already_added(link):
    # If the link is in the local text file "alreadyAdded" return true. If not, false. Also check the file exists.
    try:
        if link in open("alreadyAdded", 'r').read():
            return True
        else:
            return False
    except IOError:
        open('alreadyAdded', 'a')
        return False


def bot_cycle(r, youtube):
    # Runs the bot's logic. Scans top posts for unadded posts, then adds them to the YT playlist.
    while True:
        playlist_id = default_playlist_id
        subreddit = r.get_subreddit(search_subreddit)

        # Search depthLimit links and round them up if they're youtube
        for link in subreddit.get_hot(limit=depth_limit):
            url = link.url

            # Filter out non YT links, such as self-posts/announcements
            is_match = any(string in url for string in text_to_match)
            if is_match and not already_added(url):

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
                        print "Problem adding video url to url list file"
                    except HttpError:
                        print "Problem finding playlist"
            if not is_match:
                # If it doesn't meet the url(either weird YT link or another site)
                print("Not adding {}. Wrong form/site.".format(url))
        print("Cycled through top posts, all done.\n\n")
        # write_playlist_id(playlistID)
        time.sleep(1800)


def extract_id(url):
    # Given a youtube URL, extracts the id for the video and returns it.
    try:
        url_parsed = urlparse.urlparse(url)
        print "netloc", url_parsed.netloc
        if url_parsed.netloc == "youtu.be":
            # Get path of mobile video, remove the leading slash
            print url_parsed.path[1:]
            return url_parsed.path[1:]
        else:
            query = urlparse.parse_qs(url_parsed.query)
            video_id = query["v"][0]
            return video_id
    except HttpError:
        print "Error retrieving the video id"
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
                # 'position': 0
            }
        }
    ).execute()


def main():
    # Start youtube and reddit apis, and runs the bot.
    youtube = get_authenticated_service(argparser.parse_args())
    r = praw.Reddit(user_agent="LTT To YT Playlist v 1.1 /u/BlueFireAt")
    bot_cycle(r, youtube)


main()
