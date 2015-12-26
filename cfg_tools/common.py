from cfg_tools import utils
from struct import unpack
import logging


class guid:

    EMPTY = None

    def __init__(self, data):
        self.data = data

    def __str__(self):
        return utils.bytes_to_guid(self.data) if utils.BYTES16_AS_GUID else utils.b2s(self.data)

    def __hash__(self):
        return hash(self.data)

    def __eq__(self, other):
        return self.data == other.data if hasattr(other, 'data') else self.data == other

guid.EMPTY = guid(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')


class ref(guid):

    def __init__(self, data, name):
        super(ref, self).__init__(data)
        self.name = name

    def __str__(self):
        return self.name


class BlockReader:

    CHUNK_SIZE = 4096

    def __init__(self):
        pass

    def _set_position(self, addr):
        pass

    def _read(self, n):
        return None

    def _get_obj_addr_iter(self, address):
        pass

    def read_block(self, addr):
        self._set_position(addr)
        return self._read()


class FileBlockReader(BlockReader):

    PAGE_SIZE = 4096

    def __init__(self, db_file, ):
        self.db_file = db_file

    def _set_position(self, addr):
        self.db_file.seek(self.PAGE_SIZE * addr)

    def _read(self, n=None):
        return self.db_file.read(self.PAGE_SIZE if n is None else n)

    def read_obj(self, obj_addr):
        gen = self.read_obj_iter(obj_addr)
        obj_data = bytearray(b'\x00' * next(gen))

        pos = 0
        for buff in gen:
            obj_data[pos: pos + len(buff)] = buff
            pos += len(buff)

        return obj_data

    def get_data_address(self, info_address):
        data = self.read_block(info_address)
        obj_size = unpack('i', data[8:12])[0]
        if obj_size == 0:
            return 0, None
        block_count = (obj_size - 1) // 0x3ff000 + 1
        blocks_numbers = unpack(str(block_count) + 'i', data[24: 24 + block_count * 4])

        if obj_size == 0 or blocks_numbers is None:
            return obj_size, None
        address = []
        for addr in blocks_numbers:
            block_info = self.read_block(addr)

            sub_blocks_count = unpack('i', block_info[:4])[0]
            address.extend(unpack(str(sub_blocks_count) + 'i', block_info[4: 4 + sub_blocks_count * 4]))
        return obj_size, address

    def read_obj_iter(self, obj_addr, part_size=PAGE_SIZE):
        obj_size, address = self.get_data_address(obj_addr)
        yield obj_size
        if obj_size == 0:
            return
        lost = obj_size
        buff_pos = 0
        buff_lost = 0

        address_iter = iter(address)

        if part_size == self.PAGE_SIZE:
            for addr in address_iter:
                if not addr:
                    return
                self._set_position(addr)
                readed = min(lost, self.PAGE_SIZE)
                lost -= readed
                buff = self._read(readed)
                yield buff
        else:
            while 1:
                if buff_lost < part_size:
                    try:
                        addr = next(address_iter)
                    except StopIteration:
                        break
                    self.db_file.seek(self.PAGE_SIZE * addr)
                    readed = min(lost, self.PAGE_SIZE)
                    lost -= readed
                    if buff_lost:
                        buff = buff[buff_pos:] + self.db_file.read(readed)
                    else:
                        buff = self.db_file.read(readed)
                    buff_pos = 0
                    buff_lost = len(buff)

                yield buff[buff_pos: buff_pos + part_size]
                buff_pos += part_size
                buff_lost -= part_size

logger = logging.getLogger('1CD')