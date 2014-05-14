#!/usr/bin/env python

"""
Command line remote for Rhythmbox (tested with 2.97)

commands:
start       - Starts playing (Play)
pause       - Pause
next        - Plays next song in the playlist
prev OR p   - Plays previous song in playlist
what OR w   - Displays information about the song playing now
play        - Plays the song, searches your media library folder. (look in fuzzySearch.py)
lyrics OR l - Downloads lyrics from chartlyrics.com and displays with less
rating      - Displays the current song rating/rate the current song
shuffle     - Displays if shuffle is on/switch shuffle on or off

Author
Ahmed Azaan Hassan
azaan@outlook.com
[github.com/aeonaxan/]
"""

import dbus
import sys
from termcolor import colored
from urllib import unquote

iProperties, iPlayer, iDB = None, None, None


# rates the current playing song and then prints it
def rateSong(rating):
    metadata = dbus.Dictionary(iProperties.Get("org.mpris.MediaPlayer2.Player", "Metadata"))
    uri = str(metadata['xesam:url'])
    iDB.SetEntryProperties(uri, {'rating': float(rating)})
    printCurrentSong()


# Pretty prints the current playing song
def printCurrentSong(metadata=None):
    if metadata is None:
        metadata = dbus.Dictionary(iProperties.Get("org.mpris.MediaPlayer2.Player", "Metadata"))
    title = str(metadata['xesam:title'])
    artist = str(metadata['xesam:artist'][0])
    rating = int(float(metadata['xesam:userRating']) * 5)

    print "Title  : ", colored(title, 'red', attrs=['bold'])
    print "Artist : ", colored(artist, 'red')

    if rating > 0:
        print "Rating : ", colored('* ' * int(rating), 'blue')


# Downloads lyrics for a current song
def downloadLyrics(artist, title, savepath):
    import urllib
    import bs4

    url = "http://api.chartlyrics.com/apiv1.asmx/SearchLyricDirect?artist=%s&song=%s"
    url %= (urllib.quote(artist), urllib.quote(title))
    #print "Artist: %s , Title: %s" % (artist,title)

    retry = 0
    while 1:
        if retry == 10:
            print "Maximum retires reached"
            return False

        try:
            res = urllib.urlopen(url)
            break
        except IOError:
            retry += 1
            print "Retrying... (%d)" % retry

    if res.code != 200:
        print "Error contacting server"
        return False
    else:
        res = res.read()

    # Parse the xml
    p = bs4.BeautifulSoup(res,"xml")
    lyrics = p.GetLyricResult.Lyric.text

    if len(lyrics) == 0:
        print "No lyrics for current song"
        return False
        
    # Save lyrics to file
    print "Saving lyrics to file: %s" % savepath
    lyricfile = open(savepath, "w")
    lyricfile.write(lyrics)
    lyricfile.close()

    return True


# Prints the lyrics of the current playing song
def printLyrics():
    import os, subprocess

    metadata = dbus.Dictionary(iProperties.Get("org.mpris.MediaPlayer2.Player", "Metadata"))
    title = str(metadata['xesam:title'])
    artist = str(metadata['xesam:artist'][0])
    url = unquote(str(metadata['xesam:url']))[7:-3]+'lrc'

    print url
    display = False
    if os.path.isfile(url):
        display = True
    else:
        print "No local file found, downloading lyrics from internet"
        display = downloadLyrics(artist, title, url)

    # print it with less (args taken from git)
    if display:
        pager = subprocess.Popen(['less', '-F', '-R', '-S', '-X', '-K', '-M', url], stdin=sys.stdin, stdout=sys.stdout)
        pager.wait()
    
    #if display:
        # print it using Vim's version of less
    #    pager = subprocess.Popen(['/usr/share/vim/vim73/macros/less.sh',url], stdin=sys.stdin, stdout=sys.stdout)
    #    pager.wait()


# Plays a song indicated in the args
def playSong(args):
    perc = 0.85
    num = 3
    searchall = False
    sid = 0

    if len(args) > 0 and "-" in args[0]:
        # if the first arg contains a '-' we are likely dealing
        # with command line args

        from optparse import OptionParser
        parser = OptionParser()

        parser.add_option("-s", "--song", dest="name",
                          help="Name of Song", default=None)

        parser.add_option("-n", "--num", dest="num",
                          help="Number of results to Display", default=num)

        parser.add_option("-p", "--perc", dest="perc",
                          help="Threshold Percentage (float)", default=perc)

        parser.add_option("-i", "--id", dest="id",
                          help="Id of the song as displayed in table", default=0)

        (options, args) = parser.parse_args(args)
        name = options.name
        num = int(options.num)
        searchall = True
        sid = int(options.id)

        perc = float(options.perc)
        if perc > 1:
            perc /= 100

        if name is None and sid == 0:
            print "Must pass -s argument for song, see -h"
            return

    elif len(args) == 0:
        print "Enter a song name, or use --help"
        return

    else:
        name = ' '.join(args)

    # Do a fuzzy search
    import fuzzySearch
    import urllib

    # If an id given
    if sid != 0:
        res = fuzzySearch.getFromId(sid)
    else:
        res = fuzzySearch.search(name, perc, num, searchall)

    if len(res) == 0:
        print "No matches for [%s]" % name
        return

    # start playing the highest match
    path = 'file://' + urllib.quote(res[0]['path'])
    iPlayer.OpenUri(path)

    # print table
    print "Matches, (Playing first)"
    for song in res:
        print "%4d | " % song['index'],
        print "%.2f%% | " % song['match'],
        print colored(song['filename'], 'red', attrs=['bold']) + " - ",
        print colored(song['artist'], 'red')

    print "\n", printCurrentSong()


# converts an argument to a boolean
def getBoolean(arg):
    if arg is None:
        return False

    if arg in ("On", "on", "true", "True"):
        return True

    return False


# Print a formatted boolean with a message
def printBoolean(string, boolean):
    color = 'red'
    msg = 'Off'
    if boolean:
        color = 'green'
        msg = 'On'

    print string + " : " + colored(msg, color)


def main(command):
    session_bus = dbus.SessionBus()

    # Get the bus objects
    try:
        player = session_bus.get_object('org.mpris.MediaPlayer2.rhythmbox', '/org/mpris/MediaPlayer2')
        pDB = session_bus.get_object('org.mpris.MediaPlayer2.rhythmbox', '/org/gnome/Rhythmbox3/RhythmDB')
    except dbus.exceptions.DBusException:
        print "RythmBox not running"
        return 1

    # get the interfaces
    global iProperties, iPlayer, iDB
    iPlayer = dbus.Interface(player, dbus_interface='org.mpris.MediaPlayer2.Player')
    iProperties = dbus.Interface(player, dbus_interface='org.freedesktop.DBus.Properties')
    iDB = dbus.Interface(pDB, dbus_interface='org.gnome.Rhythmbox3.RhythmDB')

    # get the arguments
    com = command[0]
    try:
        arg = command[1]
    except IndexError:
        arg = None

    # main switch
    if com in ("start", ):
        iPlayer.Play()
        printCurrentSong()

    elif com in ("pause", ):
        iPlayer.Pause()
        print "Song paused"

    elif com in ("next", "n"):
        iPlayer.Next()
        printCurrentSong()

    elif com in ("prev", "p"):
        iPlayer.Previous()
        printCurrentSong()

    elif com in ("what", "w"):
        printCurrentSong()

    elif com in ("play", ):
        playSong(command[1:])

    elif com in ("lyrics", "l"):
        printLyrics()

    elif com in ("rating", "r", "rate"):
        # if only rate, or rating given print the song else set the rating
        if arg is None:
            print "Rating is out of 5"
            printCurrentSong()
        else:
            arg = int(arg)
            if 0 <= arg <= 5:
                rateSong(arg)
            else:
                print "Rating is out of 5 Only"

    elif com in ("shuffle", ):
        # check if shuffle is on
        if arg is None:
            flag = iProperties.Get("org.mpris.MediaPlayer2.Player", "Shuffle")
        else:
            flag = getBoolean(arg)
            iProperties.Set("org.mpris.MediaPlayer2.Player", "Shuffle", flag)

        printBoolean("Shuffle", flag)

    else:
        print "Unrecognized command"


if __name__ == "__main__":
    if len(sys.argv) == 1:
        print __doc__
    else:
        main(sys.argv[1:])
