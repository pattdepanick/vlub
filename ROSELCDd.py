#!/usr/bin/python2
# -*- coding: utf8 -*-

import sys
import signal
import time
import unicodedata
import re
import json
from io import BytesIO
from urllib2 import Request, urlopen, URLError

LVUBINITTIMEOUT = 5

from lcdbackpack import LcdBackpack
from mpd import MPDClient


# We have 2 LCD displays of 2 lines of 16 columns
LVUBSCREENS = 2
LVUBROWS = 2
LVUBCOLUMNS = 16
LVUBSPEED = 115200

#MPD CLient Connection Settings
LVUBHOST = 'localhost'
LVUBPORT = '6600'
LVUBPASSWORD = False
##
	
class LVUBSong:
	def __init__(self,player):
		
		if player.state == 'play':
			try:
				self.title = unicodedata.normalize('NFKD',player.currentsong()['title']).encode('ascii','ignore')
			except KeyError:
				self.title = 'Empty title'
			try:
				self.album = unicodedata.normalize('NFKD',player.currentsong()['album']).encode('ascii','ignore')
			except KeyError:
				self.album = 'Empty album'
			try:
				self.artist = unicodedata.normalize('NFKD',player.currentsong()['artist']).encode('ascii','ignore')
			except KeyError:
				self.artist = 'Empty artist'
			try:
				self.trackType = unicodedata.normalize('NFKD',player.currentsong()['trackType']).encode('ascii','ignore')
			except KeyError:
				self.trackType = 'Empty tracktype'
			try:
				bitrate = str(player.player.status()['audio'])
			except KeyError:
				bitrate = '0000:00:0'
			print('Found bitrate: %s'%bitrate)
			m = re.search(r'([1-9]+)[0-9]00:([1-9][0-9]):.*', bitrate)
			if m == None:
				self.bitrate = '0000:00:0'
			else:
				self.bitrate = m.group(1)+' KHz|'+m.group(2)+' bits'
			try:
				self.duration = player.currentsong()['duration']
			except KeyError:
				self.duration = 0
			try:
				self.url = unicodedata.normalize('NFKD',player.currentsong()['file']).encode('ascii','ignore')
			except KeyError:
				self.url = 'Empty url'
			print("URL:",self.url)
			m = re.search(r'^http[s]*://',self.url)
			if m == None:
				# It's a file
				self.source = 'file'
			else:
				self.source = 'webradio'
				req = Request(self.url)
				try:
					response = urlopen(req)
				except HTTPError as e:
					print 'The server couldn\'t fulfill the request.'
					print 'Error code: ', e.code
				except URLError as e:
					print 'We failed to reach a server.'
					print 'Reason: ', e.reason
				else:
					# everything is fine
					self.album = 'WebRadio'
					try:
						self.artist = response.info()['icy-name']
					except:
						m = re.search(r'qobuz.com',self.url)
						if m == None:
							self.artist = 'Unknown'
						else:
							self.artist = 'Qobuz'
							self.album = 'Empty Artist'
							# In the URL we have eid=<ongid> we can use to query /data/queue
							m = re.search('(?<=eid=)([0-9]+)',self.url)
							print("EID:",m.group(0))
							with open('/data/queue') as handle:
									dictdump = json.loads(handle.read())
							for s in dictdump:
								print(s['uri'])
								m1 = re.search(r'/'+re.escape(m.group(0)),s['uri'])
								if m1 == None:
									pass
								else:
									self.album = s['album'].encode('ascii','ignore')
									self.artist = s['artist'].encode('ascii','ignore')
									self.title = s['title'].encode('ascii','ignore')
									break
					print('webradio: %s'%self.artist)

		elif player.state == 'stop':
			self.title = "Choose now"
			self.album = "Status stopped"
			self.artist = "Musical Streamer"
			self.bitrate = "Some good music"
			self.duration = 0
			self.url = ""
			self.source = ""
		elif player.state == 'pause':
			self.title = "Waiting for"
			self.album = "Status paused"
			self.artist = "Musical Streamer"
			self.bitrate = "Some good music"
			self.duration = 0
			self.url = ""
			self.source = ""

		else:
			print('Player in mode: %s'%str(player.state))
			self.title = "Waiting for"
			self.album = "Status maintenance"
			self.artist = "Musical Streamer"
			self.bitrate = "Some good music"
			self.duration = 0
			self.url = ""
			self.source = ""

	
class LVUBPlayer(MPDClient):
	def __init__(self):
		client = MPDClient()               # create client object
		client.timeout = None              # network timeout in seconds (floats allowed), default: None
		client.use_unicode = True          # Can be switched back later
		client.idletimeout = None          # timeout for fetching the result of the idle command is handled seperately, default:$
		client.connect(LVUBHOST, LVUBPORT)
		# Required so that fetch/send_idle methods work on a LVUBPlayer object
		for atr in dir(client):
			if atr[:1] == '_' and atr[1:2] != '_':
				setattr(self, atr, getattr(client,atr))
		self.player = client
		self.state = str(self.player.status()['state'])
		
	def get_status(self):
		#stat = [ 'play', 'stop', 'pause', 'addtagid', 'prio', 'move', 'setvol', 'kill', 'find', 'listallinfo', 'previous', 'mixrampdb', 'listplaylistinfo', 'pause', 'toggleoutput', 'add', 'swap','plchangesposid', 'save', 'seekid', 'random', 'playlistsearch', 'stop', 'playlistfind', 'sendmessage', 'password', 'listall', 'playlistclear', 'config', 'list','listplaylists', 'clearerror', 'tagtypes', 'searchaddpl', 'playid', 'close', 'replay_gain_mode', 'stats', 'enableoutput', 'mixrampdelay', 'rm', 'lsinfo', 'swapid','urlhandlers', 'addid', 'search', 'disableoutput', 'playlistid', 'findadd', 'prioid', 'load', 'shuffle', 'consume', 'rangeid', 'rescan', 'channels', 'subscribe','crossfade', 'playlistinfo', 'replay_gain_status', 'readmessages', 'playlist', 'notcommands', 'next', 'listplaylist', 'playlistadd', 'outputs', 'commands','unsubscribe', 'currentsong', 'count', 'searchadd', 'cleartagid', 'seekcur', 'mount', 'idle', 'playlistmove', 'readcomments', 'delete', 'rename', 'decoders','single', 'listfiles', 'seek', 'ping', 'listmounts', 'status', 'play', 'repeat', 'update', 'plchanges', 'playlistdelete', 'clear', 'moveid', 'deleteid' ]
		stat = [ 'play', 'stop', 'pause']
		if self.player.status()['state'] not in stat:
			self.player.disconnect()
			self.player.connect(LVUBHOST, LVUBPORT)
			mystate = 'maintenance'
		else:
			mystate = str(self.player.status()['state'])
		print("Player State :  %s "%mystate)
		self.state = mystate
		return mystate
		
	def __del__(self):
		self.player.disconnect() 
		
	def send_idle(self):
		super(LVUBPlayer, self).send_idle()
		
	def fetch_idle(self):
		super(LVUBPlayer, self).fetch_idle()
		self.get_status()

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
		print("Display created with %d screens"%(self.nb))

	def display_song(self,player):
		# Some logic is needed here
		# If we have 1 screen, we limit the display to title and artist (later rotate with album and bit rate)
		# If we have 2 screens, we limit the display to title and artist + album and bit rate
		if self.nb == 1:
			pass
		if self.nb == 2:
			s = LVUBSong(player)
			# TODO: externalyze in a table the allocation of fields into spaces
			print('Song created',s.artist, s.album, s.title, s.bitrate, s.url)
			self.screens[0].display_ct(1,s.artist)
			self.screens[0].display_ct(2,s.album)
			self.screens[1].display_ct(1,s.title)
			self.screens[1].display_ct(2,s.bitrate)
			
# To display a specific string at startup
init = True

# Our LCD/OLED/... Display
s0 = LVUBScreen(0, LVUBROWS, LVUBCOLUMNS, "/dev/ttyACM0", LVUBSPEED)
s1 = LVUBScreen(1, LVUBROWS, LVUBCOLUMNS, "/dev/ttyACM1", LVUBSPEED)
time.sleep(LVUBINITTIMEOUT)

#s0.display_ct(1,"Salut Fredo xxxxxxxxx")
#s1.display_ct(2,"Salut Bruno yyyyyyyyy")

# Talking to our MDP daemon
p = LVUBPlayer()
d = LVUBDisplay(s0, s1)

#display info
# We're a daemon, so loop forever
while True:
	# display info
	d.display_song(p)

	# Get status
	p.send_idle()
	p.fetch_idle()

	time.sleep(1)
