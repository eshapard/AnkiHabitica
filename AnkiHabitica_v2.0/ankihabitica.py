#AnkiHabitica
#Anki 2 plugin for use with Habitica http://habitica.com
#Author: Edward Shapard <ed.shapard@gmail.com>
#Version 2.0
#License: GNU GPL v3 <www.gnu.org/licenses/gpl.html>

import urllib2, os, sys, json
from anki.hooks import wrap, addHook
from aqt.reviewer import Reviewer
from anki.sched import Scheduler
from aqt.profiles import ProfileManager
from aqt import *
from aqt.main import AnkiQt
from AnkiHabitica.habitica_class import Habitica
settings={}

### Reward Schedule - YOU MAY EDIT THESE

settings['name'] = 'Anki User' #temporary, will be replaced with real Habitica name
settings['sched'] = 12 #score habitica for this many correct answers
settings['threshold'] = 8 #should be about 80% of sched. Your points double here
settings['step'] = 1 #this is how many points each tick of the progress bar represents
settings['tries_eq'] = 3 #this many wrong answers gives us one correct answer point
settings['barcolor'] = '#603960' #progress bar highlight color
settings['barbgcolor'] = '#bfbfbf' #progress bar background color
settings['timeboxpoints'] = 1 #points earned for a timebox
settings['deckpoints'] = 0 #points earned for clearing a deck

### Nothing for users to edit below this point###

#Set some initial values
config ={}
settings['configured'] = False #If config file exists
settings['initialized'] = False #If habitica class is initialized
settings['internet'] = False #Can connect to habitica
settings['profile'] = 'User 1' #Will be changed to current password
settings['token'] = None #Holder for current profile api-token
settings['user'] = None #Holder for current profile user-id

###################################
### config files and icon files ###
###################################
#Note: I may move the icon files to the habitica_class file

#old_conffile = os.path.join(os.path.dirname(os.path.realpath(__file__)), ".habitrpg.conf")
conffile = os.path.join(os.path.dirname(os.path.realpath(__file__)), "AnkiHabitica/AnkiHabitica.conf")
iconfile = os.path.join(os.path.dirname(os.path.realpath(__file__)), "AnkiHabitica/habitica_icon.png")
avatarfile = os.path.join(os.path.dirname(os.path.realpath(__file__)), "AnkiHabitica/avatar.png")
conffile = conffile.decode(sys.getfilesystemencoding())
iconfile = iconfile.decode(sys.getfilesystemencoding())
avatarfile = avatarfile.decode(sys.getfilesystemencoding())
if os.path.exists(avatarfile): #use avatar.png as icon if it exists
	iconfile = avatarfile


#Function to read the configuration file and give warning message if a problem exists
def read_conf_file(conffile):
	global settings, config
	if os.path.exists(conffile):    # Load config file
		config = json.load(open(conffile, 'r'))
	try:
		settings['token'] = config[settings['profile']]['token']
	except:
		utils.showInfo("Could not retrive api_token from configuration file.\nTry deleting %s. and re-running Tools >> Setup Habitica" % (conffile))
		settings['token'] = False
		return

	try:
		settings['user'] = config[settings['profile']]['user']
	except:
		utils.showInfo("Could not retrive user_id from configuration file.\nTry deleting %s. and re-running Tools >> Setup Habitica" % (conffile))
		settings['user'] = False
		return
	#add defualt scores if missing
	for i in ['score','tries']:
		if i not in config[settings['profile']]:
			config[settings['profile']][i] = 0
	settings['configured'] = True
	
#Save stats to config file 
def save_stats(x,y):
	global config, conffile
	json.dump( config, open( conffile, 'w' ) )

#Read values from file if it exists
if os.path.exists(conffile):    # Load config file
	read_conf_file(conffile)

##################
### Setup Menu ###
##################

#Setup menu to configure HRPG userid and api key
def setup():
	global config, settings, conffile
	api_token = None
	user_id = None
	need_info = True
	#create dictionary for profile in config if not there
	profile = settings['profile']
	temp_keys={} #temporary dict to store keys
	if profile not in config:
		#utils.showInfo("%s not in config." % profile)
		config[profile] = {}

	if os.path.exists(conffile):
		need_info = False
		config = json.load(open(conffile, 'r'))
		try:
			temp_keys['token'] = config[profile]['token']
			temp_keys['user'] = config[profile]['user']
		except:
			need_info = True
	if not need_info:
		if utils.askUser("Habitica user credentials already entered for profile: %s.\nEnter new Habitica User ID and API token?" % profile):
			need_info = True
	if need_info:
		for i in [['user', 'User ID'],['token', 'API token']]:
			#utils.showInfo("profile: %s" % profile)
			#utils.showInfo("config: %s" % str(config[profile]))
			temp_keys[i[0]], ok = utils.getText("Enter your %s:\n(Go to Settings --> API to find your %s)" % (i[1],i[1]))
		if not ok:
			utils.showWarning('Habitica setup cancelled. Run setup again to use AnkiHabitica')
			settings['configured'] = False
			return
	
		if ok:
			# Create config file and save values
			#strip spaces that sometimes creep in from copy/paste
			for i in ['user', 'token']:
				temp_keys[i] = str(temp_keys[i]).replace(" ", "")
				config[profile][i] = temp_keys[i]
			json.dump( config, open( conffile, 'w' ) )
			try:
				read_conf_file(conffile)
				utils.showInfo("Congratulations!\n\nAnkiHabitica has been setup for profile: %s." % profile)
				settings['configured'] = True
			except:
				utils.showInfo("An error occured. AnkiHabitica was NOT setup.")
					


#Add Setup to menubar
action = QAction("Setup Anki Habitica", mw)
mw.connect(action, SIGNAL("triggered()"), setup)
mw.form.menuTools.addAction(action)

####################################
### Update Score Based on Events ###
####################################

#Configure AnkiHabitica
#We must run this after Anki has initialized and loaded a profile
def configure_ankihabitica():
	global conffile
	if os.path.exists(conffile):    # Load config file
		read_conf_file(conffile)
	else:
		settings['configured'] = False

#Timebox Reached
def timebox_habit(self):
	global settings
	if not settings['configured']:
		configure_ankihabitica()
	elapsed = self.mw.col.timeboxReached()
	if elapsed:
		config[settings['profile']]['score'] += settings['timeboxpoints']

#Deck Completed
def deck_complete_habit(self):
	global settings
	if not settings['configured']:
		configure_ankihabitica()
	config[settings['profile']]['score'] += settings['deckpoints']

#Run after a card is answered
def card_answered(self, ease):  # Cache number of correct answers and tries
	global config
	global settings
	if not settings['configured']:
		configure_ankihabitica()
	if settings['configured']:
		if ease <= 1:
			config[settings['profile']]['tries'] += 1
			#Every X tries adds 1 to the score
			if config[settings['profile']]['tries'] % settings['tries_eq'] == 0 and config[settings['profile']]['tries'] > settings['tries_eq']:
				config[settings['profile']]['score'] += 1
				config[settings['profile']]['tries'] -= settings['tries_eq']
			  
		if ease > 1:
			#Answered Question Correctly
			config[settings['profile']]['score'] += 1
		#double points if above threshold
		if (config[settings['profile']]['score'] % settings['sched']) > settings['threshold']:
			config[settings['profile']]['score'] += 1

		if settings['user'] and settings['token']:
		    #Score points in real time only if we have a userid and token
		    hrpg_realtime()  

####################
### Progress Bar ###
####################

#Make progress bar
def make_habit_progbar():
	global settings
	if not settings['configured']:
		configure_ankihabitica()
	length = int(settings['sched'] / settings['step'])
	if settings['configured']:
		point_length = int(config[settings['profile']]['score']/settings['step']) % length
		bar = min(length, point_length)
		hrpg_progbar = '<font color="%s">' % settings['barcolor']
		for i in range(bar):
			hrpg_progbar += "&#9608;"
		hrpg_progbar += '</font>'
		points_left = int(length) - int(bar)
		hrpg_progbar += '<font color="%s">' % settings['barbgcolor']
		for i in range(points_left):
			hrpg_progbar += "&#9608"
		hrpg_progbar += '</font>'
		return hrpg_progbar
	else:
		return ""

################################
### Score Habit in Real Time ###
################################

#Process Habitica Points in real time
def hrpg_realtime():
	global config, settings, iconfile, conffile
	#if not settings['configured']:
	#	configure_ankihabitica()
	crit_multiplier = 0
	streak_multiplier = 0
	drop_text = ""
	drop_type = ""

	#Return immediately if we don't have both the userid and token
	if not settings['user'] and not settings['token']:
		return

	#initialize habitica class if AnkiHabitica is configured
	#and class is not yet initialized
	if settings['configured'] and not settings['initialized']:
		#utils.showInfo("Initializing Habitica Class\n\n%s\n%s\n%s\n%s\n%s" % (settings['user'], settings['token'], settings['profile'], iconfile, conffile))
		settings['habitica'] = Habitica(settings['user'], settings['token'], settings['profile'], iconfile, conffile)
		settings['initialized'] = True
	
	#Evaluate score if Anki Habitica is configured
	if settings['configured']:
		#Post to Habitica if score is over sched
		if config[settings['profile']]['score'] >= settings['sched']:
			#Check internet if down
			if not settings['internet']:
				settings['internet'] = settings['habitica'].test_internet()
			if settings['internet'] and settings['initialized']:
				#Update habitica stats if we haven't yet
				if settings['habitica'].lvl == 0:
					settings['habitica'].update_stats()
				#try to score habit
				if settings['habitica'].earn_points():
					#Remove points from score tally
					config[settings['profile']]['score'] -= settings['sched']
				else:
					#Scoring failed. Check internet
					settings['internet'] = settings['habitica'].test_internet()

#################################
### Support Multiple Profiles ###
#################################

def grab_profile(self, name, passwd=None ):
	global config, settings
	settings['profile'] = name
	if settings['profile'] not in config:
		#utils.showInfo("adding %s to config dict" % settings['profile'])
		config[settings['profile']]={}
	#utils.showInfo("your profile is %s" % settings['profile'])



#################
### Wrap Code ###
#################

Reviewer._answerCard = wrap(Reviewer._answerCard, card_answered, "before")
if settings['timeboxpoints']:
	Reviewer.nextCard = wrap(Reviewer.nextCard, timebox_habit, "before")
if settings['deckpoints']:
	Scheduler.finishedMsg = wrap(Scheduler.finishedMsg, deck_complete_habit, "before")
AnkiQt.closeEvent = wrap(AnkiQt.closeEvent, save_stats, "before")
ProfileManager.load = wrap(ProfileManager.load, grab_profile)


#Insert progress bar into bottom review stats
def my_remaining(self):
	hrpg_progbar = make_habit_progbar()
	ret = orig_remaining(self)
	if not hrpg_progbar == "":
		ret += " : %s" % (hrpg_progbar)
	return ret
orig_remaining = Reviewer._remaining
Reviewer._remaining = my_remaining
