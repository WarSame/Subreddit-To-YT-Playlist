#!/usr/bin/python
#ListenToThis Subreddit To Youtube Playlist Bot
#V 1.1
#/u/BlueFireAt or /u/WarSame
#This bot will repeatedly cycle through the top list of /r/listentothis, to a set depth
#It will then take all top youtube links and add them to the Youtube playlist if they
#Haven't been added already
#Then it will sleep until it wants to cycle through the list again


import praw
import time

#YT Authentication
import gdata.youtube
import gdata.youtube.service

yt_service = gdata.youtube.service.YouTubeService()
yt_service.ssl = True


import httplib2
import os
import sys
import urlparse

from apiclient.discovery import build
from apiclient.errors import HttpError
from oauth2client.client import flow_from_clientsecrets
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

def get_authenticated_service():
	flow = flow_from_clientsecrets(CLIENT_SECRETS_FILE,
	  message=MISSING_CLIENT_SECRETS_MESSAGE,
	  scope=YOUTUBE_READ_WRITE_SCOPE)

	storage = Storage("%s-oauth2.json" % sys.argv[0])
	credentials = storage.get()

	if credentials is None or credentials.invalid:
	  flags = argparser.parse_args()
	  credentials = run_flow(flow, storage, flags)

	return build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION,
	  http=credentials.authorize(httplib2.Http()))

#User-defined variables
#The maximum the bot will search is the top [depthLimit] posts. Default is 25
depthLimit=25
 
#The subreddit it will search for videos. Default is /r/listentothis
searchSubreddit = "listentothis"
#The text it will match. Default is *youtube.com/*
textToMatch = ["youtube.com/"]

def addLink(text):
	#When a link is first added to the youtube playlist, store the link in a local text file.
	f = open('alreadyAdded', 'a')
	f.write(text + "\n")

def alreadyAdded(text):
	#If the link is not in the local text file, return false. If it is, return true.
	if text in open("alreadyAdded").read():
		return True
	else:
		return False

def botCycle(r):
    #Runs the bot's logic. Scans top posts for unadded posts, then adds them to the YT playlist.
    while True:
        subreddit = r.get_subreddit(searchSubreddit)
        #Search depthLimit links and round them up if they're youtube
        for link in subreddit.get_hot(limit=depthLimit):
            url = link.url
            #Filter out non YT links, such as self-posts/announcements
            isMatch = any(string in url for string in textToMatch)
            if isMatch and not alreadyAdded(url):
		#Strip the id from the link to use in YT API
		videoID = extractId(url)
                #Login to YT and add the linked video to the playlist
                addToYTPlaylist(youtube, videoID, 'PL0123Jmy2GdkAROYNrbti51KtYSohr-R0')
		addLink(url)
        print("Cycled through top posts, all done.")
        time.sleep(1800)

def extractId(url):
	#Given a youtube URL, extracts the id for the video and returns it.
	url_data = urlparse.urlparse(url)
	query = urlparse.parse_qs(url_data.query)
	video = query["v"][0]
	return video

def addToYTPlaylist(youtube, videoID, playlistID):
	#Given video and playlist, adds the video to the playlist
	add_video_request=youtube.playlistItems().insert(
		part="snippet",
			body={
			'snippet': {
				'playlistId': playlistID, 
				'resourceId': {
					'kind': 'youtube#video',
					'videoId': videoID
					}
					#'position': 0
				}
			}
	).execute()

#Start youtube and reddit apis, and runs the bot.
youtube = get_authenticated_service()
r = praw.Reddit(user_agent = "LTT To YT Playlist Bot v 1.0 /u/BlueFireAt")
botCycle(r)
