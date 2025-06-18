import os
from abc import ABC, abstractmethod
from datetime import datetime

import cv2

from session.detection_metadata import DetectionMetadata
from session.detection_session_client import DetectionSessionClient


class DetectSessionClient:
    pass


class DetectFlow(ABC):

    def __init__(self, min_score, lores_size, main_size, model,max_tracking):
        os.environ['LIBCAMERA_LOG_LEVELS'] = '4'

        #self.session = session_manager.new_session()
        self.min_score = min_score
        self.lores_size = lores_size
        self.main_size = main_size
        self.model = model

        now = datetime.now()
        self.current_session = now.strftime("%Y%d%m%H%M%S")
        self.session_client = DetectionSessionClient(max_tracking, self.current_session)

    @abstractmethod
    def flow_task(self):
        pass

    def save_detections(self, frame, detections):
        for box, track_id, score, clazz in detections:

            scaled_box = self.scale(box)
            print("scaled-box", scaled_box)
            x0, y0, x1, y1 = scaled_box
            img_width = x1-x0
            img_height = y1-y0

            metadata = self.session_client.get_detection_metadata(track_id)
            current_datetime = datetime.now()
            current_timestamp_ms = int(current_datetime.timestamp() * 1000)

            if metadata is None:
                current_metadata = DetectionMetadata(
                    self.current_session,
                    track_id,
                    current_timestamp_ms,
                    current_timestamp_ms,
                    score,
                    clazz,
                    img_width,
                    img_height
                )
                crop = self.to_jpeg(frame.array[y0:y1, x0:x1])
                self.session_client.new_detection(current_metadata, crop)

            else :
                if score > metadata.score :
                    metadata.score = score
                    metadata.updated = current_timestamp_ms
                    metadata.width = img_width
                    metadata.height = img_height

                    crop = self.to_jpeg(frame.array[y0:y1, x0:x1])
                    self.session_client.update_detection(metadata, crop)

                else:
                    metadata.updated = current_timestamp_ms
                    self.session_client.update_detection_meta(metadata)


    def scale(self, rect):
        s_w, s_h = self.lores_size
        d_w, d_h = self.main_size
        x0, y0, x1, y1 = rect
        x_scale = d_w / s_w
        y_scale = d_h / s_h
        return int(x0 * x_scale), int(y0 * y_scale), int(x1 * x_scale), int(y1 * y_scale)

    def to_jpeg(self, img):
        is_success, im_buf = cv2.imencode(".jpg", img)
        if is_success:
            return im_buf.tobytes()
        else:
            return None

