import logging
import time
from mng import Mng
from cfg_tools.store_reader import StoreReader
from cfg_tools import utils


t1 = time.time()

logging.basicConfig(level=logging.DEBUG)
mng = Mng(
          r'C:\store\apecs_repo',
          r'C:\store\apecs_store\1cv8ddb.1CD',
          r'git@dzhigit.bios.guru:autoprodix/Apecs.git'
)
# mng.init_repo()
mng.export_versions(3730, 99999, True)
mng.repo.push()


logging.info('export delay: %s sec.' % (time.time() - t1))
