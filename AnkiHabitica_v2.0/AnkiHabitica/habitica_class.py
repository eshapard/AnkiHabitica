#!/usr/bin/python
from habitica_api import HabiticaAPI
import os, sys, json, datetime, time, thread
from aqt import *
from aqt.main import AnkiQt
import db_helper

class Habitica(object):
    habitlist = ["Anki Points"] #list of habits to check
    #find icon file
    iconfile = os.path.join(os.path.dirname(os.path.realpath(__file__)), "habitica_icon.png")
    avatarfile = os.path.join(os.path.dirname(os.path.realpath(__file__)), "avatar.png")
    iconfile = iconfile.decode(sys.getfilesystemencoding())
    avatarfile = avatarfile.decode(sys.getfilesystemencoding())
    if os.path.exists(avatarfile): #use avatar.png as icon if it exists
        iconfile = avatarfile
    
    def __init__(self, user_id, api_token, profile, conffile, show_popup=True):
        self.api = HabiticaAPI(user_id, api_token)
        self.profile = profile
        self.conffile = conffile
        self.show_popup = show_popup
        self.name = 'Anki User'
	self.user = None
        self.lvl = 0
        self.xp = 0
	self.xt = 0
        self.gp = 0
        self.hp = 0
	self.ht = 50
        self.mp = 0
	self.mt = 0
        self.stats = {}
        self.hrpg_attempt = 0
	self.hnote = {}
	self.habit_checked = {}
	self.missing = {} #holds missing habits
	for habit in Habitica.habitlist:
		self.habit_checked[habit] = False
		#create a thread to check the habit as to not slow down
		#the startup process
		thread.start_new_thread(self.check_anki_habit, (habit,))
	#Grab user object in the background
	thread.start_new_thread(self.init_grab_stats, ())

    #Try updating stats silently on init
    def init_grab_stats(self):
        try:
            self.update_stats(True)
        except:
            return



    def hrpg_showInfo(self, text):
        #display a small message window with an OK Button
        parent = aqt.mw.app.activeWindow() or aqt.mw
        icon = QMessageBox.Information
        mb = QMessageBox(parent)
        mb.setText(text)
        if os.path.isfile(Habitica.iconfile):
            mb.setIconPixmap(QPixmap(Habitica.iconfile))
        else:
            mb.setIcon(icon)
        mb.setWindowModality(Qt.WindowModal)
        mb.setWindowTitle("Anki Habitica")
        b = mb.addButton(QMessageBox.Ok)
        b.setDefault(True)
	return mb.exec_()

    def hrpg_tooltip(self, text):
        utils.tooltip(_(text), period=1500)


    def get_user_object(self):
        return self.api.user()

    def update_stats(self, silent=False):
        #self.hrpg_tooltip("Connecting to Habitica")
        try:
            user = self.get_user_object()
        except:
            if not silent: self.hrpg_showInfo("Unable to log in to Habitica.\n\nCheck that you have the correct user-id and api-token in\n%s.\n\nThese should not be your username and password.\n\nPost at github.com/eshapard/AnkiHRPG if this issue persists." % (self.conffile))
            return
        self.name = user['profile']['name']
        self.stats = user['stats']
        self.lvl = self.stats['lvl']
        self.xp = self.stats['exp']
        self.gp = self.stats['gp']
        self.hp = self.stats['hp']
        self.mp = self.stats['mp']
	self.xt = self.stats['toNextLevel']
	self.ht = self.stats['maxHealth']
	self.mt = self.stats['maxMP']
        return

    def score_anki_points(self, habit):
        return self.api.perform_task(habit, "up")

    def update_anki_habit(self, habit):
        #return self.api.alter_task("Anki Points", True, False, None, None, None, "int", None)
        data = {'up': True, 'down': False, 'attribute': 'int'}
        return self.api.update_task(habit, data)

    def check_anki_habit(self, habit):
        #Check to see if habit exists
	#utils.showInfo("Checking %s habit" % habit)
        if habit not in self.missing:
                found = False
                tasks = self.api.tasks()
                #utils.showInfo(tasks) 
                for t in tasks:
                    if t['id'] == habit:
                        found = True
                if found:
                    self.missing[habit] = False
		    #utils.showInfo("Task found")
                    return True
                else:
                    self.missing[habit] = True
		    #utils.showInfo("Task not found")
                    return False

        #Check to see that habitica habit is set up properly
        try:
            response = self.api.task(habit)
        except:
          return False
        if response['down'] or response['attribute'] != "int":
            try:
                self.update_anki_habit(habit)
                return True
            except:
                hrpg_showInfo("Your %s habit is not configured correctly yet.\nPlease set it to Up only and Mental attribute." % habit)
                return False
        return True

    def reset_scorecounter(self, habit):
        curtime = int(time.time())
        self.hnote[habit] = {'scoresincedate' : curtime, 'scorecount': 0}
	self.habit_checked[habit] = True

    def grab_scorecounter(self, habit):
	#utils.showInfo("grabbing scorecounter")
	try:
            response = self.api.task(habit)
        except:
            #Check if habit exists
            if habit not in self.missing:
                self.check_anki_habit(habit)
            #Reset scorecount if habit is missing
            if self.missing[habit]: 
                self.reset_scorecounter(habit)
            return False
        #Try to grab the scorecount and score since date
        try: 
           self.hnote[habit] = json.loads(response['notes'])
           if 'scoresincedate' not in self.hnote[habit] or 'scorecount' not in self.hnote[habit]:
               #reset habit score counter if both keys not found
               self.reset_scorecounter(habit)
	   self.habit_checked[habit] = True
           return True
	except:
           #failed to grab, so reset
           self.reset_scorecounter(habit)
           return False

    def post_scorecounter(self, habit):
	#utils.showInfo("posting scorecounter")
	datastring = json.dumps(self.hnote[habit])
	#self.hrpg_showInfo(datastring)
	data = {"notes" : datastring}
        return self.api.update_task(habit, data)

    def scorecount_on_sync(self, x=None):
            for habit in self.habit_checked:
	        if self.habit_checked[habit]:
                    self.post_scorecounter(habit)
	        else:
                    self.grab_scorecounter(habit)

    def test_internet(self):
        #self.hrpg_tooltip("Testing Internet Connection")
        return self.api.test_internet()
            
    def make_score_message(self, new_lvl, new_xp, new_mp, new_gp, new_hp, streak_bonus=0, crit_multiplier=0, drop_dialog=None):
        hrpgresponse = "Huzzah! You Get Points!\nWell Done %s!\n" % (self.name)
        #Check for increases and add to message
        if new_lvl > self.lvl:
            diff = int(new_lvl) - int(self.lvl)
            hrpgresponse += "\nYOU LEVELED UP! NEW LEVEL: %s" % (new_lvl)
	hrpgresponse += "\nHP: %s" % (int(self.hp))
	if new_hp > self.hp:
            diff = int(new_hp) - int(self.hp)
            hrpgresponse += "  +%s!" % (diff)
        hrpgresponse += "\nXP: %s" % (int(self.xp))
        if new_xp > self.xp:
            diff = int(new_xp) - int(self.xp)
            hrpgresponse += "  +%s!" % (diff)
        hrpgresponse += "\nGP: %s" % (round(self.gp, 2))
        if new_gp > self.gp:
            diff = int(new_gp) - int(self.gp)
            hrpgresponse += "  +%s!" % (diff)
        hrpgresponse += "\nMP: %s" % (int(self.mp))
        if new_mp > self.mp:
            diff = int(new_mp) - int(self.mp)
            hrpgresponse += "  +%s!" % (diff)
        #Check for drops, streaks, and critical hits
        if crit_multiplier:
            hrpgresponse += "\nCritical Hit! Bonus: +%s%%" % (int(float(crit_multiplier)))
        if streak_bonus:
            hrpgresponse += "\nStreak Bonus! +%s" % (int(streak_bonus))   
        if drop_dialog:
            hrpgresponse += "\n%s" % (drop_dialog)
        #Show message box
        if self.show_popup:
            self.hrpg_showInfo(hrpgresponse)
        else:
            self.hrpg_tooltip("Huzzah! You Scored Points!")

        #update levels
        if new_lvl > self.lvl and self.lvl > 0:
            self.update_stats(False)
        else:
            self.lvl = new_lvl
            self.xp = new_xp
            self.mp = new_mp
            self.gp = new_gp
            self.hp = new_hp
        return True

    def earn_points(self, habit):
        #get user stats if we don't have them
        if 'lvl' not in self.stats:
            self.update_stats(False)
        #check habit if is is unchecked
        if not self.habit_checked[habit]:
	    try:
                self.hrpg_tooltip("Checking Habit Score Counter")
	        self.check_anki_habit(habit)
                self.grab_scorecounter(habit)
	    except:
                pass
        crit_multiplier = 0
        streak_bonus = 0
	drop_dialog = None
        try:
            msg = self.score_anki_points(habit)
            self.hnote[habit]['scorecount'] += 1
        except:
	    self.hrpg_showInfo("Sorry,\nI couldn't score your %s habit on Habitica.\nDon't worry, I'll remember your points and try again later." % habit)
            return False
        
        new_lvl = msg['lvl']
        new_xp = msg['exp']
        new_mp = msg['mp']
        new_gp = msg['gp']
        new_hp = msg['hp']
        if msg['_tmp']:
            if 'streakBonus' in msg['_tmp']:
                #streak
                streak_bonus = str(round((100 * msg['_tmp']['streakBonus']), 0))
            if 'crit' in msg['_tmp']:
                #critical
                crit_multiplier = str(round((100 * msg['_tmp']['crit']), 0))
                if 'drop' in msg['_tmp'] and 'dialog' in msg['_tmp']['drop']:
                    #drop happened
		    #drop_string = json.loads(msg['_tmp']['drop'])
                    #drop_text = msg['_tmp']['drop']['text']
                    #drop_type = msg['_tmp']['drop']['type']
                    drop_dialog = msg['_tmp']['drop']['dialog']
        #Update habit if it was just created
        if habit in self.missing and self.missing[habit]:
            if self.check_anki_habit(habit):
                self.missing[habit] = False

        return self.make_score_message(new_lvl, new_xp, new_mp, new_gp, new_hp, streak_bonus, crit_multiplier, drop_dialog)

    #Compact Habitica Stats for Progress Bar
    def compact_habitica_stats(self):
    	if self.ht and self.xt and self.mt:
		health = int( 100 * self.hp / self.ht )
		experience = int( 100 * self.xp / self.xt )
		mana = int( 100 * self.mp / self.mt )
		string = "<font color='firebrick'>%s</font> | <font color='darkorange'>%s</font> | <font color='darkblue'>%s</font>" % (health, experience, mana)
	else:
		string = False
	return string
	
    #Silent Version of Earn Points
    def silent_earn_points(self, habit):
	#check habit if is is unchecked
        if not self.habit_checked[habit]:
	    try:
	        self.check_anki_habit(habit)
                self.grab_scorecounter(habit)
	    except:
                pass
        try:
            self.score_anki_points(habit)
            self.hnote[habit]['scorecount'] += 1
        except:
            return False
        
        return True
