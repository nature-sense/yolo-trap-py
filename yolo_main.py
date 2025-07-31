import asyncio
import logging

from aiomultiprocess import Process, Pool

from camera_process.process import CameraProcess
from control_process.process import ControlProcess

def setup_logging(level=logging.DEBUG):
    logging.basicConfig(level=level)

async def main() :
    logger = logging.getLogger()

    control_process = Process(target=ControlProcess().start_services, initializer=setup_logging)
    control_process.start()
    camera_process = Process(target=CameraProcess().start_services, initializer=setup_logging)
    camera_process.start()
    await control_process.join()
    await camera_process.join()

if __name__ == "__main__":
    asyncio.run(main())