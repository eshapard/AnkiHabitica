#AnkiHabitica
#Anki 2 plugin for use with Habitica http://habitica.com
#Author: Edward Shapard <ed.shapard@gmail.com>
#With Database Code by: Tim Wilson
#Version 2.0
#License: GNU GPL v3 <www.gnu.org/licenses/gpl.html>

import urllib2, os, sys, json, thread
from anki.hooks import wrap, addHook, runHook
from aqt.reviewer import Reviewer
from anki.sched import Scheduler
from anki.sync import Syncer
from aqt.profiles import ProfileManager
from aqt import *
from aqt.main import AnkiQt
import AnkiHabitica
# import logging, AnkiHabitica.logging.handlers
#from AnkiHabitica.habitica_class import Habitica
#from AnkiHabitica import db_helper
from AnkiHabitica.ah_common import AnkiHabiticaCommon as ah, setupLog

class ah_settings: #tiny class for holding settings
    ### Reward Schedule and Settings - YOU MAY EDIT THESE
    #Note: Anki Habitica keeps track of its own points.
    #      Once those points reach the 'sched' limit,
    #      Anki Habitica scores the 'Anki Points' habit.
    
    ############### YOU MAY EDIT THESE SETTINGS ###############
    sched = 12 #score habitica for this many points
    step = 1 #this is how many points each tick of the progress bar represents
    tries_eq = 2 #this many wrong answers gives us one point
    barcolor = '#603960' #progress bar highlight color
    barbgcolor = '#BFBFBF' #progress bar background color
    timeboxpoints = 1 #points earned for each 15 min 'timebox'
    matured_eq = 2 #this many matured cards gives us one point
    learned_eq = 2 #this many newly learned cards gives us one point
    deckpoints = 10 #points earned for clearing a deck
    show_mini_stats = True #Show Habitica HP, XP, and MP %s next to prog bar
    show_popup = True #show a popup window when you score points.
    ############# END USER CONFIGURABLE SETTINGS #############



### NOTHING FOR USERS TO EDIT below this point ####
ah.settings = ah_settings #monkey patch settings to commonly shared class
ah.settings.debug = True
ah.settings.allow_threads = True #No threads yet in this file, so it doesn't matter habitica_class.py has its own setting to allow threads.

#Setup logging
setupLog(ah)
ah.log.info('Logfile initialized')

#list of habits used
ah.settings.habitlist = ["Anki Points"]

#Set some initial settings whenever we load a profile
#  This includes reloading a profile
def reset_ah_settings():
    ah.log.debug("Begin function")
    ah.settings.name = 'Anki User' #temporary, will be replaced with real Habitica name
    ah.settings.initialized = False #If habitica class is initialized
    ah.settings.token = None #Holder for current profile api-token
    ah.settings.user = None #Holder for current profile user-id
    ah.settings.progbar = ""
    ah.log.debug("End function")

#Set these settings on initial run
ah.settings.threshold = int(0.8 * ah.settings.sched)
ah.settings.internet = False #Can connect to habitica
ah.settings.conf_read = False #Read conf file only once
ah.settings.profile = 'User 1' #Will be changed to current password
ah.settings.configured = False #If config file exists
ah.settings.import_rejected = False #Prompt to import old config only once
reset_ah_settings()

#Submenu 
ah.log.debug('Adding AnkiHabitica menu')
AnkiHabiticaMenu = QMenu("AnkiHabitica", mw)
mw.form.menuTools.addMenu(AnkiHabiticaMenu)
ah.log.debug('AnkiHabitica menu added')

#####################################
### Prompt to Delete Old Versions ###
#####################################
#search for old versions and prompt about deleting them
ah.log.debug('Checking for old versions of add-on')
for f in ["Anki_HRPG.py", "ankiHRPG.py", "ankiHRPG_v0.5.py", "ankiHRPG_v1.0.py", "ankiHRPG_v1.2.py"]:
    old_version_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), f)
    old_version_file = old_version_file.decode(sys.getfilesystemencoding())
    if os.path.exists(old_version_file):
        ah.log.info("Old version found: %s" % old_version_file)
        warning = "I've detected an old version of ankiHRPG installed.\n We must remove the old version and restart Anki.\n\nPlease delete %s.\n\nWould you like me to delete the file for you?" % old_version_file
        ah.log.debug(warning.replace('\n', ' '))
        delete_me = utils.askUser(warning)
        if delete_me: 
            ah.log.info("Deleting old version of add-on: %s" % old_version_file)
            os.remove(old_version_file)
            utils.showInfo("Please shut down and restart Anki.")
            ah.log.info("Please shut down and restart Anki.")


####################
### Config Files ###
####################
ah.old_conffile = os.path.join(os.path.dirname(os.path.realpath(__file__)), ".habitrpg.conf")
ah.conffile = os.path.join(os.path.dirname(os.path.realpath(__file__)), "AnkiHabitica", "AnkiHabitica.conf")
ah.conffile = ah.conffile.decode(sys.getfilesystemencoding())
ah.old_conffile = ah.old_conffile.decode(sys.getfilesystemencoding())

#Handle old config files
ah.old_config_exists = False
ah.log.debug('Checking if old conf file exists')
if os.path.exists(ah.old_conffile):   #Create dictionary if old conf file exists
    ah.old_config = {}
    ah.old_config_exists = True
ah.log.debug('Old conf file exists: %s' % ah.old_config_exists)


#Function to read the configuration file and give warning message if a problem exists
def read_conf_file(conffile):
    ah.log.debug("Begin function")
    ah.log.info("Reading in conf file: %s" % conffile)
    #Return immediately if we already checked credentials
    if ah.settings.conf_read:
#        if ah.settings.debug: utils.showInfo("conf file already read")
        ah.log.warning("conf file already read")
        ah.log.debug("End function")
        return

    if os.path.exists(conffile):    # Load config file
#        if ah.settings.debug: utils.showInfo("reading conffile\n%s" % conffile)
        ah.log.info("reading conffile: %s" % conffile)
        ah.config = json.load(open(conffile, 'r'))
        ah.log.info(ah.config)
        ah.settings.conf_read = True

    #add profile to config if not there
    if ah.settings.profile not in ah.config:
        ah.config[ah.settings.profile] = {}

    try:
        ah.settings.token = ah.config[ah.settings.profile]['token']
#        if ah.settings.debug: utils.showInfo("token: %s" % ah.settings.token)
        ah.log.info("token: %s" % ah.settings.token)
    except:
        utils.showInfo("Could not retrieve api_token from configuration file.\nTry running Tools >> Setup Habitica")
        ah.log.error("Could not retrieve api_token from configuration file. Try running Tools >> Setup Habitica")
        ah.settings.token = False
        ah.log.error("End function")
        return

    try:
        ah.settings.user = ah.config[ah.settings.profile]['user']
        ah.log.info("User: %s" % ah.settings.user)
    except:
        utils.showInfo("Could not retrieve user_id from configuration file.\nTry running Tools >> Setup Habitica")
        ah.log.error("Could not retrieve user_id from configuration file. Try running Tools >> Setup Habitica")
        ah.settings.user = False
        ah.log.error("End function")
        return
    #add defualt scores if missing
    for i in ['score', 'oldscore']:
        if i not in ah.config[ah.settings.profile]:
            ah.config[ah.settings.profile][i] = 0
    #add habit_id dictionary if it does not exist
    if 'habit_id' not in ah.config[ah.settings.profile]:
        ah.config[ah.settings.profile]['habit_id'] = {}
    ah.settings.configured = True
    ah.log.debug("Settings contents: %s" % ah.settings)
    ah.log.debug("End function")
    
#Function to read the OLD configuration file if it exists
def read_OLD_conf_file(old_conffile):
    ah.log.debug("Begin function")
    if os.path.exists(old_conffile):    # Load OLD config file
        ah.old_config = json.load(open(old_conffile, 'r'))
    if 'token' in ah.old_config and 'user' in ah.old_config:
        #ah.old_config['token']
        #ah.old_config['user']
        ah.log.debug("End function returning: %s" %  True)
        return True
    ah.log.debug("End function returning: %s" %  False)
    return False


#Save stats to config file 
def save_stats(x=None,y=None):
    ah.log.debug("Begin function")
    json.dump( ah.config, open( ah.conffile, 'w' ) )
    ah.log.debug("End function")

#Read values from file if it exists #Wait until profile is loaded first!
#if os.path.exists(ah.conffile):    # Load config file
#	read_conf_file(ah.conffile)

#Configure AnkiHabitica
#We must run this after Anki has initialized and loaded a profile
def configure_ankihabitica():
    ah.log.debug("Begin function")
    if os.path.exists(ah.conffile):    # Load config file
        read_conf_file(ah.conffile)
    else:
        ah.settings.configured = False

    #Now see if we need to import the old file
    if not ah.settings.import_rejected and ah.old_config_exists and not ah.settings.configured:
        if read_OLD_conf_file(ah.old_conffile):
            #Ask user if he wants to import old settings
            ah.log.debug("I can't find any Habitica credentials for this profile (%s), but I did find an old config file for an older version of ankiHRPG. Would you like to import these credentials?" % ah.settings.profile)
            if utils.askUser("I can't find any Habitica credentials for this profile (%s), but I did find an old config file for an older version of ankiHRPG.\n\nWould you like to import these credentials?" % ah.settings.profile):
                ah.log.debug('Importing settings from old conf file')
                ah.config[ah.settings.profile]['user'] = ah.old_config['user']
                ah.config[ah.settings.profile]['token'] = ah.old_config['token']
                ah.settings.user = ah.old_config['user']
                ah.settings.token = ah.old_config['token']
                ah.settings.configured = True            
                ah.log.debug("OK, I imorted the userID and APItoken from the old config file. Would you like to delete the old configuration file?")
                if utils.askUser("OK, I imorted the userID and APItoken from the old config file.\n\nWould you like to delete the old configuration file?"):
                    ah.log.debug('Deleting old conf file')
                    os.remove(ah.old_conffile)
                    ah.old_config_exists = False
                #save new config and re-read
                save_stats()
                ah.settings.conf_read = False
                read_conf_file(ah.conffile)


            else:
                #Only ask once
                ah.log.debug('not importing settings from old conf file per user response')
                ah.settings.import_rejected = True

    ah.log.debug("End function")
##################
### Setup Menu ###
##################

#Setup menu to configure HRPG userid and api key
def setup():
    ah.log.debug("Begin function")
    api_token = None
    user_id = None
    need_info = True
    profile = ah.settings.profile
    temp_keys={} #temporary dict to store keys

    if os.path.exists(ah.conffile):
        need_info = False
        ah.config = json.load(open(ah.conffile, 'r'))
        try:
            temp_keys['token'] = ah.config[profile]['token']
            temp_keys['user'] = ah.config[profile]['user']
        except:
            need_info = True

    #create dictionary for profile in config if not there
    if profile not in ah.config:
#        if ah.settings.debug: utils.showInfo("%s not in config." % profile)
        ah.log.warning("%s not in config." % profile)
        ah.config[profile] = {}

    if not need_info:
        ah.log.debug("Habitica user credentials already entered for profile: %s. Enter new Habitica User ID and API token?" % profile)
        if utils.askUser("Habitica user credentials already entered for profile: %s.\nEnter new Habitica User ID and API token?" % profile):
            need_info = True
    if need_info:
        for i in [['user', 'User ID'],['token', 'API token']]:
#            if ah.settings.debug: utils.showInfo("profile: %s" % profile)
            ah.log.info("profile: %s" % profile)
#            if ah.settings.debug: utils.showInfo("config: %s" % str(ah.config[profile]))
            ah.log.info("config: %s" % str(ah.config[profile]))
            ah.log.debug("Enter your %s: (Go to Settings --> API to find your %s)" % (i[1],i[1]))
            temp_keys[i[0]], ok = utils.getText("Enter your %s:\n(Go to Settings --> API to find your %s)" % (i[1],i[1]))
            ah.log.debug("User response: %s" % temp_keys[i[0]])
        if not ok:
            ah.log.warning('Habitica setup cancelled. Run setup again to use AnkiHabitica')
            utils.showWarning('Habitica setup cancelled. Run setup again to use AnkiHabitica')
            ah.settings.configured = False
            ah.log.warning("End function")
            return
 
        if ok:
            # Create config file and save values
            #strip spaces that sometimes creep in from copy/paste
            for i in ['user', 'token']:
                temp_keys[i] = str(temp_keys[i]).replace(" ", "")
                ah.config[profile][i] = temp_keys[i]
            #save new config file
            save_stats(None, None)
            try:
                #re-read new config file
                ah.settings.conf_read = False
                read_conf_file(ah.conffile)
                ah.settings.initialized = False
                utils.showInfo("Congratulations!\n\nAnkiHabitica has been setup for profile: %s." % profile)
                ah.log.info("Congratulations! AnkiHabitica has been setup for profile: %s." % profile)
            except:
                utils.showInfo("An error occured. AnkiHabitica was NOT setup.")
                ah.log.error("An error occured. AnkiHabitica was NOT setup.")

    ah.log.debug("End function")

#Add Setup to menubar
ah.log.debug('Adding setup to menubar')
action = QAction("Setup Anki Habitica", mw)
mw.connect(action, SIGNAL("triggered()"), setup)
#mw.form.menuTools.addAction(action)
AnkiHabiticaMenu.addAction(action)

###############################
### Calculate Current Score ###
###############################


#Compare score to database
def compare_score_to_db():
    ah.log.debug("Begin function")
    #Return immediately if not ready
    if not ready_or_not():
#        if ah.settings.debug: utils.showInfo("compare score: not ready")
        ah.log.error("compare score: not ready")
        ah.log.warning("End function returning: %s" %  False)
        return False

    if ah.settings.initialized:
        if 'Anki Points' in ah.habitica.hnote and ah.habitica.hnote['Anki Points']['scoresincedate']:
            score_count = ah.habitica.hnote['Anki Points']['scorecount']
            start_date = ah.habitica.hnote['Anki Points']['scoresincedate']
        else: #We started offline and could not cotact Habitica
            score_count = AnkiHabitica.habitica_class.Habitica.offline_scorecount #Starts at 0
            start_date = AnkiHabitica.habitica_class.Habitica.offline_sincedate #start time of program
        scored_points = int(score_count * ah.settings.sched)
        dbscore = calculate_db_score(start_date)
        newscore = dbscore - scored_points
        if newscore < 0: newscore = 0 #sanity check
        ah.config[ah.settings.profile]['oldscore'] = ah.config[ah.settings.profile]['score'] # Capture old score
        ah.config[ah.settings.profile]['score'] = newscore
#        if ah.settings.debug: utils.showInfo("compare score: success")
        ah.log.info("compare score: success")
        ah.log.debug("End function returning: %s" %  True)
        return True
#    if ah.settings.debug: utils.showInfo("compare score: failed")
    ah.log.error("compare score: failed")
    ah.log.error("End function returning: %s" %  False)
    return False

#Calculate score from database
def calculate_db_score(start_date):
    ah.log.debug("Begin function")
    dbcorrect = int(AnkiHabitica.db_helper.correct_answer_count(start_date))
    dbwrong = int(AnkiHabitica.db_helper.wrong_answer_count(start_date) / ah.settings.tries_eq)
    dbtimebox = int(AnkiHabitica.db_helper.timebox_count(start_date) * ah.settings.timeboxpoints)
    dbdecks = int(AnkiHabitica.db_helper.decks_count(start_date) * ah.settings.deckpoints)
    dblearned = int(AnkiHabitica.db_helper.learned_count(start_date) / ah.settings.learned_eq)
    dbmatured = int(AnkiHabitica.db_helper.matured_count(start_date) / ah.settings.matured_eq)
    dbscore = dbcorrect + dbwrong + dbtimebox + dbdecks + dblearned + dbmatured    
    #utils.tooltip(_("%s\ndatabase says we have %s\nrecord shows we have %s\nscore: %s" % (start_date, dbscore, temp, ah.config[ah.settings.profile]['score'])), 2000)
    if dbscore < 0: dbscore = 0 #sanity check
    ah.log.debug("End function returning: %s" %  dbscore)
    return dbscore


####################
### Progress Bar ###
####################

#Make progress bar
def make_habit_progbar():
    ah.log.debug("Begin function")
    cur_score = ah.config[ah.settings.profile]['score']
    if not ah.settings.configured:
        configure_ankihabitica()
    #length of progress bar excluding increased rate after threshold
    real_length = int(ah.settings.sched / ah.settings.step)
    #length of progress bar including apparent rate increase after threshold
    fake_length = int(1.2 * real_length)
    if ah.settings.configured:
        #length of shaded bar excluding threshold trickery
        real_point_length = int(cur_score / ah.settings.step) % real_length #total real bar length
        #Find extra points to add to shaded bar to make the
        #   bar seem to double after threshold
        if real_point_length >= ah.settings.threshold:
            extra = real_point_length - ah.settings.threshold
        else:
            extra = 0
        #length of shaded bar including threshold trickery
        fake_point_length = int(real_point_length + extra)
        #shaded bar should not be larger than whole prog bar
        bar = min(fake_length, fake_point_length) #length of shaded bar
        hrpg_progbar = '<font color="%s">' % ah.settings.barcolor
        #full bar for each tick
        for i in range(bar):
            hrpg_progbar += "&#9608;"
        hrpg_progbar += '</font>'
        points_left = int(fake_length) - int(bar)
        hrpg_progbar += '<font color="%s">' % ah.settings.barbgcolor
        for i in range(points_left):
            hrpg_progbar += "&#9608"
        hrpg_progbar += '</font>'
        ah.log.debug("End function returning: %s" %  hrpg_progbar)
        return hrpg_progbar
    else:
        ah.log.debug("End function returning: %s" %  "")
        return ""

################################
### Score Habit in Real Time ###
################################

#Initialize habitica class
def initialize_habitica_class():
    ah.log.debug("Begin function")
    #Create dictionary of reward schedules for habits
    ah.settings.sched_dict = {}
    for habit in ah.settings.habitlist:
        ah.settings.sched_dict[habit] = ah.settings.sched
    #INITIALIZE HABITICA CLASS
    ah.habitica = AnkiHabitica.habitica_class.Habitica()
    ah.settings.initialized = True
    # Keep track of the reward schedule, so if it ever changes, we reset
    # the scorecounter and scoresincedate to prevent problems
    for habit in ah.settings.habitlist:
        #set up oldsched dict in config
        if 'oldsched' not in ah.config[ah.settings.profile]:
            ah.config[ah.settings.profile]['oldsched'] = {}
        #set oldsched for current habit of not there
        if habit not in ah.config[ah.settings.profile]['oldsched']:
            ah.config[ah.settings.profile]['oldsched'][habit] = ah.settings.sched_dict[habit]
        #Find habits with a changed reward scedule
        if ah.config[ah.settings.profile]['oldsched'][habit] != ah.settings.sched_dict[habit]:
            #reset scorecounter and scoresincedate
            if ah.habitica.reset_scorecounter(habit):
                #set oldsched to current sched
                ah.config[ah.settings.profile]['oldsched'][habit] = ah.settings.sched_dict[habit]
    ah.log.debug("End function")

#Run various checks to see if we are ready
def ready_or_not():
    ah.log.debug("Begin function")
#    if ah.settings.debug: utils.showInfo("Checking if %s is ready" % ah.settings.profile)
    ah.log.info("Checking if %s is ready" % ah.settings.profile)
    #Configure if not already
    if not ah.settings.configured:
#        if ah.settings.debug: utils.showInfo("Ready or Not: not configured")
        ah.log.info("Ready or Not: not configured")
        configure_ankihabitica()

    #Grab user and token if in config
    if not ah.settings.user and not ah.settings.token:
        try:
            ah.settings.user = ah.config[ah.settings.profile]['user']
            ah.settings.token = ah.config[ah.settings.profile]['token']
        except:
            pass

    #Return immediately if we still don't have both the userid and token
    if not ah.settings.user and not ah.settings.token:
#        if ah.settings.debug: utils.showInfo("Not Ready: no user or token")
        ah.log.warning("Not Ready: no user or token")
        ah.log.warning("End function returning: %s" %  False)
        return False

    #initialize habitica class if AnkiHabitica is configured
    #and class is not yet initialized
    if ah.settings.configured and not ah.settings.initialized:
#        if ah.settings.debug: utils.showInfo("Ready or not: Initializing habitica")
        ah.log.info("Ready or not: Initializing habitica")
        initialize_habitica_class()
    #Check to make sure habitica class is initialized
    if not ah.settings.initialized: 
#        if ah.settings.debug: utils.showInfo("Ready or not: Not initialized")
        ah.log.warning("Ready or not: Not initialized")
        ah.log.warning("End function returning: %s" %  False)
        return False
        
    if ah.settings.configured and ah.settings.initialized:
#        if ah.settings.debug: utils.showInfo("Ready: %s %s" % (ah.settings.user, ah.settings.token))
        ah.log.info("Ready: %s %s" % (ah.settings.user, ah.settings.token))
        # Try to grab any habit ids that we've found.
        try:
            ah.config[ah.settings.profile]['habit_id'] = ah.habitica.habit_id
        except:
            pass
        #If we don't have any habits grabbed, attempt to grab them
#        if ah.settings.debug: utils.showInfo("Hnote length: %s" % len(ah.habitica.hnote))
        ah.log.info("Hnote length: %s" % len(ah.habitica.hnote))
        if len(ah.habitica.hnote) == 0:
            AnkiHabitica.habitica_class.Habitica.offline_recover_attempt += 1
            if AnkiHabitica.habitica_class.Habitica.offline_recover_attempt % 3 == 0:
#                if ah.settings.debug: utils.showInfo("Trying to grab habits")
                ah.log.info("Trying to grab habits")
                ah.habitica.init_update()
        ah.log.debug("End function returning: %s" %  True)
        return True
    else:
#        if ah.settings.debug: utils.showInfo("Not Ready Final")
        ah.log.warning("Not Ready Final")
        ah.log.warning("End function returning: %s" %  False)
        return False


#Process Habitica Points in real time
def hrpg_realtime(dummy=None):
    ah.log.debug("Begin function")
    crit_multiplier = 0
    streak_multiplier = 0
    drop_text = ""
    drop_type = ""

    #Check if we are ready; exit if not
    if not ready_or_not(): 
        ah.log.warning("End function returning: %s" %  False)
        return False

    #Compare score to database an make score progbar
    if compare_score_to_db():
        ah.settings.hrpg_progbar = make_habit_progbar()
    else:
        ah.settings.hrpg_progbar = ""


    #Post to Habitica if we just crossed a sched boundary
    #  because it's possible to earn multiple points at a time,
    #  (due to matured cards, learned cards, etc.)
    #  We can't rely on the score always being a multiple of sched
    #  as in the commented condition below...
    #if ah.config[ah.settings.profile]['score'] % ah.settings.sched == 0:
    if int(ah.config[ah.settings.profile]['score'] / ah.settings.sched) > int(ah.config[ah.settings.profile]['oldscore'] / ah.settings.sched):
        #Check internet if down
        if not ah.settings.internet:
            ah.settings.internet = ah.habitica.test_internet()
        #If Internet is still down
        if not ah.settings.internet:
            ah.habitica.hrpg_showInfo("Hmmm...\n\nI can't connect to Habitica. Perhaps your internet is down.\n\nI'll remember your points and try again later.")

        #if Internet is UP
        if ah.settings.internet:
            ah.habitica.earn_points("Anki Points")
            ##### MOVED looping functions below to habitica_class.py
            #Loop through scoring up to 3 times
            #-- to account for missed scoring opportunities
            #i = 0 #loop counter
            #while i < 3 and ah.config[ah.settings.profile]['score'] >= ah.settings.sched and ah.settings.internet:
            #    #try to score habit
            #    if ah.habitica.earn_points("Anki Points"):
            #        #Remove points from score tally
            #        ah.config[ah.settings.profile]['score'] -= ah.settings.sched
            #    else:
            #        #Scoring failed. Check internet
            #        ah.settings.internet = ah.habitica.test_internet()
            #    i += 1
            #just in case
            if ah.config[ah.settings.profile]['score'] < 0:
                ah.config[ah.settings.profile]['score'] = 0
    ah.log.debug("End function")


#############################
### Process Score Backlog ###
#############################

#    Score habitica task for reviews that have not been scored yet
#    for example, reviews that were done on a smartphone.
def score_backlog(silent=False):
    ah.log.debug("Begin function")
    #Warn User that this can take some time
    warning = "Warning: Scoring backlog may take some time.\n\nWould you like to continue?"
    if not silent:
        ah.log.debug(warning.replace('\n', ' '))
        cont = utils.askUser(warning)
    else:
        cont = True
    ah.log.debug("User chose to score backlog (or silent mode is on): %s" % cont)
    if not cont:
        ah.log.warning("End function returning: %s" %  False)
        return False

    #Exit if not ready
    if not ready_or_not(): 
        ah.log.warning("End function returning: %s" %  False)
        return False

    #Check internet if down
    if not ah.settings.internet:
        ah.settings.internet = ah.habitica.test_internet()
    #If Internet is still down but class initialized
    if not ah.settings.internet and ah.settings.initialized:
        if not silent: ah.habitica.hrpg_showInfo("Hmmm...\n\nI can't connect to Habitica. Perhaps your internet is down.\n\nI'll remember your points and try again later.")
        ah.log.warning("No internet connection")
        ah.log.warning("End function returning: %s" %  False)
        return False
    #Compare database to scored points
    if compare_score_to_db():
        if ah.config[ah.settings.profile]['score'] < ah.settings.sched:
            if not silent: 
                utils.showInfo("No backlog to score")
            ah.log.info("No backlog to score")
            ah.log.debug("End function returning: %s" %  True)
            return True
        #OK, now we can score some points...
        p = 0 #point counter
        i = 0 #limit tries to 25 to prevent endless loop
        while i < 25 and ah.config[ah.settings.profile]['score'] >= ah.settings.sched and ah.settings.internet:
            try:
                ah.habitica.silent_earn_points("Anki Points")
                ah.config[ah.settings.profile]['score'] -= ah.settings.sched
                i += 1
                p += 1
            except:
                i += 1
        if not silent: utils.showInfo("%s points scored on Habitica" % p)
        ah.log.error("%s points scored on Habitica" % p)
#        if ah.settings.debug: utils.showInfo("New scorecount: %s" % ah.habitica.hnote['Anki Points']['scorecount'])
        ah.log.info("New scorecount: %s" % ah.habitica.hnote['Anki Points']['scorecount'])
        save_stats(None, None)
    ah.log.debug("End function")

#Add Score Backlog to menubar
ah.log.debug('Adding Score Backlog to menubar')
backlog_action = QAction("Score Habitica Backlog", mw)
mw.connect(backlog_action, SIGNAL("triggered()"), score_backlog)
#mw.form.menuTools.addAction(backlog_action)
AnkiHabiticaMenu.addAction(backlog_action)

#Refresh Habitica Avatar
#    Sometimes it comes down malformed.
def refresh_habitica_avatar():
    ah.log.debug("Begin function")
    if ah.settings.initialized and ah.settings.internet:
        if AnkiHabitica.habitica_class.Habitica.allow_threads:
            thread.start_new_thread(ah.habitica.save_avatar, ())
        else:
            ah.habitica.save_avatar()
    ah.log.debug("End function")

#Add Refresh Habitica Avatar to menubar
ah.log.debug('Adding Refresh Habitica Avatar to menubar')
avatar_action = QAction("Refresh Habitica Avatar", mw)
mw.connect(avatar_action, SIGNAL("triggered()"), refresh_habitica_avatar)
#mw.form.menuTools.addAction(avatar_action)
AnkiHabiticaMenu.addAction(avatar_action)

#################################
### Support Multiple Profiles ###
#################################

def grab_profile():
    ah.log.debug("Begin function")
    reset_ah_settings()
    ah.settings.profile = str(aqt.mw.pm.name)
#    if ah.settings.debug: utils.showInfo("your profile is %s" % (ah.settings.profile))
    ah.log.info("your profile is %s" % (ah.settings.profile))
    if ah.settings.profile not in ah.config:
        ah.config[ah.settings.profile] = {}
#        if ah.settings.debug: utils.showInfo("adding %s to config dict" % ah.settings.profile)
        ah.log.info("adding %s to config dict" % ah.settings.profile)
    ready_or_not()
    ah.log.debug("End function")

#############
### Sync ####
#############

#This is the function that will be run on sync.
# DEPRICATED
def ahsync(stage):
    ah.log.debug("Begin function")
    if stage == "login" and ah.settings.initialized:
        save_stats(None, None)
        #ah.habitica.scorecount_on_sync()
        #scorecount now sent in a background thread after scoring
        if ah.settings.score_on_sync:
            score_backlog(True)
    ah.log.debug("End function")


#################
### Wrap Code ###
#################

addHook("profileLoaded", grab_profile)
#addHook("sync", ahsync)
addHook("unloadProfile", save_stats)
#AnkiQt.closeEvent = wrap(AnkiQt.closeEvent, save_stats, "before")
Reviewer.nextCard = wrap(Reviewer.nextCard, hrpg_realtime, "before")

#Insert progress bar into bottom review stats
#       along with database scoring and realtime habitica routines
orig_remaining = Reviewer._remaining
def my_remaining(x):
    ah.log.debug("Begin function")
    ret = orig_remaining(x)
    #if compare_score_to_db():
    #hrpg_progbar = make_habit_progbar()
    #hrpg_realtime()
    if not ah.settings.hrpg_progbar == "":
        ret += " : %s" % (ah.settings.hrpg_progbar)
    if ah.settings.initialized and ah.settings.show_mini_stats:
        mini_stats = ah.habitica.compact_habitica_stats()
        if mini_stats: ret += " : %s" % (mini_stats)
    ah.log.debug("End function returning: %s" %  ret)
    return ret
Reviewer._remaining = my_remaining
