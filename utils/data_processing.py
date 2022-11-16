# -*- coding: utf-8 -*-
# ==============================================================================
# @ Author :
# @ Desc : 数据处理工具
# @ Date : 2021/5/17
# ==============================================================================
import json
import os
import re
import string
import uuid

import requests

from fetch_core.config import ES_URL
from utils.exceptions import ESCallException, ESRespException
from utils.init_logger import get_logger

logger = get_logger("data_processing")


def get_file_size(file):
    return os.path.getsize(file)


def get_uuid4():
    return uuid.uuid4().__str__().replace("-", "")


def remove_non_printable(s):
    return ''.join(c for c in s if c in string.printable)


def get_decrypted_password(key, password):
    """
    获取原始邮箱密码

    :param str key: 加密后的密钥
    :param str password: 加密后的密码
    :return: 原始邮箱密码
    """
    pwd = "pass"

    return remove_non_printable(pwd)


def get_es_words_from_subject(subject):
    """
    调用es拆词API得到标题词组

    :param subject: 邮件标题
    :return: 拆词词组
    :rtype: list
    """

    params = {
        "indexName": "",
        "text": subject
    }

    logger.info("调用ES分词接口, 当前标题内容:{}".format(subject))
    try:
        res = requests.get(url=ES_URL, params=params)

        if res.status_code != 200:
            logger.error(res.text)
            raise ESCallException(res.text)

        # 分词结果判断
        res_data = json.loads(res.text)
        status = res_data.get("status")
        if not status or status != 1:
            raise ESRespException("返回status值不为1")

        es_words = res_data.get("data")  # 拆词结果
        return es_words
    except requests.exceptions.RequestException as err:
        logger.error("es call err: 调用es分词服务出错，请检查网络是否可以访问{}".format(ES_URL))
        return []


def get_target_info(exp, text):

    return re.findall(exp, text)


def email_addr_cleaning(sender):
    """
    数据清洗获取发件人邮箱

    :param sender: email_message["FROM"]
    :return: 发件人邮箱
    """
    try:
        return get_target_info(r"<(.*?)>", sender)[0]
    except Exception as err:
        logger.warn("提取发件人信息异常, 源信息内容：[{}], 异常报错: {}".format(sender, err))
        return sender


def etag_rm_quotation(etag):
    """
    去除cos返回的Etag中的双引号

    :param etag: cos上传接口返回的ETag
    :return: 去除双引号的ETag
    """
    try:
        return get_target_info(r'"(.*?)"', etag)[0]
    except Exception as err:
        logger.error("提取ETag信息异常, 源信息内容：[{}], 异常报错: {}".format(etag, err))
        return etag


def get_pdf_data(file_abspath):
    """
    读取pdf文件的页数和内容

    :param file_abspath: 文件绝对路径
    :return: (页数, 内容)
    :rtype: tuple
    """
    from io import StringIO
    from pdfminer.high_level import extract_pages, extract_text_to_fp

    output_string = StringIO()

    with open(file_abspath, 'rb') as in_file:
        page_num = len(list(extract_pages(in_file)))
        extract_text_to_fp(in_file, output_string)

    logger.info("pdf附件页数:{}, 附件前300字段内容:{}...".format(page_num, output_string.getvalue().strip()[:297]))
    return page_num, output_string.getvalue().strip()


def get_excel_data(file_abspath):
    """
    读取Excel文档所有内容

    :param file_abspath: 文件绝对路径
    :return: 文档所有内容字符串拼接
    """
    import openpyxl
    from io import StringIO

    output_string = StringIO()
    wb_obj = openpyxl.load_workbook(filename=file_abspath)
    sheet_obj = wb_obj.active

    for i in sheet_obj.values:
        output_string.write(str(i))

    result = output_string.getvalue().replace("None, ", "").replace("None", "")
    logger.info("xlsx附件前300字段内容:{}...".format(result[:297]))

    return result


def remove_html_tag(text):
    """
    邮件描述去除html标签

    :param text: 邮件正文
    :return:
    """
    exp = re.compile('<.*?>|&([a-z0-9]+|#[0-9]{1,6}|#x[0-9a-f]{1,6});')
    cleaned_text = re.sub(exp, '', text)
    return cleaned_text.strip()[:300]
