# -*- coding: utf-8 -*-
from struct import unpack
import logging
import re
from datetime import datetime
import cfg_tools.utils as utils
from cfg_tools.common import BlockReader, guid, PAGE_SIZE


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

    def init_table(self):
        self.row_size = 1
        version_pos = -1
        for field in self.fields:
            if field.type == 'B' and field.length == 16:
                field.type = 'GUID'
            elif field.type == 'RV':
                version_pos = self.fields.index(field)

        if version_pos > 1:
            self.fields.insert(0, self.fields.pop(version_pos))

        for field in self.fields:
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


class Reader1CD:

    __instance = None

    def __new__(cls, file_name):
        if Reader1CD.__instance is None:
            Reader1CD.__instance = object.__new__(cls)
            Reader1CD.__instance.__init__(file_name)
        return Reader1CD.__instance

    def __init__(self, file_name):
        self.file_name = file_name
        self.db_file = open(file_name, 'rb')
        self.reader = BlockReader(self.db_file)
        self.tables = None
        self.version = None
        self.baseLength = None
        self.lang = None

    def __del__(self):
        if self.db_file:
            self.db_file.close()
            self.db_file = None

    def __read_root_object(self, block_info):
        obj_data = self.reader.read_obj(obj_info=block_info)
        root_info = utils.read_struct(obj_data, '32si')
        lang = root_info[0].rstrip(b'\x00').decode()

        address_tables_info = utils.read_struct(obj_data, str(root_info[1]) + 'i', 36)
        tables = []
        for addr in address_tables_info:
            tables.append(parse_table_info(self.reader.read_obj(addr).decode('UTF-16')))
        return tables, lang

    def read(self):
        buffer = self.db_file.read(PAGE_SIZE)
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
                    tables, self.lang = self.__read_root_object(buffer)
                    self.tables = {table.name.lower(): table for table in tables}
                    break

            buffer = self.db_file.read(PAGE_SIZE)
        logger.info('version: %s' % self.version)
        logger.info('lang: %s' % self.lang)
        logger.info('base length: %s' % self.baseLength)
        logger.info('tables count: %s' % len(self.tables))

    def print_tables(self, print_fields=1):
        for table in self.tables:
            print(table.name)
            if print_fields:
                for field in table.fields:
                    print('\t%s (%s)' % (field.name, field.type))

    def read_tables_size(self):
        for table_desc in self.tables.values():
            table_desc.init_table()
            gen = self.reader.read_obj_iter(obj_addr=table_desc.data_addr, part_size=table_desc.row_size)
            self.__set_table_size(table_desc, gen)

    @staticmethod
    def __set_table_size(table_desc, gen):
        table_desc.table_size = next(gen)
        table_desc.rows_count = table_desc.table_size//table_desc.row_size

    def read_table_by_name(self, table, read_blob=False, filter_function=None, push_headers=True):
        logger.debug('Read table: %s' % table.upper())
        table_desc = self.get_table_info(table)
        table_desc.init_table()
        gen = self.reader.read_obj_iter(obj_addr=table_desc.data_addr, part_size=table_desc.row_size)

        self.__set_table_size(table_desc, gen)

        read_blob = read_blob and table_desc.blob_addr
        if push_headers:
            yield table_desc.fields

        offset = 0
        blob_fields = []
        for i in range(len(table_desc.fields)):
            if table_desc.fields[i].type == 'NT' or table_desc.fields[i].type == 'I':
                blob_fields.append(i)
        for row_data in gen:
            values = [None] * len(table_desc.fields)
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
                        if val and field.type == 'NT':
                            val = val.decode('utf-16')
                        values[i] = val
                yield values

    def __read_blob(self, table_desc, blob_info):
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
        table_desc = self.get_table_info(table.lower())
        if table_desc is None:
            raise Exception('Не найдена таблица с именем "%s"' % table)
        return self.__read_blob(table_desc, blob_info)

    def get_table_info(self, table_name):
        table_desc = self.tables[table_name.lower()]

        if table_desc is None:
            raise Exception('Не найдена таблица с именем "%s"' % table_name)
        else:
            return table_desc

logger = logging.getLogger('1CD')

