# -*- coding: utf-8 -*-
# ==============================================================================
# @ Author :
# @ Desc : 全局配置
# @ Date : 2021/4/26
# ==============================================================================
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_DIR = os.path.join(BASE_DIR, "log")

#  邮箱配置
EMAIL_HOST = "partner.outlook.cn"
EMAIL_PORT = 993
EMAIL_USERNAME = ""
EMAIL_PASSWORD = ""
DES_KEY = ""


# 腾讯云用户属性配置
TENCENTCLOUD_CONFIG = {
    "SECRET_ID": "",
    "SECRET_KEY": "",
    "REGION": "",
    "BUCKET_NAME": "",
    "APPID": "",
    "TOKEN": None,
}

# MySQL数据库配置（demo阶段测试用）
MySQL_CONFIG = {
    "host": "",
    "port": 4000,
    "user": "",
    "password": "",
    "db_name": ""
}

# ES拆词接口
ES_URL = "http://ip:port/es/analyzerReturnList?"

# 本地附件存储路径
LOCAL_ATTACHMENT_ABSPATH = os.path.join(BASE_DIR, "attachments") + os.sep

# 加密
ENCODING_GB18030 = "gb18030"
ENCODING_UTF8 = "utf-8"
ENCODING_ISO_8859_1 = "iso-8859-1"
