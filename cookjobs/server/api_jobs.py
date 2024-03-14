import json
import falcon
import api_utils
from datetime import  timedelta
from sqlalchemy import desc,func,or_

class API_Jobs(object):
    def __init__(self, Jobs):
        self.Jobs = Jobs


    def on_get(self, req, resp):
        orderBy = req.get_param('orderBy')
        orderDir = req.get_param('orderDir')
        page = int(req.get_param('page', '0'))
        perPage = int(req.get_param('perPage','0'))

        with api_utils.session_scope() as session:
            total = session.query(func.count(self.Jobs.id)).scalar()
            if orderDir == 'desc':
                jobs = session.query(self.Jobs).order_by(desc(orderBy)).limit(perPage-1).offset((page-1)*perPage)
            else:
                jobs = session.query(self.Jobs).limit(perPage-1).offset((page-1)*perPage)

            data = {"count":0, "rows":[], "total": total}

            for job in jobs:
                j = vars(job)
                data['rows'].append(
                    {
                    "id": j['id'],
                    "update_time": j['update_time'].strftime("%Y-%m-%d %H:%M:%S"),
                    "job_name": j['job_name'],
                    "job_nlu": j['job_nlu'],
                    "slot_json": str(j['slot_json']),
                    "api_type": j['api_type'],
                    "api": j['api'],
                    "comment":j['comment'],
                    }
                )

            resp.body = api_utils.response(0,"success", data)
            resp.status = falcon.HTTP_200


    def on_post(self, req, resp):
        data = json.load(req.bounded_stream)
        # {'job_name': 'test', 'job_nlu': 'test', 'slot_data': [{'slot_type': '0', 'slot_key': 'tt', 'slot_desc': 'tttt'}, {'slot_type': '1', 'slot_key': 'aabb', 'regexs': '44444'}], 'api': 'test', 'comment': 'test', 'api_type': 'post'}

        with api_utils.session_scope() as session:
            job = self.Jobs(job_name=data['job_name'], 
                            job_nlu=data['job_nlu'],
                            slot_json={'slot_data': str(data['slot_data'])},
                            api=data['api'],
                            api_type=data['api_type'],
                            comment=data['comment']
                            )
            session.add(job)

            resp.body = api_utils.response(0,"success", data)
            resp.status = falcon.HTTP_200
            return
        
    def on_delete(self, req, resp):
        """
        删除作业任务
        """
        data = json.load(req.bounded_stream)
        id = data['id']
        with api_utils.session_scope() as session:
            job = (
                session.query(self.Jobs)
                .filter((self.Jobs.id == id))
                .first()
            )

            if job is not None:
                session.delete(job)
            
                resp.body = api_utils.response(0, "删除作业成功", {})
                resp.status = falcon.HTTP_200
            else:
                resp.body = api_utils.response(302, "删除作业失败", {})
                resp.status = falcon.HTTP_404