# -*- coding: utf-8 -*-
from cfg_tools import utils
from struct import unpack
import logging


class Guid:
    """
    Описывает GUID 1с: данные 16 байт
    Реализовано правильное отображение, сравнение и вычисление хэш функции
    """
    EMPTY = None

    def __init__(self, data):
        self.data = data

    def __str__(self):
        return utils.bytes_to_guid(self.data) if utils.BYTES16_AS_GUID else utils.b2s(self.data)

    def __hash__(self):
        return hash(self.data)

    def __eq__(self, other):
        return self.data == other.data if hasattr(other, 'data') else self.data == other

Guid.EMPTY = Guid(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')


class Ref(Guid):
    """
    Базовый класс для ссылочных объектов
    Ссылка - GUID
    """
    def __init__(self, data, name):
        """
        :param data: Данные GUID'а
        :param name: Представление ссылки
        :return:
        """
        super(Ref, self).__init__(data)
        self.name = name

    def __str__(self):
        return self.name


class BlockReader:
    """
    Базовый класс для блочных чтецов
    """
    CHUNK_SIZE = 4096

    def __init__(self):
        pass

    def _set_position(self, addr):
        """
        Установка позиции в потоке
        :param addr: Позиция блока
        :return:
        """
        pass

    def _read(self, n):
        """
        Чтение блока длинной n байт
        :param n: длинна блока
        :return:
        """
        return None

    def read_block(self, addr):
        """
        Чтение блока по адресу(номеру)
        :param long addr: адрес(номер блока)
        :return:
        """
        self._set_position(addr)
        return self._read()

    def read_obj_iter(self, *args):
        """
        Получение итератора для объекта находящегося по адресу
        Первая итерация возвращает размер объекта, а потом данные
        :param args: список параметров
        :return:
        """
        pass

    def read_obj(self, *args):
        """
        Чтитает объект из потока
        :param args: список параметров
        :return:
        """
        gen = self.read_obj_iter(*args)
        if gen is None:
            return None
        try:
            obj_data = bytearray(b'\x00' * next(gen))
        except StopIteration:
            return None

        pos = 0
        for buff in gen:
            obj_data[pos: pos + len(buff)] = buff
            pos += len(buff)

        return obj_data


logger = logging.getLogger('1CD')