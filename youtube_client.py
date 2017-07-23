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

def get_new_videos(channels, history):
    """
        Yields list of videos for each channel
    """
    for a in channels:
        channel_url, channel_name = a
        time.sleep(5)
        yield [Video(a[0], TODAY, channel_name, a[1] ) for a in get_videos(channel_url) 
                                                       if a[0] not in history]

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
        t = threading.Thread(target=self.get_videos)
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
        
    def get_videos(self):
        history_file = expanduser(pjoin("~", ".config","ytsub","history.txt"))
        url_file = expanduser(pjoin("~", ".config", "ytsub", "channels.txt"))
        Video = namedtuple("Video", ["url", "date", "channel", "title"])
        TODAY = datetime.date.today().strftime("%m/%d/%y")

        with open(history_file) as f:
            old_videos = [a.split()[0].strip() for a in f]
            
        with open(url_file) as f:
            channels = [Channel(a.split()[0], a.split()[1]) for a in f]
    
        channels_checked = 0
        for channel_videos in get_new_videos(channels, old_videos):
            channels_checked += 1
            print(channels_checked)
            self.progress["text"] = "channels checked: {0} / {1}".format(channels_checked, len(channels))
            for vid in channel_videos:
                
                self.results.insert(0, "{0} {1}".format(vid.channel, vid.title))
                add_history(vid, history_file)
                print("found new video", vid)

if __name__ == "__main__":
    root = tk.Tk()
    root.wm_title("ytgui")
    app = Application(master=root)
    app.mainloop()

