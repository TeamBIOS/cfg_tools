import subprocess
import logging
import time
from mng import Mng
import sys
import os


def init(args):
    mng = Mng(config_file=args[1])
    try:
        for i in range(2, len(argv)):
            arg = argv[i].split('=')
            if len(arg) == 2:
                if arg[0] == 'use_pull':
                    mng.use_pull = bool(arg[1]) and mng.export_to_remote_repo
    except:
        print('Error: Ошибка рабора параметров')
        return False
    return mng.init_repo(True)


def export(args):
    mng = Mng(config_file=args[1])
    try:
        for i in range(2, len(argv)):
            arg = argv[i].split('=')
            if len(arg) == 2:
                if arg[0] == 'use_pull':
                    mng.use_pull = bool(arg[1]) and mng.export_to_remote_repo
    except:
        print('Error: Ошибка рабора параметров')
        return False
    return mng.export_new()


def show_help():
    print('python run.py [%s] <config_file>)' % '|'.join(commands))
    for key, info in commands.items():
        print('%s - %s' % (key, info['description']))
    pass


commands = {
    'init': {
        'func': init,
        'description': 'инициализация локального репозитория, подготовка данных',
        'need_config': True
    },
    'export': {
        'func': export,
        'description': 'выгрузка версий в git',
        'need_config': True
    },
    'help': {
        'func': show_help,
        'description': 'выводит эту справку',
        'need_config': False
    }
}

t1 = time.time()

argv = [arg.lower() for arg in sys.argv[1:]]

if len(argv) == 0:
    show_help()
    sys.exit(0)

if argv[0] not in commands:
    print('Error: Неизвестная команда')
    show_help()
    sys.exit(1)

command_name = argv[0]
command = commands[command_name]

if command['need_config'] and len(argv) == 1:
    print('Error: Не указан файл конфигурации')
    show_help()
    sys.exit(1)

success = False
if command['need_config']:
    config_file = argv[1]
    if not os.path.exists(config_file):
        print('Error: Не найден файл конфигурации')
        show_help()
        sys.exit(1)
    try:
        success = command['func'](argv)
    except:
        print('Выполение команды %s' % command_name)
else:
    try:
        success = command['func']()
    except:
        print('Выполение команды %s' % command_name)

logging.info('export delay: %s sec.' % (time.time() - t1))
sys.exit(0 if success else 1)
