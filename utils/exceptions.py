# -*- coding: utf-8 -*-
# ==============================================================================
# @ Author :
# @ Desc : 定义异常
# @ Date : 2021/5/12
# ==============================================================================
from typing import Optional


class Save2DBException(Exception):
    def __init__(self, err_msg: Optional[str]):
        """
        保存至MySQL异常

        :param err_msg: 错误消息
        """
        self._err_msg = err_msg

    def __str__(self):
        return "保存至MySQL异常!异常信息:{}".format(self._err_msg)


class ESCallException(Exception):
    def __init__(self, err_msg: Optional[str]):
        """
        调用ES分词接口异常

        :param err_msg: 错误消息
        """
        self._err_msg = err_msg

    def __str__(self):
        return "call es api err: {}".format(self._err_msg)


class ESRespException(Exception):
    def __init__(self, err_msg: Optional[str]):
        """
        ES分词接口解析异常

        :param err_msg: 错误消息
        """
        self._err_msg = err_msg

    def __str__(self):
        return "es api return err: {}".format(self._err_msg)
