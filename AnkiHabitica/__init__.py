# AnkiHabitica
# Anki 2 plugin for use with Habitica http://habitica.com
# Author: Edward Shapard <ed.shapard@gmail.com>
# With Database Code by: Tim Wilson
# Port to Anki 2.1 by 71e6fd52 <71e6fd52@gmail.com>
# Maintainer (since 2019-05): 71e6fd52 <71e6fd52@gmail.com>
# Version 2.1.14
# License: GNU GPL v3 <www.gnu.org/licenses/gpl.html>

import time
import urllib.request
import urllib.error
import urllib.parse
import os
import sys
import json
import _thread
from PyQt6 import QtCore, QtGui, QtWidgets *
from anki.hooks import wrap, addHook, runHook
from aqt.reviewer import Reviewer
from anki.sched import Scheduler
from anki.sync import Syncer
from aqt.profiles import ProfileManager
from aqt import *
from aqt.main import AnkiQt
from anki.utils import intTime
try:
    from aqt import gui_hooks
    new_hook = True
except:
    new_hook = False

from . import db_helper, habitica_class
from .ah_common import AnkiHabiticaCommon as ah

__version__ = "2.1.14"

ah.user_settings = mw.addonManager.getConfig(__name__)

# No threads yet in this file, so it doesn't matter habitica_class.py has its own setting to allow threads.
ah.settings.allow_threads = True

# Setup logging
# The log file is saved in the AnkiHabitica subfolder of the Anki add-ons folder.
# A log file will be rotated when Anki start.
# There can be as many as 5 log files, before old files will be removed.
# The log file will be made regardless of logging being enabled, but its size will be
# null unless logging is enabled.
ah.setupLog()
if ah.user_settings["keep_log"]:
    ah.log.info("Logfile initialized")


# Set some initial settings whenever we load a profile
#  This includes reloading a profile
def reset_ah_settings():
    if ah.user_settings["keep_log"]:
        ah.log.debug("Begin function")
    # temporary, will be replaced with real Habitica name
    ah.settings.name = 'Anki User'
    ah.settings.initialized = False  # If habitica class is initialized
    ah.settings.token = None  # Holder for current profile api-token
    ah.settings.user = None  # Holder for current profile user-id
    ah.settings.hrpg_progbar = ""
    if ah.user_settings["keep_log"]:
        ah.log.debug("End function")


# Set these settings on initial run
ah.settings.threshold = int(0.8 * ah.user_settings["sched"])
ah.settings.internet = False  # Can connect to habitica
ah.settings.conf_read = False  # Read conf file only once
ah.settings.profile = 'User 1'  # Will be changed to current password
ah.settings.configured = False  # If config file exists
ah.settings.import_rejected = False  # Prompt to import old config only once
reset_ah_settings()

# Submenu
if ah.user_settings["keep_log"]:
    ah.log.debug('Adding AnkiHabitica menu')
AnkiHabiticaMenu = QMenu("AnkiHabitica", mw)
mw.form.menuTools.addMenu(AnkiHabiticaMenu)
if ah.user_settings["keep_log"]:
    ah.log.debug('AnkiHabitica menu added')

####################
### Config Files ###
####################

ah.conffile = os.path.join(os.path.dirname(
    os.path.realpath(__file__)), "user_files", "AnkiHabitica.conf")


# Function to read the configuration file and give warning message if a problem exists
def read_conf_file(conffile):
    if ah.user_settings["keep_log"]:
        ah.log.debug("Begin function")
    if ah.user_settings["keep_log"]:
        ah.log.info("Reading in conf file: %s" % conffile)
    # Return immediately if we already checked credentials
    if ah.settings.conf_read:
        if ah.user_settings["keep_log"]:
            ah.log.warning("conf file already read")
        if ah.user_settings["keep_log"]:
            ah.log.debug("End function")
        return

    if os.path.exists(conffile):    # Load config file
        if ah.user_settings["keep_log"]:
            ah.log.info("reading conffile: %s" % conffile)
        ah.config = json.load(open(conffile, 'r'))
        if ah.user_settings["keep_log"]:
            ah.log.info(ah.config)
        ah.settings.conf_read = True

    # add profile to config if not there
    if ah.settings.profile not in ah.config:
        ah.config[ah.settings.profile] = {}

    try:
        ah.settings.token = ah.config[ah.settings.profile]['token']
        if ah.user_settings["keep_log"]:
            ah.log.info("token: %s" % ah.settings.token)
    except:
        utils.showInfo(
            "Could not retrieve api_token from configuration file.\nTry running Tools >> Setup Habitica")
        if ah.user_settings["keep_log"]:
            ah.log.error(
                "Could not retrieve api_token from configuration file. Try running Tools >> Setup Habitica")
        ah.settings.token = False
        if ah.user_settings["keep_log"]:
            ah.log.error("End function")
        return

    try:
        ah.settings.user = ah.config[ah.settings.profile]['user']
        if ah.user_settings["keep_log"]:
            ah.log.info("User: %s" % ah.settings.user)
    except:
        utils.showInfo(
            "Could not retrieve user_id from configuration file.\nTry running Tools >> Setup Habitica")
        if ah.user_settings["keep_log"]:
            ah.log.error(
                "Could not retrieve user_id from configuration file. Try running Tools >> Setup Habitica")
        ah.settings.user = False
        if ah.user_settings["keep_log"]:
            ah.log.error("End function")
        return
    # add default scores if missing
    for i in ['score', 'oldscore']:
        if i not in ah.config[ah.settings.profile]:
            ah.config[ah.settings.profile][i] = 0
    # add habit_id if it does not exist
    try:
        if ah.config[ah.settings.profile]['habit_id'].__class__ == dict:
            ah.config[ah.settings.profile]['habit_id'] = ah.config[ah.settings.profile]['habit_id'][ah.user_settings["habit"]]
    except:
        ah.config[ah.settings.profile]['habit_id'] = None
    ah.settings.configured = True
    if ah.user_settings["keep_log"]:
        ah.log.debug("Settings contents: %s" % ah.settings)
    if ah.user_settings["keep_log"]:
        ah.log.debug("End function")


# Save stats to config file
def save_stats(x=None, y=None):
    if ah.user_settings["keep_log"]:
        ah.log.debug("Begin function")
    os.makedirs(os.path.dirname(ah.conffile), exist_ok=True)
    json.dump(ah.config, open(ah.conffile, 'w'))
    if ah.user_settings["keep_log"]:
        ah.log.debug("End function")


# Configure AnkiHabitica
# We must run this after Anki has initialized and loaded a profile
def configure_ankihabitica():
    if ah.user_settings["keep_log"]:
        ah.log.debug("Begin function")
    if os.path.exists(ah.conffile):    # Load config file
        read_conf_file(ah.conffile)
    else:
        ah.settings.configured = False

    if ah.user_settings["keep_log"]:
        ah.log.debug("End function")

##################
### Setup Menu ###
##################


# Setup menu to configure HRPG userid and api key
def setup():
    if ah.user_settings["keep_log"]:
        ah.log.debug("Begin function")
    api_token = None
    user_id = None
    need_info = True
    profile = ah.settings.profile
    temp_keys = {}  # temporary dict to store keys

    if os.path.exists(ah.conffile):
        need_info = False
        ah.config = json.load(open(ah.conffile, 'r'))
        try:
            temp_keys['token'] = ah.config[profile]['token']
            temp_keys['user'] = ah.config[profile]['user']
        except:
            need_info = True

    # create dictionary for profile in config if not there
    if profile not in ah.config:
        if ah.user_settings["keep_log"]:
            ah.log.warning("%s not in config." % profile)
        ah.config[profile] = {}

    if not need_info:
        if ah.user_settings["keep_log"]:
            ah.log.debug(
                "Habitica user credentials already entered for profile: %s. Enter new Habitica User ID and API token?" % profile)
        if utils.askUser("Habitica user credentials already entered for profile: %s.\nEnter new Habitica User ID and API token?" % profile):
            need_info = True
    if need_info:
        for i in [['user', 'User ID'], ['token', 'API token']]:
            if ah.user_settings["keep_log"]:
                ah.log.info("profile: %s" % profile)
            if ah.user_settings["keep_log"]:
                ah.log.info("config: %s" % str(ah.config[profile]))
            if ah.user_settings["keep_log"]:
                ah.log.debug(
                    "Enter your %s: (Go to Settings --> API to find your %s)" % (i[1], i[1]))
            temp_keys[i[0]], ok = utils.getText(
                "Enter your %s:\n(Go to Settings --> API to find your %s)" % (i[1], i[1]))
            if ah.user_settings["keep_log"]:
                ah.log.debug("User response: %s" % temp_keys[i[0]])
        if not ok:
            if ah.user_settings["keep_log"]:
                ah.log.warning(
                    'Habitica setup cancelled. Run setup again to use AnkiHabitica')
            utils.showWarning(
                'Habitica setup cancelled. Run setup again to use AnkiHabitica')
            ah.settings.configured = False
            if ah.user_settings["keep_log"]:
                ah.log.warning("End function")
            return

        if ok:
            # Create config file and save values
            # strip spaces that sometimes creep in from copy/paste
            for i in ['user', 'token']:
                temp_keys[i] = str(temp_keys[i]).replace(" ", "")
                temp_keys[i] = str(temp_keys[i]).replace("\n", "")
                ah.config[profile][i] = temp_keys[i]
            # save new config file
            save_stats(None, None)
            try:
                # re-read new config file
                ah.settings.conf_read = False
                read_conf_file(ah.conffile)
                ah.settings.initialized = False
                utils.showInfo(
                    "Congratulations!\n\nAnkiHabitica has been setup for profile: %s." % profile)
                if ah.user_settings["keep_log"]:
                    ah.log.info(
                        "Congratulations! AnkiHabitica has been setup for profile: %s." % profile)
            except:
                utils.showInfo(
                    "An error occurred. AnkiHabitica was NOT setup.")
                if ah.user_settings["keep_log"]:
                    ah.log.error(
                        "An error occurred. AnkiHabitica was NOT setup.")

    if ah.user_settings["keep_log"]:
        ah.log.debug("End function")


# Add Setup to menubar
if ah.user_settings["keep_log"]:
    ah.log.debug('Adding setup to menubar')
action = QAction("Setup Anki Habitica", mw)
action.triggered.connect(setup)
AnkiHabiticaMenu.addAction(action)

###############################
### Calculate Current Score ###
###############################


# Compare score to database
# return weather success
def compare_score_to_db():
    if ah.user_settings["keep_log"]:
        ah.log.debug("Begin function")
    # Return immediately if not ready
    if not be_ready():
        if ah.user_settings["keep_log"]:
            ah.log.error("compare score: not ready")
        return False

    if ah.habitica.hnote != None and ah.habitica.hnote['scoresincedate']:
        score_count = ah.habitica.hnote['scorecount']
        start_date = ah.habitica.hnote['scoresincedate']
        if ah.user_settings["keep_log"]:
            ah.log.debug("From Habitica note. Score count: %s, Start date: %s (%s)" % (
                score_count, start_date, db_helper.prettyTime(start_date)))
    else:  # We started offline and could not cotact Habitica
        score_count = habitica_class.Habitica.offline_scorecount  # Starts at 0
        start_date = habitica_class.Habitica.offline_sincedate  # start time of program
        if ah.user_settings["keep_log"]:
            ah.log.debug("Offline. Score count: %s, Start date: %s (%s)" % (
                score_count, start_date, db_helper.prettyTime(start_date)))
    scored_points = int(score_count * ah.user_settings["sched"])
    if ah.user_settings["keep_log"]:
        ah.log.debug("Scored points: %s" % scored_points)
    db_score = calculate_db_score(start_date)
    if ah.user_settings["keep_log"]:
        ah.log.debug("Database score: %s" % db_score)
    newscore = db_score - scored_points
    if newscore < 0:
        newscore = 0  # sanity check
    # Capture old score
    ah.config[ah.settings.profile]['oldscore'] = ah.config[ah.settings.profile]['score']
    ah.config[ah.settings.profile]['score'] = newscore
    if ah.user_settings["keep_log"]:
        ah.log.debug("Old score: %s" %
                     ah.config[ah.settings.profile]['oldscore'])
    if ah.user_settings["keep_log"]:
        ah.log.debug("New score: %s" % newscore)
    if ah.user_settings["keep_log"]:
        ah.log.info("compare score: success")
    if ah.user_settings["keep_log"]:
        ah.log.debug("End function returning: %s" % True)
    return True


# Calculate score from database
def calculate_db_score(start_date):
    if ah.user_settings["keep_log"]:
        ah.log.debug("Begin function")
    db_correct = int(db_helper.correct_answer_count(start_date))

    if ah.user_settings["tries_eq"]:
        db_wrong = int(db_helper.wrong_answer_count(start_date) /
                       ah.user_settings["tries_eq"])
    else:
        db_wrong = 0

    if ah.user_settings["timeboxpoints"]:
        db_timebox = int(db_helper.timebox_count(start_date) *
                         ah.user_settings["timeboxpoints"])
    else:
        db_timebox = 0

    if ah.user_settings["deckpoints"]:
        db_decks = int(db_helper.decks_count(start_date) *
                       ah.user_settings["deckpoints"])
    else:
        db_decks = 0

    if ah.user_settings["learned_eq"]:
        db_learned = int(db_helper.learned_count(start_date) /
                         ah.user_settings["learned_eq"])
    else:
        db_learned = 0

    if ah.user_settings["matured_eq"]:
        db_matured = int(db_helper.matured_count(start_date) /
                         ah.user_settings["matured_eq"])
    else:
        db_matured = 0

    db_score = db_correct + db_wrong + db_timebox + db_decks + db_learned + db_matured
    if db_score < 0:
        db_score = 0  # sanity check
    if ah.user_settings["keep_log"]:
        ah.log.debug("End function returning: %s" % db_score)
    return db_score


####################
### Progress Bar ###
####################

# Make progress bar
def make_habit_progbar():
    if ah.user_settings["keep_log"]:
        ah.log.debug("Begin function")
    cur_score = ah.config[ah.settings.profile]['score']
    if ah.user_settings["keep_log"]:
        ah.log.debug("Current score for progress bar: %s out of %s" %
                     (cur_score, ah.user_settings["sched"]))
    if not ah.settings.configured:
        configure_ankihabitica()
    # length of progress bar excluding increased rate after threshold
    real_length = int(ah.user_settings["sched"] / ah.user_settings["step"])
    # length of progress bar including apparent rate increase after threshold
    fake_length = int(1.2 * real_length)
    if ah.settings.configured:
        # length of shaded bar excluding threshold trickery
        # total real bar length
        real_point_length = int(
            cur_score / ah.user_settings["step"]) % real_length
        # Find extra points to add to shaded bar to make the
        #   bar seem to double after threshold
        if real_point_length >= int(ah.settings.threshold / ah.user_settings["step"]):
            extra = real_point_length - \
                int(ah.settings.threshold / ah.user_settings["step"])
        else:
            extra = 0
        # length of shaded bar including threshold trickery
        fake_point_length = int(real_point_length + extra)
        # shaded bar should not be larger than whole prog bar
        bar = min(fake_length, fake_point_length)  # length of shaded bar
        hrpg_progbar = '<font color="%s">' % ah.user_settings["barcolor"]
        # full bar for each tick
        for i in range(bar):
            hrpg_progbar += "&#9608;"
        hrpg_progbar += '</font>'
        points_left = int(fake_length) - int(bar)
        hrpg_progbar += '<font color="%s">' % ah.user_settings["barbgcolor"]
        for i in range(points_left):
            hrpg_progbar += "&#9608"
        hrpg_progbar += '</font>'
        if ah.user_settings["keep_log"]:
            ah.log.debug("End function returning: %s" % hrpg_progbar)
        return hrpg_progbar
    else:
        if ah.user_settings["keep_log"]:
            ah.log.debug("End function returning: %s" % "")
        return ""

################################
### Score Habit in Real Time ###
################################


# Initialize habitica class
def initialize_habitica_class():
    if ah.user_settings["keep_log"]:
        ah.log.debug("Begin function")

    ah.habitica = habitica_class.Habitica()
    ah.settings.initialized = True
    # Keep track of the reward schedule, so if it ever changes, we reset
    # the scorecounter and scoresincedate to prevent problems
    habit = ah.user_settings["habit"]
    # set up oldsched dict in config
    try:
        if ah.config[ah.settings.profile]['oldsched'].__class__ == dict:
            ah.config[ah.settings.profile]['oldsched'] = ah.config[ah.settings.profile]['oldsched'][ah.user_settings["habit"]]
    except:
        ah.config[ah.settings.profile]['oldsched'] = ah.user_settings["sched"]
    # Find habits with a changed reward schedule
    if ah.config[ah.settings.profile]['oldsched'] != ah.user_settings["sched"]:
        # reset scorecounter and scoresincedate
        if ah.habitica.reset_scorecounter():
            # set oldsched to current sched
            ah.config[ah.settings.profile]['oldsched'] = ah.user_settings["sched"]
    if ah.user_settings["keep_log"]:
        ah.log.debug("End function")


# Run various checks to see if we are ready and try to make it ready
def be_ready():
    if ah.user_settings["keep_log"]:
        ah.log.debug("Begin function")
    if ah.user_settings["keep_log"]:
        ah.log.info("Checking if %s is ready" % ah.settings.profile)

    # Configure if not already
    if not ah.settings.configured:
        if ah.user_settings["keep_log"]:
            ah.log.info("Not configured")
        configure_ankihabitica()

    if not ah.settings.configured:
        if ah.user_settings["keep_log"]:
            ah.log.info("Not Ready: can't configured")
        return False

    # Grab user and token if in config
    if not ah.settings.user and not ah.settings.token:
        try:
            ah.settings.user = ah.config[ah.settings.profile]['user']
            ah.settings.token = ah.config[ah.settings.profile]['token']
        except:
            pass

    if not ah.settings.user and not ah.settings.token:
        if ah.user_settings["keep_log"]:
            ah.log.warning("Not Ready: no user or token")
        return False

    # initialize habitica class if AnkiHabitica is configured
    # and class is not yet initialized
    if not ah.settings.initialized:
        if ah.user_settings["keep_log"]:
            ah.log.info("Initializing habitica")
        initialize_habitica_class()

    # Check to make sure habitica class is initialized
    if not ah.settings.initialized:
        if ah.user_settings["keep_log"]:
            ah.log.warning("Not Ready: Not initialized")
        return False

    if ah.user_settings["keep_log"]:
        ah.log.info("Ready: %s %s" % (ah.settings.user, ah.settings.token))
    # Try to grab any habit ids that we've found.
    try:
        ah.config[ah.settings.profile]['habit_id'] = ah.habitica.habit_id
    except:
        pass
    # If we don't have any habits grabbed, attempt to grab them
    if ah.habitica.hnote == None:
        habitica_class.Habitica.offline_recover_attempt += 1
        if habitica_class.Habitica.offline_recover_attempt % 3 == 0:
            if ah.user_settings["keep_log"]:
                ah.log.info("Trying to grab habits")
            ah.habitica.init_update()
    if ah.user_settings["keep_log"]:
        ah.log.debug("End function returning: %s" % True)
    return True


# Process Habitica Points in real time
def hrpg_realtime(dummy=None):
    if ah.user_settings["keep_log"]:
        ah.log.debug("Begin function")
    crit_multiplier = 0
    streak_multiplier = 0
    drop_text = ""
    drop_type = ""

    # Check if we are ready; exit if not
    if not be_ready():
        if ah.user_settings["keep_log"]:
            ah.log.warning("End function returning: %s" % False)
        return False

    if not ah.user_settings["auto_earn"]:
        if ah.user_settings["keep_log"]:
            ah.log.warning(
                "End function for user disable: returning: %s" % False)
        return False

    # Compare score to database an make score progbar
    if compare_score_to_db():
        ah.settings.hrpg_progbar = make_habit_progbar()
    else:
        ah.settings.hrpg_progbar = ""

    # Post to Habitica if we just crossed a sched boundary
    #  because it's possible to earn multiple points at a time,
    #  (due to matured cards, learned cards, etc.)
    #  We can't rely on the score always being a multiple of sched
    #  as in the commented condition below...
    if int(ah.config[ah.settings.profile]['score'] / ah.user_settings["sched"]) > int(ah.config[ah.settings.profile]['oldscore'] / ah.user_settings["sched"]):
        # Check internet if down
        if not ah.settings.internet:
            ah.settings.internet = ah.habitica.test_internet()
        # If Internet is still down
        if not ah.settings.internet:
            ah.habitica.hrpg_showInfo(
                "Hmm...\n\nI can't connect to Habitica. Perhaps your internet is down.\n\nI'll remember your points and try again later.")

        if ah.settings.internet:
            ah.habitica.earn_points()
            if ah.config[ah.settings.profile]['score'] < 0:
                ah.config[ah.settings.profile]['score'] = 0
    if ah.user_settings["keep_log"]:
        ah.log.debug("End function")


#############################
### Process Score Backlog ###
#############################

#    Score habitica task for reviews that have not been scored yet
#    for example, reviews that were done on a smartphone.
def score_backlog(silent=False):
    if ah.user_settings["keep_log"]:
        ah.log.debug("Begin function")
    # Warn User that this can take some time
    warning = "Warning: Scoring backlog may take some time.\n\nMake sure Anki is synced across your devices before you do this. If you do this and you have unsynced reviews on another device, those reviews will not be counted towards Habitica points!\n\nWould you like to continue?"
    if not silent:
        if ah.user_settings["keep_log"]:
            ah.log.debug(warning.replace('\n', ' '))
        cont = utils.askUser(warning)
    else:
        cont = True
    if ah.user_settings["keep_log"]:
        ah.log.debug(
            "User chose to score backlog (or silent mode is on): %s" % cont)
    if not cont:
        if ah.user_settings["keep_log"]:
            ah.log.warning("End function returning: %s" % False)
        return False

    # Exit if not ready
    if not be_ready():
        if ah.user_settings["keep_log"]:
            ah.log.warning("End function returning: %s" % False)
        return False

    # Check internet if down
    if not ah.settings.internet:
        ah.settings.internet = ah.habitica.test_internet()
    # If Internet is still down but class initialized
    if not ah.settings.internet and ah.settings.initialized:
        if not silent:
            ah.habitica.hrpg_showInfo(
                "Hmm...\n\nI can't connect to Habitica. Perhaps your internet is down.\n\nI'll remember your points and try again later.")
        if ah.user_settings["keep_log"]:
            ah.log.warning("No internet connection")
        if ah.user_settings["keep_log"]:
            ah.log.warning("End function returning: %s" % False)
        return False

    ah.habitica.grab_scorecounter()

    # Compare database to scored points
    if compare_score_to_db():
        if ah.config[ah.settings.profile]['score'] < ah.user_settings["sched"]:
            if not silent:
                utils.showInfo("No backlog to score")
            if ah.user_settings["keep_log"]:
                ah.log.info("No backlog to score")
            if ah.user_settings["keep_log"]:
                ah.log.debug("End function returning: %s" % True)
            return True
        # OK, now we can score some points...
        p = 0  # point counter
        i = 0  # limit tries to 25 to prevent endless loop
        numScores = ah.config[ah.settings.profile]['score'] // ah.user_settings["sched"]
        if ah.user_settings["keep_log"]:
            ah.log.debug("%s points to score" % numScores)
        progressLabel = "Scoring %s point%s to Habitica" % (
            numScores, "" if numScores == 0 else "s")
        mw.progress.start(max=numScores, label=progressLabel)
        while i <= 25 and ah.config[ah.settings.profile]['score'] >= ah.user_settings["sched"] and ah.settings.internet:
            try:
                ah.habitica.silent_earn_points()
                ah.config[ah.settings.profile]['score'] -= ah.user_settings["sched"]
                i += 1
                p += 1
                mw.progress.update()
            except urllib.error.HTTPError as e:
                if e.code == 429:
                    break
                i += 1
        mw.progress.finish()
        tip_text = "%s point%s scored on Habitica%s" % (p, "" if p == 1 else "s",
            "" if ah.config[ah.settings.profile]['score'] == 0 else ", and ignore the remaining beacuse of Habitica limit")
        if not silent:
            utils.showInfo(tip_text)
        if ah.user_settings["keep_log"]:
            ah.log.info(tip_text)
            ah.log.info("New scorecount: %s" %
                        ah.habitica.hnote['scorecount'])
            ah.log.info("New config score: %s" %
                        ah.config[ah.settings.profile]['score'])
        ah.habitica.hnote['scorecount'] = habitica_class.Habitica.offline_scorecount = 0
        ah.habitica.hnote['scoresincedate'] = habitica_class.Habitica.offline_sincedate = db_helper.latest_review_time()
        ah.config[ah.settings.profile]['score'] = 0
        ah.habitica.post_scorecounter()
        runHook("HabiticaAfterScore")
        time.sleep(1)
        save_stats(None, None)
    if ah.user_settings["keep_log"]:
        ah.log.debug("End function")


# Add Score Backlog to menubar
if ah.user_settings["keep_log"]:
    ah.log.debug('Adding Score Backlog to menubar')
backlog_action = QAction("Score Habitica Backlog", mw)
backlog_action.triggered.connect(score_backlog)
AnkiHabiticaMenu.addAction(backlog_action)


# Refresh Habitica Avatar
#    Sometimes it comes down malformed.
def refresh_habitica_avatar():
    if ah.user_settings["keep_log"]:
        ah.log.debug("Begin function")
    if ah.settings.initialized and ah.settings.internet:
        if habitica_class.Habitica.allow_threads:
            _thread.start_new_thread(ah.habitica.save_avatar, ())
        else:
            ah.habitica.save_avatar()
    if ah.user_settings["keep_log"]:
        ah.log.debug("End function")


# Add Refresh Habitica Avatar to menubar
if ah.user_settings["keep_log"]:
    ah.log.debug('Adding Refresh Habitica Avatar to menubar')
avatar_action = QAction("Refresh Habitica Avatar", mw)
avatar_action.triggered.connect(refresh_habitica_avatar)
AnkiHabiticaMenu.addAction(avatar_action)


def check_unsynced_score():
    if ah.user_settings["keep_log"]:
        ah.log.debug("Begin function")

    if not (be_ready() and ah.user_settings["check_db_on_profile_load"] and ah.habitica.grab_scorecounter() and compare_score_to_db()):
        if ah.user_settings["keep_log"]:
            ah.log.debug("Can't check")
        return

    if ah.user_settings["keep_log"]:
        ah.log.debug("%s point(s) earned of %s required" % (
            ah.config[ah.settings.profile]['score'], ah.user_settings["sched"]))
    if ah.config[ah.settings.profile]['score'] >= ah.user_settings["sched"] or ah.config[ah.settings.profile]['oldscore'] >= ah.user_settings["sched"]:
        if ah.user_settings["keep_log"]:
            ah.log.debug("Asking user to sync backlog.")
        if utils.askUser(
            '''New reviews found. Sync with Habitica now? Anki will freeze while syncing.

WARNING: Make sure Anki is synced across your devices before you do this. If you do this and you have unsynced reviews on another device, those reviews will not be counted towards Habitica points!
'''):
            if ah.user_settings["keep_log"]:
                ah.log.debug('Syncing backlog')
            score_backlog()


if new_hook:
    try:
        gui_hooks.sync_did_finish.append(check_unsynced_score)
    except AttributeError:
        pass

#################################
### Support Multiple Profiles ###
#################################


def grab_profile():
    if ah.user_settings["keep_log"]:
        ah.log.debug("Begin function")
    reset_ah_settings()
    ah.settings.profile = aqt.mw.pm.name
    if ah.user_settings["keep_log"]:
        ah.log.info("your profile is %s" % (ah.settings.profile))
    if ah.settings.profile not in ah.config:
        ah.config[ah.settings.profile] = {}
        if ah.user_settings["keep_log"]:
            ah.log.info("adding %s to config dict" % ah.settings.profile)

    check_unsynced_score()

#################
### Wrap Code ###
#################


addHook("profileLoaded", grab_profile)
addHook("unloadProfile", save_stats)
Reviewer.nextCard = wrap(Reviewer.nextCard, hrpg_realtime, "before")

# Insert progress bar into bottom review stats
#       along with database scoring and realtime habitica routines
orig_remaining = Reviewer._remaining


def my_remaining(x):
    if ah.user_settings["keep_log"]:
        ah.log.debug("Begin function")
    ret = orig_remaining(x)
    if ah.user_settings["show_progress_bar"] and not ah.settings.hrpg_progbar == "":
        ret += " : %s" % (ah.settings.hrpg_progbar)
    if ah.settings.initialized and ah.user_settings["show_mini_stats"]:
        mini_stats = ah.habitica.compact_habitica_stats()
        if mini_stats:
            ret += " : %s" % (mini_stats)
    if ah.user_settings["keep_log"]:
        ah.log.debug("End function returning: %s" % ret)
    return ret


Reviewer._remaining = my_remaining
