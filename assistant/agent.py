import json
import re
import uuid
from http import HTTPStatus

import requests

from act.seeker import *
from act.trigger import *
from act.writer import *
from config import *

auto.uiautomation.SetGlobalSearchTimeout(1)

window = get_window()
chat_list_panel = get_chat_list_panel(window)
chat_list = chat_list_panel.GetChildren()
notify_list = []
name = None


def execute(num):
    global window
    global chat_list_panel
    global chat_list
    global notify_list
    global name
    if num == "0":
        # 重新获得新消息
        time.sleep(1)
        window = get_window()
        chat_list_panel = get_chat_list_panel(window)
        chat_list = chat_list_panel.GetChildren()
        notify_list = []
        for chat_shot in chat_list:
            if is_notify_with_text(chat_shot):
                name = find_control_with_control_type(chat_shot, "ButtonControl").Name
                if name in name_exclude:
                    continue
                notify_list.append(chat_shot)
        if len(notify_list) == 0:
            return "0"
        else:
            return "1"
    elif num == "1":
        # 点击chat_shot
        for chat_shot_inner in notify_list:
            name = find_control_with_control_type(chat_shot_inner, "ButtonControl").Name
            if name in name_exclude:
                continue
            chat_shot = chat_shot_inner

        chat_shot.Click(simulateMove=False, waitTime=1)
        try:
            window.EditControl(Name=name)
        except:
            return "0"
        chat_text = get_chat_text(window)
        latest_chat = chat_text.split('\n')[-1]
        print(latest_chat)
        # 私聊，说话人等于聊天窗的人
        pattern1 = re.compile("(.*)\\s说\\s(.*)")
        match = pattern1.match(latest_chat)
        if match:
            username = match.group(1)
            content = match.group(2)
            if name == username:
                ret = call_moss("DirectMessage", username, content)
            else:
                # 群聊，@了才回复
                pattern = re.compile("(.*)\\s说\\s@" + bot_name + "\\s(.*)")
                match = pattern.match(latest_chat)
                if match:
                    username = match.group(1)
                    content = match.group(2)
                    ret = call_moss(name, username, content)
                else:
                    return "0"
        else:
            return "0"
        try:
            send_msg(name, window, ret)
        except:
            return "0"
        if len(notify_list) <= 1:
            notify_list = []
            fileup = auto.ButtonControl(Name="文件传输助手")
            fileup.Click(simulateMove=False, waitTime=1)
            return "0"
        else:
            notify_list = notify_list[1:]
            return "1"


def call_moss(groupname, username, content):
    data = {"groupname": groupname,
            "query": {"content": content, "type": "text"}, "query_id": str(uuid.uuid1()).replace("-", ""),
            "username": username}
    print(data)
    try:
        response = requests.post(moss_api_url, json.dumps(data))
        if response.status_code == HTTPStatus.OK:
            res = response.json().get("reply")
            print(res)
            return res
        else:
            return "Moss不知道哇"
    except Exception as e:
        print(e)
        return "Moss下班啦，明天再来问问看吧! [工作时间 9:00~18:00]"
