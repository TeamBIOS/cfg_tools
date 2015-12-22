from cfg_tools import store_reader as store_reader
from git_mng import GitMng


class Mng:

    def __init__(self, path, store_path, remote_url):
        self.path = path
        self.store_path = store_path
        self.reader = None
        self.repo = GitMng(path, remote_url)

    def __init_reader(self):
        if self.reader is None:
            self.reader = store_reader.StoreReader(self.store_path)
            self.reader.read()
            self.reader.read_versions()

    def __commit(self, version_info):
        self.repo.add()
        self.repo.commit(version=version,
                         msg=version_info['comment'],
                         author=version_info['user'].present,
                         email=version_info['user'].email,
                         date=version_info['date'])
    def init_repo(self):
        self.repo.init()
    def export_version(self, version, commit=False):
        self.__init_reader()
        version_info = self.reader.versions[version]
        self.reader.export_version(version, self.path, True)
        if commit:
            self.__commit(version_info)

    def export_versions(self, start_version, last_version=9999999, commit=True):
        self.__init_reader()
        for v in sorted(self.reader.versions):
            if start_version <= v <= last_version:
                version_info = self.reader.versions[v]
                self.reader.export_version(v, self.path, True)
                if commit:
                    self.__commit(version_info)

