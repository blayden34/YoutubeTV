# -*- coding: utf-8 -*-
# Module: default
# Author: Roman V. M.
# Created on: 28.11.2014
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
###################
import sys
from urlparse import parse_qsl
import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon
###################
import urllib
import os
import subprocess
import datetime
import pickle
###################
class masterDebug():
	# master debug object for debugging plugin
	def __init__(self):
		self.banner(' PYTHON DEBUG ')
		self.text=[]
	def add(self,title=None,content=None):
		# - All arguments given here are casted to strings
		# if user gives two arguements the first is considered the title
		if content!= None:
			# append the content with a title
			self.text.append(str(title)+' : '+str(content))
			print(str(title)+' : '+str(content))
		else:
			# otherwise add the first argument as a debug line
			self.text.append(str(title))
			print(str(title))

	def get(self):
		# return the text array
		return self.text
	def banner(self,titleString=None):
		if titleString != None:
			title=str(titleString)
			edge='#'*((80-len(title))/2)
			print('#'*80)
			print(edge+title+edge)
			print('#'*80)
		else:
			print('#'*80)
	def display(self):
		# draw banner divider
		self.banner(' PYTHON DEBUG ')
		# write each line of the debug
		for line in self.text:
			# add debug to each line to use grep for error searching
			print('DEBUG:'+str(line))
		# draw bottom divider
		self.banner()
		#os.system('xterm -e bash -c \'echo "'+str(self.text)+'" | less\'')
# create master debug object
debug=masterDebug()
# session class for youtubeTV session starting
class YoutubeTV():
	def __init__(self):
		'''This object loads up the youtubeTV session for cache functionality and automated work.'''
		# create the cache for this session
		self.cache=self.loadConfig('cache','dict')
		# cache timer
		self.timer=self.loadConfig('timer','dict')
		# load the channels config
		self.channels=self.loadConfig('channels','array')
		# load the channels cache
		self.channelCache=self.loadConfig('channelCache','dict')
		debug.add('channel cache',self.channelCache)
		#self.addChannel('bluexephos')#DEBUG this is to see if any channels are picked up
		# update the channels
		for channel in self.channels:
			# if channel has no values
			if channel not in self.cache.keys():
				# create an array to sit in it
				self.cache[channel]=[]	
				#update the channel videos
				self.getUserVideos(channel)
	def saveFile(self,fileName,content):
		# open the file to write
		fileObject=open(('~/.kodi/userdata/addon_data/plugin.video.youtubetv/'+fileName),'w')
		# write file content
		fileObject.write(content)
		# close the file
		fileObject.close()
	def loadFile(self,fileName):
		# this is where all files related to the plugin will be stored
		basePath=('~/.kodi/userdata/addon_data/plugin.video.youtubetv/')
		# if the base config directory does not exist
		if os.path.exists(basePath) != True:
			# create the base config path 
			thumbnail=subprocess.Popen(['mkdir', '-p',basePath])
		# concat the basepath and file fileName for the file to load
		path=(basePath+fileName)
		# check if the config file exists already
		if os.path.exists(path):
			debug.add('file path exists : '+str(path))
			# open the file to write
			fileObject=open(path,'r')
			# temp string to hold file content
			temp=''
			# read each line into a string
			for line in fileObject:
				temp+=line
			# return the contents of the file as a string
			debug.add('fileContent : '+str(temp))
			return temp
			# return the string text of the file
			#return fileObject.read()
		else:
			debug.add('file path does not exists : '+str(path))
			# return false if the file is not found
			return False
	def saveConfig(self,config,newValue):
		'''Convert objects into strings and save in xbmc settings
		for the addon.'''
		# convert the new value into a string for storage
		debug.add('saveConfig NOT PICKLED',newValue)
		temp=pickle.dumps(newValue)
		debug.add('saveConfig PICKLED',temp)
		# write new config back to the addon settings
		#self.saveFile(config,temp)
		addonObject.setSetting(config,temp)
		#xbmcplugin.setSettings(_handle,config,temp)
	def loadConfig(self,config,blankType):
		'''Used for loading objects from xbmc settings that were
		stored using pythons pickle functionality.'''
		# open the pickled settings using xbmcs settings api
		configObject=addonObject.getSetting(config)
		#configObject=xbmcplugin.getSettings(_handle,config)
		#configObject=self.loadFile(config)
		if bool(configObject):
			# if config exists load up the config into channels
			return pickle.loads(configObject)
		else:
			if blankType=='array':
				# otherwise create a blank array
				return []
			elif blankType=='dict':
				# return a blank dict
				return {}
			else:
				# default to return an array
				return []
	def addChannel(self,channelUsername):
		# check if username is already in channels
		if channelUsername not in self.channels:
			# add username to channels
			self.channels.append(channelUsername)
			self.cache[channelUsername]=[]
			# also update the things in the channel
			self.getUserVideos(channelUsername)
		else:
			# end execution since it would be a dupe
			return
		# save the config changes
		self.saveConfig('channels',self.channels)
	def checkTimer(self,userName):
		debug.add('checking timer for',userName)
		'''
		Checks timer on username to see if videos in that channel have been
		refreshed within the past hour.
		True means the timer says the video needs refreshed.
		
		returns bool
		'''
		if userName in self.timer.keys():
			debug.add('checking timer for username',userName)
			debug.add('lastTime',self.timer[userName])
			debug.add('nowTime',datetime.datetime.now())
			# update videos if videos were updated more than an hour ago
			if self.timer[userName]<datetime.datetime.now():
				# if the timer is over an hour old everything needs updated
				#############
				# update the timer to only update one hour from now
				self.timer[userName]=datetime.datetime.now()+datetime.timedelta(hours=1)
				# save timer changes
				self.saveConfig('timer',self.timer)
				return True
			else:
				# the timer has been reset within the last hour
				return False
		else:
			# the username has not time logged for last update
			# this means no cache exists, and all videos need updated
			#############
			# update the timer to only update one hour from now
			self.timer[userName]=datetime.datetime.now()+datetime.timedelta(hours=1)
			# save timer changes
			self.saveConfig('timer',self.timer)
			return True
	def refreshCache(self):
		# get list of channels to update cache
		for channel in self.channels:
			# refresh all videos in channel
			self.getUserVideos(channel)
	def searchChannel(self,searchString):
		# searches on youtube can be placed with the below string
		# add your search terms at the end of the string
		#"https://www.youtube.com/results?search_query="
		searchResults=self.grabWebpage("https://www.youtube.com/results?search_query="+searchString)
		# to do next page you can add page=2 to the request
		
		# users can be found by scanning the search results for
		#'href="/user/'userName'"'
		searchResults=searchResults.split('"')	
		temp=[]
		for link in searchResults:
			# if the link is a link to a channel
			if '/user/' in link:
				# remove the user prefix to leave only the username
				link = link.replace('/user/','')
				# do not add duplicate entries found in the search
				if link not in temp:
					# add the link 
					temp.append(link)
		# search results is now a array of usernames
		searchResults=temp
		# we can take the usernames and use them to grab the user channel information
		# listing for creating directory
		listing=[]
		# create back button in the search results
		listing.append(createButton(action='main',title='..',thumb='default',icon='default',fanart='default'))
		for channel in searchResults:
			# if the channel info already exists use cached data
			if channel in self.channelCache.keys():
				title=self.channelCache[channel]['title']
				icon=self.channelCache[channel]['icon']
			else:
				# if channel is not in the cache then grab info from the website
				##############
				# user channel information can be found by downloading the
				# user channel page with
				#"https://youtube.com/user/"userName
				channelPage=self.grabWebpage("https://www.youtube.com/user/"+channel)
				# split the page based on tag opening
				channelPage=channelPage.split("<")
				for tag in channelPage:
					# the channels metadata is stored in a image tag for the users
					# profile picture, so search for
					#'class="channel-header-profile-image"'
					if 'class="channel-header-profile-image"' in tag:
						# inside this string you will have two important variables
						# - first src="" will have the icon you should use for the channel
						# - second title="" will have the human readable channel title
						# you should store these things in the cache somehow to use them 
						# when rendering the channels view
						debug.banner()
						debug.add('found tag string',tag)
						debug.add('channel username',channel)
						# grab text in src attribute between parathenesis
						icon=tag.split('src="')
						icon=icon[1].split('"')
						icon=icon[0]
						debug.add('Icon Path',icon)
						# grab text in title attribute for channel title
						title=tag.split('title="')
						title=title[1].split('"')
						title=title[0]
						debug.add('Title',title)
						# add channel information to the channel cache
						self.channelCache[channel]={}
						# add title and icon
						self.channelCache[channel]['title']=title
						self.channelCache[channel]['icon']=icon
			# create a button to add the channel in the results	
			temp=createButton(action=('addChannel&value='+channel),\
					title=title,\
					thumb=icon,\
					icon=icon,\
					fanart=icon)
			listing.append(temp)
		# save the channels into the channel cache
		self.saveConfig('channelCache',self.channelCache)
		xbmcplugin.addDirectoryItems(_handle, listing, len(listing))
		# Add a sort method for the virtual folder items (alphabetically, ignore articles)
		#xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
		# change the default view to thumbnails
		xbmc.executebuiltin('Container.SetViewMode(%d)' % 500)
		# Finish creating a virtual folder.
		xbmcplugin.endOfDirectory(_handle)
		# the banner image seems to use a dynamically generated css link so I
		# have no fucking idea how I would grab that to use in kodi
	def grabWebpage(self,url):
		# get the youtube users webpage
		webpageText=urllib.urlopen(url)
		temp=''
		for line in webpageText:
			# mash everything into a string because they use code obscification
			# also strip endlines to avoid garbage
			temp+=(line.strip())
		return temp
	def getUserVideos(self,userName):
		debug.add('getting user videos for username',userName)
		# create the progress bar
		progressDialog=xbmcgui.DialogProgress()
		# check the timer on the username
		if self.checkTimer(userName) != True:
			# if the timer is false then time is not up and use the cached version
			return self.cache[userName]
		# get the youtube users webpage
		temp=self.grabWebpage("https://www.youtube.com/user/"+str(userName)+"/videos")
		# split page based on parathensis since we are looking for video play strings 
		webpageText=temp.split('"')
		# create an array to hold the video watch strings
		videos=[]
		# run though the split text array looking for watch strings in lines
		for line in webpageText:
			if '/watch?v=' in line:
				# create real youtube url from found strings
				temp='https://youtube.com'+str(line)
				# avoid duplicate entries
				if temp not in videos:
					# add video if it does not exist in the file already
					videos.append(temp)
		# start the progress dialog
		progressDialog.create(('Adding Videos to '+userName),'Processing...')
		progressTotal=float(len(videos))
		progressCurrent=0.0
		# generate the data for drawing videos in kodi menu
		for video in videos:
			# update the progress bar on screen and increment the counter
			progressDialog.update(int(100*(progressCurrent/progressTotal)),video)
			progressCurrent+=1
			debug.add('updating video info for link',video)
			# build a list of existing video urls in cache to check aginst
			videoList=[] 
			for videoDict in self.cache[userName]:
				# add the url of each video in the cache already
				# to the videoList array for checking
				videoList.append(videoDict['video'])
			# check if the video already exists in the video cache by
			# referencing it against the previously create videoList
			if video not in videoList:
				# begin building dict to add to the category array
				temp={}
				# set the video url to the found url
				temp['video']=video
				# find the video title using youtube-dl
				title=subprocess.Popen(['youtube-dl', '--get-title',str(video)],stdout=subprocess.PIPE)
				title=title.communicate()[0].strip()
				# set the title
				temp['name']=title
				# get the thumbnail url
				thumbnail=subprocess.Popen(['youtube-dl', '--get-thumbnail',str(video)],stdout=subprocess.PIPE)
				thumbnail=thumbnail.communicate()[0].strip()
				# set the thumbnail
				temp['thumb']=thumbnail
				# set the genre to youtube
				temp['genre']='youtube'
				# set user data in the cache
				self.cache[userName].append(temp)
		# update the settings in the saved cache after the loops
		self.saveConfig('cache',self.cache)
		# return the cached videos
		return self.cache[userName]
################################################################################
def createButton(action='',title='default',thumb='default',icon='default',fanart='default'):
	'''Create a list item to be created that is used as a menu button'''
	debug.add('creating button')
	url=(_url+'?action='+action)
	list_item = xbmcgui.ListItem(label=title)
	list_item.setInfo('video', {'title':title , 'genre':'menu' })
	list_item.setArt({'thumb': thumb, 'icon': icon, 'fanart': fanart})
	list_item.setProperty('IsPlayable', 'true')
	is_folder = True
	listingItem=(url, list_item, is_folder)
	return listingItem
################################################################################
# create addon object
#addonObject=xbmcaddon.Addon(id="plugin.video.youtubetv")
#addonObject=xbmcaddon.Addon()
# Get the plugin url in plugin:// notation.
_url = sys.argv[0]
debug.add('sys.argv is',sys.argv)
# Get the plugin handle as an integer number.
_handle = int(sys.argv[1])
debug.add('plugin handle is',_handle)
# load the youtube videos on that channel from
#addonObject=xbmcaddon.Addon(str(_handle))
#addonObject=xbmcaddon.Addon(str('plugin.video.youtubetv'))
addonObject=xbmcaddon.Addon(id=str('plugin.video.youtubetv'))
session=YoutubeTV()
#debug.add(os.listdir('.'))#DEBUG

#fileObject=open('~/.kodi/userdata/addon_data/plugin.video.youtubetv/channels','r')

#for line in fileObject:
	#print(line)
# Free sample videos are provided by www.vidsplay.com
# Here we use a fixed set of properties simply for demonstrating purposes
# In a "real life" plugin you will need to get info and links to video files/streams
# from some web-site or online service.
####################################################################
# Read videos from text file where each line contains a username to 
# load the cache into videos, needs reloaded upon changes
VIDEOS = session.cache
#~ VIDEOS = {'Animals': [{'name': 'Crab',
					   #~ 'thumb': 'http://www.vidsplay.com/vids/crab.jpg',
					   #~ 'video': 'http://www.vidsplay.com/vids/crab.mp4',
					   #~ 'genre': 'Animals'},
					  #~ {'name': 'Alligator',
					   #~ 'thumb': 'http://www.vidsplay.com/vids/alligator.jpg',
					   #~ 'video': 'http://www.vidsplay.com/vids/alligator.mp4',
					   #~ 'genre': 'Animals'},
					  #~ {'name': 'Turtle',
					   #~ 'thumb': 'http://www.vidsplay.com/vids/turtle.jpg',
					   #~ 'video': 'http://www.vidsplay.com/vids/turtle.mp4',
					   #~ 'genre': 'Animals'}
					  #~ ],
			#~ 'Cars': [{'name': 'Postal Truck',
					  #~ 'thumb': 'http://www.vidsplay.com/vids/us_postal.jpg',
					  #~ 'video': 'http://www.vidsplay.com/vids/us_postal.mp4',
					  #~ 'genre': 'Cars'},
					 #~ {'name': 'Traffic',
					  #~ 'thumb': 'http://www.vidsplay.com/vids/traffic1.jpg',
					  #~ 'video': 'http://www.vidsplay.com/vids/traffic1.avi',
					  #~ 'genre': 'Cars'},
					 #~ {'name': 'Traffic Arrows',
					  #~ 'thumb': 'http://www.vidsplay.com/vids/traffic_arrows.jpg',
					  #~ 'video': 'http://www.vidsplay.com/vids/traffic_arrows.mp4',
					  #~ 'genre': 'Cars'}
					 #~ ],
			#~ 'Food': [{'name': 'Chicken',
					  #~ 'thumb': 'http://www.vidsplay.com/vids/chicken.jpg',
					  #~ 'video': 'http://www.vidsplay.com/vids/bbqchicken.mp4',
					  #~ 'genre': 'Food'},
					 #~ {'name': 'Hamburger',
					  #~ 'thumb': 'http://www.vidsplay.com/vids/hamburger.jpg',
					  #~ 'video': 'http://www.vidsplay.com/vids/hamburger.mp4',
					  #~ 'genre': 'Food'},
					 #~ {'name': 'Pizza',
					  #~ 'thumb': 'http://www.vidsplay.com/vids/pizza.jpg',
					  #~ 'video': 'http://www.vidsplay.com/vids/pizza.mp4',
					  #~ 'genre': 'Food'}
					 #~ ]}


def get_categories():
	"""
	Get the list of video categories.
	Here you can insert some parsing code that retrieves
	the list of video categories (e.g. 'Movies', 'TV-shows', 'Documentaries' etc.)
	from some site or server.

	:return: list
	"""
	debug.add("get_categories categories",session.cache.keys())
	# update the videos in the cache for each category
	#session.refreshCache()
	#return session.channels
	return session.cache.keys()

def get_videos(category):
	"""
	Get the list of videofiles/streams.
	Here you can insert some parsing code that retrieves
	the list of videostreams in a given category from some site or server.

	:param category: str
	:return: list
	"""
	# check for updates to the category and return category
	return session.getUserVideos(category)

def list_categories():
	"""
	Create the list of video categories in the Kodi interface.
	"""
	# Get video categories
	categories = get_categories()
	debug.add('list_categories categories',categories)
	# Create a list for our items.
	listing = []
	# create a add channel button in the channels view
	listing.append(createButton(action='searchChannel',title='Search Channels',thumb='default',icon='default',fanart='default'))
	# Iterate through categories
	for category in categories:
		# if a category has nothing in it then no category will be listed in the interface
		if len(category)==0:
			return
		# Create a list item with a text label and a thumbnail image.
		list_item = xbmcgui.ListItem(label=session.channelCache[category]['title'])
		# Set graphics (thumbnail, fanart, banner, poster, landscape etc.) for the list item.
		# Here we use the same image for all items for simplicity's sake.
		# In a real-life plugin you need to set each image accordingly.
		list_item.setArt({'thumb': session.channelCache[category]['icon'],\
				  'icon': session.channelCache[category]['icon'],\
				  'fanart': VIDEOS[category][0]['thumb']})
		# Set additional info for the list item.
		# Here we use a category name for both properties for for simplicity's sake.
		# setInfo allows to set various information for an item.
		# For available properties see the following link:
		# http://mirrors.xbmc.org/docs/python-docs/15.x-isengard/xbmcgui.html#ListItem-setInfo
		list_item.setInfo('video', {'title': session.channelCache[category]['title'], 'genre': category})
		# Create a URL for the plugin recursive callback.
		# Example: plugin://plugin.video.example/?action=listing&category=Animals
		url = '{0}?action=listing&category={1}'.format(_url, category)
		# is_folder = True means that this item opens a sub-list of lower level items.
		is_folder = True
		# Add our item to the listing as a 3-element tuple.
		listing.append((url, list_item, is_folder))
	# Add our listing to Kodi.
	# Large lists and/or slower systems benefit from adding all items at once via addDirectoryItems
	# instead of adding one by ove via addDirectoryItem.
	xbmcplugin.addDirectoryItems(_handle, listing, len(listing))
	# Add a sort method for the virtual folder items (alphabetically, ignore articles)
	#xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
	# change the default view to thumbnails
	xbmc.executebuiltin('Container.SetViewMode(%d)' % 500)
	# Finish creating a virtual folder.
	xbmcplugin.endOfDirectory(_handle)

def list_videos(category):
	"""
	Create the list of playable videos in the Kodi interface.

	:param category: str
	"""
	# Get the list of videos in the category.
	videos = get_videos(category)
	#back=[{'video':(_url+'?action=addChannel'),'genre':'menu','name':'..','thumb':'..'}]

	#list_item = xbmcgui.ListItem(label='lol')
	#list_item.setInfo('video', {'title': video['name'], 'genre': video['genre']})
	#list_item.setArt({'thumb': video['thumb'], 'icon': video['thumb'], 'fanart': video['thumb']})
	#list_item.setProperty('IsPlayable', 'true')
	#is_folder = False
	#listing.append((url, list_item, is_folder))

	# add the back button to the video list
	#videos=back+videos
	debug.add('videos object for list_videos',videos)
	#plugin://plugin.video.youtube/
	# Create a list for our items.
	listing = []
	# create the back button to return to the main menu
	listing.append(createButton(action='main',title='..',thumb='default',icon='default',fanart='default'))
	# Iterate through videos.
	for video in videos:
		# Create a list item with a text label and a thumbnail image.
		list_item = xbmcgui.ListItem(label=video['name'])
		# Set additional info for the list item.
		list_item.setInfo('video', {'title': video['name'], 'genre': video['genre']})
		# Set graphics (thumbnail, fanart, banner, poster, landscape etc.) for the list item.
		# Here we use the same image for all items for simplicity's sake.
		# In a real-life plugin you need to set each image accordingly.
		list_item.setArt({'thumb': video['thumb'], 'icon': video['thumb'], 'fanart': video['thumb']})
		# Set 'IsPlayable' property to 'true'.
		# This is mandatory for playable items!
		list_item.setProperty('IsPlayable', 'true')
		# Create a URL for the plugin recursive callback.
		# Example: plugin://plugin.video.example/?action=play&video=http://www.vidsplay.com/vids/crab.mp4
		url = '{0}?action=play&video={1}'.format(_url, video['video'])
		# Add the list item to a virtual Kodi folder.
		# is_folder = False means that this item won't open any sub-list.
		is_folder = False
		# Add our item to the listing as a 3-element tuple.
		listing.append((url, list_item, is_folder))
	# Add our listing to Kodi.
	# Large lists and/or slower systems benefit from adding all items at once via addDirectoryItems
	# instead of adding one by ove via addDirectoryItem.
	xbmcplugin.addDirectoryItems(_handle, listing, len(listing))
	# Add a sort method for the virtual folder items (alphabetically, ignore articles)
	#xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
	# change the default view to thumbnails
	xbmc.executebuiltin('Container.SetViewMode(%d)' % 500)
	# Finish creating a virtual folder.
	xbmcplugin.endOfDirectory(_handle)
def play_video(path):
	"""
	Play a video by the provided path.

	:param path: str
	"""
	# if the previous two if statements dont hit then the path is a 
	# video path so modify the string and play it with the youtube plugin
	###############
	# the path to let videos be played by the youtube plugin
	youtubePath='plugin://plugin.video.youtube/?action=play_video&videoid='
	debug.add('play_video path',path)
	# remove the full webaddress to make youtube plugin work correctly
	path=path.replace('https://youtube.com/watch?v=','')
	# add youtube path to path to make videos play with the kodi youtube plugin
	path=youtubePath+path
	# Create a playable item with a path to play.
	play_item = xbmcgui.ListItem(path=path)
	# Pass the item to the Kodi player.
	xbmcplugin.setResolvedUrl(_handle, True, listitem=play_item)

def router(paramstring):
	"""
	Router function that calls other functions
	depending on the provided paramstring

	:param paramstring:
	"""
	# Parse a URL-encoded paramstring to the dictionary of
	# {<parameter>: <value>} elements
	params = dict(parse_qsl(paramstring))
	debug.add('parameters for router',params)
	# Check the parameters passed to the plugin
	if params:
		if params['action'] == 'listing':
			debug.add('action=listing was activated in router')
			# Display the list of videos in a provided category.
			list_videos(params['category'])
		elif params['action'] == 'play':
			debug.add('action=play was activated in router')
			# Play a video from a provided URL.
			play_video(params['video'])
		elif params['action'] == 'main':
			debug.add('action=main was activated in router')
			# the item is a return to main menu button
			list_categories()
		elif params['action'] == 'addChannel':
			# check for blank strings and ignore them
			if len(params['value']) > 0:
				session.addChannel(params['value'])
			list_categories()
		elif params['action'] == 'searchChannel':
			debug.add('addChannel invoked, creating dialog')
			# the item is a button to display a input dialog
			# that will add a new channel to the addon
			dialogObject=xbmcgui.Dialog()
			returnString=dialogObject.input('Type a youtube username')
			debug.add('input return string',returnString)
			# check for blank strings and ignore them
			if len(returnString) > 0:
				session.searchChannel(returnString)
			else:
				list_categories()
	else:
		debug.add('listing categories...')
		# If the plugin is called from Kodi UI without any parameters,
		# display the list of video categories
		list_categories()

if __name__ == '__main__':
	# Call the router function and pass the plugin call parameters to it.
	# We use string slicing to trim the leading '?' from the plugin call paramstring
	debug.add('sys.argv[2][1:]',sys.argv[2][1:])
	router(sys.argv[2][1:])
