from django.core.files.storage import Storage
from django.conf import settings
from fdfs_client.client import Fdfs_client

class FDFSStorage(Storage):
    '''fast dfs 文件存储类'''
    def __init__(self, client_conf=None, base_url=None):
        if client_conf == None:
            self.client_conf = settings.FASTDFS_CLIENT_CONF
        else:
            self.client_conf = client_conf

        if base_url == None:
            self.base_url = settings.DAST_URL
        else:
            self.base_url = base_url

    def _open(self, name, mode='rb'):
        pass

    def _save(self, name, content):
        '''保存文件使用'''
        client = Fdfs_client(self.client_conf)
        ret = client.upload_by_buffer(content.read())
        '''return dict {
            'Group name'      : group_name,
            'Remote file_id'  : remote_file_id,
            'Status'          : 'Upload successed.',
            'Local file name' : '',
            'Uploaded size'   : upload_size,
            'Storage IP'      : storage_ip
        } if success else None'''
        if ret.get('Status') != 'Upload successed.':
            raise Exception('上传文件到 fast dfs失败')
        filename = ret.get('Remote file_id')
        return filename

    def exists(self, name):
        '''django判断文件名是否可以使用'''
        return False

    def url(self, name):
        return self.base_url + name