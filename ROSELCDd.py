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
import requests
# For LCD2USB type of devices
from lcd2usb import LCD

VLUBCONFFILE = "/etc/ROSELCDd.conf"

from lcdbackpack import LcdBackpack
from mpd import MPDClient


def handler(signum, frame):
	print("Clearing display 1")
	for i in range(0,d.nb):
		if i == 0:
			name = d.name
		else:
			name = "Musical streamer"
		
		print("Printing on screen %d"%i)
		d.screens[i].display_ct(name,"Shutting down %d"%i)

	print("Clearing display 2")
	time.sleep(VLUBINITTIMEOUT)
	sys.exit(0)

signal.signal(signal.SIGINT, handler)

def sec2ms(sec):
	"""Transforms seconds sec into a printable chain "mm:ss" """
	"""Inspired from http://python.jpvweb.com/python/mesrecettespython/doku.php?id=compte_a_rebours """
	m=0
	s=int(sec)
	if s >= 60:
		m = s//60
		s -= m*60
	return "%02d:%02d" % (m, s)

def ms2mns(millis):
		"""Transforms milliseconds sec into a printable chain "mm:ss" """
		"""Inspired from https://stackoverflow.com/questions/35989666/convert-milliseconds-to-hours-min-and-seconds-python"""
		s =(millis/1000)%60
		m =(millis/(1000*60))%60
		h =(millis/(1000*60*60))%24
		return "%02d:%02d" % (m, s)

class VLUBSong:
	def __init__(self,player):

		if player != None:
			print("Creating object VLUBSong with player state %s"%player.state)
		else:
			print("Creating Fake object VLUBSong")
		# elapsed time
		self.et = 0
		# Mode in which we display metatdata if one screen
		self.title = ''
		self.oldtitle = 'old'

	def display(self,player,d):
		player.get_name()
		player.get_status()
		if player.state == 'play':
			self.oldtitle = self.title
			self.title = player.title
			self.seek = player.seek
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
			self.album = VLUBMSGSTATUSSTOPPED
			self.artist = player.name
			self.bitrate = "Some Good Music"
			self.seek = 0
			self.duration = 0
			self.url = ""
			self.service = ""
		elif player.state == 'pause':
			self.title = "Waiting for"
			self.album = VLUBMSGSTATUSPAUSED
			self.artist = player.name
			self.bitrate = "Some Good Music"
			self.seek = player.seek
			self.duration = 0
			self.url = ""
			self.service = ""

		else:
			print('Player in mode: %s'%str(player.state))
			self.title = "Waiting for"
			self.album = "Status Maintenance"
			self.artist = player.name
			self.bitrate = "Some Fix ..."
			self.seek = 0
			self.duration = 0
			self.url = ""
			self.service = ""
		print('Song created',self.artist, self.album, self.title, self.bitrate, self.seek, self.url)

		# Handle monoscreen case
		if self.et%VLUBFLIP == 0:
			d.flag = not d.flag
		d.display(self)
		# As we loop every VLUBLOOP seconds
		self.et += VLUBLOOP

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
				try:
					self.state = str(data['status'])
				except:
					self.state = ''
				try:
					print('TYPE: %s',type(data['title']))
				except:
					pass
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
				try:
					self.uri = unicodedata.normalize('NFKD',data['uri']).encode('ascii','ignore')
				except:
					self.uri = ""
				try:
					self.duration = str(data['duration'])
				except:
					self.duration = 0
				try:
					self.seek = str(data['seek'])
				except:
					self.seek = 0
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
		print("Creating object VLUBplayer on %s:%s"%(VLUBMPDHOST,VLUBMPDPORT))
		client = MPDClient()				# create client object
		client.timeout = None				# network timeout in seconds (floats allowed), default: None
		client.use_unicode = True			# Can be switched back later
		client.idletimeout = None			# timeout for fetching the result of the idle command is handled seperately, default:$
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
	def __init__(self,id,type,lines,columns,port,speed,color,brightness,contrast):
		print("Creating object VLUBScreen %s",id)
		self.id = id
		self.lines = lines
		self.columns = columns
		self.__port = port
		self.__speed = speed
		self.__offset = 0
		self.type = type
		if type == "LCD2USB":
			self.scr = LCD()
			self.scr.info()
			self.__port = "USB device"
			self.__speed = "unknown speed"
		else:
			self.scr = LcdBackpack(port, speed)
		self.color = color
		self.brightness = brightness
		self.contrast = contrast
		if type != "LCD2USB":
			self.scr.connect()
			self.scr.display_on()
		# Clear the screen
		self.scr.clear()
		if type != "LCD2USB":
			#set the blinking cursor to off - True for this !
			self.scr.set_block_cursor(True)
			#set autoscrolling to off
			self.scr.set_autoscroll(False)
		if type == "LCD" or type == "LCD2USB":
			self.scr.set_brightness(brightness)
			self.scr.set_contrast(contrast)
		if type == "LCD":
			self.scr.set_backlight_rgb(color[0], color[1], color[2])
		print("screen %d created - %dx%d on %s at %d"%(id,columns,lines,port,speed))
	
	# display all messages centered on a given screen line by line
	def display_ct(self,*msg):
		if self.type == "LCD2USB":
			for l in range(0,self.lines):
				print("Printing %s on line %d of screen %d"%(msg[l],l+1,self.id))
				self.display_line_ct(l,msg[l])
		else:
			for l in range(self.lines,0,-1):
				print("Printing %s on line %d of screen %d"%(msg[self.lines-l],l,self.id))
				self.display_line_ct(l,msg[self.lines-l])

	# display centered on a single line of a given screen
	def display_line_ct(self,line,text):
		output = text.center(self.columns, ' ')
		if self.type != "LCD2USB":
			self.scr.set_cursor_position(1,line)
		else:
			self.scr.goto(1,line)
		#set autoscrolling to correct value based on config file - not for LCD2USB
		#self.scr.set_autoscroll(False)
		if len(output) > self.columns:
			if VLUBMODE == "fixed":
				self.scr.write(output[:self.columns-3:]+'...')
			elif VLUBMODE == "scrolling":
				self.__offset = self.__offset + 1
				# Adds space to end properly the string (erase the last char moving forward)
				# Number of space is based on text end and columns (length of screen)
				self.scr.write(output[self.__offset:self.__offset+self.columns]+" ")
				if self.__offset == len(output):
					self.__offset = -1
			else:
				print("Error in conf file: mode %s unknown"%(VLUBMODE))
		else:
			self.scr.write(output)
		
	def __del__(self):
		print("Clearing scren %d"%self.id)
		self.scr.clear()
		if self.type != "LCD2USB":
			self.scr.display_off()
			self.scr.disconnect()
		else:
			self.scr.set_brightness(0)
			self.scr.close()
		
class VLUBDisplay:
	def __display_ct__(self,*msg):
		pass

	def display(self,s):
		# Display msg based on number of screens
		if self.nb == 1:
			# If we have 1 screen, we limit the display to title and artist then rotate with album and bit rate
			if self.flag:
				self.screens[0].display_ct(s.artist,s.album)
			else:
				self.screens[0].display_ct(s.title,s.bitrate)
		if self.nb == 2:
			# If we have 2 screens, we limit the display to title and artist + album and bit rate
			# TODO: externalyze in a table the allocation of fields into spaces
			self.screens[0].display_ct(s.artist,s.album)
			# If we have 2 screens, we rotate betwwen elapsed time and bit rate if seek exists
			if self.flag and s.seek != 0:
				self.screens[1].display_ct(s.title,s.bitrate)
			else:
				self.screens[1].display_ct(s.title,"-- "+ms2mns(int(s.seek))+" --")

	def __init__(self,*screens):
		# nb equal the number of screens so starts at 1
		self.nb = len(screens)
		self.screens = screens
		self.name = str(platform.node())
		self.flag = True

		print("Creating object VLUBDisplay (%s) with %d screens"%(self.name,self.nb))
		for i in range(0,self.nb):
			if i == 0:
				name = self.name
			else:
				name = "Musical streamer"
			
			self.screens[i].display_ct(name,"Starting on %d"%i)

	def __del__(self):
		print("Clearing display")
			
# To display a specific string at startup
init = True

# Hardcoded default values
DEFVLUBSCREENS = 2
DEFVLUBCOLOR = 255,255,255
DEFVLUBBRIGHTNESS = 200
DEFVLUBCONTRAST = 220
DEFVLUBROWS = 2
DEFVLUBCOLUMNS = 16
DEFVLUBSPEED = 115200
DEFVLUBDEVICE = "/dev/ttyACM"
DEFVLUBTYPE = "OLED"
# Loop every second by default
DEFVLUBLOOP = 1
# If one screen flip between metadata every 5 seconds by default
DEFVLUBFLIP = 5
#
DEFVLUBINITTIMEOUT = 5
DEFVLUBMODE = "fixed"

#Volmuio CLient Connection Settings
DEFVLUBHOST = 'localhost'
DEFVLUBPORT = '3000'
#MPD CLient Connection Settings
DEFVLUBMPDHOST = 'localhost'
DEFVLUBMPDPORT = '6600'
DEFVLUBMPDPASSWORD = False
##
DEFVLUBMSGSTATUSSTOPPED = "Status Stopped"
DEFVLUBMSGSTATUSPAUSED = "Status Paused"

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
	VLUBCOLOR = [int(x) for x in screen.get('color', DEFVLUBCOLOR).split(',')]
	VLUBBRIGHTNESS = int(screen.get('brightness', DEFVLUBBRIGHTNESS))
	VLUBCONTRAST = int(screen.get('contrast', DEFVLUBCONTRAST))
	VLUBROWS = int(screen.get('rows', DEFVLUBROWS))
	VLUBCOLUMNS = int(screen.get('columns', DEFVLUBCOLUMNS))
	VLUBSPEED = int(screen.get('speed', DEFVLUBSPEED))
	VLUBDEVICE = screen.get('device', DEFVLUBDEVICE)
	VLUBTYPE = screen.get('type', DEFVLUBTYPE)
	VLUBMODE = screen.get('mode', DEFVLUBMODE)
else:
	VLUBSCREENS = DEFVLUBSCREENS
	VLUBCOLOR = DEFVLUBCOLOR
	VLUBBRIGHTNESS = DEFVLUBBRIGHTNESS
	VLUBCONTRAST = DEFVLUBCONTRAST
	VLUBROWS = DEFVLUBROWS
	VLUBCOLUMNS = DEFVLUBCOLUMNS
	VLUBSPEED = DEFVLUBSPEED
	VLUBDEVICE = DEFVLUBDEVICE
	VLUBTYPE = DEFVLUBTYPE
	VLUBMODE = DEFVLUBMODE

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

if 'Msg' in config:
	msg = config['Msg']
	VLUBMSGSTATUSSTOPPED = str(msg.get('Status Stopped', DEFVLUBMSGSTATUSSTOPPED))
	VLUBMSGSTATUSPAUSED = str(msg.get('Status Paused', DEFVLUBMSGSTATUSPAUSED))
else:
	VLUBMSGSTATUSSTOPPED = DEFVLUBMSGSTATUSSTOPPED
	VLUBMSGSTATUSPAUSED = DEFVLUBMSGSTATUSPAUSED

# Our LCD/LCD2USB/OLED/... Display
s = []
for i in range(0,VLUBSCREENS):
	s.append(VLUBScreen(i, VLUBTYPE, VLUBROWS, VLUBCOLUMNS, VLUBDEVICE+str(i), VLUBSPEED, VLUBCOLOR, VLUBBRIGHTNESS, VLUBCONTRAST))
# use the screens found
d = VLUBDisplay(*s)
time.sleep(VLUBINITTIMEOUT)

#s0.display_ct(1,"  player.name ")
#s1.display_ct(2,"  Initializing ")

# Talking to our MDP daemon
p = VLUBPlayer()
s = VLUBSong(p)

#display info
# We're a daemon, so loop forever
while True:
	# display info
	s.display(p,d)
	time.sleep(VLUBLOOP)

