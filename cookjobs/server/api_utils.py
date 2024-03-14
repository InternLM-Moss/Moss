import json
import hashlib
from datetime import date
import falcon
import os
import random
import string
import app_cfg
import pickle
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager

tokenx = "wweNEIXNxUWBNFU@fsx"

def response(status, msg, data):
    return json.dumps({
        "status": status,
        "msg": msg,
        "data": data
    })

@contextmanager
def session_scope():
    engine = create_engine(app_cfg.DB_CONFIG)
    session = sessionmaker(engine)()
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()

def token_gen(account):
    day = date.today().strftime('%Y-%m-%d')
    token = hashlib.sha256((account + day + tokenx).encode()).hexdigest()
    return token

def token_check(token, account):
    day = date.today().strftime('%Y-%m-%d')
    checker = hashlib.sha256((account + day + tokenx).encode()).hexdigest()
    if checker ==  token:
        return True
    return False


def login_check(req, resp, resource, params, allow_roles):
    # 验证是否有登录
    try:
        account = req.headers['ACCOUNT']
    except:
        account = None
    #if not account or not token_check(req.headers['AUTHORIZATION'], account):
    #    resp.body = response(1,"请先登录", {"login_out": "登录"})
    #    resp.status = falcon.HTTP_400
    #    raise falcon.HTTPBadRequest(title='请先登录，点击右上角登录')
    return True
    
    
def get_random_string(length):
    result_str = ''.join(random.choice(string.ascii_letters+'0123456789') for i in range(length))
    return result_str
    