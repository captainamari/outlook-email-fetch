# -*- coding: utf-8 -*-
# ==============================================================================
# @ Author :
# @ Desc :
# @ Date : 2021/5/16
# ==============================================================================

WEEK = {
    "MON": "1",
    "TUE": "2",
    "WED": "3",
    "THU": "4",
    "FRI": "5",
    "SAT": "6",
    "SUN": "7"
}

MONTH = {
    "JAN": "1",
    "FEB": "2",
    "MAR": "3",
    "APR": "4",
    "MAY": "5",
    "JUN": "6",
    "JUL": "7",
    "AUG": "8",
    "SEP": "9",
    "OCT": "10",
    "NOV": "11",
    "DEC": "12"
}


def converter(time):
    """
    时间格式转换

    :param str time: 传入时间格式，邮件中直接获取到的，如"Sat, 8 May 2021 10:23:44 +0800"
    :return: 格式化后时间与日期
    :rtype: str
    """
    temp = time.split(",")
    if len(temp) == 1:
        dt = temp[0].split()
    else:
        # wk = temp[0]
        dt = temp[1].split()
    result = "{year}-{mon}-{date} {time}".format(
        year=dt[2], mon=MONTH[dt[1].upper()], date=dt[0], time=dt[3]
    )
    return result
