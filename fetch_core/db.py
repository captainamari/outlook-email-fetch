# -*- coding: utf-8 -*-
# ==============================================================================
# @ Author :
# @ Desc : MySQL数据库相关函数
# @ Date : 2021/5/13
# ==============================================================================
import random
import time

# 第三方库
from peewee import MySQLDatabase, Model, AutoField, CharField, IntegerField, SmallIntegerField, \
    TextField, DateTimeField, BigIntegerField, DoesNotExist
# 项目内部库
from fetch_core.config import MySQL_CONFIG
from utils.init_logger import get_logger
from utils.data_processing import get_es_words_from_subject, get_uuid4, remove_html_tag

logger = get_logger("database")


def gen_mysql():
    """ 生成数据库连接对象 """
    db = MySQLDatabase(
        host=MySQL_CONFIG["host"],
        port=MySQL_CONFIG["port"],
        user=MySQL_CONFIG["user"],
        password=MySQL_CONFIG["password"],
        database=MySQL_CONFIG["db_name"]
    )
    return db


# 初始化数据库连接
db_mysql = gen_mysql()


# 定义模型类##############################################################################################################
class BaseModel(Model):
    """ 模型类基类 """
    # 数据库表名
    t_report = "t_report"
    t_report_content = "t_report_content"
    t_tag = "t_tag"
    t_attachment = "t_attachment"
    t_report_other_user = "t_report_other_user"

    class Meta:
        database = db_mysql


class TReport(BaseModel):
    """ 定义研报表模型类 """
    REPORT_STATUS = ((1, "草稿"), (2, "发布"))

    id = AutoField(primary_key=True)
    uuid = CharField(max_length=64, unique=True, verbose_name="唯一uuid")
    name = CharField(max_length=512, verbose_name="研报标题(邮件标题)")
    type = IntegerField(verbose_name="研报类型", default=5, help_text="5:外部研报;其他情况均内部研报")
    status = SmallIntegerField(choices=REPORT_STATUS, verbose_name="研报状态")
    stock_id = IntegerField(default=0)
    associated_id = IntegerField(default=0)
    is_delete = IntegerField(default=0)
    category_id = IntegerField(default=0)
    tag_id_list = CharField()
    description = CharField()
    summary = CharField()
    content_id = IntegerField(verbose_name="内容id", help_text="来源t_report_content")
    author = CharField(max_length=64, verbose_name="机构名称", help_text="来源t_report_other_user")
    author_id = IntegerField(default=0, verbose_name="作者userId", help_text="外部研报默认0")
    attachment_list = TextField(verbose_name="附件uuid列表", help_text="来源t_attachment")
    attachment_text = TextField(verbose_name="附件文字内容")
    attachment_page = IntegerField(verbose_name="附件页数")
    report_time = DateTimeField(verbose_name="发布时间", help_text="邮件发送时间")
    create_time = DateTimeField(verbose_name="创建时间")
    update_time = DateTimeField(verbose_name="更新时间")
    send_time = DateTimeField(verbose_name="邮箱发送时间")
    from_email = CharField(max_length=32, verbose_name="来源邮箱", help_text="外部研报必填")

    class Meta:
        managed = False
        db_table = BaseModel.t_report
        verbose_name = "研报表"


class TReportContent(BaseModel):
    """ 定义研报内容表模型类 """
    id = AutoField(primary_key=True)
    report_id = IntegerField(verbose_name="研报id")
    content = TextField(verbose_name="内容")
    create_time = DateTimeField(verbose_name="创建时间")

    class Meta:
        managed = False
        db_table = BaseModel.t_report_content
        verbose_name = "研报内容表"


class TTag(BaseModel):
    """ 定义标签表模型类 """
    STOCK_TYPE = ((4, "A股股票"), (5, "港股股票"), (6, "美股股票"))

    id = AutoField(primary_key=True)
    type_id = IntegerField(choices=STOCK_TYPE, verbose_name="股票类型id")
    name = CharField(max_length=32, verbose_name="标签名称")
    stock_name = CharField(max_length=64, verbose_name="股票名称")

    class Meta:
        managed = False
        db_table = BaseModel.t_tag
        verbose_name = "标签表"


class TAttachment(BaseModel):
    """ 定义附件表模型类 """
    id = AutoField(primary_key=True)
    uuid = CharField(max_length=64, verbose_name="附件id", help_text="上传到腾讯云的id")
    name = CharField(max_length=256, verbose_name="附件真实名称")
    size = BigIntegerField(verbose_name="附件大小")

    class Meta:
        managed = False
        db_table = BaseModel.t_attachment
        verbose_name = "附件表"


class TReportOtherUser(BaseModel):
    """ 定义外部研报机构表模型类 """
    id = AutoField(primary_key=True)
    author = CharField(max_length=64, verbose_name="机构名称")
    suffix = CharField(max_length=32, verbose_name="邮箱后缀")
    report_count = BigIntegerField(verbose_name="邮件数量")

    class Meta:
        managed = False
        db_table = BaseModel.t_report_other_user
        verbose_name = "外部研报机构表"
########################################################################################################################


class DBManagement:
    """ 数据库管理(通过模型类保存数据至相关数据库表)"""

    def __init__(self):
        self.author = ""  # 机构名

    def _save_t_attachment(self, attachment_list):
        """
        保存附件信息至MySQL

        :param list attachment_list: 附件信息, 数据结构: [(attach_uuid, attach_name, attach_size), ...]
        :return: attach_uuid_list
        :rtype: list
        """
        attach_uuid_list = []

        for uuid, name, size in attachment_list:
            # 先查询该附件是否保存过
            count = TAttachment.filter(uuid=uuid).count()
            if count != 0:
                attach_uuid_list.append(uuid)
                continue
            attach = TAttachment(
                uuid=uuid,
                name=name,
                size=size
            )
            attach.save()
            attach_uuid_list.append(uuid)
        logger.info("附件信息保存成功, uuid_list: {}".format(attach_uuid_list))
        return attach_uuid_list

    def _save_t_report_content(self, body):
        """
        保存邮件正文信息至MySQL

        :param str body: 邮件body
        :return: report_id
        :rtype: int
        """

        content = TReportContent(content=body)
        content.save()
        content_id = content.id
        logger.info("邮件内容保存成功, content_id: {}".format(content_id))
        return content_id

    def _save_back_report_id(self, content_id, report_id):

        content = TReportContent.get_by_id(content_id)
        content.report_id = report_id
        content.save()

    def _get_tag_id(self, subject):
        """
        从邮件标题拆词，去tag表查相应的股票名称的tag_id

        :param str subject: 邮件标题
        :return: [{"id": id, "type": type, "type_id": type_id}, ...]
        :rtype: list
        """
        t_tag_id_list = []

        # es拆词拿到词组
        es_word_list = get_es_words_from_subject(subject)
        for word in es_word_list:
            try:
                tag = TTag.get(stock_name=word)
                t_tag_id_list.append(tag.id)
            except DoesNotExist:
                pass
        return t_tag_id_list

    def get_author(self, sender):
        """
        获取外部研报机构名

        :param sender: 发件人邮箱
        :return: 研报机构名
        """
        index = sender.rfind("@")
        suffix = sender[index:]

        # 通过发件人邮箱后缀查外部研报机构表获得
        try:
            author = TReportOtherUser.get(suffix=suffix)
        except DoesNotExist:
            author = None

        if not author:  # 如果没查到，邮件跳过不处理
            logger.info("发件人邮箱 [{}] 未在白名单邮箱中，不作处理。".format(sender))
            # 没有通过邮箱后缀查找到机构名，直接返回 0
            return None

        logger.info("邮箱后缀: [{}] 对应的研报机构名为: [{}]".format(suffix, author.author))
        return author.author

    def _save_t_report(self, data: dict):
        """
        保存邮件信息至研报表

        :param data:
        :return: report.id
        """

        report = TReport(
            uuid=data["uuid"],
            name=data["subject"],
            type=data["type"],
            status=data["status"],
            stock_id=data["stock_id"],
            is_delete=data["is_delete"],
            associated_id=data["associated_id"],
            category_id=data["category_id"],
            tag_id_list=data["tag_id_list"],
            description=data["description"],
            summary=data["summary"],
            content_id=data["content_id"],
            author=data["author"],
            author_id=data["author_id"],
            attachment_list=data["attachment_list"],
            attachment_text=data["attachment_text"],
            attachment_page=data["attachment_page"],
            report_time=data["datetime"],
            send_time=data["datetime"],
            from_email=data["sender"]
        )
        report.save()
        report_id = report.id
        logger.info("研报表保存成功, report_id: {}".format(report_id))
        return report_id

    def save_email_to_mysql(self, data):
        """
        保存邮件至MySQL

        :param dict data: 邮件内容
        :return:
        """
        # 判断研报标题是否重名，重名则跳过保存。此处再判断一次，担心多线程引起的重复保存
        if self.if_report_name_repeat(data["subject"]):
            return

        # 补充t_report表中其它非必填数据
        data["stock_id"] = 0
        data["is_delete"] = 0
        data["associated_id"] = 0
        data["category_id"] = 0
        data["author_id"] = 0
        data["status"] = 2
        data["type"] = 5
        data["description"] = remove_html_tag(data["body"])
        data["summary"] = ""

        # 创建uuid
        data["uuid"] = get_uuid4()
        # 获取 tag_id_list
        subject = data["subject"].replace(data["author"], "")  # 标题剔除本地机构名
        data["tag_id_list"] = self._get_tag_id(subject=subject)

        try:
            with db_mysql.atomic():
                # 保存邮件正文至t_report_content
                content_id = self._save_t_report_content(data["body"])
                data["content_id"] = content_id

                # 保存邮件附件到t_attachment, data["attachment_list"]信息更新为 attach_uuid_list
                data["attachment_list"] = self._save_t_attachment(data["attachment_list"])

                report_id = self._save_t_report(data)

                self._save_back_report_id(content_id, report_id)
                logger.info("""
================================邮件内容已成功保存至MySQL================================
                            """)
        except Exception as err:
            logger.error(f"[{data['subject']}]保存至数据库异常，异常信息: {err}")


    def get_latest_report_time(self):
        """ 获取研报表最新一条记录的邮件发送时间 """

        report = TReport.select().order_by(TReport.id.desc()).get()
        send_time = report.send_time

        logger.info("研报表最新一条记录的邮件发送时间: {}".format(report.send_time))

        return send_time

    def if_report_name_repeat(self, subject):
        """ 检查是否名称重复 """
        time.sleep(random.randint(1, 4))
        count = TReport.filter(name=subject).count()
        # print(f"[{subject}] 标题在研报表中的数量: {count}")
        if count != 0:
            logger.info("研报表标题[{}]重复，跳过保存".format(subject))
            return True

        else:
            return False
