from flask import Flask
from flask import request
import requests
import socket
import socks
import json
import random
from user_agents import user_agents

__author__ = 'nibil'

app = Flask(__name__)

TOR_KEY = ""


def random_user_agent():
    agents = [i.strip() for i in user_agents]
    return random.choice(agents)


def scroket_call(url):
    scroket = socket.socket
    socks.setdefaultproxy(proxy_type=socks.PROXY_TYPE_SOCKS5,
                          addr="127.0.0.1", port=9050)
    socket.socket = socks.socksocket
    req = requests.get(url, timeout=20,
                       headers={"User-Agent": random_user_agent()})
    socket.socket = scroket
    return req


@app.route('/')
def get_from_tor():
    """
    NOTE: Must be deployed in a private environment.
    Make sure that tor server is installed and running on the instance.
    pass url as the GET/POST parameter
    Eg: http://127.0.0.1:8000/?url=https://google.com
    """
    url = request.args.get('url', '')
    key = request.args.get('key', '')
    if key == TOR_KEY:
        try:
            response = scroket_call(url)
            return json.dumps({
                                "success": True,
                                "status_code": response.status_code,
                                "content": response.content
                                })
        except:
            return json.dumps({
                            "success": False,
                            "status_code": 4003,
                            "content": ""
                            })
    else:
        return json.dumps({
                        "success": False,
                        "status_code": 4005,
                        "content": ""
                        })


if __name__ == '__main__':
    app.run(port=8000)
