#Class for storing and sharing common data such as
#	config and settings data
import logging, logging.handlers, os


class AnkiHabiticaCommon:
	config = {} #dictionary for configuration
	log = logging.Logger
	class settings: pass #empty class for holding settings

# I would have preferred to setup the log like below, but I get an
# eror that "self" isn't defined, so I put it as its own function
# rather than a method of AnkiHabiticaCommon.
# The problem probably has to do with the way that "ah" is instantiated
# in the import command rather than created as a variable.
# I'm not familiar enough with Python to know the details of that
# or how to get around it.
# At any rate, the below method works.

# 	def setupLog(self):
# 		self.log = logging.getLogger('AnkiHabitica')
#         if self.settings.debug:
#             self.log.setLevel(logging.DEBUG)
#         else:
#             self.log.setLevel(logging.ERROR)
#             
#         logName = os.path.join(os.path.dirname(os.path.realpath(__file__)), "AnkiHabitica", "AnkiHabitica.log")
#         fh = logging.handlers.RotatingFileHandler(logName, maxBytes=1e6, backupCount=5)
#         fmt = logging.Formatter('%(asctime)s %(threadName)s %(levelname)s %(message)s')
#         fh.setFormatter(fmt)
#         self.log.addHandler(fh)

def setupLog(ah):
	    ah.log = logging.getLogger('AnkiHabitica')
	    if ah.settings.debug:
	        ah.log.setLevel(logging.DEBUG)
	    else:
	        ah.log.setLevel(logging.ERROR)
	        
	    logName = os.path.join(os.path.dirname(os.path.realpath(__file__)), "AnkiHabitica.log")
	    fh = logging.handlers.RotatingFileHandler(logName, maxBytes=1e6, backupCount=5)
	    fmt = logging.Formatter('%(asctime)s [%(threadName)s:%(filename)s:%(lineno)s - %(funcName)20s()] %(levelname)s: %(message)s')
	    fh.setFormatter(fmt)
	    ah.log.addHandler(fh)

