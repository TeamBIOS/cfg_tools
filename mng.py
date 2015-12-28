from cfg_tools import store_reader as store_reader
from git_mng import GitMng
import logging
import configparser
import datetime
import os


class Mng:

    push_step = 0

    @staticmethod
    def init_log(log_level, file_name=None):
        logging.basicConfig(level=log_level,
                            format='%(asctime)-15s %(levelname)7s: %(name)5s: %(message)s',
                            handlers=[logging.StreamHandler()
                                      if file_name is None else
                                      logging.FileHandler(file_name, encoding='utf-8')])

    def __init__(self, config_file=None, path=None, store_path=None, remote_url=None):
        self.local_repo = None
        self.store_path = None
        self.remote_repo_url = None
        if config_file:
            self.__load_config(config_file)
        else:
            self.local_repo = path
            self.store_path = store_path
            self.remote_repo_url = remote_url
        self.export_to_remote_repo = True if self.remote_repo_url else False
        self.reader = None
        self.repo = GitMng(self.local_repo, self.remote_repo_url)

    def __init_reader(self):
        if self.reader is None:
            self.reader = store_reader.StoreReader(self.store_path)

    def __before_export(self):
        if not os.path.exists(os.path.join(self.local_repo, '.git')):
            logger.error('Не найден репозиторий. Для создания репозитория используйте команду "init"')

        self.load_authors()
        self.read_versions()

    def __commit(self, version_info):
        self.repo.add()
        self.repo.commit(version=version_info['verion'],
                         msg=version_info['comment'] if version_info['comment'] is not None else '<no comment>',
                         author=version_info['user'].git_name,
                         email=version_info['user'].email,
                         date=version_info['date'])

    def __load_config(self, file_name):
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

    def __save_exported_version_info(self, version):
        with open(self.__last_version_file(), 'w') as f:
            f.write(str(version))
            f.close()

    def __last_version_file(self):
        return os.path.join(self.local_repo, 'last_version.txt')

    def __export_version(self, version, commit=True):
        version_info = self.reader.versions[version]
        logger.info('================================== Export version: %s' % version)
        logger.debug(str(version_info))
        self.reader.export_version(version, self.local_repo, True)
        self.__save_exported_version_info(version)
        if commit:
            self.__commit(version_info)

    def init_repo(self, check_exist=True):
        if check_exist and os.path.exists(os.path.join(self.local_repo, '.git')):
            logger.info('Репозиторий уже существует, инициализация не выполнена')
            return
        self.repo.init()
        if self.export_to_remote_repo:
            self.repo.pull()
        logger.info('Репозиторий инициализирован')
        with open(os.path.join(self.local_repo, '.gitignore'), 'w+') as f:
            f.write('# Service files')
            f.write('authors.csv')
            f.close()
        self.load_authors()

    def load_authors(self):
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
        self.__init_reader()
        self.reader.read_versions()
        return self.reader.versions

    def export_version(self, version, commit=True):
        self.__before_export()
        self.__export_version(version, commit)

    def export_versions(self, start_version, last_version=9999999, commit=True):
        self.__before_export()
        count = 0
        for v in sorted(self.reader.versions):
            if start_version <= v <= last_version:
                self.__export_version(v, commit)
                count += 1
                if self.push_step and count == self.push_step:
                    count = 0
                    if self.export_to_remote_repo:
                        self.repo.push()
        if self.export_to_remote_repo:
            self.repo.push()

    def export_new(self):
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
        self.export_versions(start_version)
        return True


logger = logging.getLogger('MNG')
