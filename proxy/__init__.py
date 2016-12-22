from tor_client import TorClient
from luminati_client import LuminatiClient
# from proxymesh_client import ProxymeshClient
from redis import Redis
from logist import Logist
from datetime import datetime

__author__ = 'atm'

r = Redis()
l = Logist()


def fetch(url, prefered_proxy=None):
    """
    request a url through :: tor -> Luminati -> Proxymesh
    returns content of the page as string
    prefered_proxy
    Returns only 3 statuses - 200 - success
                            - 404 - url does not exist
                            - 4001 - retried KNOCK_LIMIT times and no response
    0 - tor
    1 - luminati
    // 2 - proxymesh (inactive)
    """
    knock = 0
    KNOCK_LIMIT = 10
    if not url.startswith("http"):
        url = "http://%s" % url
    content = {}
    l.info("TIMEPIECE", "%s %s" % (url, datetime.now()))
    if not r.get("proxy_rotator"):
        r.set("proxy_rotator", 0)
    if prefered_proxy is not None:
        proxy_rotator = prefered_proxy
    else:
        proxy_rotator = int(r.get("proxy_rotator"))
    while 1:
        # print knock, proxy_rotator
        if proxy_rotator == 0 and not content.get("content"):
            try:
                knock += 1
                if knock > KNOCK_LIMIT:
                    break
                r.set("proxy_rotator", "1")
                l.info("TIMEPIECE", "%s START//TOR %s" % (url, datetime.now()))
                tor = TorClient()
                content = tor.get_url(url)
                if content.get("status_code") == 200:
                    l.info("TIMEPIECE", "%s FINISH//TOR %s" %
                           (url, datetime.now()))
                    return content
                elif content.get("status_code") == 404:
                    l.info("TIMEPIECE", "%s FINISH//TOR//404 %s" %
                           (url, datetime.now()))
                    return {
                            "source": "TOR",
                            "success": False,
                            "status_code": 404,
                            "content": ""
                            }
                else:
                    l.info("TIMEPIECE", "%s ERROR//TOR %s" %
                           (url, datetime.now()))
                    raise
            except:
                proxy_rotator = int(r.get("proxy_rotator"))
        if (proxy_rotator == 1) and not content.get("content"):
            try:
                knock += 1
                if knock > KNOCK_LIMIT:
                    break
                r.set("proxy_rotator", "0")
                l.info("TIMEPIECE", "%s START//LUMINATI %s" %
                       (url, datetime.now()))
                luminati = LuminatiClient(zone="route1")
                content = luminati.get_url(url)

                if content.get("status_code") == 200:
                    l.info("TIMEPIECE", "%s FINISH//LUMINATI %s" %
                           (url, datetime.now()))
                    return content
                elif content.get("status_code") == 404:
                    l.info("TIMEPIECE", "%s FINISH//LUMINATI//404 %s" %
                           (url, datetime.now()))
                    return {
                            "source": "TOR",
                            "success": False,
                            "status_code": 404,
                            "content": ""
                            }
                else:
                    l.info("TIMEPIECE", "%s ERROR//TOR %s" %
                           (url, datetime.now()))
                    raise
            except:
                proxy_rotator = int(r.get("proxy_rotator"))

        # elif proxy_rotator == 2 and not content:
        #     try:
        #         r.set("proxy_rotator", "0")
        #         proxymesh = ProxymeshClient()
        #         content = proxymesh.get_url(url)
        #         if content.get('success', False):
        #             return content
        #         else:
        #             raise
        #     except:
        #         knock += 1
        #         if knock > 2:
        #             break
    return {
            "source": "NONE",
            "success": False,
            "status_code": 4001,
            "content": ""
            }
