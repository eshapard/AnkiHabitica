#AnkiHRPG
#Anki 2 plugin for use with HabitRPG http://habitrpg.com
#Author: Edward Shapard <ed.shapard@gmail.com>
#Version 1.2
#License: GNU GPL v3 <www.gnu.org/licenses/gpl.html>

import urllib2, urllib,  os, sys, json
from anki.hooks import wrap, addHook
from aqt.reviewer import Reviewer
from anki.sched import Scheduler
from aqt import *
from aqt.main import AnkiQt
a_profile = aqt.mw.pm.name


#Reward Schedule - YOU MAY EDIT THESE
hrpg_name = 'Anki User' #temporary, will be replaced with real Habitica name
hrpg_sched = 12 #score habitica for this many correct answers
hrpg_threshold = 8 #should be about 80% of hrpg_sched. Your points double here
hrpg_step = 1 #this is how many points each tick of the progress bar represents
hrpg_tries_eq = 3 #this many wrong answers gives us one correct answer point
hrpg_barcolor = '#603960' #progress bar highlight color
hrpg_barbgcolor = '#bfbfbf' #progress bar background color
hrpg_timeboxpoints = 1 #points earned for a timebox
hrpg_deckpoints = 0 #points earned for clearing a deck

#config file stuff
config ={}
conffile = os.path.join(os.path.dirname(os.path.realpath(__file__)), ".habitrpg.conf")
conffile = conffile.decode(sys.getfilesystemencoding())
score_habitpost = urllib2.Request('https://habitica.com:443/api/v2/user/tasks/Anki%20Points/up','')
user_object = urllib2.Request('https://habitica.com:443/api/v2/user')
hrpg_score = 0
hrpg_tries = 0
hrpg_habit_configured = False

#inital levels of habitica items; just leave these as they are
hrpg_lvl = 0
hrpg_xp = 0
hrpg_gp = 0
hrpg_hp = 0
hrpg_mp = 0
hrpg_stats = {}
hrpg_attempt = 0 
hrpg_progbar = ""

#Check if we can connect to the habitica website
def internet_on():
	try:
		response=urllib2.urlopen('http://habitica.com',timeout=1)
		return True
	except urllib2.URLError as err: pass
	return False

#Function to read the configuration file and give warning message if a problem exists
def read_conf_file():
	global hrpg_habit_configured, conffile, config, api_token, user_id, hrpg_score, hrpg_tries, score_habitpost, user_object
	try:
		api_token = config['token'].replace(" ", "")
	except:
		utils.showInfo("Could not retrive api_token from configuration file.\nTry deleting %s. and re-running Tools >> Setup HabitRPG" % (conffile))
		return

	try:
		user_id = config['user'].replace(" ", "")
	except:
		utils.showInfo("Could not retrive user_id from configuration file.\nTry deleting %s. and re-running Tools >> Setup HabitRPG" % (conffile))
		return

	try:
		hrpg_score = config['score']
	except:
		hrpg_score = 0
	
	try:
		hrpg_tries = config['tries']
	except:
		hrpg_tries = 0

	hrpg_habit_configured = True
	


#Function to add headers to  habitica requests
def add_hrpg_headers():
	global score_habitpost, user_object, hrpg_habit_configured, a_profile, user_id, api_token, a_profile
	a_profile = aqt.mw.pm.name
	score_habitpost.add_header('x-api-user', user_id)
	score_habitpost.add_header('x-api-key', api_token)
	user_object.add_header('x-api-user', user_id)
	user_object.add_header('x-api-key', api_token)
	hrpg_habit_configured = True

#Read values from file if it exists
if os.path.exists(conffile):    # Load config file
	config = json.load(open(conffile, 'r'))
	read_conf_file()



#Setup menu to configure HRPG userid and api key
def setup():
	global config, hrpg_score, hrpg_tries, hrpg_habit_configured, score_habitpost, user_id, api_token, conffile, a_profile
	a_profile = aqt.mw.pm.name
	config['score'] = hrpg_score
	config['tries'] = hrpg_tries
	user_id, ok = utils.getText("Enter your user-ID (not your username):")
	if ok == True:
		api_token, ok = utils.getText('Enter your API-token (not your password):')
		if ok == True:          # Create config file and save values
			api_token = str(api_token).replace(" ", "")
			user_id = str(user_id).replace(" ", "")
			config['user'] = user_id
			config['token'] = api_token
			json.dump( config, open( conffile, 'w' ) )
			try:
				read_conf_file()
				utils.showInfo("The add-on has been setup.")
			except:
				utils.showInfo("The add-on was NOT setup.")



#Add Setup to menubar
action = QAction("Setup HabitRPG", mw)
mw.connect(action, SIGNAL("triggered()"), setup)
mw.form.menuTools.addAction(action)

#Timebox Reached
def timebox_habit(self):
	global hrpg_score, hrpg_timeboxpoints
	elapsed = self.mw.col.timeboxReached()
	if elapsed:
		hrpg_score += hrpg_timeboxpoints
#Deck Completed
def deck_complete_habit(self):
	global hrpg_score, hrpg_deckpoints
	hrpg_score += hrpg_deckpoints

#Get HRPG User Info
def get_user():
	global hrpg_lvl, hrpg_xp, hrpg_gp, hrpg_hp, hrpg_mp, hrpg_stats, hrpg_name, conffile, a_profile
	
	add_hrpg_headers()

	try:
		response = json.load(urllib2.urlopen(user_object))
	except:
		utils.showInfo("Unable to log in to Habitica.\n\nCheck that you have the correct user-id and api-token in\n%s.\n\nThese should not be your username and password.\n\nPost at github.com/eshapard/AnkiHRPG if this issue persists." % (conffile))
		return
	hrpg_name = response['profile']['name']
	utils.showInfo("Welcome %s!\nYour Anki session is now connected to Habitica.\nProfile: %s" % (hrpg_name, a_profile))
	hrpg_stats = response['stats']
	hrpg_lvl = hrpg_stats['lvl']
	hrpg_xp = hrpg_stats['exp']
	hrpg_gp = hrpg_stats['gp']
	hrpg_hp = hrpg_stats['hp']
	hrpg_mp = hrpg_stats['mp']

#Make progress bar
def hrpg_make_progbar():
	global hrpg_progbar, hrpg_sched, hrpg_step, hrpg_barcolor, hrpg_barbgcolor
	length = int(hrpg_sched / hrpg_step)
	bar = int(hrpg_score / hrpg_step)
	hrpg_progbar = ""
	hrpg_progbar += '<font color="%s">' % hrpg_barcolor
	for i in range(bar):
		hrpg_progbar += "&#9608;"
	hrpg_progbar += '</font>'
	points_left = int(length) - int(bar)
	hrpg_progbar += '<font color="%s">' % hrpg_barbgcolor
	for i in range(points_left):
		hrpg_progbar += "&#9608"
	hrpg_progbar += '</font>'
	hrpg_progbar += ""
   
#Process Habitica Points in real time
def hrpg_realtime():
	global config
	global hrpg_lvl, hrpg_xp, hrpg_gp, hrpg_hp, hrpg_mp, hrpg_stats, hrpg_name, hrpg_sched, hrpg_step, hrpg_attempt, score_habitpost, hrpg_progbar, hrpg_score, hrpg_tries, hrpg_habit_configured
	if hrpg_habit_configured:
		#Post to Habitica if score is over hrpg_sched
		if hrpg_score >= hrpg_sched:
			if internet_on:
				if hrpg_lvl == 0:
					get_user()
				hrpg_attempt = 0
				hrpg_success = 0
				while hrpg_attempt < 5: #attempt to contact habitica 5 times
					try:
						msg = json.load(urllib2.urlopen(score_habitpost))
						hrpg_attempt = 5
						hrpg_success = 1
					except:
						hrpg_attempt += 1
						utils.showInfo("Oh No, %s!\nThere was a problem contacting Habitica.\nLet's try again." % (hrpg_name))

				if hrpg_success == 1:
					#Remove points from score tally
					hrpg_score -= hrpg_sched
					config['score'] = hrpg_score

					#Collect levels and make notification window
					hrpgresponse = "Huzzah! You Get Points!\nWell Done %s!" % (hrpg_name)
					new_lvl = msg['lvl']
					new_xp = msg['exp']
					new_mp = msg['mp']
					new_gp = msg['gp']
					new_hp = msg['hp']

					#Check for increases and add to message
					if new_lvl > hrpg_lvl:
						diff = int(new_lvl) - int(hrpg_lvl)
						hrpgresponse += "\nYOU LEVELED UP! NEW LEVE: %s" % (new_lvl)
					if new_xp > hrpg_xp:
						diff = int(new_xp) - int(hrpg_xp)
						hrpgresponse += "\n+ %s XP" % (diff)
					if new_hp > hrpg_hp:
						diff = int(new_hp) - int(hrpg_hp)
						hrpgresponse += "\n+ %s Health" % (diff)
					if new_gp > hrpg_gp:
						diff = int(new_gp) - int(hrpg_gp)
						hrpgresponse += "\n+ %s Gold" % (diff)
					if new_mp > hrpg_mp:
						diff = int(new_mp) - int(hrpg_mp)
						hrpgresponse += "\n+ %s Mana" % (diff)                  
					utils.showInfo(hrpgresponse)
					hrpg_make_progbar()


					#update levels
					hrpg_lvl = new_lvl
					hrpg_xp = new_xp
					hrpg_mp = new_mp
					hrpg_gp = new_gp
					hrpg_hp = new_hp
			
		else:	
			hrpg_make_progbar()

#Run after a card is answered
def card_answered(self, ease):  # Cache number of correct answers
	global config
	global hrpg_lvl, hrpg_xp, hrpg_gp, hrpg_hp, hrpg_mp, hrpg_stats, hrpg_name, hrpg_tries, hrpg_tries_eq, hrpg_score, hrpg_tries, hrpg_habit_configured, hrpg_tries_eq
	if hrpg_habit_configured:
		if ease <= 1:
			hrpg_tries += 1
			#Every 5 tries adds 1 to the score
			if hrpg_tries % hrpg_tries_eq == 0 and hrpg_tries > hrpg_tries_eq:
				hrpg_score += 1
				hrpg_tries -= hrpg_tries_eq
			  
		if ease > 1:
			#Answered Question Correctly
			hrpg_score += 1
		#double points if above threshold
		if (hrpg_score % hrpg_sched) > hrpg_threshold:
			hrpg_score += 1
		config['score'] = hrpg_score
		hrpg_realtime()  

#Save stats to config file 
def save_stats(x,y):
	global config, hrpg_score, hrpg_tries, conffile
	config['score'] = hrpg_score
	config['tries'] = hrpg_tries
	json.dump( config, open( conffile, 'w' ) )


#Wrap Code
Reviewer._answerCard = wrap(Reviewer._answerCard, card_answered, "before")
if hrpg_timeboxpoints:
	Reviewer.nextCard = wrap(Reviewer.nextCard, timebox_habit, "before")
if hrpg_deckpoints:
	Scheduler.finishedMsg = wrap(Scheduler.finishedMsg, deck_complete_habit, "before")
AnkiQt.closeEvent = wrap(AnkiQt.closeEvent, save_stats, "before")


#Insert progress bar into bottom review stats
def my_remaining(self):
	global hrpg_progbar
	ret = orig_remaining(self)
	if not hrpg_progbar == "":
		ret += " : %s" % (hrpg_progbar)
	return ret
orig_remaining = Reviewer._remaining
Reviewer._remaining = my_remaining
