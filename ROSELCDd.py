#!/usr/bin/python2
# -*- coding: utf8 -*-

import sys
import os
import signal
import time
import unicodedata
import re
import json
import platform
import configparser
from io import BytesIO
#from urllib2 import requests, urlopen, URLError, HTTPError;
import requests

VLUBCONFFILE = "/etc/ROSELCDd.conf"

from lcdbackpack import LcdBackpack
from mpd import MPDClient


class VLUBSong:
	def __init__(self,player):

		print("Creating object VLUBSong with player state",player.state)
		# elapsed time
		self.et = 0
		# Mode in which we display metatdata if one screen
		self.flag = True
		self.title = ''
		self.oldtitle = 'old'

	def display(self,player,lcds):
		player.get_name()
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
			self.name = player.name
			if player.samplerate != '' and player.bitdepth != '':
				self.bitrate = player.samplerate+"|"+player.bitdepth+'s'
			else:
				# volumio doesn't provide samplerate for webradio
				if self.service == 'webradio':
					mpd = VLUBMPDPlayer()
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
			print ("PLayer Name:",self.name)

		elif player.state == 'stop':
			self.title = "Choose Now"
			self.album = "Status Stopped"
			self.artist = player.name
			self.bitrate = "Some Good Music"
			self.duration = 0
			self.url = ""
			self.service = ""
		elif player.state == 'pause':
			self.title = "Waiting for"
			self.album = "Status Paused"
			self.artist = player.name
			self.bitrate = "Some Good Music"
			self.duration = 0
			self.url = ""
			self.service = ""

		else:
			print('Player in mode: %s'%str(player.state))
			self.title = "Waiting for"
			self.album = "Status Maintenance"
			self.artist = player.name
			self.bitrate = "Some Fix ..."
			self.duration = 0
			self.url = ""
			self.service = ""
		print('Song created',self.artist, self.album, self.title, self.bitrate, self.url)

		# Handle monoscreen case
		if self.et%VLUBFLIP == 0:
			self.flag = not self.flag
		# As we loop every VLUBLOOP seconds
		self.et += VLUBLOOP

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

class VLUBPlayer():

	def __init__(self):
		print("Creating object VLUBPplayer on %s:%s"%(VLUBHOST,VLUBPORT))
		self.state = "init"

	def get_name(self):
		self.name = str(platform.node())
		print("Player Name: %s"%(self.name))

	def get_status(self):
		# Possible status for volumio
		stat = [ 'play', 'stop', 'pause']
		try:
			req = requests.get("http://"+VLUBHOST+":"+VLUBPORT+"/api/v1/getstate")
			print("Return code: ",req.status_code)
		except:
			print("We failed to reach the server at http://%s:%s/api/v1/getstate"%(VLUBHOST,VLUBPORT))
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
				print("VLUBPplayer has state ",self.state)
				if self.state not in stat:
					mystate = 'maintenance'
				else:
					mystate = self.state
				print("Player State: %s "%mystate)
				self.state = mystate
				return mystate
		
class VLUBMPDPlayer(MPDClient):
	def __init__(self):
		print("Creating object VLUBPplayer on %s:%s"%(VLUBMPDHOST,VLUBMPDPORT))
		client = MPDClient()               # create client object
		client.timeout = None              # network timeout in seconds (floats allowed), default: None
		client.use_unicode = True          # Can be switched back later
		client.idletimeout = None          # timeout for fetching the result of the idle command is handled seperately, default:$
		client.connect(VLUBMPDHOST, VLUBMPDPORT)
		# Required so that fetch/send_idle methods work on a VLUBPlayer object
		for atr in dir(client):
			if atr[:1] == '_' and atr[1:2] != '_':
				setattr(self, atr, getattr(client,atr))
		self.player = client
		self.state = str(self.player.status()['state'])
		print("VLUBPplayer has state ",self.state)
		
	def get_status(self):
		#stat = [ 'play', 'stop', 'pause', 'addtagid', 'prio', 'move', 'setvol', 'kill', 'find', 'listallinfo', 'previous', 'mixrampdb', 'listplaylistinfo', 'pause', 'toggleoutput', 'add', 'swap','plchangesposid', 'save', 'seekid', 'random', 'playlistsearch', 'stop', 'playlistfind', 'sendmessage', 'password', 'listall', 'playlistclear', 'config', 'list','listplaylists', 'clearerror', 'tagtypes', 'searchaddpl', 'playid', 'close', 'replay_gain_mode', 'stats', 'enableoutput', 'mixrampdelay', 'rm', 'lsinfo', 'swapid','urlhandlers', 'addid', 'search', 'disableoutput', 'playlistid', 'findadd', 'prioid', 'load', 'shuffle', 'consume', 'rangeid', 'rescan', 'channels', 'subscribe','crossfade', 'playlistinfo', 'replay_gain_status', 'readmessages', 'playlist', 'notcommands', 'next', 'listplaylist', 'playlistadd', 'outputs', 'commands','unsubscribe', 'currentsong', 'count', 'searchadd', 'cleartagid', 'seekcur', 'mount', 'idle', 'playlistmove', 'readcomments', 'delete', 'rename', 'decoders','single', 'listfiles', 'seek', 'ping', 'listmounts', 'status', 'play', 'repeat', 'update', 'plchanges', 'playlistdelete', 'clear', 'moveid', 'deleteid' ]
		stat = [ 'play', 'stop', 'pause']
		if self.player.status()['state'] not in stat:
			self.player.disconnect()
			self.player.connect(VLUBHOST, VLUBPORT)
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
		super(VLUBPlayer, self).send_idle()
		
	def fetch_idle(self):
		print("fetch_idle called")
		super(VLUBPlayer, self).fetch_idle()
		self.get_status()

class VLUBScreen:
	def __init__(self,id,lines,columns,port,speed):
		print("Creating object VLUBScreen %s",id)
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
		self.lcd.set_brightness(60)
		#set contrast Sets the contrast of the LCD character text:param contrast: integer value from 0 - 255
		self.lcd.set_contrast(180)
		#clear the lcd
		self.lcd.clear()
		#set the blinking cursor to off
		#self.lcd.block_cursor_off()
		#set autoscrolling of test to off
		#self.lcd.autoscroll_off()
		print("Screen %d created - %dX%d on %s at %d"%(id,columns,lines,port,speed))
	
	# Display centered
	def display_ct(self,line,text):
		output = text.center(self.columns, ' ')
		#self.lcd.autoscroll_off()
		#self.lcd.block_cursor_off()
		self.lcd.set_cursor_position(1,line)
		if len(output) > self.columns:
			self.lcd.write(output[:self.columns-3:]+'...')			
		else:
			self.lcd.write(output)
		
	def __del__(self):
		self.lcd.disconnect()
		
class VLUBDisplay:
	def __init__(self,*screens):
		# nb equal the number of screens so starts at 1
		self.nb = len(screens)
		self.screens = screens
		self.name = str(platform.node())

		print("Creating object VLUBDisplay (%s) with %d screens"%(self.name,self.nb))
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

# Hardcoded default values
DEFVLUBSCREENS = 2
DEFVLUBROWS = 2
DEFVLUBCOLUMNS = 16
DEFVLUBSPEED = 115200
DEFVLUBDEVICE = "/dev/ttyACM"
# Loop every second by default
DEFVLUBLOOP = 1
# If one screen flip between metadata every 5 seconds by default
DEFVLUBFLIP = 5
#
DEFVLUBINITTIMEOUT = 5

#Volmuio CLient Connection Settings
DEFVLUBHOST = 'localhost'
DEFVLUBPORT = '3000'
#MPD CLient Connection Settings
DEFVLUBMPDHOST = 'localhost'
DEFVLUBMPDPORT = '6600'
DEFVLUBMPDPASSWORD = False
##


# Manage a configuration file
config = configparser.ConfigParser()

exists = os.path.isfile(VLUBCONFFILE)
if exists:
	config.read(VLUBCONFFILE)

if 'Screen' in config:
	screen = config['Screen']
	# defaults forced
	# We have 2 LCD displays of 2 lines of 16 columns
	VLUBSCREENS = int(screen.get('nb', DEFVLUBSCREENS))
	VLUBROWS = int(screen.get('rows', DEFVLUBROWS))
	VLUBCOLUMNS = int(screen.get('columns', DEFVLUBCOLUMNS))
	VLUBSPEED = int(screen.get('speed', DEFVLUBSPEED))
	VLUBDEVICE = screen.get('device', DEFVLUBDEVICE)
else:
	VLUBSCREENS = DEFVLUBSCREENS
	VLUBROWS = DEFVLUBROWS
	VLUBCOLUMNS = DEFVLUBCOLUMNS
	VLUBSPEED = DEFVLUBSPEED
	VLUBDEVICE = DEFVLUBDEVICE

if 'Timeout' in config:
	timeout = config['Timeout']
	VLUBINITTIMEOUT = int(timeout.get('init', DEFVLUBINITTIMEOUT))
	VLUBLOOP = int(timeout.get('loop', DEFVLUBLOOP))
	VLUBFLIP = int(timeout.get('flip', DEFVLUBFLIP))
else:
	VLUBINITTIMEOUT = DEFVLUBINITTIMEOUT
	VLUBLOOP = DEFVLUBLOOP
	VLUBFLIP = DEFVLUBFLIP

if 'Volumio' in config:
	volumio = config['Volumio']
	VLUBHOST = str(volumio.get('host', DEFVLUBHOST))
	VLUBPORT = str(volumio.get('port', DEFVLUBPORT))
else:
	VLUBHOST = DEFVLUBHOST
	VLUBPORT = DEFVLUBPORT

if 'Mpd' in config:
	mpd = config['Mpd']
	VLUBMPDHOST = str(mpd.get('host', DEFVLUBMPDHOST))
	VLUBMPDPORT = str(mpd.get('port', DEFVLUBMPDPORT))
	VLUBMPDPASSWORD = mpd.getboolean('password', DEFVLUBMPDPASSWORD)
else:
	VLUBMPDHOST = DEFVLUBMPDHOST
	VLUBMPDPORT = DEFVLUBMPDPORT
	VLUBMPDPASSWORD = DEFVLUBMPDPASSWORD

# Our LCD/OLED/... Display
s = []
for i in range(0,VLUBSCREENS):
	s.append(VLUBScreen(i, VLUBROWS, VLUBCOLUMNS, VLUBDEVICE+str(i), VLUBSPEED))
# use the screens found
d = VLUBDisplay(*s)
time.sleep(VLUBINITTIMEOUT)

#s0.display_ct(1,"Salut Fredo xxxxxxxxx")
#s1.display_ct(2,"Salut Bruno yyyyyyyyy")

# Talking to our MDP daemon
p = VLUBPlayer()
s = VLUBSong(p)

#display info
# We're a daemon, so loop forever
while True:
	# display info
	s.display(p,d)
	time.sleep(VLUBLOOP)
