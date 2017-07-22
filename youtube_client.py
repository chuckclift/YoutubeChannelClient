#!/usr/bin/env python3

import urllib
from bs4 import BeautifulSoup, SoupStrainer
import json
import datetime
import time
from collections import namedtuple
import sys
import os
from os.path import expanduser
from os.path import join as pjoin
    
Video = namedtuple("Video", ["url", "date", "channel", "title"])
Channel = namedtuple("Channel", ["url", "name"])
TODAY = datetime.date.today().strftime("%m/%d/%y")

def add_history(video, history_file):
    with open(history_file, "a") as f:
        f.write(" ".join([video.url, video.date, video.channel, video.title]) + "\n")

def get_videos(url):
    try:
        response = urllib.request.urlopen(url)
        strain = SoupStrainer("h3")
        doc = BeautifulSoup(response.read(), "html.parser", parse_only=strain) 
        video_entries = doc.find_all("h3", attrs={"class" : "yt-lockup-title"})
        return [(a.find("a").get("href"), a.find("a").text) for a in video_entries]
    except (urllib.error.URLError, urllib.error.HTTPError) as e:
        print("Problem with:", url, e)
        return []

def get_new_videos(channels, history):
    for a in channels:
        channel_url, name = a
        time.sleep(5)
        for vid in get_videos(channel_url):
            video_url, title = vid 
            if video_url not in history:
                yield Video(video_url, TODAY, name, title)
    
if __name__ == "__main__":
    if "-h" in sys.argv:
        print("yt_sub.py <history_file> <url_file>")
        exit(0)
    if len(sys.argv) == 1:
        history_file = expanduser(pjoin("~", ".config","ytsub","history.txt"))
        url_file = expanduser(pjoin("~", ".config", "ytsub", "channels.txt"))
    elif len(sys.argv) == 3:
        history_file = sys.argv[1]
        url_file =     sys.argv[2]
    
    if "-v" in sys.argv:
        print(history_file, url_file)

    with open(history_file) as f:
        old_videos = [a.split()[0].strip() for a in f]
        
    with open(url_file) as f:
        channels = [Channel(a.split()[0], a.split()[1]) for a in f]

    for video in get_new_videos(channels, old_videos):
        add_history(video, history_file)
        print("found new video", video)
