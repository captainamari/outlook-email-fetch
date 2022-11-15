# Outlook 邮箱邮件内容抓取

* Based on Imaplib with Python

---

<h3 id="ProjectInfo">项目简介</h3>

* 项目基于imaplib抓取邮件内容（包含附件）
* 邮件的 标题、内容、来源（邮件所属机构）存入系统数据库表结构；同时更新机构的研报数量
* 附件通过 cos 上传到腾讯云保存

---

<h3 id="ProjectDetails">项目目录说明</h3>

抓取服务入口：
* 先去 `config.py` 配置基本信息！！！
* run.py
* concurrent_run.py

* fetch_core

    * config.py
        * 抓取服务基本配置，如：`邮箱账号密码`, `MySQL基本配置`, `腾讯云用户属性配置`, `本地附件存储路径`, ～～`ES拆词接口`～～

    * outlook.py
        * 使用 `imaplib` 模块连接和获取邮件内容
        * 邮件内容抓取，包含邮件的`标题`, `发件人`, `发件时间`, `正文`和`附件`

    * db.py
        * 使用 `peewee` 作为ORM框架
        * 保存顺序：先将`邮件正文`和`邮件附件`分别保存至`t_report_content`和`t_attachment`表，再保存邮件其它信息到`t_report`表，最后回填`report_id`至`t_report_content`

    * tencentyun.py
        * 封装 `cos-python-sdk-v5` 模块上传方法

* utils:
    * init_logger.py
    * exceptions.py
    * decorator.py
    * time_converter.py
    * data_processing.py

* attachments
    * 放置邮件附件

* log
    * 放置log日志

---
