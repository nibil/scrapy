import hashlib
import random
import re
import requests

from datetime import datetime
from user_agents import user_agents

USERNAME = ""
PASSWORD = ""


class LuminatiClient(object):

    def __init__(self, username=USERNAME, password=PASSWORD, zone="gen", port="22225"):
        self.username = username
        self.password = password
        self.zone = zone
        self.port = port
        self.connection = None
        self.country = None

        self.urls = {
            "master_proxy": "http://client.luminati.io/api/get_super_proxy"
        }
        self.get_connection()

    def get_connection(self, country=None, dns_resolution="remote",
                       session=None):
        ip_address = self.fetch_master_proxy()
        user_auth = self.generate_user_auth(country=country,
                                            dns_resolution=dns_resolution,
                                            session=session)

        result = {"ip_address": ip_address, "port": self.port,
                  "password": self.password}
        result.update(user_auth)
        self.connection = result
        self.country = country
        return result

    def generate_user_auth(self, country=None, dns_resolution="remote",
                           session=None):
        country = "-country-{country}".format(country=country) \
            if country else ""
        zoned = "-zone-{zone}".format(zone=self.zone)
        dns_resolution = "-dns-{dns}".format(dns=dns_resolution)
        session_id = session if session else self.generate_session_id()
        session = "-session-{ses_id}".format(ses_id=session_id)
        user = self.username + zoned + country + dns_resolution + session

        return {"username": user, "session_id": session_id}

    def fetch_master_proxy(self, country=None):
        arguments = {"raw":  1}
        if country:
            arguments.update({"country": country})
        proxy = self.get_response(self.urls["master_proxy"], arguments)
        return proxy

    def fetch_master_proxies(self, limit=10):
        arguments = {"format": "json", "limit": limit}
        proxies = self.get_response(self.urls["master_proxy"], arguments)
        return proxies

    def ping_master_proxy(self, address, port=None):
        if port is None:
            port = self.port
        url = "http://%s:%s/ping" % (address, port)

        return self.get_response(url)

    def ping_master_proxies(self, proxies, port=None):
        if port is None:
            port = self.port
        data = {}
        for proxy in proxies:
            data[proxy] = self.ping_master_proxy(proxy, port)

        return data

    def generate_session_id(self):
        sha1 = hashlib.sha1()
        sha1.update(datetime.now().isoformat() + str(random.random()))
        return sha1.hexdigest()

    def format_username(self, username):
        username = username if \
            re.match(".*-zone-([a-z0-9]*)",
                     username) else"{user}-zone-{zone}".format(user=username,
                                                               zone=self.zone)
        return username

    def get_response(self, url, arguments={}, options={}):
        arguments.update({"user": self.format_username(self.username),
                          "key": self.password})
        response = requests.get(url, params=arguments, **options)
        # response = connection.get(url, arguments)
        self.check_response_for_errors(response)
        response = response.text if (response and response.text) else None
        return response

    def get_url(self, url, timeout=10):
        response = ""
        headers, proxy = self.build_proxy_param()
        response = requests.get(url, headers=headers,
                                proxies=proxy, timeout=timeout)
        # print "luminati"
        if response and response.status_code in [200, 404]:
            return {
                    "source": "LUMINATI",
                    "success": True,
                    "status_code": response.status_code,
                    "content": response.content
                    }
        else:
            return {
                    "source": "LUMINATI",
                    "success": False,
                    "status_code": 4003,
                    "content": ""
                    }

    def build_proxy_param(self):
        headers = {'User-Agent': random_user_agent()}
        proxy = {'http': "http://" + self.connection['username'] + ":" +
                 self.connection['password'] + "@" +
                 str(self.connection['ip_address']) + ":" +
                 str(self.connection['port'])}
        proxy['https'] = proxy['http'].replace('http', 'https')
        return (headers, proxy)

    def check_response_for_errors(self, response):
        if response.status_code != 200:
            raise ValidationError(
                "Invalid input: Error message is  %s" % response.text)
        return True


def random_user_agent():
    agents = [i.strip() for i in user_agents]
    return random.choice(agents)


class ValidationError(Exception):

    def __init__(self, errors):
        super(ValidationError, self).__init__(errors)

        self.errors = errors
