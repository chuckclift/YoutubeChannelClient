#!/usr/bin/env python3

import argparse

from tkinter import Frame, Button,  Label, Listbox, Tk
from tkinter import X as FILLX 
from tkinter import BOTH as FILLBOTH
from tkinter.ttk import Treeview
import threading

import requests 
from bs4 import BeautifulSoup, SoupStrainer
import json
import datetime
import time
from collections import namedtuple
import sys
import os
from os.path import expanduser
from os.path import join as pjoin
    
TODAY = datetime.date.today().strftime("%m/%d/%y")

def clean_unicode(data):
    """
        since tkinter can't display unicode over 0xFFFF, they are removed
        before being displayed on tkinter
    """
    return "".join([a if ord(a) < 0xFFFF else "*" for a in data ])

def get_videos(url):
    """ 
        returns a list of videos from a given channel.  
        The list has the format of [(url, title), (url, title), ... , (url, title)] 
    """
    try:
        strain = SoupStrainer("h3")
        doc = BeautifulSoup(requests.get(url).text, "html.parser", parse_only=strain) 
        video_entries = doc.find_all("h3", attrs={"class" : "yt-lockup-title"})
        return [(a.find("a").get("href"), a.find("a").text) for a in video_entries]
    except Exception as e:
        print("Problem with:", url, e)
        return []

def get_today_videos():
    history_file = expanduser(pjoin("~", ".config","ytsub","history.txt"))
    TODAY = datetime.date.today().strftime("%m/%d/%y")
    
    with open(history_file) as f:
        for a in f:
            date = a.strip().split()[1]
            if date == TODAY:
                yield " ".join(a.strip().split()[2:])

class YoutubeClient(Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.pack(fill=FILLBOTH, expand=1)

        self.show_today = Button(self, text="show todays vids",  width=70, height=3, command=self.show_todays_vids)
        self.show_today.pack(side="top", fill=FILLX)

        self.update = Button(self, text="update video lists", width=70, height=3, command=self.update_vids)
        self.update.pack(side="top", fill=FILLX)

        self.progress = Label(self, text="progress")
        self.progress.pack(side="top")


        # results tree
        self.results = Treeview(self)
        self.results["columns"] = ("video")

        self.results.column("#0", width=175, stretch=False)
        self.results.heading("#0", text="channel")

        self.results.column("video")
        self.results.heading("video", text="video")

        self.results.pack(side="top", fill=FILLBOTH, expand=1)

    #########################
    ###  button functions ###
    #########################

    def update_vids(self):
        self.clear_results()
        t = threading.Thread(target=self.get_recent_videos)
        t.daemon = True
        t.start()

    def show_todays_vids(self):
        self.clear_results()

        for a in get_today_videos():
            channel = a.split()[0]
            title = " ".join(a.split()[1:])
            self.add_video(channel, title)
                
    ##########################
    ###  utility functions ###
    ##########################

    def clear_results(self):
        if self.results.get_children():
            for a in self.results.get_children():
                self.results.delete(a)

    def add_video(self, channel, video_title):
        channel_tree = [b for b in self.results.get_children() if b == channel]
        if channel_tree:
            video_leaf = self.results.insert(channel_tree[0], 0, values=(video_title,))
            self.results.see(video_leaf)
        else:
            channel_tree_branch = self.results.insert("", 0, channel, text=channel)
            video_leaf = self.results.insert(channel_tree_branch, 0, values=(video_title,)) 
            self.results.see(video_leaf)

    def clear_box(self):
        for i in range(self.results.size()):
            self.results.delete(0)
        
    def get_recent_videos(self):
        history_file = expanduser(pjoin("~", ".config","ytsub","history.txt"))
        url_file = expanduser(pjoin("~", ".config", "ytsub", "channels.txt"))
        TODAY = datetime.date.today().strftime("%m/%d/%y")

        with open(history_file) as f:
            old_videos = [a.split()[0].strip() for a in f]
            
        with open(url_file) as f:
            channels = [a.split() for a in f]

        for i, channel in enumerate(channels):
            channel_url, channel_title = channel
            self.progress["text"] = "channels checked: {0} / {1}".format(i + 1, len(channels))
            time.sleep(3)

            for video in get_videos(channel_url):
                video_link, video_title = video
                if video_link not in old_videos:
                    # since tkinter can't display unicode over 0xFFFF, they are removed
                    # before being displayed on tkinter
                    self.add_video(clean_unicode(channel_title), clean_unicode(video_title))
                    with open(history_file, "a") as f:
                        struct = [video_link, TODAY, channel_title, video_title]
                        f.write(" ".join(struct) + "\n")
                
if __name__ == "__main__":


    parser = argparse.ArgumentParser()
    parser.add_argument("-g", "--gui", action="store_true", help="run gui")
    args = parser.parse_args()

    if args.gui:
        root = Tk()
        root.geometry('800x800+50+50')
        root.wm_title("ytgui")
        app = YoutubeClient(master=root)
        app.mainloop()
    else:
        history_file = expanduser(pjoin("~", ".config","ytsub","history.txt"))
        url_file = expanduser(pjoin("~", ".config", "ytsub", "channels.txt"))
        TODAY = datetime.date.today().strftime("%m/%d/%y")

        with open(history_file) as f:
            old_videos = [a.split()[0].strip() for a in f]
            
        with open(url_file) as f:
            channels = [a.split() for a in f]

        for i, channel in enumerate(channels):
            channel_url, channel_title = channel
            time.sleep(3)

            for video in get_videos(channel_url):
                video_link, video_title = video
                if video_link not in old_videos:
                    with open(history_file, "a") as f:
                        struct = [video_link, TODAY, channel_title, video_title]
                        f.write(" ".join(struct) + "\n")

