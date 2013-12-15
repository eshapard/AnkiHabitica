#AnkiRPG
#Anki 2 plugin for use with HabitRPG http://habitrpg.com
#Author: Edward Shapard <ed.shapard@gmail.com>
#License: GNU GPL v3 <www.gnu.org/licenses/gpl.html>

import urllib2, urllib,  os, sys, json
from anki.hooks import wrap
from aqt.reviewer import Reviewer
from anki.sched import Scheduler
from aqt import *




config ={}
conffile = os.path.join(os.path.dirname(os.path.realpath(__file__)), ".habitrpg.conf")
conffile = conffile.decode(sys.getfilesystemencoding())
deck_habitpost = urllib2.Request('https://habitrpg.com/api/v1/user/task/Anki%20Deck%20Complete/up','POST')
timebox_habitpost = urllib2.Request('https://habitrpg.com/api/v1/user/task/Anki%20Timebox%20Reached/up','POST')

if os.path.exists(conffile):    # Load config file
    config = json.load(open(conffile, 'r'))
    api_token = config['token']
    user_id = config['user']
    deck_habitpost.add_header('x-api-user', user_id)
    deck_habitpost.add_header('x-api-key', api_token)
    timebox_habitpost.add_header('x-api-user', user_id)
    timebox_habitpost.add_header('x-api-key', api_token)

def internet_on():
    try:
        response=urllib2.urlopen('http://habitrpg.com',timeout=1)
        return True
    except urllib2.URLError as err: pass
    return False


def deck_habit_score():
    #sent post reqest
    if internet_on:
        urllib2.urlopen(deck_habitpost)

def timebox_habit_score():
    #sent post reqest
    if internet_on:
        urllib2.urlopen(timebox_habitpost)

#Setup menu to configure HRPG userid and api key
def setup():
    if os.path.exists(conffile):
        config = json.load(open(conffile, 'r'))
        api_token = config['token']
        user_id = config['user']
    user_id, ok = utils.getText("Enter your user ID:")
    if ok == True:
        api_token, ok = utils.getText('Enter your API token:')
        if ok == True:          # Create config file and save values
            api_token = str(api_token)
            user_id = str(user_id)
            config = {'token' : api_token, 'user' : user_id }
            json.dump( config, open( conffile, 'w' ) )
            deck_habitpost.add_header('x-api-user', user_id)
            deck_habitpost.add_header('x-api-key', api_token)
            timebox_habitpost.add_header('x-api-user', user_id)
            timebox_habitpost.add_header('x-api-key', api_token)
            utils.showInfo("The add-on has been setup.")


#Add Setup to menubar
action = QAction("Setup HabitRPG", mw)
mw.connect(action, SIGNAL("triggered()"), setup)
mw.form.menuTools.addAction(action)


#Timebox Reached
def timebox_habit(self):
    elapsed = self.mw.col.timeboxReached()
    if elapsed:
        timebox_habit_score()

#Deck Completed
def deck_complete_habit(self):
    deck_habit_score()

#Wrap Code
Reviewer.nextCard = wrap(Reviewer.nextCard, timebox_habit, "before")
Scheduler.finishedMsg = wrap(Scheduler.finishedMsg, deck_complete_habit, "before")
