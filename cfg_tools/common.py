from cfg_tools import utils
from struct import unpack
import logging


PAGE_SIZE = 4096
logger = None

def get_address_list(db_file, block_length):
    pass


def read_block(db_file, address):
    db_file.seek(PAGE_SIZE * address)
    return db_file.read(PAGE_SIZE)


def read_object(db_file, block_info):
    obj_size = unpack('i', block_info[8:12])[0];
    block_count = (obj_size - 1) // 0x3ff000 + 1
    block_numbers = unpack(str(block_count) + 'i', block_info[24: 24 + block_count * 4])
    obj_data = bytearray(b'\x00' * obj_size)

    block_info = read_block(db_file, block_numbers[0])

    sub_blocks_count = unpack('i', block_info[:4])[0]
    sub_blocks = unpack(str(sub_blocks_count) + 'i', block_info[4: 4 + sub_blocks_count * 4])

    pos = 0
    lost = obj_size
    for addr in sub_blocks:
        db_file.seek(PAGE_SIZE * addr)
        to_read = min(lost, PAGE_SIZE)
        obj_data[pos:pos + to_read] = db_file.read(to_read)
        pos += to_read
        lost -= to_read
    return obj_data


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

    def __init__(self, data, present):
        super(ref, self).__init__(data)
        self.present = present

    def __str__(self):
        return self.present


class BlockReader:

    def __init__(self, db_file, ):
        self.db_file = db_file

    def read_block(self, address):
        self.db_file.seek(PAGE_SIZE * address)
        return self.db_file.read(PAGE_SIZE)

    def read_block_info_old(self, block_info):

        obj_size = unpack('i', block_info[8:12])[0]
        if obj_size == 0:
            return 0, 0, None
        block_count = (obj_size - 1) // 0x3ff000 + 1
        block_numbers = unpack(str(block_count) + 'i', block_info[24: 24 + block_count * 4])

        block_info = self.read_block(block_numbers[0])

        sub_blocks_count = unpack('i', block_info[:4])[0]
        sub_blocks = unpack(str(sub_blocks_count) + 'i', block_info[4: 4 + sub_blocks_count * 4])
        return obj_size, block_numbers,  sub_blocks

    def read_obj(self, obj_addr=None, obj_info=None):
        gen = self.read_obj_iter(obj_addr, obj_info)
        obj_data = bytearray(b'\x00' * next(gen))

        pos = 0
        for buff in gen:
            obj_data[pos: pos + len(buff)] = buff
            pos += len(buff)

        # obj_size, block_numbers,  sub_blocks = self.read_block_info(obj_info if obj_info else self.read_block(obj_addr))
        # if obj_size == 0:
        #     return None
        # pos = 0
        # lost = obj_size
        # obj_data = bytearray(b'\x00' * obj_size)
        # for addr in sub_blocks:
        #     self.db_file.seek(PAGE_SIZE * addr)
        #     to_read = min(lost, PAGE_SIZE)
        #     obj_data[pos:pos + to_read] = self.db_file.read(to_read)
        #     pos += to_read
        #     lost -= to_read
        return obj_data

    def read_block_info(self, block_info):

        obj_size = unpack('i', block_info[8:12])[0]
        if obj_size == 0:
            return 0, 0, None
        block_count = (obj_size - 1) // 0x3ff000 + 1
        block_numbers = unpack(str(block_count) + 'i', block_info[24: 24 + block_count * 4])

        return obj_size, block_numbers

    def read_obj_iter(self, obj_addr=None, obj_info=None, part_size=PAGE_SIZE):
        obj_size, blocks_numbers = self.read_block_info(obj_info if obj_info is not None else self.read_block(obj_addr))
        yield obj_size
        if obj_size == 0:
            return
        lost = obj_size
        buff_pos = 0
        buff_lost = 0
        for block_addreses in blocks_numbers:
            block_info = self.read_block(block_addreses)

            sub_blocks_count = unpack('i', block_info[:4])[0]
            sub_blocks = unpack(str(sub_blocks_count) + 'i', block_info[4: 4 + sub_blocks_count * 4])
            if part_size == PAGE_SIZE:
                for addr in sub_blocks:
                    if not addr:
                        return
                    self.db_file.seek(PAGE_SIZE * addr)
                    readed = min(lost, PAGE_SIZE)
                    lost -= readed
                    buff = self.db_file.read(readed)
                    yield buff
            else:
                sub_bl_iter = iter(sub_blocks)

                while 1:
                    if buff_lost < part_size:
                        try:
                            addr = next(sub_bl_iter)
                        except StopIteration:
                            break
                        self.db_file.seek(PAGE_SIZE * addr)
                        readed = min(lost, PAGE_SIZE)
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

    def read_obj_iter__old(self, obj_addr=None, obj_info=None, part_size=PAGE_SIZE):
        obj_size, block_numbers,  sub_blocks = self.read_block_info(obj_info if obj_info else self.read_block(obj_addr))
        yield obj_size
        if obj_size == 0:
            return
        lost = obj_size
        buff_pos = 0
        buff_lost = 0
        sub_bl_iter = iter(sub_blocks)

        while 1:
            if buff_lost < part_size:
                addr = next(sub_bl_iter)
                if not addr:
                    return
                self.db_file.seek(PAGE_SIZE * addr)
                readed = min(lost, PAGE_SIZE)
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