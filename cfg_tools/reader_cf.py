from cfg_tools.common import FileBlockReader
from struct import unpack
import datetime
import logging


flag7fffff = 0x07fffffff
bytes7fffffff = b'\xff\xff\xff\x7f'


class ReaderCF:

    def __init__(self, stream, packed=True):
        self.stream = stream
        self.packed = packed
        self.files = {}

    @staticmethod
    def __read_item_header(stream):
        data = stream.read(31)

        return {
            'data_len': int(data[2:10], 16),
            'page_len': int(data[11:19], 16),
            'next_item': data[20:28]
        }

    @staticmethod
    def read_container(stream):
        stream.seek(16)
        item_header = ReaderCF.__read_item_header(stream)
        addresses = []
        files = {}
        while 1:
            block_addr = unpack('III', stream.read(12))
            if block_addr[2] != flag7fffff:
                break
            addresses.append(block_addr)

        for addr in addresses:
            stream.seek(addr[0])
            item_header = ReaderCF.__read_item_header(stream)
            data = stream.read(item_header['data_len'])
            name = data[20:].decode('utf-16').rstrip('\x00')
            stream.seek(addr[1])
            item_header = ReaderCF.__read_item_header(stream)
            data = stream.read(item_header['data_len'])
            files[name] = data
        return files
        # logger.debug('files: %s' % list(self.files.keys()))

    def read(self):
        self.files = self.read_container(self.stream)

logger = logging.getLogger('1CD')
