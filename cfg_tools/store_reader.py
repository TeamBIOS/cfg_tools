import cfg_tools.reader_1cd as reader_1cd
import os
from cfg_tools import utils
import xml.etree.ElementTree as etree
from cfg_tools.common import ref
from cfg_tools import reader_cf
import io
import logging
from cfg_tools import common


logger = None


class User(common.ref):

    def __init__(self, data, present, email=None):
        super(User, self).__init__(data, present)
        self.email = email if email is not None else present + '@localhost'


class StoreReader(reader_1cd.Reader1CD):

    def __init__(self, file):
        super(StoreReader, self).__init__(file)
        self.users = None
        self.versions = None
        self.meta_classes = None
        self.format_83 = True
        self.root_uid = None

        self.objects_info = None

    def read(self):
        super(StoreReader, self).read()
        for f in self.get_table_info('history').fields:
            if f.name == 'OBJDATA':
                self.format_83 = False
                break

    def read_versions(self):
        if not self.users:
            gen = self.read_table_by_name('USERS',
                                          read_blob=True,
                                          push_headers=False)
            self.users = {row[0]: User(row[0], row[1]) for row in gen}
        if not self.versions:
            gen = self.read_table_by_name('VERSIONS',
                                          read_blob=True,
                                          push_headers=False)
            self.versions = {row[0]: {
                'verion': row[0],
                'user': self.users[row[1]],
                'comment': row[6] if self.format_83 else row[3],
                'date': row[2]
            } for row in gen}

    def export_version(self, version_number, path, hierarchy=False):
        objects_path = os.path.join(os.path.dirname(self.file_name), 'data', 'objects')
        self.__load_classes()
        self.__read_objects()
        logger.info('Export version: %s' % version_number)

        objects = self.__get_objects_by_version(version_number)
        files = []
        for obj in objects:
            meta_class = obj['class']
            full_name = ''
            parent = obj
            while 1:
                if hierarchy:
                    full_name = str(parent['class'].multiple) + os.path.sep + parent['name'] + os.path.sep + full_name
                else:
                    full_name = str(parent['class'].name) + '.' + parent['name'] + '.' + full_name
                parent = parent['parent']
                if parent is None:
                    break
            logger.debug('Export %s' % full_name)
            obj_path = os.path.join(path, full_name)
            if hierarchy and not os.path.exists(obj_path):
                os.makedirs(obj_path)
            for file in obj['files']:
                name = file['name']
                if '.' in name and name[name.rindex('.'):] in meta_class.files:
                    name = meta_class.files[name[name.rindex('.'):]]

                if self.format_83:
                    source = os.path.join(objects_path, file['hash'][:2], file['hash'][2:])
                    with open(source, 'rb') as f:
                        data = f.read()
                        f.close()
                else:
                    data = file['data']
                if data is None:
                    continue
                if file['packed']:
                    data = utils.inflate_inmemory(data)

                if data[:4] == reader_cf.bytes7fffffff:
                    cf_reader = reader_cf.ReaderCF(io.BytesIO(data))
                    cf_reader.read()
                    if name == "__form__":
                        self.__write_file(cf_reader.files['form'], obj_path + 'Форма.txt')
                        self.__write_file(cf_reader.files['module'], obj_path + 'Модуль.txt')
                    else:
                        for file_name in cf_reader.files:
                            if file_name == 'info':
                                continue
                            elif file_name == 'form' and obj['class'] and obj['class'].type == 'form':
                                self.__write_file(cf_reader.files['form'], obj_path + 'Форма.txt')
                                files.append(obj_path + 'Форма.txt')
                            elif file_name == 'module' and obj['class'] and obj['class'].type == 'form':
                                self.__write_file(cf_reader.files['module'], obj_path + 'Модуль.txt')
                                files.append(obj_path + 'Модуль.txt')
                            else:
                                self.__write_file(data, '%s%s.txt' % (os.path.join(obj_path, name + '.'), file_name))
                                files.append('%s%s.txt' % (os.path.join(obj_path, name + '.'), file_name))
                else:
                    self.__write_file(data, os.path.join(obj_path, name + '.txt'))
                    files.append(os.path.join(obj_path, name + '.txt'))
        return files

    @staticmethod
    def __write_file(data, file_name):
        with open(file_name, 'wb+') as f:
            f.write(data)
            f.close()

    def __read_objects(self):
        if self.objects_info is not None:
            for obj in self.objects_info.values():
                obj['files'] = []
            return
        self.objects_info = {}
        for row in self.read_table_by_name('objects', push_headers=False):
            obj = {
                    'guid': row[0],
                    'class': self.meta_classes[row[1]] if row[1] in self.meta_classes else row[1],
            }
            if not self.format_83:
                obj['parent'] = row[2]
            self.objects_info[row[0]] = obj
            if obj['parent'] == common.guid.EMPTY:
                self.root_uid = row[0]
        if not self.format_83:
            for obj in self.objects_info.values():
                if obj['parent'] != common.guid.EMPTY and \
                   obj['parent'] != self.root_uid and \
                   obj['parent'] in self.objects_info:
                    obj['parent'] = self.objects_info[obj['parent']]
                else:
                    obj['parent'] = None

    def __set_parrents(self, objects):
        if len(objects):
            return
        parents = {}
        for o in objects:
            if o['parent'] in self.objects_info:
                o['parent'] = self.objects_info[o['parent']]
            else:
                if o['parent'] not in parents:
                    parents[o['parent']] = [o]
                else:
                    parents[o['parent']].append(o)
        gen = self.read_table_by_name('objects',
                                      filter_function=lambda x: x[6] in parents,
                                      push_headers=False)
        objects = []
        for row in gen:
            parent_obj = self.__create_obj(self, row)
            self.objects_info[row[0]] = parent_obj
            for o in parents[row[0]]:
                o['parent'] = parent_obj
            objects.extend(parents[row[0]])
        self.__set_parrents(objects)

    def __get_objects_by_version(self, version_number):
        objects = []
        for row in self.read_table_by_name('history',
                                           push_headers=False):
            obj = self.objects_info[row[0]]
            obj['name'] = row[6] if self.format_83 else row[5]
            if self.format_83:
                obj['parent'] = row[4]

            if row[1] != version_number:
                continue
            objects.append(obj)
            if self.format_83:
                obj['name'] = row[6]
                obj['parent'] = row[4]
                obj['files'] = [{
                    'hash': row[11],
                    'packed': row[9],
                    'name': 'info'
                }]
            else:
                obj['name'] = row[5]
                obj['files'] = [{
                    'data': row[9],
                    'packed': row[8],
                    'name': 'info'
                }]
        if not self.format_83:
            for obj in objects:
                obj['files'][0]['data'] = self.read_blob('history', obj['files'][0]['data'])

        gen = self.read_table_by_name('externals',
                                      push_headers=False,
                                      read_blob=not self.format_83,
                                      filter_function=lambda x: x[1] == version_number)
        if self.format_83:
            for row in gen:
                if row[6] is None:
                    continue
                self.objects_info[row[0]]['files'].append(
                    {
                        'name': row[2],
                        'hash': row[6],
                        'packed': row[4],
                    })
        else:
            for row in gen:
                if row[5] is None:
                    continue
                self.objects_info[row[0]]['files'].append(
                    {
                        'name': row[2],
                        'data': row[5],
                        'packed': row[4],
                    })

        return objects

    def __load_classes(self):
        if self.meta_classes:
            return
        tree = etree.parse(os.path.join(os.path.dirname(__file__), 'classID.xml'))
        file_groups = {
            group.attrib['name']: {
                                    file.attrib['id']: file.attrib['name']
                                    for file in group.getiterator('file')}
            for group in tree.getiterator('type')
        }
        self.meta_classes = {}
        for cls in tree.getiterator('class'):
            meta_class = ref(
                utils.guid_to_bytes(cls.attrib['id']),
                cls.attrib['single'])
            meta_class.type = cls.attrib['type'] if 'type' in cls.attrib else None
            meta_class.multiple = cls.attrib['multiple'] if 'multiple' in cls.attrib else meta_class.name
            if meta_class.type is not None and meta_class.type in file_groups:
                meta_class.files = file_groups[meta_class.type]
            else:
                meta_class.files = []
            self.meta_classes[utils.guid_to_bytes(cls.attrib['id'])] = meta_class

logger = logging.getLogger('Store')