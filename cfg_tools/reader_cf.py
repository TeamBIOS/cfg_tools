from struct import unpack
import datetime
import logging


flag7fffff = 0x07fffffff
bytes7fffffff = b'\xff\xff\xff\x7f'


class ReaderCF:
    """
    Читает содержимое cf, epf, epr файлов-контейнеров
    """
    def __init__(self, stream, packed=True):
        self.stream = stream
        self.packed = packed
        self.files = {}

    @staticmethod
    def __read_item_header(stream):
        """
        Считывает заголовок блока
        :param stream: Поток чтения
        :return dict: Описание блока
        """
        data = stream.read(31)

        return {
            'data_len': int(data[2:10], 16),
            'page_len': int(data[11:19], 16),
            'next_item': data[20:28]
        }

    @staticmethod
    def read_container(stream):
        """
        Читает данные(объекты) контейнера из потока
        :param stream: Поток чтения
        :return dict: Имя документа - данные документа
        """
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

    @staticmethod
    def read_file(file_name):
        """
        Читает данные(объекты) контейнера из файла
        :param file_name: Имя файла контейнера
        :return dict: Имя документа - данные документа
        """
        with open(file_name, 'rb') as stream:
            data = ReaderCF.read_container(stream)
            stream.close()
            return data

    def read(self):
        self.files = self.read_container(self.stream)

logger = logging.getLogger('1CD')
