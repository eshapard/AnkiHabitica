#Habitica API
import urllib2, urllib
import json
import random

class HabiticaAPI(object):
    DIRECTION_UP = "up"
    DIRECTION_DOWN = "down"

    TYPE_HABIT = "habit"
    TYPE_DAILY = "daily"
    TYPE_TODO = "todo"
    TYPE_REWARD = "reward"

    def __init__(self, user_id, api_key, base_url = "https://habitica.com:443/api/v2/"):
        self.user_id = user_id
        self.api_key = api_key
        self.base_url = base_url
        self.v3_url = "https://habitica.com/api/v3/"


    def request(self, method, path, data=None):
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

        return json.load(urllib2.urlopen(req))


    def v3_request(self, method, path, data=None):
        path = path if not path.startswith("/") else path[1:]
        path = urllib2.quote(path,'/')
        #print(path)
        url = self.v3_url + path
        #print(url)
        if data:
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

        response = json.load(urllib2.urlopen(req, timeout=5))

        if response['success']:
            return response['data']
        else:
            return False

    def user(self):
        return self.v3_request("get", "/user")

    def tasks(self):
        return self.v3_request("get", "/tasks/user")

    def task(self, task_id):
        return self.v3_request("get", "/tasks/%s" % str(task_id))

    def create_task(self, task_type, text, date=False, note=False, attrib="rand", priority=1, up_only=False):
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
	if note: date['note'] = note
	if up_only:
		data['up'] = True
		data['down'] = False
        return self.v3_request("post", "/tasks/user", data)

    def alter_task(self, task_id, up, down, text, date, note, attrib, priority):
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
        return self.v3_request("put", "/tasks/%s" % task_id, data)
    
    def create_reward(self, text, value, note = ""):
        data = {
            'type': 'reward',
            'text': text,
            'value': value,
            'notes': note
        }
        return self.v3_request("post", "/tasks/user", data)

    def update_task(self, task_id, data):
        return self.v3_request("put", "/tasks/%s" % task_id, data)
    
    def delete_task(self, task_id):
        return self.v3_request("delete", "/tasks/%s" % task_id)

    def perform_task(self, task_id, direction):
        url = "/tasks/%s/score/%s" % (task_id, direction)
        return self.v3_request("post", url)
    
    def health_potion(self):
        return self.v3_request("post", "/user/buy-health-potion")
    
    def defensive_stance(self, target='self'):
        #return self.request("post", "/user/class/cast/defensiveStance/?targetType=%s" % (target))
        return self.v3_request("post", "/user/class/cast/defensiveStance")
    
    def feed_pet(self, pet, food):
        return self.v3_request("post", "/user/equip/feed/%s/%s" % (pet, food))

    def get_content_items(self):
        return self.v3_request("post", "/content")

    def test_internet(self):
        return self.get_api_status() #Checking the status of the api is more accurate
#        try:
#            response=urllib2.urlopen('http://habitica.com', timeout=1)
#            return True
#        except urllib2.URLError as err:
#            pass
#        return False

    def export_avatar_as_png(self):
        url = "http://habitica.com/export/avatar-%s.png" % self.user_id
        req = urllib2.Request(url)
        req.add_header('x-api-user', self.user_id)
        req.add_header('x-api-key', self.api_key)
        return urllib2.urlopen(req).read()

    def get_api_status(self):
        try:
            response = self.v3_request("get", "/status")
        except:
            return False
        if 'status' in response and response['status'] == 'up':
            return True
        else:
            return False

    #Find a habit's ID
    def find_habit_id(self, name):
        tasks = self.tasks()
        if tasks:
            for t in tasks:
                if t["text"] == name:
                    return str(t["_id"])
            return False
        else:
            return 2
