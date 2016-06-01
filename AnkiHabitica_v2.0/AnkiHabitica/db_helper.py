#Anki Database Helper Functions
from __future__ import division
import datetime
from aqt import mw
from anki.utils import ids2str

timebox_seconds = 900 #hard-set 'timebox' length in seconds
# having a hard-coded 'timebox' length solves the problem of
# a user changing a timebox setting and suddenly having a ton
# of new points.

#Return current local time as seconds from epoch
def newTime():
	return int((datetime.datetime.now() - datetime.datetime.fromtimestamp(0)).total_seconds())

# Return a formatted date string
def prettyTime(secFromEpoch):
	return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(secFromEpoch))

#Find correct answers since start_date
def correct_answer_count(start_date):
	# only get number of correct answers
	dbScore = mw.col.db.scalar("""select 
		count()
		from revlog where 
		ease is not 1 and
		id/1000 > ?""", 
		start_date)
	return dbScore

#Find wrong answers since start_date
def wrong_answer_count(start_date):
	# only get number of wrong answers
	dbScore = mw.col.db.scalar("""select 
		count()
		from revlog where 
		ease = 1 and
		id/1000 > ?""", 
		start_date)
	return dbScore

#Find total time in seconds of all activity since start_date
def seconds_count(start_date):
	dbTime = mw.col.db.scalar("""select 
		sum(time)/1000 
		from revlog where 
		id/1000 > ?""", 
		start_date)
	# In case no reviews were found, dbTime will be None, so fix that
	if dbTime is None: dbTime = 0 
	return dbTime

#Find timeboxes since start_date
def timebox_count(start_date):
	dbTime = seconds_count(start_date)
	#Original code used actual timebox settings
	# but this leads to big problems when the user
	# changes the timebox length.
	#if mw.col.conf['timeLim'] > 0:
	#	dbTboxes = dbTime // mw.col.conf['timeLim']
	#else:
	#	dbTboxes = 0
	dbTboxes = dbTime // timebox_seconds
	return dbTboxes

#Count mature cards
def matured_count(start_date):
	dbMatured = mw.col.db.scalar("""
		select count() 
		from revlog 
		where ivl >= 21 and
		lastIvl < 21
		and id/1000 > ?
		""",start_date)
	if dbMatured is None: dbMatured = 0
	return dbMatured

#Count newly learned cards
def learned_count(start_date):
	learned = 0
	learned = mw.col.db.scalar("""
		select
		sum(case when type = 0 then 1 else 0 end)
		from revlog where
		id/1000 > :oldTime
		""",
		oldTime = start_date)
	if learned is None: learned = 0
	return learned

#Find number of decks completed
def decks_count(start_date):
	'''
	new decks from db
	Here it takes a little bit of work. 
	For each deck we'll get the number of reviews due for each
	day since start_date and the number of reviews performed for
	the same days.
	For a given day, if there are zero reviews due but more than 
	zero reviews completed, then it means the user finished all reviews
	for that day.
	'''
	dbDecks = 0
	finishedDecks = []
	# See how many previous days we need to check 
	numDays = int((newTime() - start_date)/86400)+2
	for d in mw.col.decks.all():
		# get list of number of cards due for deck each day
		cardsDue = [(-nDays,mw.col.db.scalar("""
			select 
			count()
			from cards where 
			queue in (2,3) and 
			did = :d and 
			due <= :oldDay""",
			d=d['id'],
			oldDay=mw.col.sched.today-nDays)) for nDays in range(numDays)]
		# get list of number of cards reviewed for deck each day
		cardsDone = mw.col.db.all("""
			select 
			(cast((id/1000.0 - :cut) / 86400.0 as int)) as day,
			sum(case when cid in %s then 1 else 0 end)
			from revlog where 
			id/1000 > :oldTime
			group by day order by day""" % ids2str([x[0] for x in mw.col.db.all("""
				select
				id
				from cards where
				did = ?""", d['id'])]),
			cut = mw.col.sched.dayCutoff,
			oldTime = start_date)
		'''
		The db.all() call above only returns data for days that have >= 1 completed review,
		so there is not in general a one-to-one corresponce between cardsDue and cardsDone
		(cardsDue[i] and cardsDone[i] might represent different days).
		So need to use the below ugly code to make sure that cardsDue[i] and cardsDone[j]
		are for the same day.
		'''	  
		if not cardsDue is None and not cardsDone is None:
			for due in cardsDue:
				if due[1] == 0:
					for done in cardsDone:
						if done[0] == due[0]:
							if done[1] > 0 and due[1] == 0:
								dbDecks += 1
								finishedDecks.append(d)
							break
	'''
	We've got the full list of completed decks, but there could be extras (i.e. if a user
	completes two children decks by completing the parent deck and the parent deck doesn't
	contain any cards, then it will count as 3 decks when it should count as 2.
	So check that a parent deck actually has cards of its own before giving credit for it.
	Check by getting combined cards of all child decks. If parent deck card count is not
	more than the combined child deck card count then the parent deck doesn't have any of
	its own cards and shouldn't be counted.
	'''
	for p in finishedDecks:
		children = mw.col.decks.children(p['id'])
		cCardCount = 0
		for c in children:
			cCardCount += mw.col.db.scalar("""
				select count() from cards where did = ?
				""", c[1])
		if cCardCount > 0:
			pCardCount = mw.col.db.scalar("""
				select count() from cards where did = ?
				""", p['id'])
			if not pCardCount > cCardCount: dbDecks -= 1
			
	return dbDecks
