#daily habit support for Anki Habitica
import datetime
import time
import thread
from ah_common import AnkiHabiticaCommon as ah
from anki.hooks import addHook
import db_helper
from aqt import *
from aqt.main import AnkiQt

#-------------Installation Instructions--------------------#
# Install this file in the AnkiHabitica subdirectory in your
# Anki addons folder along with the other files from the
# main Anki Habitica distribution.
#
# Be sure to edit the configuration section below.
#
# Configuration Section:

show_dialog = True
minTime = 30 #Minimum amount of time required in minutes
habitName = "Anki (%s minute%s)" % (minTime, "" if minTime == 1 else "s") #Name of daily habit to score, default to "Anki (minTime minutes)"

#-------------Do not edit below----------------------------#
habitID = None #empty placeholder
minTime *= 60 #set minTime to seconds

#set up initial times
def setup_initial_times():
    ah.log.debug("Begin function")
    global checkTime
    dayStartTime = datetime.datetime.fromtimestamp(mw.col.crt).time()
    midnight = datetime.datetime.combine(datetime.date.today(), dayStartTime)
    checkTime = int(time.mktime(midnight.timetuple()))
    ah.log.debug("End function")

#Mark daily as complete
def mark_daily_complete():
    ah.log.debug("Begin function")
    global checkTime, habitID
    if not habitID:
        habitID = ah.habitica.api.find_habit_id(habitName)
    if habitID:
        if ah.habitica.api.perform_task(habitID, "up"):
            checkTime = checkTime + (24 * 60 * 60)
    ah.log.debug("End function")

def minutes_seconds(NumSecs):
    ah.log.debug("Begin function")
    out = str(NumSecs // 60) + 'm' + str(NumSecs % 60) + 's'
    ah.log.debug("End function returning: %s" % out)
    return out

#Check to see if we have met minimum time requirements
def check_for_min_time():
    ah.log.debug("Begin function")
    #return if checkTime is scheduled for later
    if int(time.time()) < checkTime:
        ah.log.debug("End function")
        return
    timeToday = db_helper.seconds_count(checkTime)
    ah.log.debug("Studied for %s, Need %s to check off daily" % (minutes_seconds(timeToday), minutes_seconds(minTime)))
    if timeToday >= minTime:
        ah.log.debug("Daily Anki study time reached, checking off daily!")
        #Mark daily habit complete if not already
        thread.start_new_thread(mark_daily_complete, ())
        if show_dialog:
            utils.showinfo("Daily Anki study time reached, checking off daily!")
    ah.log.debug("End function")

addHook("profileLoaded", setup_initial_times)
addHook("HabiticaAfterScore", check_for_min_time)
