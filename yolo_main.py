import asyncio
import configparser
import logging
import os

from aiomultiprocess import Process, Pool

from camera_process.camera_ahq import CameraAhq
from camera_process.camera_picam3 import CameraPicam3
from camera_process.process import CameraProcess
from control_process.process import ControlProcess
from settings.settings_manager import SettingsManager


def setup_logging(level=logging.DEBUG):
    logging.basicConfig(level=level)

async def main() :
    logger = logging.getLogger()

    camera_name = "picamera3"
    camera = CameraPicam3()

    config = configparser.ConfigParser()
    if os.path.exists('config.ini') :
        config.read('config.ini')
        camera_name = config["trap"]["camera"]

    if camera_name == "arducam-hq" :
        camera = CameraAhq()

    settings = SettingsManager()

    print(f"Camera {camera_name}")
    control_process = Process(target=ControlProcess(settings).start_services, initializer=setup_logging)
    control_process.start()
    camera_process = Process(target=CameraProcess(settings, camera).start_services, initializer=setup_logging)
    camera_process.start()
    await control_process.join()
    await camera_process.join()

if __name__ == "__main__":
    asyncio.run(main())