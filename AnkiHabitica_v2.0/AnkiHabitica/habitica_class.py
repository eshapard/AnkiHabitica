#!/usr/bin/python
from habitica_api import HabiticaAPI
import os, sys, json, datetime, time, thread
from aqt import *
from aqt.main import AnkiQt
from anki.hooks import runHook
import db_helper
from anki.utils import intTime
from ah_common import AnkiHabiticaCommon as ah

#TODO: make sure script can survive internet outages.

class Habitica(object):
    debug = False
    allow_threads = True #startup config processes checking habits, etc.
    allow_post_scorecounter_thread = True #Maybe a source of database warnings?
    #find icon file
    iconfile = os.path.join(os.path.dirname(os.path.realpath(__file__)), "habitica_icon.png")
    iconfile = iconfile.decode(sys.getfilesystemencoding())
    offline_sincedate = intTime() #Score Since date for when we are offline
    offline_scorecount = 0 #Starting score for offline 
    offline_recover_attempt = 0 #attempt to recover from offline state every third time

    
    def __init__(self):
        self.api = HabiticaAPI(ah.settings.user, ah.settings.token)
        #ah.settings.profile = profile
        #ah.conffile = ah.conffile
	#self.habitlist = ah.settings.habitlist
        #ah.settings.show_popup = show_popup
	#ah.settings.sched_dict = ah.settings.sched_dict #holder for habit reward schedules
        self.name = 'Anki User'
        self.lvl = 0
        self.xp = 0
	self.xt = 0
        self.gp = 0
        self.hp = 0
	self.ht = 50
        self.mp = 0
	self.mt = 0
        self.stats = {}
	self.hnote = {}
	self.habit_grabbed = {} #marked true when we get scorecounter.
	self.habit_id = ah.config[ah.settings.profile]['habit_id'] #holder for habit IDs 
	self.missing = {} #holds missing habits
	self.init_update() #check habits, grab user object, get avatar


    def init_update(self):
	for habit in ah.settings.habitlist:
		self.habit_grabbed[habit] = False
		#create a thread to check the habit as to not slow down
		#the startup process
		if Habitica.allow_threads:
			thread.start_new_thread(self.check_anki_habit, (habit,))
		else:
			self.check_anki_habit(habit)
	#Grab user object in the background
	if Habitica.allow_threads:
		thread.start_new_thread(self.init_grab_stats, ())
	else:
		self.init_grab_stats()
	#Grab avatar from habitica
	if Habitica.allow_threads:
		thread.start_new_thread(self.save_avatar, ())
	else:
		self.save_avatar()

    #Try updating stats silently on init
    def init_grab_stats(self):
        try:
            self.update_stats(True)
        except:
            return

    #Save avatar from habitica as png
    def save_avatar(self):
	#See if there's an image for this profile
	profile_pic = ah.settings.profile + ".png"
	self.avatarfile = os.path.join(os.path.dirname(os.path.realpath(__file__)), profile_pic)
	self.avatarfile = self.avatarfile.decode(sys.getfilesystemencoding())
	try:
        	pngfile = self.api.export_avatar_as_png() #Grab avatar png from Habitica
		if not pngfile: return False #Exit if we failed
		with open(self.avatarfile, 'wb') as outfile:
			outfile.write(pngfile)
		del pngfile
	except:
		pass
	if os.path.exists(self.avatarfile): 
		#use {profile}.png as icon if it exists
		self.iconfile = self.avatarfile
	else:
		self.iconfile = Habitica.iconfile


    def hrpg_showInfo(self, text):
        #display a small message window with an OK Button
        parent = aqt.mw.app.activeWindow() or aqt.mw
        icon = QMessageBox.Information
        mb = QMessageBox(parent)
        mb.setText(text)
        if os.path.isfile(self.iconfile):
            mb.setIconPixmap(QPixmap(self.iconfile))
        else:
            mb.setIcon(icon)
        mb.setWindowModality(Qt.WindowModal)
        mb.setWindowTitle("Anki Habitica")
        b = mb.addButton(QMessageBox.Ok)
        b.setDefault(True)
	return mb.exec_()

    def get_user_object(self):
        return self.api.user()

    def update_stats(self, silent=False):
        #self.hrpg_tooltip("Connecting to Habitica")
        try:
            user = self.get_user_object()
        except:
            if not silent: self.hrpg_showInfo("Unable to log in to Habitica.\n\nCheck that you have the correct user-id and api-token in\n%s.\n\nThese should not be your username and password.\n\nPost at github.com/eshapard/AnkiHRPG if this issue persists." % (ah.conffile))
            return False
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
	if Habitica.debug: utils.showInfo(self.name)
        return True

    def score_anki_points(self, habit):
      try:
        habitID = self.habit_id[habit]
        return self.api.perform_task(habitID, "up")
      except:
        return False

    def update_anki_habit(self, habit):
      try:
        habitID = self.habit_id[habit]
        #return self.api.alter_task("Anki Points", True, False, None, None, None, "int", None)
        data = {'up': True, 'down': False, 'attribute': 'int'}
        return self.api.update_task(habitID, data)
      except:
        return False

    #Check Anki Habit, make new one if it does not exist, and try to
    #	grab the note string.
    def check_anki_habit(self, habit):
        found = False
	if Habitica.debug: utils.showInfo("checking %s" % habit)
        if habit not in self.habit_id:
          try:
            self.habit_id[habit] = self.api.find_habit_id(habit)
	    habitID = self.habit_id[habit]
          except:
            return False
        else:
            habitID = self.habit_id[habit]
	    #We have an ID, but we may want to check that the habit still exists
	if Habitica.debug: utils.showInfo("HabitID: %s" % habitID)
        if not habitID: #find_habit_id returned False; habit not found!
            if Habitica.debug: utils.showInfo("Habit ID Missing")
            del self.habit_id[habit]
            self.missing[habit] = True
            if Habitica.debug: utils.showInfo("Task not found")
            self.create_missing_habit(habit)
            return False
        #Check to see if habit Still exists
	if Habitica.debug: utils.showInfo("Checking %s habit" % habit)
        if not found:
            try:
                tasks = self.api.tasks()
		if Habitica.debug: utils.showInfo(json.dumps(tasks)) 
                for t in tasks:
                    if str(t['id']) == str(habitID):
                        found = True
                if found:
                    self.missing[habit] = False
		    del tasks
		    if Habitica.debug: utils.showInfo("Task found")
                else:
                    self.missing[habit] = True
		    if Habitica.debug: utils.showInfo("Task not found")
                    self.create_missing_habit(habit)
		    del tasks
                    return False
            except:
                pass
        #Check to see that habitica habit is set up properly
	if Habitica.debug: utils.showInfo("Checking habit setup")
        try:
           response = self.api.task(habitID)
        except:
            if Habitica.debug: utils.showInfo("Could not retrieve task")
            return False
        if response['down'] or response['attribute'] != "int":
            try:
                if Habitica.debug: utils.showInfo("Updating Habit")
                self.update_anki_habit(habitID)
                return True
            except:
                hrpg_showInfo("Your %s habit is not configured correctly yet.\nPlease set it to Up only and Mental attribute." % habit)
                return False
	if Habitica.debug: utils.showInfo("Habit looks good")
	#Grab scorecounter from habit
	return self.grab_scorecounter(habit)

    #Create a missing habits
    def create_missing_habit(self, habit):
        try:
            #create habit
            if Habitica.debug: utils.showInfo("Trying to create %s habit" % habit)	    
            #create task on habitica
            curtime = intTime()
            self.hnote[habit] = {'scoresincedate' : curtime, 'scorecount': 0, 'sched': ah.settings.sched_dict[habit]}
            note = json.dumps(self.hnote[habit])
            msg = self.api.create_task('habit', habit, False, note, 'int', 1, True)
            self.habit_id[habit] = str(msg['_id']) #capture new task ID
            if Habitica.debug: utils.showInfo("New habit created: %s" %self.habit_id[habit])
            if Habitica.debug: utils.showInfo(json.dumps(msg))
            #self.reset_scorecounter(habit)
            self.missing[habit] = False
            self.habit_grabbed[habit] = True
        except:
            return False


    def reset_scorecounter(self, habit):
        if Habitica.debug: utils.showInfo("Resetting Scorecounter")
        curtime = intTime()
	if Habitica.debug: utils.showInfo(str(curtime))
	self.hnote[habit] = {'scoresincedate' : curtime, 'scorecount': 0, 'sched': ah.settings.sched_dict[habit]}
	self.habit_grabbed[habit] = True
	if Habitica.debug: utils.showInfo("reset: %s" % json.dumps(self.hnote[habit]))
	try:
		self.post_scorecounter(habit)
		return True
	except:
		return False

    def grab_scorecounter(self, habit):
	if self.habit_grabbed[habit]: return True
	try:
            habitID = str(self.habit_id[habit])
	    if Habitica.debug: utils.showInfo("grabbing scorecounter\n%s" % habitID)
	    response = self.api.task(habitID)
	    if not habitID: return False
	    if Habitica.debug: utils.showInfo(response['notes'])
        except:
            #Check if habit exists
            if habit not in self.missing:
                if Habitica.debug: utils.showInfo("Habit not missing")
            #Reset scorecount if habit is missing
            if self.missing[habit]: 
                if Habitica.debug: utils.showInfo("Habit was missing")
                self.reset_scorecounter(habit)
            return False
        #Try to grab the scorecount and score since date
        if Habitica.debug: utils.showInfo("trying to load note string:\n%s" % response['notes'])
	try:
        	self.hnote[habit] = json.loads(response['notes'])
	except:
		if Habitica.debug: utils.showInfo("Reset 1")
		self.reset_scorecounter(habit)
		return True
        if 'scoresincedate' not in self.hnote[habit] or 'scorecount' not in self.hnote[habit]:
            #reset habit score counter if both keys not found
	    if Habitica.debug: utils.showInfo("scorecounter missing keys")
            self.reset_scorecounter(habit)
	    return False
        #reset if sched is different from last sched or is missing
        # this should prevent problems caused by changing the reward schedule
	if 'sched' not in self.hnote[habit] or (int(self.hnote[habit]['sched']) != int(ah.settings.sched_dict[habit])):
            self.reset_scorecounter(habit)
	    return False
	if Habitica.debug: utils.showInfo("Habit Grabbed")
	self.habit_grabbed[habit] = True
        return True

    def post_scorecounter(self, habit):
        try:
            habitID = self.habit_id[habit]
	    if Habitica.debug: utils.showInfo("posting scorecounter")
	    datastring = json.dumps(self.hnote[habit])
	    #self.hrpg_showInfo(datastring)
	    data = {"notes" : datastring}
            self.api.update_task(habitID, data)
            return True
        except:
            return False


    def test_internet(self):
        #self.hrpg_tooltip("Testing Internet Connection")
        return self.api.test_internet()
            
    def make_score_message(self, new_lvl, new_xp, new_mp, new_gp, new_hp, streak_bonus=0, crit_multiplier=0, drop_dialog=None):
        hrpgresponse = "Huzzah! You've Earned Points!\nWell Done %s!\n" % (self.name)
        #Check for increases and add to message
        if new_lvl > self.lvl:
            diff = int(new_lvl) - int(self.lvl)
            hrpgresponse += "\nYOU LEVELED UP! NEW LEVEL: %s" % (new_lvl)
            self.save_avatar() #save the new avatar!	    
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
            hrpgresponse += "\nCritical Hit! Bonus: +%s%%" % crit_multiplier
        if streak_bonus:
            hrpgresponse += "\nStreak Bonus! +%s" % (int(streak_bonus))   
        if drop_dialog:
            hrpgresponse += "\n\n%s" % str(drop_dialog)
        #Show message box
        if ah.settings.show_popup:
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
        runHook("HabiticaAfterScore")
        return True

    def earn_points(self, habit):
        #get user stats if we don't have them
        if 'lvl' not in self.stats:
            if Habitica.debug: utils.showInfo("lvl not in stats")
            self.update_stats(False)
        #check habit if is is unchecked
        if not self.habit_grabbed[habit]:
            if Habitica.debug: utils.showInfo("%s habit not checked" % habit)
	    try:
                if Habitica.debug: utils.showInfo("Checking Habit Score Counter")
                self.check_anki_habit(habit)
	    except:
                pass
        crit_multiplier = None
        streak_bonus = None
	drop_dialog = None
	#Loop through scoring attempts up to 3 times
	#-- to account for missed scoring opportunities (smartphones, etc.)
	i = 0 #loop counter
	success = False
	while i < 3 and ah.config[ah.settings.profile]['score'] >= ah.settings.sched and ah.settings.internet:
		try:
			msg = self.score_anki_points(habit)
			if msg['lvl']: # Make sure we really got a response
				success = True
				self.hnote[habit]['scorecount'] += 1
				ah.config[ah.settings.profile]['score'] -= ah.settings.sched
			#Collect message strings
        		if msg['_tmp']:
            			if 'streakBonus' in msg['_tmp']:
					#streak bonuses
					if not streak_bonus: 
						streak_bonus = ""
					else:
						streak_bonus += "\n"
                			streak_bonus += str(round((100 * msg['_tmp']['streakBonus']), 0))
            			if 'crit' in msg['_tmp']:
                			#critical multiplier
					if not crit_multiplier:
						crit_multiplier = ""
					else:
						crit_multiplier += ", "
                			crit_multiplier += str(round((100 * msg['_tmp']['crit']), 0))
                		if 'drop' in msg['_tmp'] and 'dialog' in msg['_tmp']['drop']:
                    			#drop happened
					if not drop_dialog:
						drop_dialog = ""
					else:
						drop_dialog += "\n"
                    			#drop_text = msg['_tmp']['drop']['text']
                    			#drop_type = msg['_tmp']['drop']['type']
                    			drop_dialog += str(msg['_tmp']['drop']['dialog'])
		except:
			pass
		i += 1
	if not success: #exit if we failed all 3 times
			self.hrpg_showInfo("Huzzah! You've earned points!\nWell done %s!\n\nSorry,\nI couldn't score your %s habit on Habitica.\nDon't worry, I'll remember your points and try again later." % (self.name, habit))
			ah.settings.internet = False #internet failed
			return False
	#Post scorecounter to Habit note field
	if Habitica.allow_post_scorecounter_thread:
		thread.start_new_thread(self.post_scorecounter, (habit,))
	else:
		self.post_scorecounter(habit)

        #Gather new levels from last successful msg
        new_lvl = msg['lvl']
        new_xp = msg['exp']
        new_mp = msg['mp']
        new_gp = msg['gp']
        new_hp = msg['hp']

	#MOVED: These data collection functions now part of above while loop
        #if msg['_tmp']:
            #if 'streakBonus' in msg['_tmp']:
                #streak
                #streak_bonus = str(round((100 * msg['_tmp']['streakBonus']), 0))
            #if 'crit' in msg['_tmp']:
                #critical
                #crit_multiplier = str(round((100 * msg['_tmp']['crit']), 0))
                #if 'drop' in msg['_tmp'] and 'dialog' in msg['_tmp']['drop']:
                    #drop happened
                    #drop_text = msg['_tmp']['drop']['text']
                    #drop_type = msg['_tmp']['drop']['type']
                    #drop_dialog = msg['_tmp']['drop']['dialog']
        #Update habit if it was just created
	#DEPRICATED: Habits no longer created automatically for us in API v3
        #if habit in self.missing and self.missing[habit]:
            #if self.check_anki_habit(habit):
                #self.missing[habit] = False

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
        if not self.habit_grabbed[habit]:
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
