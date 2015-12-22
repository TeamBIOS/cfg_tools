import logging
import time
from mng import Mng
import sys
import getopt


def print_help(error=True):
    print(' '.join([
        __file__,
        'init|export',
        ' '.join(['[-%s|--%s <%s>]' % (item[0][0], item[1][:-1], item[2])
                  if len(item[0]) == 2 else
                  '[-%s|--%s]' % (item[0][0], item[1]) for item in valid_args
                  ]),
        '<store_path>',
        '<local_repositiry_path>',
        '<remote_url>'
    ]))
    for item in valid_args:
        print('\t-%s: %s' % (item[0][0], item[1] + ' ' + item[2] if item[1] else item[2]))
    sys.exit(2 if error else 0)


def init():
    print('init')


def export():
    print('export')


t1 = time.time()

valid_args = [
    ['h', '', 'help info'],
    ['e', '', 'export versions for last'],
    ['v:', 'number', 'exporting version'],
    ['f:', 'string', 'log file'],
    ['l:', 'DEBUG|INFO|ERROR', 'log level']
]


if len(sys.argv) > 2 and sys.argv[1] in ['init', 'export']:
    argv = sys.argv[2:]
    command = sys.argv[1]
else:
    argv = sys.argv[1:]
    command = None


try:
    opts, args = getopt.getopt(argv, ''.join([item[0] for item in valid_args]))
except getopt.GetoptError:
    print_help()
    sys.exit(2)

args_dict = {opt[1]: arg.lower() for opt, arg in opts}

if len(args):
    args_dict['store'] = args[0]
if len(args) >= 2:
    args_dict['local_git'] = args[1]
if len(args) >= 3:
    args_dict['remote_git'] = args[2]

if command is None or len(args_dict) == 0 or '-h' in args_dict:
    print_help()
    sys.exit(0)

log_level = logging.INFO
if 'l' in args_dict:
    val = args_dict['l']
    if val == 'DEBUG':
        log_level = logging.DEBUG
    elif val == 'INFO':
        log_level = logging.INFO
    elif val == 'ERROR':
        log_level = logging.ERROR

if 'f' in args_dict:
    logging.basicConfig(level=log_level,
                        format='%(asctime)-15s %(levelname)7s: %(name)5s: %(message)s',
                        filename=args_dict['f'])
else:
    logging.basicConfig(level=log_level,
                        format='%(asctime)-15s %(levelname)7s: %(name)5s: %(message)s')

if len(args) >= 2:
    mng = Mng(args_dict['local_git'],
              args_dict['store'],
              args_dict.get('remote_git', ''))
else:
    print_help()

if command == 'init':
    mng.init_repo()

elif command == 'export':
    if len(args) == 3:
        version = 0
        if 'v' in args_dict:
            version = int(args_dict['v'])
        else:
            version = 0

        if 'e' in args_dict:
            mng.repo.pull()
            mng.export_versions(version if version else 1)
        elif version:
            mng.repo.pull()
            mng.export_version(version, True)
        mng.repo.push()

    else:
        print_help()

logging.info('export delay: %s sec.' % (time.time() - t1))
