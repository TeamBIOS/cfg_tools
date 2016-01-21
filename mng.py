# -*- coding: utf-8 -*-
from ensurepip import version

from cfg_tools import store_reader as store_reader
from git_mng import GitMng
import logging
import configparser
import datetime
import os


class Mng:
    """
    Управление процессом выгрузки версий и помещением в GIT
    """
    push_step = 0

    @staticmethod
    def init_log(log_level, file_name=None):
        """
        Выполняет инициализацию логера, необходимо выполнить перед первым выводом в лог
        :param int log_level: Уровень вывод лога
        :param str file_name: Имя файла вывода. если не указа будет выводиться в консоль
        :return:
        """
        logging.basicConfig(level=log_level,
                            format='%(asctime)-15s %(levelname)7s: %(name)5s: %(message)s',
                            handlers=[logging.StreamHandler()
                                      if file_name is None else
                                      logging.FileHandler(file_name, encoding='utf-8')])

    def __init__(self, config_file=None, store_path=None, local_path=None, remote_url=None):
        """
        Инициализация
        :param str config_file: Имя файла конфигурации, если указан другие параметры игнорируются
        :param str store_path: путь к файлу хранилища
        :param str local_path: путь к каталогу локального репозитория
        :param str remote_url: адрес удаленного репозитория
        :return:
        """
        self.local_repo = None
        self.store_path = None
        self.remote_repo_url = None
        if config_file:
            self.__load_config(config_file)
        else:
            self.local_repo = local_path
            self.store_path = store_path
            self.remote_repo_url = remote_url
        self.export_to_remote_repo = True if self.remote_repo_url else False
        self.reader = None
        self.repo = GitMng(self.local_repo, self.remote_repo_url)

    def __load_config(self, file_name):
        """
        Загрузка настройки выгрузки
        :param file_name: Имя файла настройки
        :return:
        """
        config = configparser.ConfigParser()
        config.read(file_name, 'utf-8')
        for sect_name in config.sections():
            section = config[sect_name]
            if sect_name.upper() == 'LOG':
                log_level = getattr(logging, section['level'], logging.DEBUG) if 'level' in section else logging.DEBUG
                file_name = section['file'] if 'file' in section else None
                if file_name is not None and '%' in file_name:
                    file_name = datetime.datetime.now().strftime(file_name)
                self.init_log(log_level, file_name)
            else:
                if 'store' in section:
                    self.store_path = section['store']
                if 'local_repo' in section:
                    self.local_repo = section['local_repo']
                if 'remote_repo' in section:
                    self.remote_repo_url = section['remote_repo']
        logger.info('Загружены настройки')

    def __init_reader(self):
        """
        инициалиция ридера хранилища
        :return:
        """
        if self.reader is None:
            self.reader = store_reader.StoreReader(self.store_path)

    def __before_export(self):
        """
        Вызывается перед выгрузкой версий
        :return:
        """
        if not os.path.exists(os.path.join(self.local_repo, '.git')):
            raise Exception('Не найден репозиторий. Для создания репозитория используйте команду "init"')

        self.load_authors()
        self.read_versions()

    def _commit(self, version_info):
        """
        Выполняет запись изменений в репозиторий
        :param dict version_info: Информация о версии(номер, пользователь, комментарий...)
        :return:
        """
        self.repo.add()
        logger.info('Commiting version: %s' % version_info['verion'])
        self.repo.commit(version=version_info['verion'],
                         msg=version_info['comment'] if version_info['comment'] is not None else '<no comment>',
                         author=version_info['user'].git_name,
                         email=version_info['user'].email,
                         date=version_info['date'])

    def __save_exported_version_info(self, version):
        """
        Сохранение информации о выгруженной версии в файл в каталоге репозитория
        :param int version: Номер версии
        :return:
        """
        with open(self.__last_version_file(), 'w') as f:
            f.write(str(version))
            f.close()

    def __last_version_file(self):
        """
        Получение имени файла сохранения версии
        :return: Имя файла версии
        """
        return os.path.join(self.local_repo, 'last_version.txt')

    def init_repo(self, check_exist=True):
        """
        инициализация репозитория и создание служебных файлов
        :param check_exist: Проверка на существование репозитория
        :return:
        """
        if check_exist and os.path.exists(os.path.join(self.local_repo, '.git')):
            logger.info('Репозиторий уже существует, инициализация не выполнена')
            return
        self.repo.init()
        if self.export_to_remote_repo:
            self.repo.pull()
        with open(os.path.join(self.local_repo, '.gitignore'), 'w+') as f:
            f.write('# Service files')
            f.write('authors.csv')
            f.close()
        self.load_authors()
        logger.info('Репозиторий инициализирован')

    def load_authors(self):
        """
        Загрузка авторов из файла-соответствия
        Если найдены пользователи отсутствующие в файле, они будут дописаны в файл
        :return:
        """
        self.__init_reader()
        authors = {}
        file_name = os.path.join(self.local_repo, 'authors.csv')
        if os.path.exists(file_name):
            with open(file_name, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    words = line.split(';')
                    if len(words) == 3:
                        authors[words[0]] = (words[1], words[2])
            f.close()
        self.__init_reader()
        self.reader.read_users()
        new_users = False
        for user in self.reader.users.values():
            if user.name in authors:
                user.git_name = authors[user.name][0].strip()
                user.email = authors[user.name][1].strip()
            else:
                new_users = True

        if new_users:
            logger.info('Создан/обновлен файл соответствия пользователей')
            with open(file_name, 'w', encoding='utf-8') as f:
                for user in self.reader.users.values():
                    f.write('%s; %s; %s\n' % (user.name, user.git_name, user.email))
                f.close()

    def read_versions(self):
        """
        Считывает версии хранилища
        :return:
        """
        self.__init_reader()
        self.reader.read_versions()
        return self.reader.versions

    def export_version(self, version, commit=True):
        """
        Выгрузка версии хранилища по номеру
        :param int version: Номер версии
        :param commit: Помещать в репозиторий
        :return:
        """
        self.__before_export()
        if version not in self.reader.versions:
            logging.error('Версия %s не найдена' % version)
            return False
        version_info = self.reader.versions[version]
        logger.info('================================== Export version: %s' % version)
        logger.debug(str(version_info))
        self.reader.export_version(version, self.local_repo, True)
        self.__save_exported_version_info(version)
        if commit:
            self._commit(version_info)

    def export_versions(self, start_version, last_version=None, commit=True):
        """
        Экспорт интервала версий(включительно), по окончании делается push
        :param int start_version: начальная версия
        :param int last_version: Последная версия
        :param commit: Помещать в репозиторий
        :return:
        """
        self.__before_export()
        count = 0
        for version_data in self.reader.export_versions(self.local_repo, start_version, last_version, True):
            version = version_data[0]
            version_info = self.reader.versions[version]
            self.__save_exported_version_info(version)
            if commit:
                self._commit(version_info)
            count += 1
            if commit and self.push_step and count == self.push_step:
                count = 0
                if self.export_to_remote_repo:
                    self.repo.push()
        if commit and self.export_to_remote_repo:
            self.repo.push()

    def export_new(self, commit=True):
        """
        Выгрузка новых версий.
        Выполняется pull. Считывается номер последней выгруженной версии. Выгружаются версии новее её
        :param commit: Помещать в репозиторий
        :return:
        """
        logger.info('============================================')
        logger.info('==== Выгрузка новых версий в GIT')
        logger.info('============================================\n')
        if self.export_to_remote_repo:
            self.repo.pull()
        start_version = 0
        if os.path.exists(self.__last_version_file()):
            with open(self.__last_version_file(), 'r') as f:
                try:
                    start_version = int(f.readline())
                except:
                    logger.critical('Не удалось определить версию предидущей выгрузки')
                    return False
        logger.info('Последная выгруженная версия: %s' % start_version)
        start_version += 1
        self.__before_export()
        logger.info('Последная версия в хранилище: %s' % max(self.reader.versions))
        self.export_versions(start_version, commit=commit)
        return True


logger = logging.getLogger('MNG')
