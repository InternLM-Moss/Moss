#!/usr/bin/env python3
# Copyright (c) OpenMMLab. All rights reserved.
"""HuixiangDou binary."""
import argparse
import os
import sys
import time
#from multiprocessing import Process, Value
from torch.multiprocessing import Pool, Process, set_start_method

import redis
import pytoml
import requests
from aiohttp import web
from loguru import logger

from .service import ErrorCode, Worker, llm_serve


def parse_args():
    """Parse args."""
    parser = argparse.ArgumentParser(description='Worker.')
    parser.add_argument('--work_dir',
                        type=str,
                        default='workdir',
                        help='Working directory.')
    parser.add_argument(
        '--config_path',
        default='config.ini',
        type=str,
        help='Worker configuration path. Default value is config.ini')
    parser.add_argument('--run',
                        action='store_true',
                        default=False,
                        help='Auto deploy required Hybrid LLM Service.')
    args = parser.parse_args()
    return args


def check_env(args):
    """Check or create config.ini and logs dir."""
    if not os.path.exists('logs'):
        os.makedirs('logs')
    CONFIG_NAME = 'config.ini'
    if not os.path.exists(CONFIG_NAME):
        logger.error(f'Failed to download file due to {CONFIG_NAME}')
        raise

    if not os.path.exists(args.work_dir):
        logger.warning(
            f'args.work_dir dir not exist, auto create {args.work_dir}.')
        os.makedirs(args.work_dir)


def build_reply_text(reply: str, references: list):
    if len(references) < 1:
        return reply

    ret = reply
    for ref in references:
        ret += '\n'
        ret += ref
    return ret

def remove_prefix(text, prefix):
    return text[text.startswith(prefix) and len(prefix):]

def wechat_personal_run(assistant, fe_config: dict):
    """Call assistant inference."""

    async def api(request):
        input_json = await request.json()
        logger.debug(input_json)

        query = input_json['query']
        history=[]
        session_name=[]
        if type(query) is dict:
            query = query['content']
            session_name = input_json['groupname'] + "-" + input_json['username']
        else:
            query = input_json['query']
            if 'history' in input_json and type(input_json['history']) is list:
                history = input_json['history']
        code, reply, references = assistant.generate(query=query,
                                                     history=history,
                                                     session_name=session_name)
        logger.debug(f"reply: {reply}")
        reply_text = build_reply_text(reply=reply, references=references)

        logger.debug(f"code: {code} reply: {reply_text}")
        return web.json_response({'code': int(code), 'reply': reply_text})

    bind_port = fe_config['wechat_personal']['bind_port']
    app = web.Application()
    app.add_routes([web.post('/api', api)])
    web.run_app(app, host='0.0.0.0', port=bind_port)


def run():
    """Automatically download config, start llm server and run examples."""
    args = parse_args()
    check_env(args)

    if args.run:
        # hybrid llm serve

        try:
            set_start_method('spawn',force=True)
        except RuntimeError:
            pass
        server_process = Process(target=llm_serve,
                                 args=(args.config_path,''))
        server_process.daemon = True
        server_process.start()
        logger.info('LLMServer start.')


    # query by worker
    with open(args.config_path, encoding='utf8') as f:
        fe_config = pytoml.load(f)['frontend']
    logger.info('Config loaded.')
    assistant = Worker(work_dir=args.work_dir, config_path=args.config_path)

    fe_type = fe_config['type']

    if fe_type == 'wechat_personal':
        wechat_personal_run(assistant, fe_config)
    else:
        logger.info(
            f'unsupported fe_config.type {fe_type}, please read `config.ini` description.'  # noqa E501
        )

    # server_process.join()


if __name__ == '__main__':
    run()