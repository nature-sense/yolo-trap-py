import os
from abc import ABC

import cv2

from session.stream_session_client import StreamSessionClient


class StreamFlow(ABC):

    def __init__(self, main_size):
        os.environ['LIBCAMERA_LOG_LEVELS'] = '4'
        self.main_size = main_size
        self.session_client = StreamSessionClient()

    def stream_task(self):
        pass

    def stream_to_session(self, timestamp, frame):
        self.session_client.stream_frame(timestamp, frame)

    def to_jpeg(self, img):
        is_success, im_buf = cv2.imencode(".jpg", img.array)
        if is_success:
            return im_buf.tobytes()
        else:
            return None