from cfg_tools.common import BlockReader
from struct import unpack
import datetime
import logging


flag7fffff = 0x07fffffff
bytes7fffffff = b'\xff\xff\xff\x7f'


class ReaderCF:

    def __init__(self, stream, packed=True):
        self.stream = stream
        self.reader = BlockReader(self.stream)
        self.packed = packed
        self.files = {}

    def read_item_header(self):
        data = self.stream.read(31)

        return {
            'data_len': int(data[2:10], 16),
            'page_len': int(data[11:19], 16),
            'next_item': data[20:28]
        }

    def read(self):
        logger.debug('Read cf-container')
        self.stream.seek(16)
        item_header = self.read_item_header()
        addresses = []
        while 1:
            block_addr = unpack('III', self.stream.read(12))
            if block_addr[2] != flag7fffff:
                break
            addresses.append(block_addr)

        for addr in addresses:
            self.stream.seek(addr[0])
            item_header = self.read_item_header()
            data = self.stream.read(item_header['data_len'])
            name = data[20:].decode('utf-16').rstrip('\x00')
            self.stream.seek(addr[1])
            item_header = self.read_item_header()
            data = self.stream.read(item_header['data_len'])
            self.files[name] = data
        logger.debug('files: %s' % list(self.files.keys()))

logger = logging.getLogger('1CD')
