import random
import requests
from redis import Redis
import json

from user_agents import user_agents

TOR_SERVER_LIST = []

# TOR_SERVER_LIST = ["http://54.208.165.1"]
TOR_KEY = ""
r = Redis()

__author__ = 'nibil'


class ValidationError(Exception):

    def __init__(self, errors):
        super(ValidationError, self).__init__(errors)
        self.errors = errors


def random_user_agent():
    agents = [i.strip() for i in user_agents]
    return random.choice(agents)


class TorClient(object):

    def __init__(self, TOR_SERVER_LIST=TOR_SERVER_LIST, TOR_KEY=TOR_KEY):
        self.TOR_SERVER_LIST = TOR_SERVER_LIST
        self.TOR_KEY = TOR_KEY

    def check_response_for_errors(self, response):
        if response.status_code != 200:
            raise ValidationError(
                "Invalid input: Error message is  %s" % response.text)
        return True

    def get_url(self, url):
        """
        request url over proxymesh and return the content in a json
        """
        tor_proxy_rotator = r.get("tor_proxy_rotator")
        tor_proxy_rotator = 0 if not tor_proxy_rotator \
            else int(tor_proxy_rotator)
        try:
            ip = self.TOR_SERVER_LIST[tor_proxy_rotator]
        except IndexError:
            ip = self.TOR_SERVER_LIST[0]
        r.set("tor_proxy_rotator",
              (tor_proxy_rotator + 1) % len(self.TOR_SERVER_LIST))
        # print ip
        try:
            response = requests.get("%s/?url=%s&key=%s" %
                                    (ip, url, self.TOR_KEY),
                                    headers={
                                        "User-Agent": random_user_agent()
                                    }, timeout=10)
            response = json.loads(response.content)
        except:
            response = {}
        if response and response['status_code'] in [200, 404]:
            return {
                    "source": "TOR-%s" % ip,
                    "success": True,
                    "status_code": response["status_code"],
                    "content": response["content"]
                    }
        else:
            return {
                    "source": "TOR-%s" % ip,
                    "success": False,
                    "status_code": 4003,
                    "content": ""
                    }

    def status(self):
        success = []
        for ip in self.TOR_SERVER_LIST:
            response = requests.get(ip, timeout=5)
            if response.ok:
                success.append((ip, True))
                print "%s: \033[92m OK \033[0m" % ip
            else:
                success.append((ip, False))
                print "%s: \033[91m NOT OK \033[0m" % ip
        return success
