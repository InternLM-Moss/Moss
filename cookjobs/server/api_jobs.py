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
                job_nlu_web = []
                for nlu in eval(j['job_nlu']['job_nlu']):
                    job_nlu_web.append({"item":nlu['job_nlu_item']})
                
                
                slot_json = []
                try:
                    slot_json = eval(j['slot_json'])
                except:
                    pass


                data['rows'].append(
                    {
                    "id": j['id'],
                    "update_time": j['update_time'].strftime("%Y-%m-%d %H:%M:%S"),
                    "job_name": j['job_name'],
                    "job_nlu": eval(j['job_nlu']['job_nlu']),
                    "job_nlu_web":job_nlu_web,
                    "slot_json": slot_json,
                    "api_type": j['api_type'],
                    "txt_msg": j['txt_msg'],
                    "api": j['api'],
                    "llm": j['llm'],
                    "cus_resp": j['cus_resp'],
                    "comment":j['comment'],
                    }
                )

            resp.body = api_utils.response(0,"success", data)
            resp.status = falcon.HTTP_200


    def on_post(self, req, resp):
        data = json.load(req.bounded_stream)
       
        
        with api_utils.session_scope() as session:

            if data['api_type'] == 'txt':
                slot_json = None
                api = ""
                txt_msg = data['txt_msg']
            else:
                slot_json = str(data['slot_json'])
                api = data['api']
                txt_msg = ""

            if "comment" not in data:
                comment = ""
            else:
                comment=data['comment']


            job = self.Jobs(
                            llm=data['llm'],
                            job_name=data['job_name'], 
                            job_nlu={'job_nlu': str(data['job_nlu'])},
                            slot_json=slot_json,
                            txt_msg=txt_msg,
                            api=api,
                            cus_resp=data['cus_resp'],
                            api_type=data['api_type'],
                            comment=comment
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

    def on_update(self, req, resp):
        """
        更新作业任务
        """
        data = json.load(req.bounded_stream)
        
        with api_utils.session_scope() as session:
            job = (
                session.query(self.Jobs)
                .filter(
                    (self.Jobs.id == data['id'])
                )
                .first()
            )
            if job is not None:
                job.llm=data['llm']
                job.api_type=data['api_type']
                job.job_name=data['job_name']
                job.job_nlu={'job_nlu': str(data['job_nlu'])}
                job.slot_json= str(data['slot_json'])
                job.txt_msg=data['txt_msg']
                job.api=data['api']
                job.cus_resp=data['cus_resp']
                job.comment=data['comment']
                
                resp.body = api_utils.response(0, "更新Moss成功", {})
                resp.status = falcon.HTTP_200
            else:
                resp.body = api_utils.response(302, "更新Moss失败", {})
                resp.status = falcon.HTTP_404