#!/usr/bin/env python3

import tkinter as tk
import threading

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
    """ 
        returns a list of videos from a given channel.  
        The list has the format of [(url, title), (url, title), ... , (url, title)] 
    """
    try:
        response = urllib.request.urlopen(url)
        strain = SoupStrainer("h3")
        doc = BeautifulSoup(response.read(), "html.parser", parse_only=strain) 
        video_entries = doc.find_all("h3", attrs={"class" : "yt-lockup-title"})
        return [(a.find("a").get("href"), a.find("a").text) for a in video_entries]
    except (urllib.error.URLError, urllib.error.HTTPError) as e:
        print("Problem with:", url, e)
        return []

def get_today_videos():
    history_file = expanduser(pjoin("~", ".config","ytsub","history.txt"))
    Video = namedtuple("Video", ["url", "date", "channel", "title"])
    TODAY = datetime.date.today().strftime("%m/%d/%y")
    
    with open(history_file) as f:
        for a in f:
            date = a.strip().split()[1]
            if date == TODAY:
                yield " ".join(a.strip().split()[2:])

class Application(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.pack()

        self.show_today = tk.Button(self, text="show todays vids", command=self.show_todays_vids, width=70, height=3)
        self.show_today.pack(side="top")

        self.update = tk.Button(self, text="update video lists", width=70, height=3, command=self.update_vids)
        self.update.pack(side="top")

        self.progress = tk.Label(self, text="progress")
        self.progress.pack(side="top")

        self.results = tk.Listbox(self, height=40, width=80)
        self.results.pack(side="top")


    #########################
    ###  button functions ###
    #########################

    def update_vids(self):
        self.clear_box()
        t = threading.Thread(target=self.get_recent_videos)
        t.daemon = True
        t.start()

    def show_todays_vids(self):
        self.clear_box()
        for a in get_today_videos():
            self.results.insert(0, a)


    ##########################
    ###  utility functions ###
    ##########################

    def clear_box(self):
        for i in range(self.results.size()):
            self.results.delete(0)
        
    def get_recent_videos(self):
        history_file = expanduser(pjoin("~", ".config","ytsub","history.txt"))
        url_file = expanduser(pjoin("~", ".config", "ytsub", "channels.txt"))
        Video = namedtuple("Video", ["url", "date", "channel", "title"])
        TODAY = datetime.date.today().strftime("%m/%d/%y")

        with open(history_file) as f:
            old_videos = [a.split()[0].strip() for a in f]
            
        with open(url_file) as f:
            channels = [Channel(a.split()[0], a.split()[1]) for a in f]

        for i, channel in enumerate(channels):
            channel_url, channel_title = channel
            self.progress["text"] = "channels checked: {0} / {1}".format(i + 1, len(channels))
            time.sleep(3)

            for video in get_videos(channel_url):
                video_link, video_title = video
                if video_link not in old_videos:
                    self.results.insert(0, "{0} {1}".format(channel_title, video_title))
                    add_history(Video(video_link, TODAY, channel_title, video_title), history_file)
                
if __name__ == "__main__":
    root = tk.Tk()
    root.wm_title("ytgui")
    app = Application(master=root)
    app.mainloop()

