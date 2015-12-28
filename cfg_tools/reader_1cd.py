# -*- coding: utf-8 -*-
from struct import unpack
import logging
import re
from datetime import datetime
import cfg_tools.utils as utils
from cfg_tools.common import FileBlockReader, BlockReader, guid
import os

logger = None


def parse_table_info(info):
    result = re.compile('{"(.+)",(\d+),\n{"Fields",([\s\S]+)},\n{"Indexes"([\s\S]*)},\n{"Recordlock","(\d)"},\n{"Files",(\d+),(\d+),(\d+)}').match(info)

    _iter = re.compile('{"(.+)","(.+)",(\d+),(\d+),(\d+),"(.+)"}').finditer(result.group(3))
    fields = [FieldDesc(name=item.group(1),
                        type=item.group(2),
                        nullable=item.group(3) == '1',
                        length=int(item.group(4)),
                        precision=int(item.group(5)),
                        case_sensitive=item.group(6)) for item in _iter]

    table_desc = TableDesc(name=result.group(1),
                           fields=fields,
                           indexes=[],
                           record_lock=result.group(5) == '1',
                           data_addr=int(result.group(6)),
                           blob_addr=int(result.group(7)),
                           index_addr=int(result.group(8)),
                           text=info)

    return table_desc


types_sz = {
    'GUID': lambda x: 16,
    'B': lambda x: x,
    'L': lambda x: 1,
    'N': lambda x: (x + 2) // 2,
    'NC': lambda x: x * 2,
    'NVC': lambda x: x * 2 + 2,
    'RV': lambda x: 16,
    'NT': lambda x: 8,
    'I': lambda x: 8,
    'DT': lambda x: 7,
}

types_fun = {
    'GUID': lambda f, x:  guid(x),
    'B': lambda f, x: utils.b2s(x),
    'L': lambda f, x: x[0] == 1,
    'N': lambda f, x: utils.bytes_to_int(f, x),
    'NC': lambda f, x: x.decode('utf-16'),
    'NVC': lambda f, x: x[2:2 + 2 * utils.read_struct(x[:2], 'h')[0]].decode('utf-16'),
    'RV': lambda f, x: utils.read_struct(x, '4I'),
    'NT': lambda f, x: utils.read_struct(x, '2I'),
    'I': lambda f, x: utils.read_struct(x, '2I'),
    'DT': lambda f, x: utils.b2s(x) if x[4:6] == b'\x00\x00' else datetime.strptime(utils.b2s(x), '%Y%m%d%H%M%S')

}


class FieldDesc:

    def __init__(self, **kwargs):
        self.name = kwargs.pop('name')
        self.type = kwargs.pop('type')
        self.nullable = kwargs.pop('nullable')
        self.length = kwargs.pop('length')
        self.precision = kwargs.pop('precision')
        self.case_sensitive = kwargs.pop('case_sensitive') == 'CS' if 'case_sensitive' else False
        self.offset = 0
        self.byte_size = 0

    def print_info(self):
        print('          name:', self.name)
        print('          type:', self.type)
        print('      nullable:', self.nullable)
        print('        length:', self.length)
        print('     precision:', self.precision)
        print('case_sensitive:', self.case_sensitive)
        print('        offset:', self.offset)
        print('     byte_size:', self.byte_size)


class TableDesc:

    def __init__(self, **kwargs):
        self.text           = kwargs.pop('text')
        self.name           = kwargs.pop('name')
        self.fields         = kwargs.pop('fields', [])
        self.indexes        = kwargs.pop('indexes', [])
        self.record_lock    = kwargs.pop('record_lock', False)
        self.data_addr      = kwargs.pop('data_addr', 0)
        self.blob_addr      = kwargs.pop('blob_addr', 0)
        self.index_addr     = kwargs.pop('index_addr', 0)
        self.row_size = 0
        self.table_size = 0
        self.rows_count = 0
        self.blob_data = None
        self.content_data = None
        self.fields_indexes = None
        self.blob_fields = None

        self.blob_reader = BlobReader(self.blob_addr) if self.blob_addr else None

    def init(self):
        self.row_size = 1
        self.blob_fields = []

        version_pos = -1
        for field in self.fields:
            if field.type == 'B' and field.length == 16:
                field.type = 'GUID'
            elif field.type == 'RV':
                version_pos = self.fields.index(field)

        if version_pos > 1:
            self.fields.insert(0, self.fields.pop(version_pos))

        ind = 0
        self.fields_indexes = {}
        for field in self.fields:
            self.fields_indexes[field.name.upper()] = ind
            if field.type == 'NT' or field.type == 'I':
                self.blob_fields.append(ind)
            ind += 1
            field.byte_size = types_sz[field.type](field.length)
            if field.nullable:
                field.byte_size += 1
            field.func = types_fun[field.type]

            field.offset = self.row_size
            self.row_size += field.byte_size

    def print_info(self):
        print('          name:', self.name)
        print(' blob contains:', self.blob_addr != 0)
        print('index contains:', self.index_addr != 0)
        print('   record_lock:', self.record_lock)
        print('      row_size:', self.row_size)
        print('    table_size:', self.table_size)
        print('    rows_count:', self.rows_count)

    def index_by_field_name(self, field_name):
        return self.fields_indexes[field_name.upper()]

    def init_row(self):
        return Row(self)


class Row(list):

    def __init__(self, table):
        self.table = table
        self.extend([None] * len(table.fields))

    def by_name(self, name):
        return self[self.table.index_by_field_name(name)]

    def get_blob(self, name):
        val = self.by_name(name)
        if isinstance(val, tuple):
            val = self.table.blob_reader.read_obj(val)
            self[self.table.index_by_field_name(name)] = val
        return val


class BlobReader(BlockReader):

    CHUNK_SIZE = 256
    reader = None

    def __init__(self, info_address):
        self.cache = {}
        self.ratio = self.reader.CHUNK_SIZE // self.CHUNK_SIZE
        self.blob_table_addr = info_address
        self.address = self.reader.get_data_address(self.blob_table_addr)[1]

    def read_block(self, addr):
        block_num = addr // self.ratio
        if block_num not in self.cache:
            data = self.reader.read_block(self.address[block_num])
            self.cache[block_num] = data
            if len(self.cache) > 100:
                self.cache.clear()
        else:
            data = self.cache[block_num]
        offset = (addr % self.ratio) * self.CHUNK_SIZE
        return data[offset: offset + self.CHUNK_SIZE]

    def read_obj(self, blob_info):
        if blob_info and blob_info[0]:
            lost = blob_info[1]
            pos = blob_info[0]
            val = bytearray(b'\x00' * lost)
            offset = 0
            while 1:
                readed = min(lost, 250)

                block = self.read_block(pos)
                val[offset: offset + readed] = block[6: 6 + readed]
                lost -= readed
                offset += readed
                pos = unpack('I', block[:4])[0]
                if pos == 0:
                    break
            return val
        else:
            return None


class Reader1CD:

    __instance = None

    def __new__(cls, file_name):
        if Reader1CD.__instance is None:
            Reader1CD.__instance = object.__new__(cls)
            Reader1CD.__instance.__init__(file_name)
        return Reader1CD.__instance

    def __init__(self, file_name):
        self.file_name = file_name
        self.db_file = None
        self.tables = None
        self.version = None
        self.baseLength = None
        self.lang = None
        self.__open_reader()
        BlobReader.reader = self.reader

    def __del__(self):
        if self.db_file:
            self.db_file.close()
            self.db_file = None

    def __open_reader(self):
        if not os.path.exists(self.file_name):
            raise Exception('Файл хранилища не существует')

        self.db_file = open(self.file_name, 'rb')
        self.reader = FileBlockReader(self.db_file)

    def __read_root_object(self, obj_addr):
        obj_data = self.reader.read_obj(obj_addr)
        root_info = utils.read_struct(obj_data, '32si')
        lang = root_info[0].rstrip(b'\x00').decode()

        address_tables_info = utils.read_struct(obj_data, str(root_info[1]) + 'i', 36)
        tables = []
        for addr in address_tables_info:
            tables.append(parse_table_info(self.reader.read_obj(addr).decode('UTF-16')))

        for table in tables:
            table.init()
        return tables, lang

    def read(self):
        block_num = 0
        buffer = self.reader.read_block(0)
        while buffer:
            block_info = utils.read_struct(buffer, '8s3iI')
            if block_info[0] == b'1CDBMSV8':
                data = utils.read_struct(buffer, '8s4bIi')
                self.version = '%s.%s.%s.%s' % tuple(data[1:5])
                self.baseLength = data[5]
            elif block_info[0] == b'1CDBOBV8':
                if block_info[4] == 0:
                    pass
                else:
                    tables, self.lang = self.__read_root_object(block_num)
                    self.tables = {table.name.upper(): table for table in tables}
                    break
            block_num += 1
            buffer = self.reader.read_block(block_num)
        logger.debug('version: %s' % self.version)
        logger.debug('lang: %s' % self.lang)
        logger.debug('base length: %s' % self.baseLength)
        logger.debug('tables count: %s' % len(self.tables))

    def print_tables(self, print_fields=1):
        for table in self.tables:
            print(table.name)
            if print_fields:
                for field in table.fields:
                    print('\t%s (%s)' % (field.name, field.type))

    def read_tables_size(self):
        for table_desc in self.tables.values():
            gen = self.reader.read_obj_iter(obj_addr=table_desc.data_addr, part_size=table_desc.row_size)
            self.__set_table_size(table_desc, gen)

    @staticmethod
    def __set_table_size(table_desc, gen):
        table_desc.table_size = next(gen)
        table_desc.rows_count = table_desc.table_size//table_desc.row_size

    def read_table_by_name(self, table, read_blob=False, filter_function=None, push_headers=True):
        logger.debug('Read table: %s' % table.upper())
        table_desc = self.get_table_info(table)

        gen = self.reader.read_obj_iter(obj_addr=table_desc.data_addr, part_size=table_desc.row_size)

        self.__set_table_size(table_desc, gen)

        read_blob = read_blob and table_desc.blob_addr
        if push_headers:
            yield table_desc.fields

        offset = 0
        blob_fields = table_desc.blob_fields
        for row_data in gen:
            values = table_desc.init_row()
            if row_data[0] == 1:
                continue
            i = 0
            for field in table_desc.fields:
                if field.nullable:
                    if row_data[field.offset] == 0:
                        val = None
                    else:
                        val = field.func(field, row_data[field.offset + 1:field.offset + field.byte_size])
                else:
                    val = field.func(field, row_data[field.offset:field.offset + field.byte_size])

                values[i] = val
                i += 1
            offset += table_desc.row_size
            if not filter_function or filter_function(values):
                if read_blob:  # BLOB
                    for i in blob_fields:
                        val = values[i]
                        val = self.__read_blob(table_desc, val)
                        if val and table_desc.fields[i].type == 'NT':
                            val = val.decode('utf-16')
                        values[i] = val
                yield values

    def __read_blob(self, table_desc, blob_info):
        return table_desc.blob_reader.read_obj(blob_info)
        if table_desc.blob_data is None:
            table_desc.blob_data = self.reader.read_obj(table_desc.blob_addr)

        if blob_info and blob_info[0]:
            lost = blob_info[1]
            pos = blob_info[0]
            val = bytearray(b'\x00' * lost)
            offset = 0
            while 1:
                pos *= 256
                readed = min(lost, 250)
                val[offset: offset + readed] = table_desc.blob_data[pos + 6: pos + 6 + readed]
                lost -= readed
                offset += readed
                pos = unpack('I', table_desc.blob_data[pos: pos + 4])[0]
                if pos == 0:
                    break
            return val
        else:
            return None

    def read_blob(self, table, blob_info):
        table_desc = self.get_table_info(table)
        if table_desc is None:
            raise Exception('Не найдена таблица с именем "%s"' % table)
        return self.__read_blob(table_desc, blob_info)

    def get_table_info(self, table_name):
        table_desc = self.tables[table_name.upper()]

        if table_desc is None:
            raise Exception('Не найдена таблица с именем "%s"' % table_name)
        else:
            return table_desc


logger = logging.getLogger('1CD')

