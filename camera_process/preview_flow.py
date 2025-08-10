import logging
import time
import cv2

from datetime import datetime
from libcamera import controls
from picamera2 import MappedArray, Picamera2
from picologging import exception

from camera_process.camera_flow import CameraFlow
from ipc.active_flow import ActiveFlow
from ipc.session_messages import FrameMessage, ActiveFlowMessage

FRAME_INTERVAL_SECONDS = 2
PREVIEW_SIZE = (320,240)

class PreviewFlow(CameraFlow):

    name = "preview_flow"

    def __init__(self, ipc_client, camera, settings):
        super().__init__(ipc_client, camera, settings)

    async def init_camera(self):
        logging.debug("PREVIEW TASK")
        msg = ActiveFlowMessage(ActiveFlow.PREVIEW_FLOW).to_proto()
        await self.ipc_client.send(msg)

        self.picam2 = Picamera2()
        camera_config = self.picam2.create_preview_configuration(
            main={'format': 'RGB888', 'size': PREVIEW_SIZE },
        )

        self.camera.setup(self.picam2, camera_config)

    async def start_flow(self):
        pass


    async def process_result(self, result):
        logging.debug("Got frame!")
        current_datetime = datetime.now()
        current_timestamp_ms = int(current_datetime.timestamp() * 1000)

        with MappedArray(result, 'main') as m:
            jpg_img = self.to_jpeg(m)
            if jpg_img is not None :
                await self.stream_to_ipc(current_timestamp_ms, jpg_img)
            result.release()
            time.sleep(FRAME_INTERVAL_SECONDS)

    async def close_camera(self):
        self.picam2.stop()
        self.picam2.close()


    async def stream_to_ipc(self, timestamp, frame):
        msg = FrameMessage(timestamp, frame).to_proto()
        logging.debug("Sending frame to session service")
        await self.ipc_client.send(msg)

    def to_jpeg(self, img):
        is_success, im_buf = cv2.imencode(".jpg", img.array)
        if is_success:
            return im_buf.tobytes()
        else:
            return None



