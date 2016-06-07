#AnkiHabitica
#Anki 2 plugin for use with Habitica http://habitica.com
#Author: Edward Shapard <ed.shapard@gmail.com>
#Version 2.0
#License: GNU GPL v3 <www.gnu.org/licenses/gpl.html>

import urllib2, os, sys, json, thread
from anki.hooks import wrap, addHook
from aqt.reviewer import Reviewer
from anki.sched import Scheduler
from anki.sync import Syncer
from aqt.profiles import ProfileManager
from aqt import *
#from aqt.main import AnkiQt
from AnkiHabitica.habitica_class import Habitica
from AnkiHabitica import db_helper
settings={}

### Reward Schedule and Settings - YOU MAY EDIT THESE
#Note: Anki Habitica keeps track of its own points.
#      Once those points reach the 'sched' limit,
#      Anki Habitica scores the 'Anki Points' habit.

############### YOU MAY EDIT THESE SETTINGS ###############
settings['sched'] = 10 #score habitica for this many points
settings['step'] = 1 #this is how many points each tick of the progress bar represents
settings['tries_eq'] = 2 #this many wrong answers gives us one point
settings['barcolor'] = '#603960' #progress bar highlight color
settings['barbgcolor'] = '#BFBFBF' #progress bar background color
settings['timeboxpoints'] = 1 #points earned for each 15 min 'timebox'
settings['matured_eq'] = 2 #this many matured cards gives us one point
settings['learned_eq'] = 2 #this many newly learned cards gives us one point
settings['deckpoints'] = 10 #points earned for clearing a deck
settings['show_mini_stats'] = True #Show Habitica HP, XP, and MP %s next to prog bar
settings['show_popup'] = True #show a popup window when you score points.
settings['score_on_sync'] = False #score any un-scored points silently when you sync Anki

### NOTHING FOR USERS TO EDIT below this point ####

#Set some initial settings whenever we load a profile
#  This includes reloading a profile
def reset_ah_settings():
	settings['name'] = 'Anki User' #temporary, will be replaced with real Habitica name
	settings['initialized'] = False #If habitica class is initialized
	settings['token'] = None #Holder for current profile api-token
	settings['user'] = None #Holder for current profile user-id
	settings['import_rejected'] = False #Prompt to import old config only once

#Set these settings on initial run
settings['threshold'] = int(0.8 * settings['sched'])
settings['internet'] = False #Can connect to habitica
settings['conf_read'] = False #Read conf file only once
settings['profile'] = 'User 1' #Will be changed to current password
settings['configured'] = False #If config file exists
reset_ah_settings()

####################
### Config Files ###
####################

old_conffile = os.path.join(os.path.dirname(os.path.realpath(__file__)), ".habitrpg.conf")
conffile = os.path.join(os.path.dirname(os.path.realpath(__file__)), "AnkiHabitica/AnkiHabitica.conf")
conffile = conffile.decode(sys.getfilesystemencoding())
old_conffile = old_conffile.decode(sys.getfilesystemencoding())

#Set empty config dictionaries
config ={}
old_config_exists = False
if os.path.exists(old_conffile):   #Create dictionary if old conf file exists
		old_config = {}
		old_config_exists = True


#Function to read the configuration file and give warning message if a problem exists
def read_conf_file(conffile):
	global settings, config
	#Return immediately if we already checked credentials
	if settings['conf_read']:
		return
	else:
		settings['conf_read'] = True

	if os.path.exists(conffile):    # Load config file
		config = json.load(open(conffile, 'r'))

	#add profile to config if not there
	if settings['profile'] not in config:
		config[settings['profile']] = {}

	try:
		settings['token'] = config[settings['profile']]['token']
		#utils.showInfo("token: %s" % settings['token'])
	except:
		utils.showInfo("Could not retrieve api_token from configuration file.\nTry running Tools >> Setup Habitica")
		settings['token'] = False
		return

	try:
		settings['user'] = config[settings['profile']]['user']
	except:
		utils.showInfo("Could not retrieve user_id from configuration file.\nTry running Tools >> Setup Habitica")
		settings['user'] = False
		return
	#add defualt scores if missing
	for i in ['score', 'oldscore']:
		if i not in config[settings['profile']]:
			config[settings['profile']][i] = 0
	settings['configured'] = True
	
#Function to read the OLD configuration file if it exists
def read_OLD_conf_file(old_conffile):
	global old_config
	if os.path.exists(old_conffile):    # Load OLD config file
		old_config = json.load(open(old_conffile, 'r'))
	if 'token' in old_config and 'user' in old_config:
		#old_config['token']
		#old_config['user']
		return True
	return False


	
#Save stats to config file 
def save_stats(x=None,y=None):
	global config, conffile, settings
	#utils.showInfo("Saving Stats")
	json.dump( config, open( conffile, 'w' ) )
	#post scorecounter to habitica
	#This is needed for profiles not synchronized to ankiweb
	if settings['internet'] and settings['initialized']:
		settings['habitica'].post_scorecounter("Anki Points")

#Read values from file if it exists #Wait until profile is loaded first!
#if os.path.exists(conffile):    # Load config file
#	read_conf_file(conffile)

#Configure AnkiHabitica
#We must run this after Anki has initialized and loaded a profile
def configure_ankihabitica():
	global conffile, settings, old_config_exists, old_conffile, config, old_config
	if os.path.exists(conffile):    # Load config file
		read_conf_file(conffile)
	else:
		settings['configured'] = False

	#Now see if we need to import the old file
	if not settings['import_rejected'] and old_config_exists and not settings['configured']:
		if read_OLD_conf_file(old_conffile):
			#Ask user if he wants to import old settings
			if utils.askUser("I can't find any Habitica credentials for this profile (%s), but I did find an old config file for an older version of ankiHRPG.\n\nWould you like to import these credentials?" % settings['profile']):
				config[settings['profile']]['user'] = old_config['user']
				config[settings['profile']]['token'] = old_config['token']
				settings['user'] = old_config['user']
				settings['token'] = old_config['token']
				settings['configured'] = True
				if utils.askUser("OK, I imorted the userID and APItoken from the old config file.\n\nWould you like to delete the old configuration file?"):
					os.remove(old_conffile)
					old_config_exists = False
				#save new config and re-read
				save_stats()
				settings['conf_read'] = False
				read_conf_file(conffile)


			else:
				#Only ask once
				settings['import_rejected'] = True

##################
### Setup Menu ###
##################

#Setup menu to configure HRPG userid and api key
def setup():
	global config, settings, conffile
	api_token = None
	user_id = None
	need_info = True
	profile = settings['profile']
	temp_keys={} #temporary dict to store keys

	if os.path.exists(conffile):
		need_info = False
		config = json.load(open(conffile, 'r'))
		try:
			temp_keys['token'] = config[profile]['token']
			temp_keys['user'] = config[profile]['user']
		except:
			need_info = True

	#create dictionary for profile in config if not there
	if profile not in config:
		#utils.showInfo("%s not in config." % profile)
		config[profile] = {}

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
			#save new config file
			save_stats(None, None)
			try:
				#re-read new config file
				settings['conf_read'] = False
				read_conf_file(conffile)
				settings['initialized'] = False
				utils.showInfo("Congratulations!\n\nAnkiHabitica has been setup for profile: %s." % profile)
			except:
				utils.showInfo("An error occured. AnkiHabitica was NOT setup.")
					


#Add Setup to menubar
action = QAction("Setup Anki Habitica", mw)
mw.connect(action, SIGNAL("triggered()"), setup)
mw.form.menuTools.addAction(action)

###############################
### Calculate Current Score ###
###############################


#Compare score to database
def compare_score_to_db():
	global config, settings
	#Return immediately if not ready
	if not ready_or_not():
		return False

	if settings['initialized'] and 'Anki Points' in settings['habitica'].hnote and settings['habitica'].hnote['Anki Points']['scoresincedate']:
		score_count = settings['habitica'].hnote['Anki Points']['scorecount']
		start_date = settings['habitica'].hnote['Anki Points']['scoresincedate']
		scored_points = int(score_count * settings['sched'])
		dbscore = calculate_db_score(start_date)
		newscore = dbscore - scored_points
		if newscore < 0: newscore = 0 #sanity check
		config[settings['profile']]['oldscore'] = config[settings['profile']]['score'] # Capture old score
		config[settings['profile']]['score'] = newscore
		return True
	return False

#Calculate score from database
def calculate_db_score(start_date):
	global config, settings
	dbcorrect = int(db_helper.correct_answer_count(start_date))
	dbwrong = int(db_helper.wrong_answer_count(start_date) / settings['tries_eq'])
	dbtimebox = int(db_helper.timebox_count(start_date) * settings['timeboxpoints'])
	dbdecks = int(db_helper.decks_count(start_date) * settings['deckpoints'])
	dblearned = int(db_helper.learned_count(start_date) / settings['learned_eq'])
	dbmatured = int(db_helper.matured_count(start_date) / settings['matured_eq'])
	dbscore = dbcorrect + dbwrong + dbtimebox + dbdecks + dblearned + dbmatured	
	#utils.tooltip(_("%s\ndatabase says we have %s\nrecord shows we have %s\nscore: %s" % (start_date, dbscore, temp, config[settings['profile']]['score'])), 2000)
	if dbscore < 0: dbscore = 0 #sanity check
	return dbscore


####################
### Progress Bar ###
####################

#Make progress bar
def make_habit_progbar():
	global settings, config
	cur_score = config[settings['profile']]['score']
	if not settings['configured']:
		configure_ankihabitica()
	#length of progress bar excluding increased rate after threshold
	real_length = int(settings['sched'] / settings['step'])
	#length of progress bar including apparent rate increase after threshold
	fake_length = int(1.2 * real_length)
	if settings['configured']:
		#length of shaded bar excluding threshold trickery
		real_point_length = int(cur_score / settings['step']) % real_length #total real bar length
		#Find extra points to add to shaded bar to make the
		#   bar seem to double after threshold
		if real_point_length >= settings['threshold']:
			extra = real_point_length - settings['threshold']
		else:
			extra = 0
		#length of shaded bar including threshold trickery
		fake_point_length = int(real_point_length + extra)
		#shaded bar should not be larger than whole prog bar
		bar = min(fake_length, fake_point_length) #length of shaded bar
		hrpg_progbar = '<font color="%s">' % settings['barcolor']
		#full bar for each tick
		for i in range(bar):
			hrpg_progbar += "&#9608;"
		hrpg_progbar += '</font>'
		points_left = int(fake_length) - int(bar)
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

#Initialize habitica class
def initialize_habitica_class():
	settings['habitica'] = Habitica(settings['user'], settings['token'], settings['profile'], conffile, settings['show_popup'])
	settings['initialized'] = True
	thread.start_new_thread(settings['habitica'].scorecount_on_sync,())

#Run various checks to see if we are ready
def ready_or_not():
	global settings, config
	profile = settings['profile']
	#Configure if not already
	if not settings['configured']:
		configure_ankihabitica()

	#Grab user and token if in config
	if not settings['user'] and not settings['token']:
		for i in ['user', 'token']:
			try:
				settings[i] = config[profile][i]
			except:
				pass

	#Return immediately if we still don't have both the userid and token
	if not settings['user'] and not settings['token']:
		#utils.showInfo("Not Ready: no user or token")
		return False

	#initialize habitica class if AnkiHabitica is configured
	#and class is not yet initialized
	if settings['configured'] and not settings['initialized']:
		initialize_habitica_class()
	#Check to make sure habitica class is initialized
	if not settings['initialized']: return False
		
	if settings['configured'] and settings['initialized']:
		#utils.showInfo("Ready: %s %s" % (settings['user'], settings['token']))
		return True
	else:
		#utils.showInfo("Not Ready")
		return False


#Process Habitica Points in real time
def hrpg_realtime():
	global config, settings, iconfile, conffile
	crit_multiplier = 0
	streak_multiplier = 0
	drop_text = ""
	drop_type = ""

	#Check if we are ready; exit if not
	if not ready_or_not(): return False

	#Post to Habitica if we just crossed a sched boundary
	#  because it's possible to earn multiple points at a time,
	#  (due to matured cards, learned cards, etc.)
	#  We can't rely on the score always being a multiple of sched
	#  as in the commented condition below...
	#if config[settings['profile']]['score'] % settings['sched'] == 0:
	if int(config[settings['profile']]['score'] / settings['sched']) > int(config[settings['profile']]['oldscore'] / settings['sched']):
		#Check internet if down
		if not settings['internet']:
			settings['internet'] = settings['habitica'].test_internet()
		#If Internet is still down
		if not settings['internet']:
			settings['habitica'].hrpg_showInfo("Hmmm...\n\nI can't connect to Habitica. Perhaps your internet is down.\n\nI'll remember your points and try again later.")

		#if Internet is UP
		if settings['internet']:
			#Loop through scoring up to 3 times
			#-- to account for missed scoring opportunities
			i = 0 #loop counter
			while i < 3 and config[settings['profile']]['score'] >= settings['sched'] and settings['internet']:
				#try to score habit
				if settings['habitica'].earn_points("Anki Points"):
					#Remove points from score tally
					config[settings['profile']]['score'] -= settings['sched']
				else:
					#Scoring failed. Check internet
					settings['internet'] = settings['habitica'].test_internet()
				i += 1
			#just in case
			if config[settings['profile']]['score'] < 0:
				config[settings['profile']]['score'] = 0


#############################
### Process Score Backlog ###
#############################

#    Score habitica task for reviews that have not been scored yet
#    for example, reviews that were done on a smartphone.
def score_backlog(silent=False):
	global config, settings
	#Warn User that this can take some time
	warning = "Warning: Scoring backlog may take some time.\n\nWould you like to continue?"
	if not silent:
		cont = utils.askUser(warning)
	else:
		cont = True
	if not cont: return False

	#Exit if not ready
	if not ready_or_not(): return False

	#Check internet if down
	if not settings['internet']:
		settings['internet'] = settings['habitica'].test_internet()
	#If Internet is still down but class initialized
	if not settings['internet'] and settings['initialized']:
		if not silent: settings['habitica'].hrpg_showInfo("Hmmm...\n\nI can't connect to Habitica. Perhaps your internet is down.\n\nI'll remember your points and try again later.")
		return False
	#Compare database to scored points
	if compare_score_to_db():
		if config[settings['profile']]['score'] < settings['sched']:
			if not silent: utils.showInfo("No backlog to score")
			return True
		#OK, now we can score some points...
		p = 0 #point counter
		i = 0 #limit tries to 25 to prevent endless loop
		while i < 25 and config[settings['profile']]['score'] >= settings['sched'] and settings['internet']:
			try:
				settings['habitica'].silent_earn_points("Anki Points")
				config[settings['profile']]['score'] -= settings['sched']
				i += 1
				p += 1
			except:
				i += 1
		if not silent: utils.showInfo("%s points scored on Habitica" % p)
		#utils.showInfo("New scorecount: %s" % settings['habitica'].hnote['Anki Points']['scorecount'])
		save_stats(None, None)

#Add Score Backlog to menubar
action = QAction("Score Habitica Backlog", mw)
mw.connect(action, SIGNAL("triggered()"), score_backlog)
mw.form.menuTools.addAction(action)


#################################
### Support Multiple Profiles ###
#################################

def grab_profile():
	global config, settings
	reset_ah_settings()
	settings['profile'] = str(aqt.mw.pm.name)
	#utils.showInfo("your profile is %s" % (settings['profile']))
	if settings['profile'] not in config:
		config[settings['profile']] = {}
		#utils.showInfo("adding %s to config dict" % settings['profile'])
	ready_or_not()

#############
### Sync ####
#############

#This is the function that will be run on sync.
def ahsync(stage):
	if stage == "login" and settings['initialized']:
		settings['habitica'].scorecount_on_sync()
		if settings['score_on_sync']:
			score_backlog(True)
		save_stats(None, None)


#################
### Wrap Code ###
#################

addHook("profileLoaded", grab_profile)
addHook("sync", ahsync)
addHook("unloadProfile", save_stats)
#AnkiQt.closeEvent = wrap(AnkiQt.closeEvent, save_stats, "before")

#Insert progress bar into bottom review stats
#       along with database scoring and realtime habitica routines
orig_remaining = Reviewer._remaining
def my_remaining(x):
	ret = orig_remaining(x)
	if compare_score_to_db():
		hrpg_progbar = make_habit_progbar()
		hrpg_realtime()
		if not hrpg_progbar == "":
			ret += " : %s" % (hrpg_progbar)
		if settings['initialized'] and settings ['show_mini_stats']:
			mini_stats = settings['habitica'].compact_habitica_stats()
			if mini_stats: ret += " : %s" % (mini_stats)
	return ret
Reviewer._remaining = my_remaining
