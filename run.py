# -*- coding: utf-8 -*-
# ==============================================================================
# @ Author :
# @ Desc : 抓取入口
# @ Date : 2021/5/23
# ==============================================================================
import datetime

from fetch_core.config import EMAIL_USERNAME, EMAIL_PASSWORD
from fetch_core.db import DBManagement
from fetch_core.outlook import EmailInfoFetch


def run_email_fetch():
    start_time = datetime.datetime.now()
    outlook = EmailInfoFetch()
    # 登录邮箱
    outlook.login(EMAIL_USERNAME, EMAIL_PASSWORD)
    # 进入 Inbox
    outlook.inbox()
    # 获取最新保存研报的发件时间
    latest_report_time = DBManagement().get_latest_report_time()
    # 获取上次保存研报时间到现在所有邮件
    ids = outlook.all_ids_since_date(latest_report_time)

    for eid in ids:
        outlook.get_email(eid.decode())

        # 抓取前判断是否满足抓取需要
        if not outlook.fetch_email_content():
            outlook.clean_last_email_info()
            continue

        # 保存邮件内容
        outlook.save_email()
        # 内存清理上一封邮件信息
        outlook.clean_last_email_info()

        # 登出
    outlook.logout()
    end_time = datetime.datetime.now()
    print("此次邮件抓取共耗时: {}".format(end_time - start_time))


if __name__ == '__main__':
    run_email_fetch()
