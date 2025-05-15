#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Time    : 2025/4/29 12:16
# @Author  : harilou
# @Describe:

import requests
import json
import time
import logging
from typing import Dict, List, Optional


class FSAPI(object):

    def __init__(self, app_id: str, app_secret: str, default_chat_id: str = None):
        self.try_max = 3
        self.app_id = app_id
        self.app_secret = app_secret
        self.default_chat_id = default_chat_id
        self.headers = self.get_headers()

    def get_headers(self):
        url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
        headers = {"Content-Type": "application/json; charset=utf-8"}
        data = {"app_id": self.app_id, "app_secret": self.app_secret}
        ret = requests.post(url, data=json.dumps(data), headers=headers).json()
        headers = {"Authorization": "Bearer " + ret["tenant_access_token"],
                   "Content-Type": "application/json; charset=utf-8"}
        return headers

    def send_msg(self, card, chat_id=None):
        if not chat_id:
            chat_id = self.default_chat_id
        url = "https://open.feishu.cn/open-apis/message/v4/send/?receive_id_type=chat_id"
        payload = json.dumps({
            "msg_type": "interactive",
            "update_multi": False,
            "card": card,
            "chat_id": chat_id,
            "uuid": str(round(time.time(), 0))
        })
        logging.info(f"send_msg payload:{payload}")
        for i in range(self.try_max):
            response = requests.request("POST", url, headers=self.headers, data=payload).json()
            if response['code'] == 0:
                break
            if (self.try_max - 1) == self.try_max:
                raise Exception(f"retry {self.try_max} Send msg fail!")
            time.sleep(i + 1)
        return response["data"]["message_id"]

    def urgent_phone(self, msg_id, user_id_list, user_id_type="open_id"):
        url = f"https://open.feishu.cn/open-apis/im/v1/messages/{msg_id}/urgent_phone?user_id_type={user_id_type}"
        payload = json.dumps({
            "user_id_list": user_id_list
        })
        logging.info(f"urgent_phone payload:{payload}")
        response = requests.request("PATCH", url, headers=self.headers, data=payload).json()
        if response['code'] != 0:
            msg = f"urgent phone fail:{response}"
            logging.error(msg)
            raise Exception(msg)
        logging.info(f"urgent_phone success! msg:{response}")
        return response

    def get_chat_info(self):
        url = "https://open.feishu.cn/open-apis/im/v1/chats?page_size=100&user_id_type=open_id"
        response = requests.request("GET", url, headers=self.headers).json()
        if response['code'] != 0:
            msg = f"get_chat_id fail: {response}"
            logging.error(msg)
            raise Exception(msg)
        return response

    def get_user_id(self, email_list, user_id_type="open_id"):
        url = f"https://open.feishu.cn/open-apis/contact/v3/users/batch_get_id?user_id_type={user_id_type}"
        payload = json.dumps({
            "emails": email_list
        })
        response = requests.request("POST", url, headers=self.headers, data=payload).json()
        if response['code'] != 0:
            msg = f"get_user_id fail: {response}"
            logging.error(msg)
            raise Exception(msg)
        return response


class FSMsgHandler(FSAPI):
    """
    消息卡片搭建工具: https://open.feishu.cn/tool/cardbuilder?from=howtoguide&templateId=ctp_AAY8p0HDLbDS
    """
    def __init__(self, app_id: str, app_secret: str, default_chat_id: str = None, user_emails_map: Dict[str, List[str]] = None):
        super(FSMsgHandler, self).__init__(app_id, app_secret, default_chat_id)
        self.user_emails_map = user_emails_map or {}

    def get_chat_id(self, name):
        data = self.get_chat_info()
        for info in data["data"]["items"]:
            if name == info["name"]:
                return info["chat_id"]
        logging.warning(f"not found chat name:{name}")
        return

    def send_urgent_phone(self, msg_id, project, user_list=None):
        """
        推送电话加急
        :param msg_id: 消息ID
        :param project: 项目
        :return: 推送结果
        """
        user_openid_list = list()
        if user_list:
            user_email_list = user_list
        elif project in self.user_emails_map:
            user_email_list = self.user_emails_map.get(project)
        else:
            user_email_list = self.user_emails_map.get("OPS")

        res = self.get_user_id(email_list=user_email_list)
        for item in res["data"]["user_list"]:
            if "user_id" in item:
                user_openid_list.append(item["user_id"])
            else:
                logging.error(f"email:{item['email']} not found!")
        return self.urgent_phone(msg_id, user_openid_list)

    def alert(self, msg, chat_id):
        template_color = {
            "P0": "grey",
            "P1": "red",
            "P2": "orange",
            "P3": "purple",
            "P4": "blue"
        }

        title = f"安全运营报告"
        color = "green"

        data = {
            "config": {
                "wide_screen_mode": True
            },
            "elements": [{
                "tag": "markdown",
                "content": msg
            },
                {
                    "tag": "action",
                    "actions": [{
                        "tag": "button",
                        "text": {
                            "tag": "plain_text",
                            "content": "打开平台"
                        },
                        "type": "primary",
                        "multi_url": {
                            "url": "http://xxxx.harilou.com",
                            "pc_url": "",
                            "android_url": "",
                            "ios_url": ""
                        }
                    }]
                }
            ],
            "header": {
                "template": color,
                "title": {
                    "content": title,
                    "tag": "plain_text"
                }
            }
        }
        return self.send_msg(card=data, chat_id=chat_id)
