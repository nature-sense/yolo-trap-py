from camera_process.camera import Camera

class CameraAhq(Camera) :
    def __init__(self):
        super().__init__()

    def setup(self, picam2, camera_config) :
        self.picam2 = picam2
        #self.picam2.set_controls({"AfMode": controls.AfModeEnum.Continuous})
        #self.picam2.video_configuration.controls.FrameRate = 10.0

        # self.picam2.set_controls({"AfRange": controls.AfRangeEnum.Macro})
        # self.picam2.set_controls({"AfMode": controls.AfModeEnum.Manual, "LensPosition": 0})  # 2.0})
        self.picam2.start(camera_config)

    async def control(self, msg):
        pass