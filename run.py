import subprocess
import logging
import time
from mng import Mng
import sys
import os


def print_help():
    print('''
python run.py [init|export|help] <config_file>')
    init - инициализация локального репозитория, подготовка данных
    export - выгрузка версий в git
    help - выводит эту справку
''')

t1 = time.time()

argv = [arg.lower() for arg in sys.argv[1:]]
if len(argv) != 2 or argv[0] == 'help':
    print_help()
    sys.exit(0)
else:
    command = sys.argv[1]
    config_file = sys.argv[2]
    if not os.path.exists(config_file):
        raise 'Файл настроек не существует'
    if command != 'init' and command != 'export':
        raise 'Неизвестная команда'

success = False
try:
    mng = Mng(config_file=config_file)
    if command == 'init':
        success = mng.init_repo(True)
    elif command == 'export':
        success = mng.export_new()
    else:
        raise 'Неизвестная команда'
except:
    logging.exception('Выгрузка версий')

logging.info('export delay: %s sec.' % (time.time() - t1))
sys.exit(0 if success else 1)
