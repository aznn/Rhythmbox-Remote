# What is this?
RhythmRemote is a Command Line remote to control Rhythm Box (Tested with 2.97). 

- rhythmRemote.py - Contains the main and the code for all functions
- fuzzySearch.py  - Search module for the `play` command.

# Commands
`start`      - Starts playing (Play)
`pause`       - Pause
`next`        - Plays next song in the playlist
`prev`, `p`  - Plays previous song in playlist
`what`, `w`   - Displays information about the song playing now
`play`        - Plays the song, searches your media library folder. (look in fuzzySearch.py). see `play --help`
`lyrics`, `l` - Downloads lyrics from chartlyrics.com and displays with less
`rating [rate out of 5]`      - Displays the current song rating/rate the current song
`shuffle [on/off]`     - Displays if shuffle is on/switch shuffle on or off

# Improvements I'd like to do
- Make the `play` command work with the RhythmDB instead of the Media Folder. This would make it much more flexible. 
- Store downloaded lyrics so it only has to be downloaded once.