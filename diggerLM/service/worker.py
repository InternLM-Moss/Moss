# Copyright (c) OpenMMLab. All rights reserved.
"""Pipeline."""
import argparse
import datetime
import re
import requests
import pickle
import redis
#import job_task

import pytoml
from loguru import logger

from .helper import ErrorCode
from .llm_client import ChatClient
from .job_task import JobTask


class Worker:
    """The Worker class orchestrates the logic of handling user queries,
    generating responses and managing several aspects of a chat assistant. It
    enables feature storage, language model client setup, time scheduling and
    much more.

    Attributes:
        llm: A ChatClient instance that communicates with the language model.
        fs: An instance of FeatureStore for loading and querying features.
        config_path: A string indicating the path of the configuration file.
        config: A dictionary holding the configuration settings.
        language: A string indicating the language of the chat, default is 'zh' (Chinese).  # noqa E501
        context_max_length: An integer representing the maximum length of the context used by the language model.  # noqa E501

        Several template strings for various prompts are also defined.
    """

    def __init__(self, work_dir: str, config_path: str, language: str = 'zh'):
        """Constructs all the necessary attributes for the worker object.

        Args:
            work_dir (str): The working directory where feature files are located.
            config_path (str): The location of the configuration file.
            language (str, optional): Specifies the language to be used. Defaults to 'zh' (Chinese).  # noqa E501
        """
        self.llm = ChatClient(config_path=config_path)

        self.config_path = config_path
        self.config = None
        self.language = language
        with open(config_path, encoding='utf8') as f:
            self.config = pytoml.load(f)
        if self.config is None:
            raise Exception('worker config can not be None')

        
        self.jobtask = JobTask(self.config['jobtask'], llm=self.llm)

        self.context_max_length = -1
        llm_config = self.config['llm']
        if llm_config['enable_local']:
            self.context_max_length = llm_config['server'][
                'local_llm_max_text_length']
        else:
            raise Exception('no llm enabled')

        
    
    def generate(self, query, history, session_name):
        """Processes user queries and generates appropriate responses. It
        involves several steps including checking for valid questions,
        extracting topics, querying the feature store, searching the web, and
        generating responses from the language model.

        Args:
            query (str): User's query.
            history (str): Chat history.
            groupname (str): The group name in which user asked the query.

        Returns:
            ErrorCode: An error code indicating the status of response generation.  # noqa E501
            str: Generated response to the user query.
            references: List for referenced filename or web url
        """
        response = ''
        references = []

        #如果不需要服务端保存session,则使用传参的history
        if not session_name:
            response = self.llm.generate_response(query, history)

        #使用服务端保存session
        else:
            u_redis = redis.StrictRedis(host='localhost', port=6379, db=0)
            session_data = u_redis.get(session_name)
            if session_data:
                session_data = pickle.loads(session_data)
            else:
                session_data = {'history':[], "running_task": False, "jobtask": {}, "need_confirm": False, "slot_full": False, "can_run": False}

            # 已知还有task在运行中
            if 'running_task' in session_data and session_data['running_task']:
                if self.jobtask.stop_task(query):
                    session_data = {'history':[], "running_task": False, "jobtask": {}, "need_confirm": False, "slot_full": False, "can_run": False}
                    u_redis.set(session_name, pickle.dumps(session_data))
                    return ErrorCode.SUCCESS, "任务已取消", references
                # 确认任务，以及开始执行任务
                elif session_data["need_confirm"]:
                    response, session_data = self.jobtask.confirm_task(query, session_data)
                    u_redis.set(session_name, pickle.dumps(session_data))
                    return ErrorCode.SUCCESS, response, references
                else:
                    response, session_data =  self.jobtask.continue_task(query, session_data)
                    logger.debug(f"response: {response}, session_data: {session_data}")
                    u_redis.set(session_name, pickle.dumps(session_data))
                    return ErrorCode.SUCCESS, response, references
            else:
                #检测语句是否有task执行
                jobtask = self.jobtask.is_ask_task(query)
                if jobtask:
                    response, session_data = self.jobtask.new_task(query, session_data, jobtask)
                    u_redis.set(session_name, pickle.dumps(session_data))
                    return ErrorCode.SUCCESS, response, references
                else:
                    response = self.llm.generate_response(query, session_data['history'])

        
            tmp_history, new_history = [query], []
            
            for item in session_data['history']:
                tmp_history.extend([item[0], item[1]])
                # 默认只关联前6句聊天记录
                if len(tmp_history) > 6:
                    break
            
            # 如果长度为基数，则补齐一个空
            if len(tmp_history) % 2 == 1:
                tmp_history.append('')    

            it = iter(tmp_history)
            new_history = [*zip(it, it)]

            session_data['history'] = new_history
            u_redis.set(session_name, pickle.dumps(session_data))

        return ErrorCode.SUCCESS, response, references



def parse_args():
    """Parses command-line arguments."""
    parser = argparse.ArgumentParser(description='Worker.')
    parser.add_argument('work_dir', type=str, help='Working directory.')
    parser.add_argument(
        '--config_path',
        default='config.ini',
        help='Worker configuration path. Default value is config.ini')
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()
    bot = Worker(work_dir=args.work_dir, config_path=args.config_path)
    queries = ['Moss是怎么做的']
    for example in queries:
        print(bot.generate(query=example, history=[], groupname=''))