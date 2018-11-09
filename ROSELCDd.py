#!/usr/bin/python2
# -*- coding: utf8 -*-

import sys
import signal
import time
LVUBINITTIMEOUT = 5

from lcdbackpack import LcdBackpack
from mpd import MPDClient


# We have 2 LCD displays of 2 lines of 16 columns
LVUBSCREENS = 2
LVUBROWS = 2
LVUBCOLUMNS = 16
LVUBSPEED = 115200

#MPD CLient Connection Settings
HOST = 'localhost'
PORT = '6600'
PASSWORD = False
##
CON_ID = {'host':HOST, 'port':PORT}

	
class LVUBSong:
	def __init__(self,player):
		
		if player.status == 'play':
			self.title = player.currentsong()['title']
			self.album = player.currentsong()['album']
			self.artist = player.currentsong()['artist']
			self.bitrate = player.status()['audio']
			self.duration = player.currentsong()['duration']
			self.source = player.currentsong()['file']
		elif player.status == 'stop':
			self.title = "Choose now"
			self.album = "Status stopped"
			self.artist = "Musical Streamer"
			self.bitrate = "Some good music"
			self.duration = 0
			self.source = ""
		elif player.status == 'pause':
			self.title = "Waiting for"
			self.album = "Status paused"
			self.artist = "Musical Streamer"
			self.bitrate = "Some good music"
			self.duration = 0
			self.source = ""
		else:
			self.title = "Waiting for"
			self.album = "Status strange"
			self.artist = "Musical Streamer"
			self.bitrate = "Some good music"
			self.duration = 0
			self.source = ""

class LVUBSongRadio(LVUBSong):
	pass
	
class LVUBSongFile(LVUBSong):
	pass
	
class LVUBPlayer:
	def __init__(self):
		client = MPDClient()               # create client object
		client.timeout = None              # network timeout in seconds (floats allowed), default: None
		client.use_unicode = True          # Can be switched back later
		client.idletimeout = None          # timeout for fetching the result of the idle command is handled seperately, default:$
		client.connect("localhost", 6600)  # connect to localhost:6600
		self.player = client
		
	def status(self):
		#stat = [ 'play', 'stop', 'pause', 'addtagid', 'prio', 'move', 'setvol', 'kill', 'find', 'listallinfo', 'previous', 'mixrampdb', 'listplaylistinfo', 'pause', 'toggleoutput', 'add', 'swap','plchangesposid', 'save', 'seekid', 'random', 'playlistsearch', 'stop', 'playlistfind', 'sendmessage', 'password', 'listall', 'playlistclear', 'config', 'list','listplaylists', 'clearerror', 'tagtypes', 'searchaddpl', 'playid', 'close', 'replay_gain_mode', 'stats', 'enableoutput', 'mixrampdelay', 'rm', 'lsinfo', 'swapid','urlhandlers', 'addid', 'search', 'disableoutput', 'playlistid', 'findadd', 'prioid', 'load', 'shuffle', 'consume', 'rangeid', 'rescan', 'channels', 'subscribe','crossfade', 'playlistinfo', 'replay_gain_status', 'readmessages', 'playlist', 'notcommands', 'next', 'listplaylist', 'playlistadd', 'outputs', 'commands','unsubscribe', 'currentsong', 'count', 'searchadd', 'cleartagid', 'seekcur', 'mount', 'idle', 'playlistmove', 'readcomments', 'delete', 'rename', 'decoders','single', 'listfiles', 'seek', 'ping', 'listmounts', 'status', 'play', 'repeat', 'update', 'plchanges', 'playlistdelete', 'clear', 'moveid', 'deleteid' ]
		stat = [ 'play', 'stop', 'pause']
		if self.player.status()['state'] not in stat:
			self.player.disconnect()
			self.player.connect("localhost", 6600)
			mystate = 'maintenance'
		else
			mystate = self.player.status()['state']
		print("Player State :  %s "%mystate)
		return mystate
		
	#def status(self,player,mixer,playlist,database,update,scan,output,options,sticker):
	#	stat = [ 'play', 'stop', 'pause' ]
	#	if status.player()['state'] not in stat:
	#		client.disconnect()
	#		client.connect("localhost", 6600)	
	#	return status()['state']
		
	def __del__(self):
		self.player.disconnect() 

class LVUBScreen:
	def __init__(self,id,lines,columns,port,speed):
		self.id = id
		self.lines = lines
		self.columns = columns
		self.__port = port
		self.__speed = speed
		self.lcd = LcdBackpack(port, speed)
		self.lcd.connect()
		self.lcd.clear()
		print("Screen %d created - %dX%d on %s at %d"%(id,columns,lines,port,speed))
		self.lcd.write("Musical streamerStarting on %d"%self.id)
		
	# We need a function to display a text on a line
	# centered and truncated if needed to columns chars
	def display_ct(self,line,text):
		output = text.center(self.columns, ' ')
		self.lcd.clear()
		self.lcd.set_cursor_position(1,line)
		if len(output) > self.columns:
			self.lcd.write(output[:self.columns-3:]+'...')			
		else:
			self.lcd.write(output)
		
	def __del__(self):
		self.lcd.disconnect() 
		
class LVUBDisplay:
	def __init__(self,*screens):
		self.nb = len(screens)
		self.screens = screens
		print("Display created with %d screens"%(self.nb))

	def display_song(self,player):
		# Some logic is needed here
		# If we have 1 screen, we limit the display to title and artist (later rotate with album and bit rate)
		# If we have 2 screens, we limit the display to title and artist + album and bit rate
		if self.nb == 1:
			pass
		if self.nb == 2:
			s = LVUBSong(player)
			self.screens[0].display_ct(1,s.artist)
			self.screens[0].display_ct(2,s.album)
			self.screens[1].display_ct(1,s.title)
			self.screens[1].display_ct(2,s.bitrate)
			
# To display a specific string at startup
init = True
# Talking to our MDP daemon
p = LVUBPlayer
# Our LCD/OLED/... Display
s0 = LVUBScreen(0, LVUBROWS, LVUBCOLUMNS, "/dev/ttyACM0", LVUBSPEED)
s1 = LVUBScreen(1, LVUBROWS, LVUBCOLUMNS, "/dev/ttyACM1", LVUBSPEED)
time.sleep(LVUBINITTIMEOUT)

#s0.display_ct(1,"Salut Fredo xxxxxxxxx")
#s1.display_ct(2,"Salut Bruno yyyyyyyyy")
p = LVUBPlayer()
d = LVUBDisplay(s0, s1)

#display info
# We're a daemon, so loop forever
while True:
	# display info
	d.display_song(p)
	time.sleep(1)