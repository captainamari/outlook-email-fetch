# -*- coding: utf-8 -*-
# ==============================================================================
# @ Author :
# @ Desc : 抓取outlook邮件内容
# @ Date : 2021/4/26
# ==============================================================================
import datetime
import email
import imaplib
import time
from email.header import decode_header

from fetch_core.config import *
from fetch_core.db import DBManagement
from fetch_core.tencentyun import upload_with_cos
from utils.decorator import retry
from utils.init_logger import get_logger
from utils.time_converter import converter
from utils.data_processing import get_file_size, email_addr_cleaning, get_decrypted_password, get_pdf_data, \
    get_excel_data, get_uuid4

logger = get_logger("outlook_fetch")


class EmailInfoFetch:

    def __init__(self):
        self.imap = None
        self.inbox_messages = None
        self.latest_report_time = None  # 数据库最新保存研报的发件时间

        # email content
        self.raw_email = None
        self.email_message = None
        self.subject = None
        self.sender = None
        self.body = None
        self.sendtime = None
        # email attach
        self.attachment = []
        self.attachment_text= ""
        self.attachment_page = 0
        # report other user
        self.author = None

    @retry((Exception,), tries=3, delay=2)
    def login(self, username, password):
        self.imap = imaplib.IMAP4_SSL(EMAIL_HOST, port=EMAIL_PORT)
        # decrypt password
        decrypted_password = get_decrypted_password(DES_KEY, password)
        # 认证
        status, d = self.imap.login(username, decrypted_password)
        assert status == "OK", "登录失败：%s" % str(status)
        logger.info("="*50 + "[{}]已登陆".format(username) + "="*50)

    def logout(self):
        # 登出并断开连接
        self.imap.close()
        self.imap.logout()
        logger.info("=" * 50 + "[{}]已登出".format(EMAIL_USERNAME) + "=" * 50)

    def list(self):
        return self.imap.list()

    def select(self, dir):
        """

        :param dir: 文件夹
        :return: (status, dir_message)
        :rtype: (str, list)
        """
        return self.imap.select(dir)

    def inbox(self):
        """

        :return: inbox_message
        :rtype: list
        """
        status, inbox_message = self.imap.select("INBOX")
        return inbox_message

    def read_only(self, folder):
        return self.imap.select(folder, readonly=True)

    def all_ids(self):
        status, data = self.imap.search(None, "ALL")
        msg_list = data[0].split()
        return msg_list

    @staticmethod
    def since_date(days):
        mydate = datetime.datetime.now() - datetime.timedelta(days=days)
        return mydate.strftime("%d-%b-%Y")

    def all_ids_since(self, days):
        status, data = self.imap.search(None, '(SINCE "'+self.since_date(days)+'")', 'ALL')
        msg_list = data[0].split()
        return msg_list

    def all_ids_since_date(self, date_time):
        self.latest_report_time = date_time
        date = date_time.strftime("%d-%b-%Y")
        status, data = self.imap.search(None, '(SINCE "'+date+'")', 'ALL')
        msg_list = data[0].split()
        logger.info(f"[{str(date_time).split()[0]}]--[{datetime.date.today()}] 共有邮件数量: {len(msg_list)}")
        return msg_list

    def get_email(self, id):
        status, data = self.imap.fetch(str(id), "(RFC822)")
        self.raw_email = data[0][1]
        self.email_message = email.message_from_bytes(self.raw_email)
        return self.email_message

    def maildatetime(self):
        self.sendtime = self.email_message["DATE"]
        # print("self.sendtime:{}".format(self.sendtime))
        return self.sendtime

    def converted_datetime(self):
        self.sendtime = converter(self.maildatetime())
        logger.info(f"邮件发送时间: {self.sendtime}")
        return self.sendtime

    def mailfrom(self):
        self.raw_sender = self.email_message["FROM"]
        return self.raw_sender

    def sender_addr(self):
        self.sender = email_addr_cleaning(self.mailfrom())
        logger.info("邮件发件人: {}".format(self.sender))
        return self.sender

    def mailsubject(self):
        raw_subject = self.email_message["SUBJECT"]
        detail, encoding = decode_header(raw_subject)[0]
        if encoding:
            try:
                detail = detail.decode(encoding)
            except UnicodeDecodeError as err:
                logger.error("标题解码失败，错误信息：{}。将尝试使用GB18030解码。".format(err))
                try:
                    detail = detail.decode(ENCODING_GB18030)
                except UnicodeDecodeError as err:
                    logger.error("标题解码失败，错误信息：{}。将尝试使用ISO-8856-1解码。".format(err))
                    detail = detail.decode(ENCODING_ISO_8859_1)
        self.subject = detail
        logger.info("邮件标题: {}".format(self.subject))
        return self.subject

    def clean_last_email_info(self):
        # email content
        self.raw_email = None
        self.email_message = None
        self.subject = None
        self.sender = None
        self.body = None
        self.sendtime = None
        # email attach
        self.attachment = []
        self.attachment_text= ""
        self.attachment_page = 0
        # report other user
        self.author = None

    @staticmethod
    def decode(data):
        detail, encoding = decode_header(data)[0]
        if encoding:
            return detail.decode(encoding)
        return detail

    @staticmethod
    def get_attachment(message):
        attachment = message.get_payload(decode=True)
        return attachment

    def get_body(self, message):
        try:
            return message.get_payload(decode=True).decode()
        except UnicodeDecodeError as err:
            logger.info(f"{self.subject} 正文[UTF-8]解码错误, err message: {err}")
            try:
                # print(message.get_payload(decode=True).decode(ENCODING_GB18030))
                return message.get_payload(decode=True).decode(ENCODING_GB18030)
            except UnicodeDecodeError as err:
                logger.info(f"{self.subject} 正文[GB18030]解码错误, err message: {err}")
                # print(message.get_payload(decode=True).decode(ENCODING_ISO_8859_1))
                return message.get_payload(decode=True).decode(ENCODING_ISO_8859_1)

    @staticmethod
    def _download_and_uplaod(attach_name, attachment):
        """
        下载附件并上传至腾讯云

        :param attach_name: 附件名称
        :param attachment: 附件内容
        :return: 上传腾讯云成功返回的etag, 附件本地绝对路径
        :rtype: tuple
        """
        index_dot = attach_name.rfind(".")
        attach_type = attach_name[index_dot:]
        original_attach_name = attach_name
        attach_name = get_uuid4() + attach_type  # 用"自己生成的uuid+文件类型"命名
        try:
            # 下载附件
            storepath = LOCAL_ATTACHMENT_ABSPATH + "{}".format(attach_name)
            with open(storepath, "wb") as f:
                f.write(attachment)
            logger.info(f"下载附件[{attach_name}]至本地成功")
        except Exception as err:
            # 遇到附件名中有特殊字符的附件，用时间戳命名该附件
            attach_name = str(int(time.time())) + attach_type
            storepath = LOCAL_ATTACHMENT_ABSPATH + "{}".format(attach_name)
            with open(storepath, "wb") as f:
                f.write(attachment)
                logger.info(f"下载附件[{original_attach_name}]至本地失败，修改附件名为{attach_name}下载成功")

        # 上传至腾讯云
        etag = upload_with_cos(attach_name)

        return attach_name, storepath

    def _build_attach(self, message):
        """
        构造附件信息结构, 保存该结构到self.attachment, 删除本地附件

        :param message: email的message对象
        :return: (attach_uuid, attach_name, attach_size)
        :rtype: tuple
        """

        attach_name = self.decode(message.get_param("name"))
        attachment = self.get_attachment(message)
        if not attachment:
            logger.error(f"邮件标题:[{self.subject}] 的附件内容获取失败")
        attach_uuid, attach_abspath = self._download_and_uplaod(attach_name, attachment)
        attach_size = get_file_size(attach_abspath)
        logger.info("邮件附件名称: {}".format(attach_name))
        # 读取附件内容
        _index = attach_name.rfind(".")
        _type = attach_name[_index:]
        if _type == ".pdf":
            page_num, attachment_text = get_pdf_data(attach_abspath)
            self.attachment_page += page_num
            self.attachment_text += attachment_text

        if _type == ".xlsx":
            attachment_text = get_excel_data(attach_abspath)
            self.attachment_page += 1
            self.attachment_text += attachment_text

        # 删除本地附件
        self.remove_local_attach(attach_uuid)

        self.attachment.append((attach_uuid, attach_name, attach_size))

    def fetch_email_content(self):
        # 先判断是否需要抓取
        self.converted_datetime()
        # 判断邮件发件时间
        if self.if_earlier_than_report_time():
            return False
        # 判断发件人是否在机构白名单
        self.sender_addr()
        if not self.if_sender_in_white_list():
            return False
        # 判断邮件标题是否已存在数据库
        self.mailsubject()
        if self.if_subject_repeat():
            return False

        # 邮件正文，邮件附件
        if self.email_message.is_multipart():
            for message in self.email_message.walk():
                content_type = message.get_content_type()
                if content_type == "text/plain":
                    body = self.get_body(message)
                    self.body = body

                if content_type == "text/html":
                    body = self.get_body(message)
                    if self.body is None and body is not None:
                        self.body = body
                    elif self.body and body:
                        self.body = self.body + "\n" + body

                if message.get_param("name"):
                    self._build_attach(message)

        else:
            message = self.email_message
            content_type = message.get_content_type()

            if content_type == "text/plain":
                body = self.get_body(message)
                self.body = body

            if content_type == "text/html":
                body = self.get_body(message)
                if self.body is None and body:
                    self.body = body
                if self.body and body:
                    self.body = self.body + "\n" + body

            if message.get_param("name"):
                self._build_attach(message)
        return True

    def save_email(self):
        """ 保存Email信息到MySQL数据库 """
        email_data = {
            "subject": self.subject,
            "sender": self.sender,
            "body": self.body,
            "datetime": self.sendtime,
            "attachment_list": self.attachment,
            "author": self.author,
            "attachment_text": self.attachment_text,
            "attachment_page": self.attachment_page
        }
        # 保存至MySQL
        DBManagement().save_email_to_mysql(email_data)

    @staticmethod
    def remove_local_attach(filename, dir_abspath=None):
        """
        删除本地附件

        :param filename: 附件名称(带文件类型后缀)
        :param dir_abspath: 目标目录绝对路径
        :return:
        """
        if not dir_abspath:
            items = os.listdir(LOCAL_ATTACHMENT_ABSPATH)
        else:
            items = os.listdir(dir_abspath)
        for item in items:
            # item = item.split(".")[0]
            if filename == item:
                os.remove(os.path.join(LOCAL_ATTACHMENT_ABSPATH, item))
                logger.info(f"本地删除附件[{filename}]成功")

    def if_earlier_than_report_time(self):
        """
        判断当前抓取邮件发件时间是否早于数据库最新研报表中邮件的发件时间

        :return: True表示早于，False表示晚于
        :rtype: bool
        """

        email_sendtime = datetime.datetime.strptime(self.sendtime, '%Y-%m-%d %H:%M:%S')
        if self.latest_report_time >= email_sendtime:
            logger.info("邮件发件时间: {} 早于数据库最新保存研报的发件时间: {}，跳过保存".format(
                email_sendtime, self.latest_report_time))
            return True

        else:
            return False

    def if_sender_in_white_list(self):
        """
        判断当前邮件发件人是否有收录到report_other_user里面的白名单邮箱, 没有则不作处理

        :return: True表示在白名单，False表示不在白名单
        :rtype: bool
        """
        author = DBManagement().get_author(self.sender)
        if author is None:
            return False
        else:
            self.author = author
            return True

    def if_subject_repeat(self):
        """
        判断当前邮件表示是否已存在于数据库

        :return: True 存在, False 不存在
        :rtype: bool
        """
        if DBManagement().if_report_name_repeat(self.subject):
            return True
        else:
            return False
