import logging
import subprocess
import os
import tempfile


logger = None


class GitMng:

    def __init__(self, path, remoute_url):
        self.path = path
        self.remote_url = remoute_url

    def __execute_cmd(self, cmd_command, verbose=True):
        os.chdir(self.path)
        pr = subprocess.Popen(cmd_command,
                              shell=True,
                              stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE)
        msg = pr.stdout.read()
        err = pr.stderr.read()
        txt = msg if msg else err
        if err:
            logger.error("Executing '%s'\n%s" % (cmd_command, err.decode()))
        else:
            logger.debug("Executing '%s'\n%s" % (cmd_command, msg.decode()))
        return msg, err

    def init(self):
        self.__execute_cmd('git init')

    def add(self):
        self.__execute_cmd('git add -A .')

    def commit(self, version, msg, author, email, date):
        os.environ['GIT_AUTHOR_DATE'] = date.strftime('"%Y-%m-%d %H:%M:%S"')
        os.environ['GIT_COMMITTER_DATE'] = date.strftime('"%Y-%m-%d %H:%M:%S"')
        comment_file = tempfile.NamedTemporaryFile(mode='w', delete=False)
        msg = 'Version %s. %s' % (version, msg)
        comment_file.write(msg)
        comment_file.close()
        logger.debug('Message %s' % msg)
        self.__execute_cmd('git commit -a --file="%s" --author "%s <%s>"' % (comment_file.name, author, email))
        os.unlink(comment_file.name)

    def push(self):
        self.__execute_cmd('git push -u --all -v %s' % self.remoute_url)
        pass

    def pull(self):
        self.__execute_cmd('git pull -v %s' % self.remoute_url)

logger = logging.getLogger('GIT')
