import json
import re
import uuid
from http import HTTPStatus
from jinja2 import Template

import requests
from loguru import logger

process = {}
puyuan_api_url = "http://127.0.0.1:9527/api"


def call_puyuan_online(groupname, username, content):
    # data = {"groupname": groupname,
    #         "query": {"content": content, "type": "text"}, "query_id": str(uuid.uuid1()).replace("-", ""),
    #         "username": username}
    data = {
        "query": content,
        "history": []
    }
    print(data)
    response = requests.post(puyuan_api_url, json.dumps(data))
    if response.status_code == HTTPStatus.OK:
        res = response.json().get("reply")
        logger(res)
        return res
    else:
        return "不知道哇"
    
def remove_prefix(text, prefix):
    return text[text.startswith(prefix) and len(prefix):]

def call_puyuan_inner(content):
    return call_puyuan_online("InnerMessage", "InnerMessage", content)


class JobTask:
    def __init__(self, jobtask_config: str, llm) -> None:
        self.jobtask_config = jobtask_config
        self.jobtask_data = {}
        self.llm = llm

    def continue_task(self, query, session_data):
        '''
        如果已任务还在执行中，则继续执行此func, 并返回response
        '''
        response = ''
        slot_res_map = {}
        llm_slot_list = []
        slot_value_key_dict = {}
        logger.debug(f"session_data: {session_data}")
        try:
            slot_json = eval(session_data['jobtask']["slot_json"])
        except:
            response = "请先取消历史任务， 输入：任务取消"
            return response, {'history':[], "running_task": False, "jobtask": {}, "need_confirm": False, "slot_full": False, "can_run": False}
        # 已经拿到主题，分别匹配槽位
        for slot in eval(slot_json['slot_data']):
            logger.debug(f"slot: {slot}")
            slot_type = slot["slot_type"]
            if slot_type == '1':
                # 正则类型的处理
                slot_value = self.step2_get_slot_value_by_regex(query, slot["regexs"])
                if slot_value:
                    slot_res_map[slot["slot_key"]] = slot_value
                    logger.debug(f"slot_res_map: {slot_res_map}")
            else:
                tmp = slot["slot_desc"] + "槽位"
                llm_slot_list.append(tmp)
                slot_value_key_dict[tmp] = slot["slot_key"]
                # llm类型的处理
                slot_value = self.step2_get_slot_value_by_llm(query, ",".join(llm_slot_list))
                res_list = slot_value.split("\n")
                for slot_res in res_list:
                    tmp = slot_res.split("：")
                    if len(tmp) == 2:
                        for s in llm_slot_list:
                            if s in tmp[0] and slot_value_key_dict.get(s):
                                slot_res_map[slot_value_key_dict[s]] = tmp[1]

        # 检查所有槽位是否填满，没有则继续返回进行确认
        if not session_data['slot_full']:
            tmp_mark = True
            logger.debug(f"will check all slot")
            for slot in eval(slot_json['slot_data']):

                key = slot['slot_key']
                value = slot_res_map.get(key)
                if value is None or "未提及" in value or "为空" in value:
                    response = "请问 {} 是？".format(slot['slot_desc'])
                    logger.debug(f"will resp: {response}")
                    tmp_mark = False
                    return response, session_data
            if tmp_mark:
                session_data['need_confirm'] = True
        else:
            session_data['slot_full'] = True

        session_data['jobtask']["slot"] = slot_res_map

        # step 3 返回确认信息
        if session_data['need_confirm']:
            slot_key_value_dict = {}
            for s in eval(slot_json['slot_data']):
                slot_key_value_dict[s["slot_key"]] = s["slot_desc"]

            response = "请确认任务： {}:".format(session_data['jobtask']['job_nlu'])
            for k, v in session_data['jobtask']["slot"].items():
                i = "\n - {}: {}".format(slot_key_value_dict.get(k), v)
                response = response + i 
        else:
            session_data['need_confirm'] = False

        return response, session_data

    def new_task(self, query, session_data):
        '''
        如当前无在执行的任务，则启动新任务，, 并返回response
        '''
        response = ''
        session_data["running_task"] = True
        session_data['need_confirm'] = False
        session_data['slot_full'] = False
        session_data['jobtask'] = {}
        logger.debug(f"runing new task: {session_data}")
        # step 1 大模型匹配主题
        suc1, jobtask = self.step1_get_job_nlu(query)
        if suc1:
            session_data['jobtask'] = jobtask
        else:
            logger.warning(f"大模型没有找到对应的主题: {query}, jobtask: {jobtask}")
            return "没有找到对应的主题，请登录Moss后台进行设置", session_data

        response, session_data = self.continue_task(query, session_data)
        return response, session_data

    def is_ask_task(self, query):
        '''
        检测语句是否有新的task需求， 并返回response
        '''

        api_url = 'http://127.0.0.1:8081/api/jobs/wechat?orderBy=id&orderDir=desc&page=1&perPage=10'
        r = requests.get(api_url)
        self.jobtask_data = r.json()
        logger.debug(f"jobtask_data: {self.jobtask_data}")

        if query.startswith(self.jobtask_config['start_flag']):
            
            logger.debug(f"this is new ask task: {query}")
            return True
        return False

    def stop_task(self, query):
        if query.startswith(self.jobtask_config['end_flag']):
            logger.debug(f"will stop task: {query}")
            return True
        return False

    def confirm_task(self, query, session_data):
        if query.startswith(self.jobtask_config['confirm_flag']):
            logger.debug(f" confirm task: {query}")
            session_data['need_confirm'] = False
            response=self.run_task(session_data)
            session_data = {'history':[], "running_task": False, "jobtask": {}, "need_confirm": False, "slot_full": False, "can_run": False}
            return response, session_data
        return False, session_data

    def run_task(self, session_data):
        logger.debug(f"will run task: {session_data}")
        jobtask = session_data['jobtask']
        #slot_json = eval(session_data['jobtask']["slot_json"])
        api = Template(jobtask['api']).render(jobtask['slot'])
        logger.debug(f"api url: {api}")
        if jobtask['api_type'] == 'post':
            return requests.post(api, data=json.dumps(session_data['jobtask']["slot"])).text
        elif jobtask['api_type'] == 'get':
            return requests.get(api).text
        else:
            return None

    def step1_get_job_nlu(self, content):
        job_nlu_list = []
        jobtask = {}
        for jt in self.jobtask_data['data']['rows']:
            job_nlu_list.append(jt['job_nlu'])
        content = remove_prefix(content, self.jobtask_config['start_flag'])
        job_nlu_list_str = ",".join(job_nlu_list)
        prompt1 = '现在有一个自然语言处理的问题，语义相似度分析。请问:"{}"与下列哪个语句的语义相似度最高:{}。请以下面格式回答：语义相似度最高的语句是XXX。'
        #resp = call_puyuan_inner(prompt1.format(content, job_nlu_list_str))
        resp = self.llm.generate_response(prompt1.format(content, job_nlu_list_str), [])
        logger.debug(f"prompt1:{prompt1.format(content, job_nlu_list_str)} resp: {resp}")
        pattern1 = re.compile('.*语义相似度最高的语句是"(.*)"。')
        match = pattern1.match(resp)
        if match:
            m = match.group(1)
            for jt in self.jobtask_data['data']['rows']:
                if jt['job_nlu'] == m:
                    jobtask = jt
                    break
            return True,  jobtask
        else:
            return False, jobtask

    def step2_get_slot_value_by_regex(self, content, regex):
        try:
            logger.debug(f"query: {content}, regex: {regex}")
            pattern3 = re.compile(regex)
            match = pattern3.search(content).group()
            logger.debug(f"match search: {match}")
            return match
        except:
            return False

    def step2_get_slot_value_by_llm(self, content, slot):
        prompt2 = '现在有一个自然语言处理的问题，槽位分析。请帮忙分析，在"{}"这段话中，{}分别是什么。请简单回答，去掉副词、量词、形容词等修饰'
        resp = call_puyuan_inner(prompt2.format(content, slot))
        return resp
