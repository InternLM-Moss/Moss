import os
import json
import falcon
import api_home
import api_menu
from sqlalchemy.sql import func
from sqlalchemy import Column, Integer, String,DateTime,JSON
from sqlalchemy.ext.declarative import declarative_base
import api_jobs


Base = declarative_base()




class Jobs(Base):
    __tablename__ = "jobs"
    id = Column(Integer, primary_key=True)
    update_time = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.current_timestamp())
    job_name = Column(String(256), nullable=False)
    job_nlu = Column(String(256), nullable=False)
    slot_json = Column(JSON, index=True, nullable=True)
    api = Column(String(256), nullable=False)
    api_type = Column(String(64), nullable=False)
    comment = Column(String(256), nullable=False)
    create_time = Column(DateTime(timezone=True), server_default=func.now())

class Health(object):
    def on_get(self, req, resp):
        msg = {
            "code":0,
            "message": "all good"
        }
        resp.body = json.dumps(msg)
        resp.status = falcon.HTTP_200


#系统初始化


api = falcon.App()

api.add_static_route('/', os.getcwd()+'/../website')
# 健康检查-用于监控
api.add_route("/api/health", Health())

# Jobs
api.add_route("/api/jobs/wechat", api_jobs.API_Jobs(Jobs))

#家目录
api.add_route("/api/home", api_home.Welcome())
api.add_route("/api/menu", api_menu.System_Menu())

