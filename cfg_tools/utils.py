import binascii
import zlib
from struct import unpack, calcsize
from datetime import datetime

BYTES16_AS_GUID = True


def read_struct(buffer, frmt, offset=0):
    if offset:
        return unpack(frmt, buffer[offset:offset + calcsize(frmt)])
    else:
        return unpack(frmt, buffer[:calcsize(frmt)])


def bytes_to_guid(data):
    hex_str = b2s(data[8:]) + b2s(bytes(reversed(data[:8])))
    return '%s-%s-%s-%s-%s' % (hex_str[24:], hex_str[20:24], hex_str[16:20], hex_str[:4], hex_str[4:16])


def guid_to_bytes(guid_str):
    parts = guid_str.split('-')
    data = binascii.unhexlify(''.join([parts[2], parts[1], parts[0], parts[3], parts[4]]))
    return bytes(reversed(data[:8])) + data[8:]


def b2s(data):
    return binascii.hexlify(data).decode()


def bytes_to_int(type_info, data):
    hex_str = b2s(data)
    if type_info.precision:
        return float(''.join(['-' if hex_str[0] == '0' else '+',
                              hex_str[1: -type_info.precision],
                              '.',
                              hex_str[-type_info.precision:]]))
    else:
        return int(''.join(['-' if hex_str[0] == '0' else '+',
                            hex_str[1:type_info.length + 1]]))


def bytes_to_datetime(type_info, data):
    byte_str = b2s(data)
    if data[:2] == b'\x00\x00':
        # TODO Убрать исключение после теста
        raise Exception("Ошибка преобразования даты. Значение: " + byte_str)
    else:
        return datetime.strptime(byte_str, '%Y%m%d%H%M%S')

def print_table_content(gen, with_headers=True):
    if with_headers:
        fields = next(gen)
        print('|'.join(['{0:20}{2:3}({3:4}{1:3})'.format(item.name, item.length, item.type, 'NULL' if item.nullable else '0') for item in fields]))
        pattern = '|'.join(['{%s:32}' % i for i in range(len(fields))])
    else:
        pattern = None
    for values in gen:
        if not pattern:
            pattern = '|'.join(['{%s:32}' % i for i in range(len(values))])
        print(pattern.format(*[str(val) if val is not None else '' for val in values]))


def save2cvs(gen, file_name):
    fields = next(gen)
    pattern = ','.join(['"{%s}"' % i for i in range(len(fields))]) + '\n'
    with open(file_name, 'w') as fl:
        fl.write(pattern.format(*[item.name for item in fields]))
        for values in gen:
            fl.write(pattern.format(*[str(val) if val is not None else '' for val in values]))
        fl.close()


def inflate(source_file, dest_file):
    with open(source_file, 'rb') as source:
        dest = open(dest_file, 'wb+')
        dest.write(zlib.decompress(source.read(), -15))
        dest.close()
        source.close()


def inflate_inmemory(source):
    return zlib.decompress(source, -15)

