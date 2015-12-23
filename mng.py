from cfg_tools import store_reader as store_reader
from git_mng import GitMng
import logging
import configparser
import datetime
import os


class Mng:

    def __init__(self, config_file=None, path=None, store_path=None, remote_url=None):
        if config_file:
            self.__load_config(config_file)
        else:
            self.local_repo = path
            self.store_path = store_path
            self.remote_repo_url = remote_url
        self.reader = None
        self.repo = GitMng(self.local_repo, self.remote_repo_url)

    def __init_reader(self):
        if self.reader is None:
            self.reader = store_reader.StoreReader(self.store_path)
            self.reader.read()
            self.reader.read_versions()

    def __commit(self, version_info):
        self.repo.add()
        self.repo.commit(version=version_info['verion'],
                         msg=version_info['comment'] if version_info['comment'] is not None else '<no comment>',
                         author=version_info['user'].present,
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


    @staticmethod
    def init_log(log_level, file_name=None):
        logging.basicConfig(level=log_level,
                            format='%(asctime)-15s %(levelname)7s: %(name)5s: %(message)s',
                            filename=file_name)

    def init_repo(self, check_exist=True):
        if check_exist and os.path.exists(os.path.join(self.local_repo, '.git')):
            return
        self.repo.init()
        self.repo.pull()
        with open(os.path.join(self.local_repo, '.gitignore'), 'w+') as f:
            f.write('# Service files')
            f.write('authors.txt')
            f.write('last_version.txt')
            f.close()

    def read_versions(self):
        self.__init_reader()
        return self.reader.versions

    def export_version(self, version, commit=False):
        self.__init_reader()
        version_info = self.reader.versions[version]
        self.reader.export_version(version, self.local_repo, True)
        if commit:
            self.__commit(version_info)

    def export_versions(self, start_version, last_version=9999999, commit=True):
        self.__init_reader()
        for v in sorted(self.reader.versions):
            if start_version <= v <= last_version:
                version_info = self.reader.versions[v]
                self.reader.export_version(v, self.local_repo, True)
                if commit:
                    self.__commit(version_info)

