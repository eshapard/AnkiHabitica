# Habitica API
import urllib.request
import urllib.error
import urllib.parse
import urllib.request
import urllib.parse
import urllib.error
import ssl
import json
import random
from .ah_common import AnkiHabiticaCommon as ah


class HabiticaAPI(object):
    DIRECTION_UP = "up"
    DIRECTION_DOWN = "down"

    TYPE_HABIT = "habit"
    TYPE_DAILY = "daily"
    TYPE_TODO = "todo"
    TYPE_REWARD = "reward"

    def __init__(self, user_id, api_key):
        if ah.user_settings["keep_log"]:
            ah.log.debug("Begin function")
        self.user_id = user_id
        self.api_key = api_key
        self.v3_url = "https://habitica.com/api/v3/"
        if ah.user_settings["keep_log"]:
            ah.log.debug("End function")

    def v3_request(self, method, path, data={'dummy': 'dummy'}, t=0):
        context = ssl._create_unverified_context()
        # Dummy data needed for post, put, and delete commands now.
        if ah.user_settings["keep_log"]:
            ah.log.debug("Begin function")
        path = path if not path.startswith("/") else path[1:]
        path = urllib.parse.quote(path, '/')
        url = self.v3_url + path
        if not method == 'get':
            # With data, method defaults to POST
            data = json.dumps(data).encode('UTF-8')
            req = urllib.request.Request(url, data)
        else:
            # Without data, method defaults to GET
            req = urllib.request.Request(url)
        req.add_header('x-api-user', self.user_id)
        req.add_header('x-api-key', self.api_key)
        if method == "put":
            req.add_header('Content-Type', 'application/json')
            req.get_method = lambda: "PUT"
        if method == "delete":
            req.get_method = lambda: "DELETE"
        if method == "post":
            req.add_header('Content-Type', 'application/json')  # Important!
            if not data:
                req.add_header('Content-Length', '0')  # makes blank data work
            req.get_method = lambda: "POST"  # Needed for no-data posts

        if t:
            response = json.load(urllib.request.urlopen(req, None, t, context=context))
        else:
            response = json.load(urllib.request.urlopen(req, context=context))

        if response['success']:
            out = response['data']
            if ah.user_settings["keep_log"]:
                ah.log.debug("End function returning: %s" % out)
            return out
        else:
            if ah.user_settings["keep_log"]:
                ah.log.error("End function returning: %s" % False)
            return False

    def user(self):
        if ah.user_settings["keep_log"]:
            ah.log.debug("Begin function")
        out = self.v3_request("get", "/user")
        if ah.user_settings["keep_log"]:
            ah.log.debug("End function returning: %s" % out)
        return out

    def tasks(self):
        if ah.user_settings["keep_log"]:
            ah.log.debug("Begin function")
        out = self.v3_request("get", "/tasks/user")
        if ah.user_settings["keep_log"]:
            ah.log.debug("End function returning: %s" % out)
        return out

    def task(self, task_id):
        if ah.user_settings["keep_log"]:
            ah.log.debug("Begin function")
        out = self.v3_request("get", "/tasks/%s" % str(task_id))
        if ah.user_settings["keep_log"]:
            ah.log.debug("End function returning: %s" % out)
        return out

    def create_task(self, task_type, text, date=None, note=None, attrib="rand", priority=1, up_only=False):
        if ah.user_settings["keep_log"]:
            ah.log.debug("Begin function")
        attributes = ['str', 'int', 'con', 'per']
        if attrib == "rand" or attrib not in attributes:
            attrib = random.choice(attributes)
        data = {
            'type': str(task_type),
            'text': str(text),
            'attribute': attrib,
            'priority': priority
        }
        if date:
            data['date'] = date
        if note:
            data['notes'] = note
        if up_only:
            data['up'] = True
            data['down'] = False
        out = self.v3_request("post", "/tasks/user", data)
        if ah.user_settings["keep_log"]:
            ah.log.debug("End function returning: %s" % out)
        return out

    def alter_task(self, task_id, up, down, text, date, note, attrib, priority):
        if ah.user_settings["keep_log"]:
            ah.log.debug("Begin function")
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
        out = self.v3_request("put", "/tasks/%s" % task_id, data)
        if ah.user_settings["keep_log"]:
            ah.log.debug("End function returning: %s" % out)
        return out

    def create_reward(self, text, value, note=""):
        if ah.user_settings["keep_log"]:
            ah.log.debug("Begin function")
        data = {
            'type': 'reward',
            'text': text,
            'value': value,
            'notes': note
        }
        out = self.v3_request("post", "/tasks/user", data)
        if ah.user_settings["keep_log"]:
            ah.log.debug("End function returning: %s" % out)
        return out

    def update_task(self, task_id, data):
        if ah.user_settings["keep_log"]:
            ah.log.debug("Begin function")
        out = self.v3_request("put", "/tasks/%s" % task_id, data)
        if ah.user_settings["keep_log"]:
            ah.log.debug("End function returning: %s" % out)
        return out

    def delete_task(self, task_id):
        if ah.user_settings["keep_log"]:
            ah.log.debug("Begin function")
        out = self.v3_request("delete", "/tasks/%s" % task_id)
        if ah.user_settings["keep_log"]:
            ah.log.debug("End function returning: %s" % out)
        return out

    def perform_task(self, task_id, direction):
        if ah.user_settings["keep_log"]:
            ah.log.debug("Begin function")
        url = "/tasks/%s/score/%s" % (task_id, direction)
        data = {'dummy': 'dummy'}
        out = self.v3_request("post", url, data)
        if ah.user_settings["keep_log"]:
            ah.log.debug("End function returning: %s" % out)
        return out

    def health_potion(self):
        if ah.user_settings["keep_log"]:
            ah.log.debug("Begin function")
        data = {'dummy': 'dummy'}
        out = self.v3_request("post", "/user/buy-health-potion", data)
        if ah.user_settings["keep_log"]:
            ah.log.debug("End function returning: %s" % out)
        return out

    def defensive_stance(self, target='self'):
        if ah.user_settings["keep_log"]:
            ah.log.debug("Begin function")
        data = {'dummy': 'dummy'}
        out = self.v3_request("post", "/user/class/cast/defensiveStance", data)
        if ah.user_settings["keep_log"]:
            ah.log.debug("End function returning: %s" % out)
        return out

    def feed_pet(self, pet, food):
        if ah.user_settings["keep_log"]:
            ah.log.debug("Begin function")
        data = {'dummy': 'dummy'}
        out = self.v3_request(
            "post", "/user/equip/feed/%s/%s" % (pet, food), data)
        if ah.user_settings["keep_log"]:
            ah.log.debug("End function returning: %s" % out)
        return out

    def get_content_items(self):
        if ah.user_settings["keep_log"]:
            ah.log.debug("Begin function")
        data = {'dummy': 'dummy'}
        out = self.v3_request("post", "/content", data)
        if ah.user_settings["keep_log"]:
            ah.log.debug("End function returning: %s" % out)
        return out

    def test_internet(self):
        if ah.user_settings["keep_log"]:
            ah.log.debug("Begin function")
        out = self.get_api_status(10)
        if ah.user_settings["keep_log"]:
            ah.log.debug("End function returning: %s" % out)
        return out

    def export_avatar_as_png(self):
        if ah.user_settings["keep_log"]:
            ah.log.debug("Begin function")
        url = "http://habitica.com/export/avatar-%s.png" % self.user_id
        req = urllib.request.Request(url)
        req.add_header('x-api-user', self.user_id)
        req.add_header('x-api-key', self.api_key)
        out = urllib.request.urlopen(req).read()
        if ah.user_settings["keep_log"]:
            ah.log.debug("End function returning avatar")
        return out

    def get_api_status(self, timeout=10):
        if ah.user_settings["keep_log"]:
            ah.log.debug("Begin function")
        try:
            response = self.v3_request("get", "/status", None, timeout)
        except:
            if ah.user_settings["keep_log"]:
                ah.log.error("End function returning: %s" % False)
            return False
        if 'status' in response and response['status'] == 'up':
            if ah.user_settings["keep_log"]:
                ah.log.debug("End function returning: %s" % True)
            return True
        else:
            if ah.user_settings["keep_log"]:
                ah.log.error("End function returning: %s" % False)
            return False

    # Find a habit's ID
    def find_habit_id(self, name):
        if ah.user_settings["keep_log"]:
            ah.log.debug("Begin function")
        tasks = self.tasks()
        if tasks:
            for t in tasks:
                if t["text"] == name:
                    out = str(t["_id"])
                    if ah.user_settings["keep_log"]:
                        ah.log.debug("End function returning: %s" % out)
                    return out
            if ah.user_settings["keep_log"]:
                ah.log.warning("End function returning: %s" % False)
            return False
        else:
            if ah.user_settings["keep_log"]:
                ah.log.error("End function returning: %s" % False)
            return False
