import json
import falcon
import api_utils
import requests

class Welcome(object):

    def on_get(self, req, resp):
        
        data = {"account": "", "need_login": False, "account": ""}
        resp.body = api_utils.response(0,"success", data)
        resp.status = falcon.HTTP_200
