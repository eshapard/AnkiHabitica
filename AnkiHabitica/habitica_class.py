from .habitica_api import HabiticaAPI
import os
import sys
import json
import datetime
import time
import _thread
from aqt import *
from aqt.main import AnkiQt
from anki.hooks import runHook
from anki.lang import _
from . import db_helper
from anki.utils import intTime
from aqt.utils import tooltip
from .ah_common import AnkiHabiticaCommon as ah
from urllib.error import HTTPError


# TODO: make sure script can survive internet outages.
class Habitica(object):
    allow_threads = True  # startup config processes checking habits, etc.
    allow_post_scorecounter_thread = True  # Maybe a source of database warnings?
    # find icon file
    iconfile = os.path.join(os.path.dirname(
        os.path.realpath(__file__)), "habitica_icon.png")
    offline_sincedate = intTime()  # Score Since date for when we are offline
    offline_scorecount = 0  # Starting score for offline
    offline_recover_attempt = 0  # attempt to recover from offline state every third time

    def __init__(self):
        if ah.user_settings["keep_log"]:
            ah.log.debug("Begin function")
        self.api = HabiticaAPI(ah.settings.user, ah.settings.token)
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
        self.hnote = None
        self.habit_grabbed = False  # marked true when we get scorecounter.
        # holder for habit IDs
        self.habit_id = ah.config[ah.settings.profile].get('habit_id')
        self.missing = False  # holds missing habits
        self.init_update()  # check habits, grab user object, get avatar
        if ah.user_settings["keep_log"]:
            ah.log.debug("End function")

    def init_update(self):
        if ah.user_settings["keep_log"]:
            ah.log.debug("Begin function")
        self.habit_grabbed = False

        self.check_anki_habit()

        # Grab user object in the background
        if Habitica.allow_threads:
            _thread.start_new_thread(self.init_grab_stats, ())
        else:
            self.init_grab_stats()
        # Grab avatar from habitica
        if Habitica.allow_threads:
            _thread.start_new_thread(self.save_avatar, ())
        else:
            self.save_avatar()
        if ah.user_settings["keep_log"]:
            ah.log.debug("End function")

    # Try updating stats silently on init
    def init_grab_stats(self):
        if ah.user_settings["keep_log"]:
            ah.log.debug("Begin function")
        try:
            self.update_stats(True)
        except:
            if ah.user_settings["keep_log"]:
                ah.log.error("End function")
            return

    # Save avatar from habitica as png
    def save_avatar(self):
        if ah.user_settings["keep_log"]:
            ah.log.debug("Begin function")
        # Check to see if we are downloading the avatar image
        if not ah.user_settings["download_avatar"]:
            if ah.user_settings["keep_log"]:
                ah.log.debug("Function Return - not downloading avatar")
            return
        # See if there's an image for this profile
        profile_pic = ah.settings.user + ".png"  # use user id instead of profile name
        self.avatarfile = os.path.join(os.path.dirname(
            os.path.realpath(__file__)), profile_pic)
        try:
            pngfile = self.api.export_avatar_as_png()  # Grab avatar png from Habitica
            if not pngfile:
                if ah.user_settings["keep_log"]:
                    ah.log.error("End function returning: %s" %
                                 False)  # Exit if we failed
                return False  # Exit if we failed
            with open(self.avatarfile, 'wb') as outfile:
                outfile.write(pngfile)
            del pngfile
        except:
            pass
        if os.path.exists(self.avatarfile):
            # use {profile}.png as icon if it exists
            self.iconfile = self.avatarfile
        else:
            self.iconfile = Habitica.iconfile
        if ah.user_settings["keep_log"]:
            ah.log.debug("End function")

    def hrpg_showInfo(self, text):
        if ah.user_settings["keep_log"]:
            ah.log.debug("Begin function")
        if ah.user_settings["keep_log"]:
            ah.log.info("Msg: %s" % text.replace('\n', ' '))
        # display a small message window with an OK Button
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
        b.setAutoDefault(True)
        out = mb.exec_()
        if ah.user_settings["keep_log"]:
            ah.log.debug("End function returning: %s" % out)
        return out

    def get_user_object(self):
        if ah.user_settings["keep_log"]:
            ah.log.debug("Begin function")
        out = self.api.user()
        if ah.user_settings["keep_log"]:
            ah.log.debug("End function returning: %s" % out)
        return out

    def update_stats(self, silent=False):
        if ah.user_settings["keep_log"]:
            ah.log.debug("Begin function")
        try:
            user = self.get_user_object()
        except:
            if ah.user_settings["keep_log"]:
                ah.log.error("End function returning: %s" % False)
            if ah.user_settings["debug"]:
                raise
            if not silent:
                self.hrpg_showInfo(
                    "Unable to log in to Habitica.\n\nCheck that you have the correct user-id and api-token in\n%s.\n\nThese should not be your username and password.\n\nPost at github.com/eshapard/AnkiHRPG if this issue persists." % (ah.conffile))
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
        if ah.user_settings["keep_log"]:
            ah.log.debug(self.name)
        if ah.user_settings["keep_log"]:
            ah.log.debug("End function returning: %s" % True)
        return True

    def score_anki_points(self):
        if ah.user_settings["keep_log"]:
            ah.log.debug("Begin function")
        try:
            out = self.api.perform_task(self.habit_id, "up")
            if ah.user_settings["keep_log"]:
                ah.log.debug("End function returning: %s" % out)
            return out
        except:
            if ah.user_settings["keep_log"]:
                ah.log.error("End function returning: %s" % False)
            if ah.user_settings["debug"]:
                raise
            return False

    def update_anki_habit(self):
        if ah.user_settings["keep_log"]:
            ah.log.debug("Begin function")
        try:
            data = {'up': True, 'down': False, 'attribute': 'int'}
            out = self.api.update_task(self.habit_id, data)
            if ah.user_settings["keep_log"]:
                ah.log.debug("End function returning: %s" % out)
            return out
        except:
            if ah.user_settings["keep_log"]:
                ah.log.error("End function returning: %s" % False)
            if ah.user_settings["debug"]:
                raise
            return False

    # Check Anki Habit, make new one if it does not exist, and try to
    #    grab the note string.
    def check_anki_habit(self):
        if ah.user_settings["keep_log"]:
            ah.log.debug("Begin function")
        habit = ah.user_settings["habit"]
        if ah.user_settings["keep_log"]:
            ah.log.debug("checking %s" % habit)
        try:
            tasks = self.api.tasks()
            if ah.user_settings["keep_log"]:
                ah.log.debug(json.dumps(tasks))
            found = False
            exists = False
            for t in tasks:
                if str(t['id']) == str(self.habit_id):
                    found = True
                if t["text"] == habit:
                    exists = True
                    found_id = str(t["_id"])
        except:
            if ah.user_settings["keep_log"]:
                ah.log.error("End function returning: %s" % False)
            if ah.user_settings["debug"]:
                raise
            return False
        if found:
            self.missing = False
            if ah.user_settings["keep_log"]:
                ah.log.debug("Task found")
        elif exists:
            self.missing = False
            self.habit_id = found_id
            if ah.user_settings["keep_log"]:
                ah.log.warning("Task id incorrect, fixed")
        else:
            self.missing = True
            if ah.user_settings["keep_log"]:
                ah.log.warning("Task not found")
            self.create_missing_habit()
            if ah.user_settings["keep_log"]:
                ah.log.warning("End function returning: %s" % False)
            return False

        if Habitica.allow_threads:
            _thread.start_new_thread(self.check_anki_habit_task, ())
        else:
            self.check_anki_habit_task()
        if ah.user_settings["keep_log"]:
            ah.log.debug("End function")

    def check_anki_habit_task(self):
        if ah.user_settings["keep_log"]:
            ah.log.debug("Begin function")
        # Check to see that habitica habit is set up properly
        if ah.user_settings["keep_log"]:
            ah.log.debug("Checking habit setup")
        try:
            response = self.api.task(self.habit_id)
        except:
            if ah.user_settings["keep_log"]:
                ah.log.error("Could not retrieve task")
            if ah.user_settings["keep_log"]:
                ah.log.error("End function returning: %s" % False)
            if ah.user_settings["debug"]:
                raise
            return False
        if response['down'] or response['attribute'] != "int":
            try:
                if ah.user_settings["keep_log"]:
                    ah.log.debug("Updating Habit")
                self.update_anki_habit(self.habit_id)
                if ah.user_settings["keep_log"]:
                    ah.log.debug("End function returning: %s" % True)
                return True
            except:
                if ah.user_settings["keep_log"]:
                    ah.log.error("End function returning: %s" % False)
                if ah.user_settings["debug"]:
                    raise
                self.hrpg_showInfo(
                    "Your %s habit is not configured correctly yet.\nDelete it on Habitica and the addon will create it properly." % ah.user_settings["habit"])
                return False
        if ah.user_settings["keep_log"]:
            ah.log.debug("Habit looks good")
        # Grab scorecounter from habit
        out = self.grab_scorecounter()
        if ah.user_settings["keep_log"]:
            ah.log.debug("End function returning: %s" % out)
        return out

    # Create a missing habits
    def create_missing_habit(self):
        habit = ah.user_settings["habit"]
        if ah.user_settings["keep_log"]:
            ah.log.debug("Begin function")
        try:
            # create habit
            if ah.user_settings["keep_log"]:
                ah.log.debug("Trying to create %s habit" % habit)
            # create task on habitica
            curtime = intTime()
            self.hnote = {'scoresincedate': curtime,
                          'scorecount': 0, 'sched': ah.user_settings["sched"]}
            note = json.dumps(self.hnote)
            msg = self.api.create_task(
                'habit', habit, False, note, 'int', 1, True)
            self.habit_id = str(msg['_id'])  # capture new task ID
            if ah.user_settings["keep_log"]:
                ah.log.debug("New habit created: %s" % self.habit_id)
            if ah.user_settings["keep_log"]:
                ah.log.debug(json.dumps(msg))
            self.missing = False
            self.habit_grabbed = True
        except:
            if ah.user_settings["keep_log"]:
                ah.log.error("End function returning: %s" % False)
            if ah.user_settings["debug"]:
                raise
            return False

    def reset_scorecounter(self):
        if ah.user_settings["keep_log"]:
            ah.log.debug("Begin function")
        if ah.user_settings["keep_log"]:
            ah.log.debug("Resetting Scorecounter")
        last_review_time = db_helper.latest_review_time()
        if ah.user_settings["keep_log"]:
            ah.log.debug(str(last_review_time))
        self.hnote = {'scoresincedate': last_review_time,
                      'scorecount': 0, 'sched': ah.user_settings["sched"]}
        self.habit_grabbed = True
        if ah.user_settings["keep_log"]:
            ah.log.debug("reset: %s" % json.dumps(self.hnote))
        try:
            self.post_scorecounter()
            if ah.user_settings["keep_log"]:
                ah.log.debug("End function returning: %s" % True)
            return True
        except:
            if ah.user_settings["keep_log"]:
                ah.log.error("End function returning: %s" % False)
            if ah.user_settings["debug"]:
                raise
            return False

    def grab_scorecounter(self):
        if ah.user_settings["keep_log"]:
            ah.log.debug("Begin function")
        if self.habit_grabbed:
            if ah.user_settings["keep_log"]:
                ah.log.debug("End function returning: %s" % True)
            return True
        if self.habit_id == None:
            self.check_anki_habit()
        if ah.user_settings["keep_log"]:
            ah.log.debug("grabbing scorecounter: %s" % str(self.habit_id))
        try:
            response = self.api.task(self.habit_id)
        except HTTPError as err:
            if err.code == 401:
                self.hrpg_showInfo("Your User ID or API Token is incorrect, please setup again with correct infomation.")
                ah.habitica = None
                ah.settings.initialized = False
                ah.config[ah.settings.profile].pop("user")
                ah.config[ah.settings.profile].pop("token")
                ah.settings.user = None
                ah.settings.token = None
                if ah.user_settings["keep_log"]:
                    ah.log.warning("End function returning: %s" % False)
                return False
            else:
                raise
        if ah.user_settings["keep_log"]:
            ah.log.debug(response['notes'])
        # Try to grab the scorecount and score since date
        if ah.user_settings["keep_log"]:
            ah.log.debug("trying to load note string: %s" % response['notes'])
        try:
            self.hnote = json.loads(response['notes'])
        except:
            if ah.user_settings["keep_log"]:
                ah.log.warning("Reset 1")
            self.reset_scorecounter()
            if ah.user_settings["keep_log"]:
                ah.log.warning("End function returning: %s" % True)
            return True
        if 'scoresincedate' not in self.hnote or 'scorecount' not in self.hnote:
            # reset habit score counter if both keys not found
            if ah.user_settings["keep_log"]:
                ah.log.debug("scorecounter missing keys")
            self.reset_scorecounter()
            if ah.user_settings["keep_log"]:
                ah.log.warning("End function returning: %s" % False)
            return False
        # reset if sched is different from last sched or is missing
        # this should prevent problems caused by changing the reward schedule
        if 'sched' not in self.hnote or (int(self.hnote['sched']) != int(ah.user_settings["sched"])):
            self.reset_scorecounter()
            if ah.user_settings["keep_log"]:
                ah.log.warning("End function returning: %s" % False)
            return False
        if ah.user_settings["keep_log"]:
            ah.log.debug("Habit Grabbed")
        if ah.user_settings["keep_log"]:
            ah.log.debug("Habit note: %s" % self.hnote)
        self.habit_grabbed = True
        if ah.user_settings["keep_log"]:
            ah.log.debug("End function returning: %s" % True)
        return True

    def post_scorecounter(self):
        if ah.user_settings["keep_log"]:
            ah.log.debug("Begin function")
        # try:
        habitID = self.habit_id
        if ah.user_settings["keep_log"]:
            ah.log.debug("posting scorecounter: %s" % self.hnote)
        datastring = json.dumps(self.hnote)
        data = {"notes": datastring}
        self.api.update_task(habitID, data)
        if ah.user_settings["keep_log"]:
            ah.log.debug("End function returning: %s" % True)
        return True
        # except:
        #     if ah.user_settings["debug"]:
        #         raise
        #     if ah.user_settings["keep_log"]:
        #         ah.log.error("End function returning: %s" % False)
        #     return False

    def test_internet(self):
        if ah.user_settings["keep_log"]:
            ah.log.debug("Begin function")
        out = self.api.test_internet()
        if ah.user_settings["keep_log"]:
            ah.log.debug("End function returning: %s" % out)
        return out

    def make_score_message(self, new_lvl, new_xp, new_mp, new_gp, new_hp, streak_bonus=0, crit_multiplier=0, drop_dialog=None):
        if ah.user_settings["keep_log"]:
            ah.log.debug("Begin function")
        hrpg_response = "Huzzah! You've Earned Points!\nWell Done %s!\n" % (
            self.name)
        # Check for increases and add to message
        if new_lvl > self.lvl:
            diff = int(new_lvl) - int(self.lvl)
            hrpg_response += "\nYOU LEVELED UP! NEW LEVEL: %s" % (new_lvl)
            self.save_avatar()  # save the new avatar!
        hrpg_response += "\nHP: %s" % (int(new_hp))
        if new_hp > self.hp:
            diff = int(new_hp) - int(self.hp)
            hrpg_response += "  +%s!" % (diff)
        hrpg_response += "\nXP: %s" % (int(new_xp))
        if new_xp > self.xp:
            diff = int(new_xp) - int(self.xp)
            hrpg_response += "  +%s!" % (diff)
        hrpg_response += "\nGP: %s" % (round(new_gp, 2))
        if new_gp > self.gp:
            diff = int(new_gp) - int(self.gp)
            hrpg_response += "  +%s!" % (diff)
        hrpg_response += "\nMP: %s" % (int(new_mp))
        if int(new_mp) > int(self.mp):
            diff = int(new_mp) - int(self.mp)
            hrpg_response += "  +%s!" % (diff)
        # Check for drops, streaks, and critical hits
        if crit_multiplier:
            hrpg_response += "\nCritical Hit! Bonus: +%s%%" % crit_multiplier
        if streak_bonus:
            hrpg_response += "\nStreak Bonus! +%s" % (int(streak_bonus))
        if drop_dialog:
            hrpg_response += "\n\n%s" % str(drop_dialog)
        # Show message box
        if ah.user_settings["show_popup"]:
            self.hrpg_showInfo(hrpg_response)
        else:
            tooltip(_("Huzzah! You Scored Points!"), period=2500)

        # update levels
        if new_lvl > self.lvl and self.lvl > 0:
            self.update_stats(False)
        else:
            self.lvl = new_lvl
            self.xp = new_xp
            self.mp = new_mp
            self.gp = new_gp
            self.hp = new_hp
        runHook("HabiticaAfterScore")
        if ah.user_settings["keep_log"]:
            ah.log.debug("End function returning: %s" % True)
        return True

    def earn_points(self):
        habit = ah.user_settings["habit"]
        if ah.user_settings["keep_log"]:
            ah.log.debug("Begin function")
        # get user stats if we don't have them
        if 'lvl' not in self.stats:
            if ah.user_settings["keep_log"]:
                ah.log.warning("lvl not in stats")
            self.update_stats(False)
        # check habit if is is unchecked
        if not self.habit_grabbed:
            if ah.user_settings["keep_log"]:
                ah.log.debug("%s habit not checked" % habit)
            try:
                if ah.user_settings["keep_log"]:
                    ah.log.debug("Checking Habit Score Counter")
                self.check_anki_habit()
            except:
                pass
        crit_multiplier = None
        streak_bonus = None
        drop_dialog = None
        success = False
        if ah.config[ah.settings.profile]['score'] >= ah.user_settings["sched"] and ah.settings.internet:
            try:
                msg = self.score_anki_points()
                if msg['lvl']:  # Make sure we really got a response
                    success = True
                    self.hnote['scorecount'] += 1
                    ah.config[ah.settings.profile]['score'] -= ah.user_settings["sched"]
                # Collect message strings
                if msg['_tmp']:
                    if 'streakBonus' in msg['_tmp']:
                        # streak bonuses
                        if not streak_bonus:
                            streak_bonus = ""
                        else:
                            streak_bonus += "\n"
                        streak_bonus += str(round((100 *
                                                   msg['_tmp']['streakBonus']), 0))
                    if 'crit' in msg['_tmp']:
                        # critical multiplier
                        if not crit_multiplier:
                            crit_multiplier = ""
                        else:
                            crit_multiplier += ", "
                        crit_multiplier += str(round((100 *
                                                      msg['_tmp']['crit']), 0))
                    if 'drop' in msg['_tmp'] and 'dialog' in msg['_tmp']['drop']:
                        # drop happened
                        if not drop_dialog:
                            drop_dialog = ""
                        else:
                            drop_dialog += "\n"
                        drop_dialog += str(msg['_tmp']['drop']['dialog'])
            except:
                if ah.user_settings["debug"]:
                    raise

        if not success:
            self.hrpg_showInfo(
                "Huzzah! You've earned points!\nWell done %s!\n\nSorry,\nI couldn't score your %s habit on Habitica.\nDon't worry, I'll remember your points and try again later." % (self.name, habit))
            ah.settings.internet = False  # internet failed
            if ah.user_settings["keep_log"]:
                ah.log.warning('Internet failed')
            if ah.user_settings["keep_log"]:
                ah.log.warning("End function returning: %s" % False)
            return False
        # Post scorecounter to Habit note field
        if Habitica.allow_post_scorecounter_thread:
            _thread.start_new_thread(self.post_scorecounter, ())
        else:
            self.post_scorecounter()

        # Gather new levels from last successful msg
        new_lvl = msg['lvl']
        new_xp = msg['exp']
        new_mp = msg['mp']
        new_gp = msg['gp']
        new_hp = msg['hp']

        out = self.make_score_message(
            new_lvl, new_xp, new_mp, new_gp, new_hp, streak_bonus, crit_multiplier, drop_dialog)
        if ah.user_settings["keep_log"]:
            ah.log.debug("End function returning: %s" % out)
        return out

    # Compact Habitica Stats for Progress Bar
    def compact_habitica_stats(self):
        if ah.user_settings["keep_log"]:
            ah.log.debug("Begin function")
        if self.ht and self.xt and self.mt:
            health = int(100 * self.hp / self.ht)
            experience = int(100 * self.xp / self.xt)
            mana = int(100 * self.mp / self.mt)
            string = "<font color='#f74e52'>%s(%s%%)</font> | <font color='#ffbe5d'>%s(%s%%)</font> | <font color='#50b5e9'>%s(%s%%)</font> | <font color='#BF7D1A'>%s</font>" % (
                int(self.hp), health, int(self.xp), experience, int(self.mp), mana, int(self.gp))
        else:
            string = False
        if ah.user_settings["keep_log"]:
            ah.log.debug("End function returning: %s" % string)
        return string

    # Silent Version of Earn Points
    def silent_earn_points(self):
        if ah.user_settings["keep_log"]:
            ah.log.debug("Begin function")
        # check habit if is is unchecked
        if not self.habit_grabbed:
            try:
                self.check_anki_habit()
                self.grab_scorecounter()
            except:
                pass
        try:
            self.score_anki_points()
            self.hnote['scorecount'] += 1
        except:
            if ah.user_settings["keep_log"]:
                ah.log.error("End function returning: %s" % False)
            if ah.user_settings["debug"]:
                raise
            return False

        if ah.user_settings["keep_log"]:
            ah.log.debug("End function returning: %s" % True)
        return True
