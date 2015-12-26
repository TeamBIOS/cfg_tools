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

    def __init__(self, data, name, email=None):
        super(User, self).__init__(data, name)
        self.email = email if email is not None else self.name + '@localhost'
        self.git_name = self.name


class StoreReader(reader_1cd.Reader1CD):

    @staticmethod
    def __write_file(data, file_name):
        with open(file_name, 'wb+') as f:
            f.write(data)
            f.close()

    def __init__(self, file):
        super(StoreReader, self).__init__(file)
        self.users = None
        self.versions = None
        self.meta_classes = None
        self.format_83 = True
        self.root_uid = None
        self.objects_info = None

        self.read()

    def __read_objects(self):
        if self.objects_info is not None:
            for obj in self.objects_info.values():
                obj['files'] = []
            return
        self.objects_info = {}
        for row in self.read_table_by_name('objects', push_headers=False):
            obj_id = row.by_name('OBJID')
            obj = {
                    'guid': obj_id,
                    'class': self.meta_classes[row[1]]
                    if row.by_name('CLASSID') in self.meta_classes
                    else row.by_name('CLASSID'),
            }
            if not self.format_83:
                obj['parent'] = row.by_name('PARENTID')
            self.objects_info[obj_id] = obj
            if obj['parent'] == common.guid.EMPTY:
                self.root_uid = obj_id
        if not self.format_83:
            for obj in self.objects_info.values():
                if obj['parent'] != common.guid.EMPTY and \
                   obj['parent'] != self.root_uid and \
                   obj['parent'] in self.objects_info:
                    obj['parent'] = self.objects_info[obj['parent']]
                else:
                    obj['parent'] = None

    def __set_parents(self, objects):
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
        self.__set_parents(objects)

    def __get_objects_by_version(self, version_number):
        objects = {}
        count = 0
        for row in self.read_table_by_name('HISTORY',
                                           push_headers=False):
            count += 1
            obj_id = row.by_name('OBJID')
            obj = self.objects_info[obj_id]

            if row.by_name('VERNUM') != version_number:
                continue
            objects[obj_id] = obj
            obj['name'] = row.by_name('OBJNAME')
            if self.format_83:
                obj['parent'] = row.by_name('PARENTID')
                obj['files'] = [{
                    'hash': row.by_name('DATAHASH'),
                    'packed': row.by_name('DATAPACKED'),
                    'name': 'info.txt'
                }]
            else:
                obj['files'] = [{
                    'data': row.by_name('OBJDATA'),
                    'packed': row.by_name('DATAPACKED'),
                    'name': 'info.txt'
                }]
        if not self.format_83:
            for obj in objects.values():
                obj['files'][0]['data'] = self.read_blob('HISTORY', obj['files'][0]['data'])

        gen = self.read_table_by_name('EXTERNALS',
                                      push_headers=False,
                                      read_blob=False,
                                      filter_function=lambda x: x.by_name('VERNUM') == version_number)

        for row in gen:
            data = row.by_name('DATAHASH') if self.format_83 else row.by_name('EXTDATA')
            if data is None:
                continue
            obj_id = row.by_name('OBJID')
            if obj_id in objects:
                files = objects[obj_id]['files']
            else:
                obj = objects[obj_id] = self.objects_info[obj_id]
                files = obj['files'] = []

            if self.format_83:
                files.append(
                    {
                        'name': row.by_name('EXTNAME'),
                        'hash': data,
                        'packed': row.by_name('DATAPACKED')
                    })
            else:
                files.append(
                    {
                        'name': row.by_name('EXTNAME'),
                        'data': self.read_blob('EXTERNALS', data),
                        'packed': row.by_name('DATAPACKED')
                    })

        logger.debug('version objects (%s) %s' % (len(objects), ', '.join([item['name'] for item in objects.values()])))
        return [v for v in objects.values()]

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

    def __save_files(self, objects, path, hierarchy=False):
        objects_path = os.path.join(os.path.dirname(self.file_name), 'data', 'objects')
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
                    cf_files = reader_cf.ReaderCF.read_container(io.BytesIO(data))
                    if name == "__form__":
                        self.__write_file(cf_files['form'], obj_path + 'Форма.txt')
                        self.__write_file(cf_files['module'], obj_path + 'Модуль.txt')
                    else:
                        for file_name in cf_files:
                            # if file_name == 'info':
                            #     continue
                            if file_name == 'form' and obj['class'] and obj['class'].type == 'form':
                                self.__write_file(cf_files['form'], obj_path + 'Форма.txt')
                                files.append(obj_path + 'Форма.txt')
                            elif file_name == 'module' and obj['class'] and obj['class'].type == 'form':
                                self.__write_file(cf_files['module'], obj_path + 'Модуль.txt')
                                files.append(obj_path + 'Модуль.txt')
                            else:
                                self.__write_file(cf_files[file_name], '%s%s' % (os.path.join(obj_path, name + '.'), file_name))
                                files.append('%s.%s' % (os.path.join(obj_path, name), file_name))
                else:
                    self.__write_file(data, os.path.join(obj_path, name))
                    files.append(os.path.join(obj_path, name))
        logger.debug('Saved %s files' % len(files))
        return files

    def read(self):
        super(StoreReader, self).read()
        for f in self.get_table_info('HISTORY').fields:
            if f.name == 'OBJDATA':
                self.format_83 = False
                break

    def read_users(self):
        if not self.users:
            gen = self.read_table_by_name('USERS',
                                          read_blob=True,
                                          push_headers=False)
            self.users = {row.by_name('USERID'): User(row.by_name('USERID'), row.by_name('NAME')) for row in gen}

    def read_versions(self):
        self.read_users()
        if not self.versions:
            gen = self.read_table_by_name('VERSIONS',
                                          read_blob=True,
                                          push_headers=False)
            self.versions = {row[0]: {
                'verion': row.by_name('VERNUM'),
                'user': self.users[row.by_name('USERID')],
                'comment': row.by_name('COMMENT'),
                'date': row.by_name('VERDATE')
            } for row in gen}

    def export_version(self, version_number, path, hierarchy=False):
        self.__load_classes()
        self.__read_objects()

        objects = self.__get_objects_by_version(version_number)
        return self.__save_files(objects, path, hierarchy)

    def export_object(self, obj_guid, path, hierarchy=False):
        self.__load_classes()
        self.__read_objects()
        objects = []
        return self.__save_files(objects, path, hierarchy)


logger = logging.getLogger('Store')
