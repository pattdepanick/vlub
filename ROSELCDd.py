#!/usr/bin/python2
# -*- coding: utf8 -*-

import sys
import signal
import time
import unicodedata
import re
import json
import platform
from io import BytesIO
#from urllib2 import requests, urlopen, URLError, HTTPError;
import requests

LVUBINITTIMEOUT = 5

from lcdbackpack import LcdBackpack
from mpd import MPDClient


# We have 2 LCD displays of 2 lines of 16 columns
LVUBSCREENS = 2
LVUBROWS = 2
LVUBCOLUMNS = 16
LVUBSPEED = 115200
# Loop every second by default
LVUBLOOP = 1
# If one screen flip between metadata every 5 seconds by default
LVUBFLIP = 5

#Volmuio CLient Connection Settings
LVUBHOST = 'localhost'
LVUBPORT = '3000'
#MPD CLient Connection Settings
LVUBMPDHOST = 'localhost'
LVUBMPDPORT = '6600'
LVUBMPDPASSWORD = False
##
	
class LVUBSong:
	def __init__(self,player):

		print("Creating object LVUBSong with player state",player.state)
		# elapsed time
		self.et = 0
		# Mode in which we display metatdata if one screen
		self.flag = True
		self.title = ''
		self.oldtitle = 'old'

	def display(self,player,lcds):
		player.get_status()
		if player.state == 'play':
			self.oldtitle = self.title
			self.title = player.title
			# Reset elapsed time as we changed song
			if self.oldtitle != self.title:
				self.et = 0
			self.album = player.album
			self.artist = player.artist
			self.service = player.service
			if player.samplerate != '' and player.bitdepth != '':
				self.bitrate = player.samplerate+"|"+player.bitdepth+'s'
			else:
				# volumio doesn't provide samplerate for webradio
				if self.service == 'webradio':
					mpd = LVUBMPDPlayer()
					try:
						bitrate = str(mpd.player.status()['audio'])
					except KeyError:
						bitrate = '0000:00:0'
					print('Found bitrate: %s'%bitrate)
					m = re.search(r'([1-9]+)[0-9]00:([1-9][0-9]):.*', bitrate)
					if m == None:
						self.bitrate = '0000:00:0'
					else:
						self.bitrate = m.group(1)+' KHz|'+m.group(2)+' bits'
					mpd.__del__()
				else:
					self.bitrate = 'Empty bitrate'
			self.duration = player.duration
			self.url = player.uri
			print("URL:",self.url)

		elif player.state == 'stop':
			self.title = "Choose now"
			self.album = "Status stopped"
			self.artist = "Musical Streamer"
			self.bitrate = "Some good music"
			self.duration = 0
			self.url = ""
			self.service = ""
		elif player.state == 'pause':
			self.title = "Waiting for"
			self.album = "Status paused"
			self.artist = "Musical Streamer"
			self.bitrate = "Some good music"
			self.duration = 0
			self.url = ""
			self.service = ""

		else:
			print('Player in mode: %s'%str(player.state))
			self.title = "Waiting for"
			self.album = "Status maintenance"
			self.artist = "Musical Streamer"
			self.bitrate = "Some good music"
			self.duration = 0
			self.url = ""
			self.service = ""
		print('Song created',self.artist, self.album, self.title, self.bitrate, self.url)

		# Handle monoscreen case
		if self.et%LVUBFLIP == 0:
			self.flag = not self.flag
		# As we loop every LVUBLOOP seconds
		self.et += LVUBLOOP

		if lcds.nb == 1:
			# If we have 1 screen, we limit the display to title and artist (later rotate with album and bit rate)
			if self.flag:
				lcds.screens[0].display_ct(1,s.artist)
				lcds.screens[0].display_ct(2,s.album)
			else:
				lcds.screens[0].display_ct(1,s.title)
				lcds.screens[0].display_ct(2,s.bitrate)

		if lcds.nb == 2:
			# If we have 2 screens, we limit the display to title and artist + album and bit rate
			# TODO: externalyze in a table the allocation of fields into spaces
			lcds.screens[0].display_ct(1,s.artist)
			lcds.screens[0].display_ct(2,s.album)
			lcds.screens[1].display_ct(1,s.title)
			lcds.screens[1].display_ct(2,s.bitrate)

class LVUBPlayer():

	def __init__(self):
		print("Creating object LVUBPplayer on %s:%s"%(LVUBHOST,LVUBPORT))
		self.state = "init"

	def get_status(self):
		# Possible status for volumio
		stat = [ 'play', 'stop', 'pause']
		try:
			req = requests.get("http://"+LVUBHOST+":"+LVUBPORT+"/api/v1/getstate")
			print ("Return code: ",req.status_code)
		except:
			print 'We failed to reach a server.'
		else:
			# For successful API call, response code will be 200 (OK)
			if (req.ok):
    				# Loading the response data into a dict variable
    				data = json.loads(req.content)
				self.state = str(data['status'])
				print('TYPE: %s',type(data['title']))
				try:
					self.service = str(data['service'])
				except:
					try:
						self.service = str(data['trackType'])
					except:
						self.service = ''
				try:
					self.title = unicodedata.normalize('NFKD',data['title']).encode('ascii','ignore')
				except:
					self.title = "Empty Title"
				try:
					self.artist = unicodedata.normalize('NFKD',data['artist']).encode('ascii','ignore')
				except:
					self.artist = "Empty Artist"
				try:
					self.album = unicodedata.normalize('NFKD',data['album']).encode('ascii','ignore')
				except:
					if self.service != '':
						self.album = self.service
					else:
						self.album = "Empty Album"
				self.uri = unicodedata.normalize('NFKD',data['uri']).encode('ascii','ignore')
				try:
					self.duration = str(data['duration'])
				except:
					self.duration = 0
				try:
					self.samplerate = str(data['samplerate'])
				except:
					self.samplerate = ""
				try:
					self.bitdepth = str(data['bitdepth'])
				except:
					self.bitdepth = ""
				print("LVUBPplayer has state ",self.state)
				if self.state not in stat:
					mystate = 'maintenance'
				else:
					mystate = self.state
				print("Player State: %s "%mystate)
				self.state = mystate
				return mystate
		
class LVUBMPDPlayer(MPDClient):
	def __init__(self):
		print("Creating object LVUBPplayer on %s:%s"%(LVUBMPDHOST,LVUBMPDPORT))
		client = MPDClient()               # create client object
		client.timeout = None              # network timeout in seconds (floats allowed), default: None
		client.use_unicode = True          # Can be switched back later
		client.idletimeout = None          # timeout for fetching the result of the idle command is handled seperately, default:$
		client.connect(LVUBMPDHOST, LVUBMPDPORT)
		# Required so that fetch/send_idle methods work on a LVUBPlayer object
		for atr in dir(client):
			if atr[:1] == '_' and atr[1:2] != '_':
				setattr(self, atr, getattr(client,atr))
		self.player = client
		self.state = str(self.player.status()['state'])
		print("LVUBPplayer has state ",self.state)
		
	def get_status(self):
		#stat = [ 'play', 'stop', 'pause', 'addtagid', 'prio', 'move', 'setvol', 'kill', 'find', 'listallinfo', 'previous', 'mixrampdb', 'listplaylistinfo', 'pause', 'toggleoutput', 'add', 'swap','plchangesposid', 'save', 'seekid', 'random', 'playlistsearch', 'stop', 'playlistfind', 'sendmessage', 'password', 'listall', 'playlistclear', 'config', 'list','listplaylists', 'clearerror', 'tagtypes', 'searchaddpl', 'playid', 'close', 'replay_gain_mode', 'stats', 'enableoutput', 'mixrampdelay', 'rm', 'lsinfo', 'swapid','urlhandlers', 'addid', 'search', 'disableoutput', 'playlistid', 'findadd', 'prioid', 'load', 'shuffle', 'consume', 'rangeid', 'rescan', 'channels', 'subscribe','crossfade', 'playlistinfo', 'replay_gain_status', 'readmessages', 'playlist', 'notcommands', 'next', 'listplaylist', 'playlistadd', 'outputs', 'commands','unsubscribe', 'currentsong', 'count', 'searchadd', 'cleartagid', 'seekcur', 'mount', 'idle', 'playlistmove', 'readcomments', 'delete', 'rename', 'decoders','single', 'listfiles', 'seek', 'ping', 'listmounts', 'status', 'play', 'repeat', 'update', 'plchanges', 'playlistdelete', 'clear', 'moveid', 'deleteid' ]
		stat = [ 'play', 'stop', 'pause']
		if self.player.status()['state'] not in stat:
			self.player.disconnect()
			self.player.connect(LVUBHOST, LVUBPORT)
			mystate = 'maintenance'
		else:
			mystate = str(self.player.status()['state'])
		print("Player State: %s "%mystate)
		self.state = mystate
		return mystate
		
	def __del__(self):
		self.player.disconnect() 
		
	def send_idle(self):
		print("send_idle called")
		super(LVUBPlayer, self).send_idle()
		
	def fetch_idle(self):
		print("fetch_idle called")
		super(LVUBPlayer, self).fetch_idle()
		self.get_status()

class LVUBScreen:
	def __init__(self,id,lines,columns,port,speed):
		print("Creating object LVUBScreen %s",id)
		self.id = id
		self.lines = lines
		self.columns = columns
		self.__port = port
		self.__speed = speed
		self.lcd = LcdBackpack(port, speed)
		self.lcd.connect()
		#set display color
                #red
                self.lcd.set_backlight_rgb(0xFF, 0, 0)
                #blue
                #self.lcd.set_backlight_rgb(0, 0, 0xFF)
                #green
                #self.lcd.set_backlight_rgb(0, 0xFF, 0)
                #white
                #self.lcd.set_backlight_rgb(0xFF, 0xFF, 0xFF)
                #set brightness Sets the brightness of the LCD backlight:param brightness: integer value from 0 - 255
                self.lcd.set_brightness(180)
                #set contrast Sets the contrast of the LCD character text:param contrast: integer value from 0 - 255
                self.lcd.set_contrast(180)
		self.lcd.clear()
		print("Screen %d created - %dX%d on %s at %d"%(id,columns,lines,port,speed))
	
	# Display centered
	def display_ct(self,line,text):
		output = text.center(self.columns, ' ')
		self.lcd.set_cursor_position(1,line)
		
		if len(output) > self.columns:
			self.lcd.write(output[:self.columns-3:]+'...')			
		else:
			self.lcd.write(output)
		
	def __del__(self):
		self.lcd.disconnect()
		
class LVUBDisplay:
	def __init__(self,*screens):
		# nb equal the number of screens so starts at 1
		self.nb = len(screens)
		self.screens = screens
		self.name = str(platform.node())

		print("Creating object LVUBDisplay (%s) with %d screens"%(self.name,self.nb))
		for i in range(0,self.nb):
			if i == 0:
				name = self.name
			else:
				name = "Musical streamer"
			self.screens[i].display_ct(1,name)
			self.screens[i].display_ct(2,"Starting on %d"%i)

	def __del__(self):
		for i in range(0,self.nb):
			if i == 0:
				name = self.name
			else:
				name = "Musical streamer"
			print("Display name (%d) is : %s",(i,name))
			self.screens[i].display_ct(1,name)
			self.screens[i].display_ct(2,"Shutting down %d"%i)

			
# To display a specific string at startup
init = True

# Our LCD/OLED/... Display
s0 = LVUBScreen(0, LVUBROWS, LVUBCOLUMNS, "/dev/ttyACM0", LVUBSPEED)
s1 = LVUBScreen(1, LVUBROWS, LVUBCOLUMNS, "/dev/ttyACM1", LVUBSPEED)
# test with two screens
d = LVUBDisplay(s0, s1)
# test with one screen only
#d = LVUBDisplay(s0)
time.sleep(LVUBINITTIMEOUT)

#s0.display_ct(1,"Salut Fredo xxxxxxxxx")
#s1.display_ct(2,"Salut Bruno yyyyyyyyy")

# Talking to our MDP daemon
p = LVUBPlayer()
s = LVUBSong(p)

#display info
# We're a daemon, so loop forever
while True:
	# display info
	s.display(p,d)
	time.sleep(LVUBLOOP)
