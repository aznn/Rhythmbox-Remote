#!/usr/bin/env python

"""
Uses jaro distance (fuzzy search) to find a given song in the music directory.
The directory is assumed to be formatted like this,
      LIBRARY_PATH/Artist Name/Album Name/song_name.mp3

Ahmed azaan
azaan@outlook.com
"""

import os
import jellyfish
from string import digits
from operator import itemgetter

LIBRARY_PATH = "/media/azaan/Delta/Media Library/Music"
PL = len(LIBRARY_PATH)
index = 0


class Song(object):

    def __init__(self, basepath, filename, artist):
        self.path = basepath + filename
        self.artist = artist
        self.filename = filename

        global index
        self.index = index
        index += 1

        s = filename

        # Normalize the name
        # Remove digits, .mp3, whitespace and tolower
        s = s.translate(None, digits)
        s = s.replace(".mp3", "")
        s = s.strip()
        s = s.lower()

        self.str = s

    def __str__(self):
        return self.str


# Array all song objects will be loaded into
songs = []
loaded = False


def loadDir():
    global songs, loaded

    # Load only once
    if loaded:
        return

    # Load up the songs array
    for dirname, subdir, files in os.walk(LIBRARY_PATH):
        if len(files) > 0:
            artist = dirname[PL+1:].split("/")[0]
            basepath = dirname + "/"

            for f in files:
                songs.append(Song(basepath, f, artist))

    loaded = True


# Get song based on the id
def getFromId(sid):
    global songs
    loadDir()

    song = songs[sid]
    o = {'index': song.index, 'filename': song.filename,
         'artist': song.artist, 'path': song.path,
         'match': 100
         }

    return [o]


# Searches for a string and returns list of matches
# Matches = (filename, artist, path, match%)
def search(string, psi=0.90, limit=10, searchall=False):
    global songs
    loadDir()

    res = []
    count = 0
    for song in songs:
        match = jellyfish.jaro_distance(string.lower(), str(song))
        if match > psi:
            res.append({'index': song.index, 'filename': song.filename,
                        'artist': song.artist, 'path': song.path,
                        'match': match * 100})

            count += 1
            if not searchall and count > limit:
                break

    return sorted(res, key=itemgetter('match'), reverse=True)


if __name__ == '__main__':
    val = raw_input()
    print '\n'.join([str(x) for x in search(val)])
