# -*- coding: utf-8 -*-
# ==============================================================================
# @ Author :
# @ Desc : 日志
# @ Date : 2021/5/12
# ==============================================================================
import json
import logging
import os
from logging import config as _c

# 启用日志,创建日志目录
from fetch_core.config import LOG_DIR

if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

"""
日志格式要求
系统;,;时间;,;日志级别;,;日志内容;,;接口url;,;用户ip
"""

_log_conf = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(prefix)s;,;%(asctime)s;,;%(levelname)s;,;%(message)s;,;,;,;,'},
        'simple': {
            'format': "[%(prefix)s][%(levelname)s] %(message)s"
        }
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',  # 实例对象，发送信息给流对象类似文件的对象
            'formatter': 'standard'
            },

        # 文件处理器 RotatingFileHandler 循环文件处理器
        "file_handler": {
            "level": "DEBUG",
            "class": "logging.handlers.RotatingFileHandler",
            # 指定路径的名字
            "filename": os.path.join(LOG_DIR, "info.log"),
            "maxBytes": 1024 * 1024 * 1024,
            # 保存的备份数量
            "backupCount": 5,
            "formatter": "standard",
            "encoding": "utf8",
        },

    },
    'loggers': {
        'prefix': {
            'handlers': ['console', 'file_handler'],
            'level': 'DEBUG',
            'propagate': False,  # 是否向上传递错误信息
        }
    }
}


_PREFIX_RED = "\033[0;31m"
_PREFIX_GREEN = "\033[0;32m"
_PREFIX_YELLOW = "\033[0;33m"
_PREFIX_DEFAULT = "\033[0m"


class _Logger(logging.LoggerAdapter):
    """prefix logger adapter"""

    def process(self, msg, kwargs):
        if not self.extra:
            self.extra = {}
        if 'prefix' not in self.extra:
            self.extra['prefix'] = 'none'

        kwargs["extra"] = self.extra

        # format msg
        msg = self.format(msg)
        return msg, kwargs

    def setLevel(self, level):
        """
        Set the logging level of this logger.
        """
        self.logger.setLevel(level)

    @staticmethod
    def format(msg):
        if isinstance(msg, (dict, list, tuple)):
            # noinspection PyBroadException
            try:
                msg = json.dumps(msg, indent=2, separators=(',', ': '), skipkeys=True, ensure_ascii=False,
                                 encoding='utf-8')
            except BaseException:
                pass
        return msg

    def red_info(self, msg, *args, **kwargs):
        return self.info(_PREFIX_RED + msg + _PREFIX_DEFAULT, *args, **kwargs)

    def green_info(self, msg, *args, **kwargs):
        return self.info(_PREFIX_GREEN + msg + _PREFIX_DEFAULT, *args, **kwargs)

    def yellow_info(self, msg, *args, **kwargs):
        return self.info(_PREFIX_YELLOW + msg + _PREFIX_DEFAULT, *args, **kwargs)

    def red_error(self, msg, *args, **kwargs):
        return self.error(_PREFIX_RED + msg + _PREFIX_DEFAULT, *args, **kwargs)


def get_logger(prefix=None):
    """
    获取一个prefix为前缀的logger， format已经指定好

    :param prefix: 前缀字符串
    :return: 日志对象logger
    """
    logger = logging.getLogger('prefix')
    extra = dict()
    if prefix:
        extra['prefix'] = prefix
    else:
        extra['prefix'] = 'email_fetch'
        logger = logging.getLogger('email_fetch')
    return _Logger(logger, extra)


_c.dictConfig(_log_conf)
