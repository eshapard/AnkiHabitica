#AnkiHRPG
#Anki 2 plugin for use with HabitRPG http://habitrpg.com
#Author: Edward Shapard <ed.shapard@gmail.com>
#Version 0.04
#License: GNU GPL v3 <www.gnu.org/licenses/gpl.html>

import urllib2, urllib,  os, sys, json
from anki.hooks import wrap, addHook
from aqt.reviewer import Reviewer
from anki.sched import Scheduler
from aqt import *
from anki.sync import Syncer
from aqt.main import AnkiQt

config ={}
conffile = os.path.join(os.path.dirname(os.path.realpath(__file__)), ".habitrpg.conf")
conffile = conffile.decode(sys.getfilesystemencoding())
deck_habitpost = urllib2.Request('https://habitica.com/api/v2/user/tasks/Anki%20Deck%20Complete/up','')
timebox_habitpost = urllib2.Request('https://habitica.com/api/v2/user/tasks/Anki%20Timebox%20Reached/up','')
score_habitpost = urllib2.Request('https://habitica.com/api/v2/user/tasks/Anki%20Correct%20Answer/up','')
Syncer.timeboxes = 0
Syncer.decks = 0
Syncer.score = 0
Syncer.habit_configured = False

def internet_on():
    try:
        response=urllib2.urlopen('http://habitica.com',timeout=1)
        return True
    except urllib2.URLError as err: pass
    return False

#Read values from file if it exists
if os.path.exists(conffile):    # Load config file
    config = json.load(open(conffile, 'r'))
    api_token = config['token']
    user_id = config['user']
    Syncer.timeboxes = config['timeboxes']
    Syncer.decks = config['decks']
    Syncer.score = config['score']
    deck_habitpost.add_header('x-api-user', user_id)
    deck_habitpost.add_header('x-api-key', api_token)
    timebox_habitpost.add_header('x-api-user', user_id)
    timebox_habitpost.add_header('x-api-key', api_token)
    score_habitpost.add_header('x-api-user', user_id)
    score_habitpost.add_header('x-api-key', api_token)
    Syncer.habit_configured = True


#Setup menu to configure HRPG userid and api key
def setup():
    global config
    if os.path.exists(conffile):
        config = json.load(open(conffile, 'r'))
        api_token = config['token']
        user_id = config['user']
        Syncer.score = config['score']
        Syncer.decks = config['decks']
        Syncer.timeboxes = config['timeboxes']
    else:
        config['score'] = Syncer.score
        config['decks'] = Syncer.decks
        config['timeboxes'] = Syncer.timeboxes
    user_id, ok = utils.getText("Enter your user ID:")
    if ok == True:
        api_token, ok = utils.getText('Enter your API token:')
        if ok == True:          # Create config file and save values
            api_token = str(api_token)
            user_id = str(user_id)
            config['user'] = user_id
            config['token'] = api_token
            json.dump( config, open( conffile, 'w' ) )
            deck_habitpost.add_header('x-api-user', user_id)
            deck_habitpost.add_header('x-api-key', api_token)
            timebox_habitpost.add_header('x-api-user', user_id)
            timebox_habitpost.add_header('x-api-key', api_token)
            score_habitpost.add_header('x-api-user', user_id)
            score_habitpost.add_header('x-api-key', api_token)
            Syncer.habit_configured = True
            utils.showInfo("The add-on has been setup.")


#Add Setup to menubar
action = QAction("Setup HabitRPG", mw)
mw.connect(action, SIGNAL("triggered()"), setup)
mw.form.menuTools.addAction(action)

#Timebox Reached
def timebox_habit(self):
    elapsed = self.mw.col.timeboxReached()
    if elapsed:
        Syncer.timeboxes += 1

#Deck Completed
def deck_complete_habit(self):
    Syncer.decks += 1

def card_answered(self, ease):  # Cache number of correct answers
    global config
    if Syncer.habit_configured:
        if ease > 1:
            Syncer.score += 1
            config['score'] = Syncer.score

def save_stats(x,y):
    global config
    config['decks'] = Syncer.decks
    config['timeboxes'] = Syncer.timeboxes
    config['score'] = Syncer.score
    json.dump( config, open( conffile, 'w' ) )


#Sync scores to HabitRPG
def habitrpg_sync(x):
    global config
    if Syncer.habit_configured:
        if internet_on:
            #Sync decks
            while Syncer.decks >= 1:
                urllib2.urlopen(deck_habitpost)
                Syncer.decks -= 1
            config['decks'] = Syncer.decks
            #Sync timeboxes
            while Syncer.timeboxes >= 1:
                urllib2.urlopen(timebox_habitpost)
                Syncer.timeboxes -= 1
            config['timeboxes'] = Syncer.timeboxes
            #Sync answers
            while Syncer.score >= 5:
                urllib2.urlopen(score_habitpost)
                Syncer.score -= 5
            config['score'] = Syncer.score
            json.dump( config, open( conffile, 'w' ) )
        else:
            config['decks'] = Syncer.decks
            config['timeboxes'] = Syncer.timeboxes
            config['score'] = Syncer.score
            json.dump( config, open( conffile, 'w' ) )

#Wrap Code
Reviewer.nextCard = wrap(Reviewer.nextCard, timebox_habit, "before")
Reviewer._answerCard = wrap(Reviewer._answerCard, card_answered, "before")
Scheduler.finishedMsg = wrap(Scheduler.finishedMsg, deck_complete_habit, "before")
Syncer.sync = wrap(Syncer.sync, habitrpg_sync, "before")
AnkiQt.closeEvent = wrap(AnkiQt.closeEvent, save_stats, "before")
