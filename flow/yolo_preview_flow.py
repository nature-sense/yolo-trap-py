import logging
import time
from datetime import datetime

from libcamera import controls
from picamera2 import MappedArray, Picamera2

from flow.stream_flow import StreamFlow

FRAME_INTERVAL_SECONDS = 4

class YoloPreviewFlow(StreamFlow):

    def __init__(self, main_size):
        self.picam2 = Picamera2()
        self.logger = logging.getLogger()

        super().__init__(main_size)

    def stream_task(self):
        print("FLOW TASK")
        camera_config = self.picam2.create_preview_configuration(
            main={'format': 'RGB888', 'size': self.main_size},
        )

        self.picam2.configure(camera_config)
        self.picam2.set_controls({"AfMode": controls.AfModeEnum.Continuous})
        #self.picam2.set_controls({"AfMode": controls.AfModeEnum.Manual, "LensPosition": 0})  # 2.0})
        self.picam2.start(camera_config)

        while True:
            request = self.picam2.capture_request()
            current_datetime = datetime.now()
            current_timestamp_ms = int(current_datetime.timestamp() * 1000)

            self.logger.debug("Got frame!");
            with MappedArray(request, 'main') as m:
                jpg_img = self.to_jpeg(m)
                if jpg_img is not None :
                    self.stream_to_session(current_timestamp_ms, jpg_img)
            request.release()
            time.sleep(FRAME_INTERVAL_SECONDS)




