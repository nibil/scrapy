import base64
import random
import requests
from user_agents import user_agents


PROXYMESH_USERNAME = ''
PROXYMESH_PASSWORD = ''


class ValidationError(Exception):

    def __init__(self, errors):
        super(ValidationError, self).__init__(errors)
        self.errors = errors


def random_user_agent():
    agents = [i.strip() for i in user_agents]
    return random.choice(agents)


class ProxymeshClient(object):

    def __init__(self, PROXYMESH_USERNAME=PROXYMESH_USERNAME,
                 PROXYMESH_PASSWORD=PROXYMESH_PASSWORD):
        self.username = PROXYMESH_USERNAME
        self.password = PROXYMESH_PASSWORD

    def proxymesh_config(self):
        """
        Configuration for using ProxyMesh
        """
        url = random.choice([
            "http://us-dc.proxymesh.com:31280",
            "http://us-ny.proxymesh.com:31280"
        ])

        auth = base64.b64encode((self.username+':'+self.password).encode('utf-8')).decode('utf-8')
        return ([{
                'http': url,
                'https': url
                },
                {
                'Proxy-Authorization': 'Basic %s' % auth,
                'User-Agent': random_user_agent(),
                'Connection': 'keep-alive',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
            }])

    def check_response_for_errors(self, response):
        if response.status_code != 200:
            raise ValidationError(
                "Invalid input: Error message is  %s" % response.text)
        return True

    def get_url(self, url, max_retries=3):
        """
        request url over proxymesh and return the content in a json
        """
        response = ""
        headers, proxy = self.proxymesh_config()
        response = requests.get(url, headers=headers, proxies=proxy)
        for _ in xrange(max_retries):
            try:
                self.check_response_for_errors(response)
            except:
                headers, proxy = self.proxymesh_config()
                response = requests.get(url, headers=headers, proxies=proxy)
                continue
            else:
                break
        if response.status_code == 200:
            return {
                    "source": "PROXYMESH",
                    "success": True,
                    "status_code": response.status_code,
                    "content": response.content
                    }
        else:
            return {
                    "source": "PROXYMESH",
                    "success": False,
                    "status_code": 4003,
                    "content": ""
                    }
