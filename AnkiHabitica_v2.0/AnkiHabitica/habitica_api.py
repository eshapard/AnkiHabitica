#Habitica API
import urllib2, urllib
import json
import random
from ah_common import AnkiHabiticaCommon as ah

class HabiticaAPI(object):
    DIRECTION_UP = "up"
    DIRECTION_DOWN = "down"

    TYPE_HABIT = "habit"
    TYPE_DAILY = "daily"
    TYPE_TODO = "todo"
    TYPE_REWARD = "reward"

    def __init__(self, user_id, api_key, base_url = "https://habitica.com:443/api/v2/"):
    	if ah.settings.keep_log: ah.log.debug("Begin function")
        self.user_id = user_id
        self.api_key = api_key
        self.base_url = base_url
        self.v3_url = "https://habitica.com/api/v3/"
        if ah.settings.keep_log: ah.log.debug("End function")


    def request(self, method, path, data=None):
    	if ah.settings.keep_log: ah.log.debug("Begin function")
        path = path if not path.startswith("/") else path[1:]
        path = urllib2.quote(path)
        url = self.base_url + path
        if data or method == 'post':
           #With data, method defaults to POST
           data = json.dumps(data)
           req = urllib2.Request(url, data)
        else:
           #Without data, method defaults to GET
           req = urllib2.Request(url)
        req.add_header('x-api-user', self.user_id)
        req.add_header('x-api-key', self.api_key)
        if method == "put":
           req.add_header('Content-Type', 'application/json')
           req.get_method = lambda:"PUT"

        out =  json.load(urllib2.urlopen(req))
        if ah.settings.keep_log: ah.log.debug("End function returning: %s" %  out)
        return out


    def v3_request(self, method, path, data={'dummy': 'dummy'}, t=0):
        #Dummy data needed for post, put, and delete commands now.
    	if ah.settings.keep_log: ah.log.debug("Begin function")
        path = path if not path.startswith("/") else path[1:]
        path = urllib2.quote(path,'/')
        #print(path)
        url = self.v3_url + path
        #print(url)
        if not method == 'get' :
           #With data, method defaults to POST
           data = json.dumps(data)
           req = urllib2.Request(url, data)
        else:
           #Without data, method defaults to GET
           req = urllib2.Request(url)
        req.add_header('x-api-user', self.user_id)
        req.add_header('x-api-key', self.api_key)
        if method == "put":
           req.add_header('Content-Type', 'application/json')
           req.get_method = lambda:"PUT"
        if method == "delete":
           req.get_method = lambda:"DELETE"
        if method == "post":
           req.add_header('Content-Type', 'application/json') #Important!
           req.get_method = lambda:"POST" #Needed for no-data posts

        if t:
            response = json.load(urllib2.urlopen(req, None, t))
        else:
            response = json.load(urllib2.urlopen(req))

        if response['success']:
            out =  response['data']
            if ah.settings.keep_log: ah.log.debug("End function returning: %s" %  out)
            return out
        else:
            if ah.settings.keep_log: ah.log.error("End function returning: %s" %  False)
            return False

    def user(self):
    	if ah.settings.keep_log: ah.log.debug("Begin function")
        out =  self.v3_request("get", "/user")
        if ah.settings.keep_log: ah.log.debug("End function returning: %s" %  out)
        return out

    def tasks(self):
    	if ah.settings.keep_log: ah.log.debug("Begin function")
        out =  self.v3_request("get", "/tasks/user")
        if ah.settings.keep_log: ah.log.debug("End function returning: %s" %  out)
        return out

    def task(self, task_id):
    	if ah.settings.keep_log: ah.log.debug("Begin function")
        out =  self.v3_request("get", "/tasks/%s" % str(task_id))
        if ah.settings.keep_log: ah.log.debug("End function returning: %s" %  out)
        return out

    def create_task(self, task_type, text, date=None, note=None, attrib="rand", priority=1, up_only=False):
    	if ah.settings.keep_log: ah.log.debug("Begin function")
        attributes = ['str', 'int', 'con', 'per']
        if attrib == "rand" or attrib not in attributes:
           attrib = random.choice(attributes)
        data = {
            'type': str(task_type),
            'text': str(text), 
            'attribute': attrib,
            'priority': priority
        }
        if date: data['date'] = date
        if note: data['notes'] = note
        if up_only:
            data['up'] = True
            data['down'] = False
        out =  self.v3_request("post", "/tasks/user", data)
        if ah.settings.keep_log: ah.log.debug("End function returning: %s" %  out)
        return out

    def alter_task(self, task_id, up, down, text, date, note, attrib, priority):
    	if ah.settings.keep_log: ah.log.debug("Begin function")
        data = {}
        if up:
            data['up'] = up
        if down:
            data['down'] = down
        if text:
            data['text'] = text
        if date:
            data['date'] = date
        if note:
            data['notes'] = note
        if attrib:
            data['attribute'] = attrib
        if priority:
            data['priority'] = priority
        out =  self.v3_request("put", "/tasks/%s" % task_id, data)
        if ah.settings.keep_log: ah.log.debug("End function returning: %s" %  out)
        return out
    
    def create_reward(self, text, value, note = ""):
    	if ah.settings.keep_log: ah.log.debug("Begin function")
        data = {
            'type': 'reward',
            'text': text,
            'value': value,
            'notes': note
        }
        out =  self.v3_request("post", "/tasks/user", data)
        if ah.settings.keep_log: ah.log.debug("End function returning: %s" %  out)
        return out

    def update_task(self, task_id, data):
    	if ah.settings.keep_log: ah.log.debug("Begin function")
        out =  self.v3_request("put", "/tasks/%s" % task_id, data)
        if ah.settings.keep_log: ah.log.debug("End function returning: %s" %  out)
        return out
    
    def delete_task(self, task_id):
    	if ah.settings.keep_log: ah.log.debug("Begin function")
        out =  self.v3_request("delete", "/tasks/%s" % task_id)
        if ah.settings.keep_log: ah.log.debug("End function returning: %s" %  out)
        return out

    def perform_task(self, task_id, direction):
    	if ah.settings.keep_log: ah.log.debug("Begin function")
        url = "/tasks/%s/score/%s" % (task_id, direction)
        data = {'dummy': 'dummy'}
        out =  self.v3_request("post", url, data)
        if ah.settings.keep_log: ah.log.debug("End function returning: %s" %  out)
        return out
    
    def health_potion(self):
    	if ah.settings.keep_log: ah.log.debug("Begin function")
        data = {'dummy': 'dummy'}
        out =  self.v3_request("post", "/user/buy-health-potion", data)
        if ah.settings.keep_log: ah.log.debug("End function returning: %s" %  out)
        return out
    
    def defensive_stance(self, target='self'):
    	if ah.settings.keep_log: ah.log.debug("Begin function")
        #out =  self.request("post", "/user/class/cast/defensiveStance/?targetType=%s" % (target))
        #if ah.settings.keep_log: ah.log.debug("End function returning: %s" %  out)
        #return out
        data = {'dummy': 'dummy'}
        out =  self.v3_request("post", "/user/class/cast/defensiveStance", data)
        if ah.settings.keep_log: ah.log.debug("End function returning: %s" %  out)
        return out
    
    def feed_pet(self, pet, food):
    	if ah.settings.keep_log: ah.log.debug("Begin function")
        data = {'dummy': 'dummy'}
        out =  self.v3_request("post", "/user/equip/feed/%s/%s" % (pet, food), data)
        if ah.settings.keep_log: ah.log.debug("End function returning: %s" %  out)
        return out

    def get_content_items(self):
    	if ah.settings.keep_log: ah.log.debug("Begin function")
        data = {'dummy': 'dummy'}
        out =  self.v3_request("post", "/content", data)
        if ah.settings.keep_log: ah.log.debug("End function returning: %s" %  out)
        return out

    def test_internet(self):
    	if ah.settings.keep_log: ah.log.debug("Begin function")
        out =  self.get_api_status(10) #Checking the status of the api is more accurate
        if ah.settings.keep_log: ah.log.debug("End function returning: %s" %  out)
        return out
#        try:
#            response=urllib2.urlopen('http://habitica.com', timeout=1)
#            return True
#        except urllib2.URLError as err:
#            pass
#        return False

    def export_avatar_as_png(self):
    	if ah.settings.keep_log: ah.log.debug("Begin function")
        url = "http://habitica.com/export/avatar-%s.png" % self.user_id
        req = urllib2.Request(url)
        req.add_header('x-api-user', self.user_id)
        req.add_header('x-api-key', self.api_key)
        out =  urllib2.urlopen(req).read()
        if ah.settings.keep_log: ah.log.debug("End function returning avatar")
        return out

    def get_api_status(self, timeout=10):
    	if ah.settings.keep_log: ah.log.debug("Begin function")
        try:
            response = self.v3_request("get", "/status", None, timeout)
        except:
            if ah.settings.keep_log: ah.log.error("End function returning: %s" %  False)
            return False
        if 'status' in response and response['status'] == 'up':
            if ah.settings.keep_log: ah.log.debug("End function returning: %s" %  True)
            return True
        else:
            if ah.settings.keep_log: ah.log.error("End function returning: %s" %  False)
            return False

    #Find a habit's ID
    def find_habit_id(self, name):
    	if ah.settings.keep_log: ah.log.debug("Begin function")
        tasks = self.tasks()
        if tasks:
            for t in tasks:
                if t["text"] == name:
                    out =  str(t["_id"])
                    if ah.settings.keep_log: ah.log.debug("End function returning: %s" %  out)
                    return out
            if ah.settings.keep_log: ah.log.warning("End function returning: %s" %  False)
            return False
        else:
            if ah.settings.keep_log: ah.log.error("End function returning: %s" %  False)
            return False
