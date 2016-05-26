#Habitica API
import urllib2
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



    def user(self):
        return self.request("get", "/user")

    def tasks(self):
        return self.request("get", "/user/tasks")

    def task(self, task_id):
        return self.request("get", "/user/tasks/%s" % task_id)

    def create_task(self, task_type, text, date = "", note = "", attrib = "rand", priority = 1):
        attributes = ['str', 'int', 'con', 'per']
        if attrib == "rand" or attrib not in attributes:
           attrib = random.choice(attributes)
        data = {
            'type': task_type,
            'text': text,
            'date': date,
            'notes': note,
            'attribute': attrib,
            'priority': priority
        }
        return self.request("post", "/user/tasks", data)

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
        return self.request("put", task_id, data)
    
    def create_reward(self, text, value, note = ""):
        data = {
            'type': 'reward',
            'text': text,
            'value': value,
            'notes': note
        }
        return self.request("post", "/user/tasks", data)

    def update_task(self, task_id, data):
        return self.request("put", "/user/tasks/%s" % task_id, data)
    
    def delete_task(self, task_id):
        return self.request("delete", "/user/tasks/%s" % task_id)

    def perform_task(self, task_id, direction):
        url = "/user/tasks/%s/%s" % (task_id, direction)
        return self.request("post", url)
    
    def health_potion(self):
        return self.request("post", "/user/inventory/buy/potion")
    
    def defensive_stance(self, target='self'):
        return self.request("post", "/user/class/cast/defensiveStance/?targetType=%s" % (target))
    
    def feed_pet(self, pet, food):
        return self.request("post", "/user/inventory/feed/%s/%s" % (pet, food))

    def test_internet(self):
        try:
            response=urllib2.urlopen('http://habitica.com', timeout=1)
            return True
        except urllib2.URLError as err:
            pass
        return False
