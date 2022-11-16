# -*- coding: utf-8 -*-
# ==============================================================================
# @ Author :
# @ Desc : 附件上传腾讯云
# @ Date : 2021/4/26
# ==============================================================================

from qcloud_cos import CosConfig, CosS3Client

from fetch_core.config import TENCENTCLOUD_CONFIG, LOCAL_ATTACHMENT_ABSPATH
from utils.init_logger import get_logger
from utils.data_processing import etag_rm_quotation

logger = get_logger("tencentcloud")


class TencentCloud:

    def __init__(self):
        self.client = self.cos_client()

    @staticmethod
    def cos_client():
        """
        获取cos客户端对象

        :return: cos客户端对象
        """
        config = CosConfig(Region=TENCENTCLOUD_CONFIG["REGION"],
                           SecretId=TENCENTCLOUD_CONFIG["SECRET_ID"],
                           SecretKey=TENCENTCLOUD_CONFIG["SECRET_KEY"],
                           Token=TENCENTCLOUD_CONFIG["TOKEN"])
        return CosS3Client(config)

    def check_buckets(self):
        # 查询存储桶列表
        return self.client.list_buckets()

    def check_list_objects(self, bucket, prefix):
        # 查询1000对象列表
        return self.client.list_objects(Bucket=bucket, Prefix=prefix)

    def check_all_list_objects(self, bucket, prefix):
        # 循环调用，查询所有的对象
        marker = ""
        while True:
            response = self.client.list_objects(
                Bucket=bucket,
                Prefix=prefix,
                Marker=marker
            )
            print(response['Contents'])
            if response['IsTruncated'] == 'false':
                break
            marker = response['NextMarker']
        return marker

    def attach_upload(self, bucket, file_name, local_file_path, part_size=3, max_thread=5):
        """
        上传附件（支持断电续传）

        :param bucket: 存储桶名称，由 BucketName-APPID 构成
        :param file_name: 对象键（Key），对象在存储桶中的唯一标识
        :param local_file_path: 本地文件的路径名
        :param part_size: 分块上传的分块大小，默认为3MB，单位为MB
        :param max_thread: 分块上传的并发数量，默认为5个线程上传分块
        :return: 上传对象的属性
        :rtype: dict
        """
        client = self.cos_client()
        response = client.upload_file(
            Bucket=bucket,
            LocalFilePath=local_file_path,
            Key=file_name,
            # 例如，在对象的访问域名 examplebucket-1250000000.cos.ap-guangzhou.myqcloud.com/doc/pic.jpg 中，对象键为 doc/pic.jpg
            PartSize=part_size,
            MAXThread=max_thread
        )
        return response["ETag"]

    def delete_object(self, bucket, key):
        """
        删除附件

        :param bucket: 存储桶名称，由 BucketName-APPID 构成
        :param key: 对象键（Key），对象在存储桶中的唯一标识
        :return:
        """
        response = self.client.delete_object(Bucket=bucket, Key=key)
        print(response)

    def download_file(self, bucket, key, file_type):
        """
        文件下载至配置的本地附件文件夹

        :param bucket(string): 存储桶名称.
        :param key(string): COS文件的路径名.
        :param file_type: 文件类型(.pdf, .xlsx...)
        :return:
        """
        file_path = LOCAL_ATTACHMENT_ABSPATH + file_type
        self.cos_client().download_file(Bucket=bucket, Key=key, DestFilePath=file_path)


def upload_with_cos(file_name, file_dir_path=None, part_size=3, max_thread=5):
    """
    附件上传腾讯云

    :param str file_name: 上传附件名称
    :param str file_dir_path: 上传附件目录的绝对路径
    :param int part_size: 分块上传的分块大小，默认为3MB，单位为MB
    :param int max_thread: 分块上传的并发数量，默认为5个线程上传分块
    :return: 上传腾讯云成功返回的etag
    :rtype: str
    """
    if not file_dir_path:
        file_path = LOCAL_ATTACHMENT_ABSPATH + file_name
    else:
        file_path = file_dir_path + file_name

    try:
        etag = TencentCloud().attach_upload(
            bucket=TENCENTCLOUD_CONFIG["BUCKET_NAME"],
            file_name=file_name,
            local_file_path=file_path,
            part_size=part_size,
            max_thread=max_thread
        )
        logger.info(f"附件[{file_name}]上传至腾讯云成功，返回ETag:{etag}")
        return etag_rm_quotation(etag)
    except Exception as err:
        logger.error(f"附件[{file_name}]上传至腾讯云失败！！错误信息: {err}")
