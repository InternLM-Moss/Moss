import json
import falcon
import api_utils

@falcon.before(api_utils.login_check, [])
class System_Menu(object):

    def on_get(self, req, resp):
    

        with api_utils.session_scope() as session:
            data= {
                "login_out": 1,
                "pages": [
                    {
                    "children": [
                      {
                        "label": "首页",
                        "url": "/",
                        "icon": "fa fa-home",
                        "schemaApi": "get:/pages/home.json"
                      },
                      {
                        "label": "Jobs",
                        "icon": "fas fa-compress-arrows-alt",
                        "children": [
                          {
                            "label": "微信机器人",
                            "url": "/jobs/wechatbot",
                            "icon": "fab fa-perbyte",
                            "schemaApi": "get:/pages/jobs/wechatbot.json"
                          }
                        ]
                      }]
                  }
                ]
            }
           


            resp.body = api_utils.response(0,"success", data)
            resp.status = falcon.HTTP_200
        
