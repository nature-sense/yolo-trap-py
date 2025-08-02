import logging
from libcamera import controls

from camera_process.camera import Camera

class CameraPicam3(Camera) :
    def __init__(self):
        super().__init__()

    def setup(self, picam2, camera_config) :
        self.picam2 = picam2
        self.picam2.set_controls({"AfMode": controls.AfModeEnum.Continuous})
        self.picam2.video_configuration.controls.FrameRate = 10.0

        # self.picam2.set_controls({"AfRange": controls.AfRangeEnum.Macro})
        # self.picam2.set_controls({"AfMode": controls.AfModeEnum.Manual, "LensPosition": 0})  # 2.0})
        self.picam2.start(camera_config)
        success = False
        retry = 0
        while not success and retry < 10:
            success = self.picam2.autofocus_cycle()
            logging.debug(f"autofocus result {success}")
            retry += 1

    async def control(self, msg):
        pass