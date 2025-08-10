import asyncio
import logging
import time
import numpy as np
import cv2

from datetime import datetime
from camera_process.camera_flow import CameraFlow
from libcamera import controls
from picamera2 import MappedArray, Picamera2
from ultralytics import YOLO

from camera_process.detections_cache import DetectionsCache
from ipc.active_flow import ActiveFlow
from ipc.detection_metadata import DetectionMetadata
from ipc.session_messages import ActiveFlowMessage

NCNN_MODEL = "./models/insects_320_ncnn_model"
MAIN_SIZE = (2028, 1520)
LORES_SIZE = (320,320)
MAX_DETECTIONS = 20

class DetectFlow(CameraFlow):

    name = "detect_flow"

    def __init__(self, ipc_client, camera, settings):
        super().__init__(ipc_client, camera, settings)

        #os.environ['LIBCAMERA_LOG_LEVELS'] = '4'
        self.model = YOLO(NCNN_MODEL,task="detect")
        self.detections_cache = DetectionsCache(MAX_DETECTIONS, self.ipc_client)
        self.current_session = None

    def do_track(self, array):
        start_model = time.perf_counter()
        results = self.model.track(array)
        end_model = time.perf_counter()
        print("model = ", (end_model - start_model) * 1000)
        return results

    async def init_camera(self):
        logging.debug("FLOW TASK")
        msg = ActiveFlowMessage(ActiveFlow.DETECT_FLOW).to_proto()
        await self.ipc_client.send(msg)

        self.picam2 = Picamera2()
        camera_config = self.picam2.create_preview_configuration(
            main={'format': 'RGB888', 'size': MAIN_SIZE},
            lores={'format': 'RGB888', 'size': LORES_SIZE}
        )

        self.camera.setup(self.picam2, camera_config)

    async def close_camera(self):
        self.picam2.stop()
        self.picam2.close()

    async def start_flow(self):
        logging.debug("Start flow")

        now = datetime.now()
        self.current_session = now.strftime("%Y%m%d%H%M%S")
        await self.detections_cache.new_session(self.current_session)


    async def process_result(self, result):

        while not self.exit:
            start_frame = time.perf_counter()
            #request = self.picam2.capture_request()

            request = await self.get_image()
            #print("GOT REQUEST")

            with MappedArray(request, 'lores') as l:
                with MappedArray(request, 'main') as m:
                    end_frame = time.perf_counter()

                    # run the tracking in a thread
                    results = await self.loop.run_in_executor(None, self.do_track, l.array)

                    try :
                        boxes = results[0].boxes.xyxy.cpu().numpy().astype(np.int32)
                        track_ids = [tid.item() for tid in results[0].boxes.id.int().cpu().numpy()]
                        scores = [s.item() for s in results[0].boxes.conf.numpy()]
                        classes = [c.item() for c in results[0].boxes.cls.numpy().astype(np.int32)]

                        await self.save_detections(m, zip(boxes, track_ids, scores, classes))
                    except AttributeError :
                        logging.debug("NO DATA")
                        await asyncio.sleep(1.0)

            request.release()

    async def save_detections(self, frame, detections):
        for box, track_id, score, clazz in detections:
            min_score = self.settings.get_settings().min_score
            logging.debug(f"score = {score} min-score = {min_score}")

            if score >= min_score :
                scaled_box = self.scale(box)
                logging.debug(f"scaled-box {scaled_box}")
                x0, y0, x1, y1 = scaled_box
                img_width = x1-x0
                img_height = y1-y0

                metadata = self.detections_cache.get_detection_metadata(track_id)
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
                    await self.detections_cache.new_detection(current_metadata, crop)

                else :
                    if score > metadata.score :
                        metadata.score = score
                        metadata.updated = current_timestamp_ms
                        metadata.width = img_width
                        metadata.height = img_height

                        crop = self.to_jpeg(frame.array[y0:y1, x0:x1])
                        await self.detections_cache.update_detection(metadata, crop)

                    else:
                        metadata.updated = current_timestamp_ms
                        #await self.detections_cache.update_detection_meta(metadata)


    def scale(self, rect):
        s_w, s_h = LORES_SIZE
        d_w, d_h = MAIN_SIZE
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
