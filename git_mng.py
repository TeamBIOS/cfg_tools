import logging
import subprocess
import os
import tempfile


logger = None


class GitMng:

    def __init__(self, path, remote_url):
        self.path = path
        self.remote_url = remote_url

    def __execute_cmd(self, cmd_command):
        os.chdir(self.path)
        logger.debug('Executing "%s"' % cmd_command)
        pr = subprocess.Popen(cmd_command,
                              shell=True,
                              stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE)
        while pr.returncode is None:
            stdpip = None
            try:
                stdpip = pr.communicate(None, 1)
            except subprocess.TimeoutExpired:
                pass
            # if stdpip is not None:
            #     logger.debug('stdout: %s' % stdpip[0].decode())
            # else:
            #     logger.debug('stdout: %s' % pr.stdout.readline().decode())
        logger.debug('Exit code: %s' % pr.returncode)
        if pr.returncode:
            logger.error(stdpip[1].decode())
        else:
            logger.debug(stdpip[0].decode())
        # if err:
        #     logger.error('Executed "%s"\n%s\n%s' % (cmd_command, msg.decode(), err.decode()))
        # else:
        #     logger.debug('%s' % msg.decode())
        # return msg, err
        return pr.returncode

    def init(self):
        exit_code = self.__execute_cmd('git init')
        if exit_code != 0:
            raise Exception('Не удалось инициализировать репозиторий. Код возврата: %s' % exit_code)
        else:
            logger.info('Инициализирован репозиторий')

    def add(self):
        exit_code = self.__execute_cmd('git add -A .')
        if exit_code != 0:
            raise Exception('Не удалось добавить измения в индекс (git add). Код возврата: %s' % exit_code)

    def commit(self, version, msg, author, email, date):
        os.environ['GIT_AUTHOR_DATE'] = date.strftime('"%Y-%m-%d %H:%M:%S"')
        os.environ['GIT_COMMITTER_DATE'] = date.strftime('"%Y-%m-%d %H:%M:%S"')
        comment_file = tempfile.NamedTemporaryFile(mode='w',
                                                   delete=False,
                                                   encoding='utf-8')
        msg = 'Version %s. %s' % (version, msg)
        comment_file.write(msg)
        comment_file.close()
        logger.debug('Message %s' % msg)
        exit_code = self.__execute_cmd('git commit -a --file="%s" --author "%s <%s>"' % (comment_file.name, author, email))
        os.unlink(comment_file.name)
        if exit_code != 0:
            raise Exception('Не удалось зафиксировать изменения (commit). Код возврата: %s' % exit_code)

    def push(self):
        self.gc()
        logger.info('Отправка данных в центральный репозиторий')
        exit_code = self.__execute_cmd('git push -u --all -v %s' % self.remote_url)
        if exit_code!= 0:
            raise Exception('Не удалось отправить данные в центральный репозиторий. Код возврата: %s' % exit_code)

    def pull(self):
        exit_code = self.__execute_cmd('git pull -v %s' % self.remote_url)
        if exit_code != 0:
            raise Exception('Не удалось получить данные из центрального репозитория. Код возврата: %s' % exit_code)
        logger.info('Получены данные из центрального репозитория')

    def gc(self):
        if self.__execute_cmd('git gc --auto') != 0:
            raise Exception('Не удалось выполнить сборку мусора')


logger = logging.getLogger('GIT')
