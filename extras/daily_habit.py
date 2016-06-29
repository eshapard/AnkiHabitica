#daily habit support for Anki Habitica
import datetime
import time
import thread
from ah_common import AnkiHabiticaCommon as ah
from anki.hooks import addHook
import db_helper

#-------------Installation Instructions--------------------#
# Install this file in the AnkiHabitica subdirectory in your
# Anki addons folder along with the other files from the
# main Anki Habitica distribution.
#
# Be sure to edit the configuration section below.
#
# Configuration Section:

habitName = "Anki:mahjong:" #Name of daily habit to score
minTime = 15 #Minimum amount of time required in minutes

#-------------Do not edit below----------------------------#
habitID = None #empty placeholder
minTime = minTime * 60 #set minTime to seconds

#set up initial times
midnight = datetime.datetime.combine(datetime.date.today(), datetime.time.min)
checkTime = int(time.mktime(midnight.timetuple()))
del midnight

#Mark daily as complete
def mark_daily_complete():
    global checkTime, habitID
    if not habitID:
        habitID = ah.habitica.api.find_habit_id(habitName)
    if habitID:
        if ah.habitica.api.perform_task(habitID, "up"):
            checkTime = checkTime + (24 * 60 * 60)

#Check to see if we have met minimum time requirements
def check_for_min_time():
    #return if checkTime is scheduled for later
    if int(time.time()) < checkTime:
        return
    timeToday = db_helper.seconds_count(checkTime)
    if timeToday >= minTime:
        #Mark daily habit complete if not already
        thread.start_new_thread(mark_daily_complete, ())


addHook("HabiticaAfterScore", check_for_min_time)
